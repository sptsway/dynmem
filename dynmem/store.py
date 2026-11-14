"""Memory store: vector database plus metadata.

`MemoryStore` is the interface. `QdrantStore` is the default backend (local mode, no Docker).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Protocol, Sequence

import numpy as np

OPEN_END = 1e18  # valid_to / t_end sentinel for "still valid"


@dataclass
class Entry:
    id: int
    text: str
    t_start: float
    t_end: float
    position: tuple[float, float, float]
    embedding: np.ndarray | None = field(default=None, repr=False)
    object: str | None = None
    instance: str | None = None
    valid_from: float = 0.0
    valid_to: float = OPEN_END
    superseded_by: int | None = None
    source: str = "caption"  # caption | gt_event | pred_event
    episode_id: str = ""

    def payload(self) -> dict:
        d = asdict(self)
        d.pop("embedding")
        x, y, z = d.pop("position")
        return {**d, "x": x, "y": y, "z": z}

    @classmethod
    def from_payload(cls, p: dict) -> "Entry":
        p = dict(p)
        pos = (p.pop("x"), p.pop("y"), p.pop("z"))
        return cls(position=pos, **p)


class MemoryStore(Protocol):
    def add(self, entries: Sequence[Entry]) -> None: ...
    def search(self, vector: np.ndarray | None, k: int, *, time_range: tuple[float, float] | None = None,
               position: Sequence[float] | None = None, radius: float | None = None,
               object: str | None = None, valid_at: float | None = None,
               source: str | None = None) -> list[tuple[Entry, float | None]]: ...
    def update(self, entry_id: int, **fields) -> None: ...
    def delete(self, entry_ids: Sequence[int]) -> None: ...
    def all(self) -> list[Entry]: ...
    def count(self) -> int: ...


class QdrantStore:
    OVERFETCH = 5  # candidates fetched per requested hit when a radial post-filter is applied

    def __init__(self, dim: int, path: str | None = None, collection: str = "memory"):
        from qdrant_client import QdrantClient, models
        self.m = models
        self.client = QdrantClient(path=path) if path else QdrantClient(":memory:")
        self.collection = collection
        if self.client.collection_exists(collection):
            self.client.delete_collection(collection)
        self.client.create_collection(
            collection, vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE))
        self.dim = dim

    def add(self, entries: Sequence[Entry]) -> None:
        pts = []
        for e in entries:
            if e.embedding is None or len(e.embedding) != self.dim:
                raise ValueError(f"entry {e.id} needs an embedding of dim {self.dim}")
            pts.append(self.m.PointStruct(id=e.id, vector=np.asarray(e.embedding, dtype=float).tolist(),
                                          payload=e.payload()))
        self.client.upsert(self.collection, pts)

    def _filter(self, time_range, position, radius, object, valid_at, source):
        m, must = self.m, []
        if time_range is not None:
            a, b = time_range  # entry overlaps [a, b]
            must += [m.FieldCondition(key="t_start", range=m.Range(lte=b)),
                     m.FieldCondition(key="t_end", range=m.Range(gte=a))]
        if position is not None and radius is not None:
            for key, c in zip("xyz", position):
                must.append(m.FieldCondition(key=key, range=m.Range(gte=c - radius, lte=c + radius)))
        if object is not None:
            must.append(m.FieldCondition(key="object", match=m.MatchValue(value=object)))
        if source is not None:
            must.append(m.FieldCondition(key="source", match=m.MatchValue(value=source)))
        if valid_at is not None:
            must += [m.FieldCondition(key="valid_from", range=m.Range(lte=valid_at)),
                     m.FieldCondition(key="valid_to", range=m.Range(gt=valid_at))]
        return m.Filter(must=must) if must else None

    def search(self, vector, k, *, time_range=None, position=None, radius=None,
               object=None, valid_at=None, source=None):
        flt = self._filter(time_range, position, radius, object, valid_at, source)
        radial = position is not None and radius is not None
        limit = k * self.OVERFETCH if radial else k
        if vector is not None:
            res = self.client.query_points(self.collection, query=np.asarray(vector, dtype=float).tolist(),
                                           query_filter=flt, limit=limit, with_payload=True).points
            hits = [(Entry.from_payload(r.payload), r.score) for r in res]
        else:  # filter-only: ordered by t_start
            pts, _ = self.client.scroll(self.collection, scroll_filter=flt, limit=max(limit, 1_000_000), with_payload=True)
            hits = sorted(((Entry.from_payload(p.payload), None) for p in pts), key=lambda h: h[0].t_start)
        if radial:
            hits = [h for h in hits if math.dist(h[0].position, position) <= radius]
        return hits[:k]

    def update(self, entry_id: int, **fields) -> None:
        payload = dict(fields)
        if "position" in payload:
            payload["x"], payload["y"], payload["z"] = payload.pop("position")
        self.client.set_payload(self.collection, payload=payload, points=[entry_id])

    def delete(self, entry_ids: Sequence[int]) -> None:
        self.client.delete(self.collection, points_selector=self.m.PointIdsList(points=list(entry_ids)))

    def all(self) -> list[Entry]:
        pts, _ = self.client.scroll(self.collection, limit=10_000_000, with_payload=True)
        return sorted((Entry.from_payload(p.payload) for p in pts), key=lambda e: e.id)

    def count(self) -> int:
        return self.client.count(self.collection).count
