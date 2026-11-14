"""Retrieval tools over the memory store (section 6 of the plan).

`Toolbox.specs(names)` gives provider-neutral function declarations.
`Toolbox.call(name, args)` runs a tool and returns a compact text result plus the entry ids.
"""
from __future__ import annotations

import math
from typing import Callable, Sequence

import numpy as np

from dynmem.store import OPEN_END, Entry, MemoryStore

XYZ = {"type": "array", "items": {"type": "number"}, "description": "[x, y, z] in metres"}
RANGE = {"type": "array", "items": {"type": "number"}, "description": "[t_start, t_end] in seconds"}

SPECS = {
    "search_text": {
        "description": "Semantic search over memory entries by text similarity only.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "k": {"type": "integer"}}, "required": ["query"]},
    },
    "search_time": {
        "description": ("Memory entries whose time span overlaps a time or a [t_start, t_end] range (seconds), ordered by time. "
                        "Entries describe past events, so to include everything up to now use a range that starts at 0."),
        "parameters": {"type": "object", "properties": {
            "time_or_range": {"type": "array", "items": {"type": "number"},
                              "description": "[t] or [t_start, t_end] in seconds"},
            "k": {"type": "integer"}}, "required": ["time_or_range"]},
    },
    "search_position": {
        "description": "Memory entries whose position lies within `radius` metres of xyz.",
        "parameters": {"type": "object", "properties": {
            "xyz": XYZ, "radius": {"type": "number"}, "k": {"type": "integer"}},
            "required": ["xyz", "radius"]},
    },
    "search": {
        "description": ("Composed search: text similarity plus any of time range, position and radius, "
                        "object name, in one call. Omit the filters you do not need (do not pass null). "
                        "time_range keeps entries whose time span overlaps it; use [0, now] to include all past entries. "
                        "position needs a radius."),
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "time_range": RANGE, "position": XYZ,
            "radius": {"type": "number"}, "object": {"type": "string"}, "k": {"type": "integer"}}},
    },
    "object_history": {
        "description": "All stored versions of one object, ordered by time.",
        "parameters": {"type": "object", "properties": {"object": {"type": "string"}}, "required": ["object"]},
    },
    "nearest_instance": {
        "description": "The closest static scene instance (label and position) to xyz.",
        "parameters": {"type": "object", "properties": {"xyz": XYZ}, "required": ["xyz"]},
    },
}


def clean_args(args: dict) -> dict:
    """Models often send explicit nulls for optional arguments. Treat those as absent."""
    out = {}
    for k, v in args.items():
        if v is None or (isinstance(v, (list, tuple)) and (not v or any(x is None for x in v))):
            continue
        out[k] = v
    return out


def _as_range(r):
    """[t] -> (t, t); [a, b] -> (a, b); anything else raises ValueError."""
    if not r:
        return None
    r = [float(x) for x in r]
    if len(r) == 1:
        return (r[0], r[0])
    if len(r) == 2:
        return (r[0], r[1])
    raise ValueError("time_range needs 1 or 2 numbers")


def format_entry(e: Entry) -> str:
    valid = "" if e.valid_to >= OPEN_END else f" valid_until={e.valid_to:.0f}s"
    obj = f" object={e.object}" if e.object else ""
    pos = f"({e.position[0]:.2f}, {e.position[1]:.2f}, {e.position[2]:.2f})"
    return f"[{e.id}] t={e.t_start:.0f}-{e.t_end:.0f}s pos={pos}{obj}{valid}: {e.text}"


class Toolbox:
    def __init__(self, store: MemoryStore, embed_query: Callable[[str], np.ndarray],
                 instances: Sequence[tuple[str, Sequence[float]]] | None = None, default_k: int = 5):
        self.store, self.embed_query, self.instances, self.default_k = store, embed_query, instances, default_k

    def specs(self, names: Sequence[str]) -> list[dict]:
        return [{"name": n, **SPECS[n]} for n in names]

    def call(self, name: str, args: dict) -> tuple[str, list[int]]:
        fn = getattr(self, f"_{name}", None)
        if fn is None or name not in SPECS:
            return f"error: unknown tool {name!r}", []
        args = clean_args(args)
        try:
            entries = fn(**args)
        except (TypeError, ValueError, KeyError, IndexError) as exc:  # arguments come from a model
            return f"error: bad arguments ({type(exc).__name__}: {exc})", []
        if isinstance(entries, str):
            return entries, []
        if not entries:
            return "no results", []
        return "\n".join(format_entry(e) for e in entries), [e.id for e in entries]

    def _vec(self, query):
        return self.embed_query(query) if query else None

    def _search_text(self, query, k=None):
        return [e for e, _ in self.store.search(self._vec(query), k or self.default_k)]

    def _search_time(self, time_or_range, k=None):
        k = k or self.default_k
        a, b = (time_or_range[0], time_or_range[0]) if len(time_or_range) == 1 else time_or_range[:2]
        hits = [e for e, _ in self.store.search(None, k, time_range=(a, b))]
        if hits:
            return hits
        mid = (a + b) / 2  # nothing overlaps: fall back to the nearest entries in time
        return sorted(self.store.all(), key=lambda e: abs((e.t_start + e.t_end) / 2 - mid))[:k]

    def _search_position(self, xyz, radius, k=None):
        return [e for e, _ in self.store.search(None, k or self.default_k, position=xyz, radius=radius)]

    def _search(self, query=None, time_range=None, position=None, radius=None, object=None, k=None):
        if position is not None and radius is None:
            return "error: position needs a radius"
        hits = self.store.search(self._vec(query), k or self.default_k,
                                 time_range=_as_range(time_range),
                                 position=position, radius=radius, object=object)
        return [e for e, _ in hits]

    def _object_history(self, object):
        return sorted((e for e in self.store.all() if e.object == object), key=lambda e: (e.valid_from, e.id))

    def _nearest_instance(self, xyz):
        if not self.instances:
            return "no static instances available"
        label, pos = min(self.instances, key=lambda i: math.dist(i[1], xyz))
        return f"nearest instance: {label} at ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}), distance {math.dist(pos, xyz):.2f} m"
