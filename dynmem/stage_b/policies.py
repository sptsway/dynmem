"""Memory update policies for Stage B.

M0 static:    holds only the initial scan state; events are ignored.
M1 overwrite: one entry per object, replaced by each new event; history is lost.
M2 versioned: append-only entries with valid_from / valid_to; history is kept.
"""
from __future__ import annotations

from typing import Callable, Sequence

import numpy as np

from dynmem.stage_b.events import Event
from dynmem.store import OPEN_END, Entry, MemoryStore

POLICIES = ("M0", "M1", "M2")
Embed = Callable[[list[str]], np.ndarray]


def fmt_pos(p: Sequence[float]) -> str:
    return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"


def _place(p, inst) -> str:
    return fmt_pos(p) + (f" near {inst}" if inst else "")


def initial_states(events: Sequence[Event]) -> dict[str, Event]:
    """Earliest event per object. Its pick pose is the object's pose in the initial scan."""
    first: dict[str, Event] = {}
    for e in sorted(events, key=lambda e: e.t_pick):
        first.setdefault(e.object, e)
    return first


class MemoryBuilder:
    def __init__(self, store: MemoryStore, policy: str, embed: Embed, source: str):
        if policy not in POLICIES:
            raise ValueError(f"unknown policy {policy!r}")
        self.store, self.policy, self.embed, self.source = store, policy, embed, source
        self._next_id = 0
        self._current: dict[str, int] = {}      # object -> id of its latest entry
        self._cache: dict[str, np.ndarray] = {}  # text -> embedding

    def _vec(self, text: str) -> np.ndarray:
        if text not in self._cache:
            self._cache[text] = self.embed([text])[0]
        return self._cache[text]

    def _add(self, text, t0, t1, pos, obj, inst, valid_from, episode) -> int:
        e = Entry(self._next_id, text, t0, t1, tuple(pos), self._vec(text), object=obj, instance=inst,
                  valid_from=valid_from, valid_to=OPEN_END, source=self.source, episode_id=episode)
        self._next_id += 1
        self.store.add([e])
        return e.id

    def ingest_initial(self, first: dict[str, Event]) -> None:
        for obj, e in first.items():
            text = f"At the start, the {obj} is at {_place(e.p_pick, e.instance_pick)}."
            self._current[obj] = self._add(text, 0.0, 0.0, e.p_pick, obj, e.instance_pick, 0.0, "scan")

    def ingest_event(self, e: Event) -> None:
        if self.policy == "M0":
            return
        obj = e.object
        if self.policy == "M1":
            self.store.delete([self._current[obj]])
            text = f"The {obj} is at {_place(e.p_place, e.instance_place)}. It was last moved at t={e.t_place:.0f} s."
            self._current[obj] = self._add(text, e.t_pick, e.t_place, e.p_place, obj, e.instance_place,
                                           e.t_place, e.recording_id)
        else:  # M2: close the previous version, append the new one
            prev = self._current[obj]
            new_id = self._next_id
            self.store.update(prev, valid_to=e.t_pick, superseded_by=new_id)
            text = (f"The {obj} was moved from {_place(e.p_pick, e.instance_pick)} at t={e.t_pick:.0f} s "
                    f"to {_place(e.p_place, e.instance_place)} at t={e.t_place:.0f} s.")
            self._current[obj] = self._add(text, e.t_pick, e.t_place, e.p_place, obj, e.instance_place,
                                           e.t_place, e.recording_id)


def build_memory(store: MemoryStore, policy: str, events: Sequence[Event], t_query: float,
                 embed: Embed, source: str, initial: dict[str, Event] | None = None) -> MemoryBuilder:
    """Fill `store` with what `policy` would hold at `t_query`.

    `initial` defaults to the first event per object in `events`. Pass it explicitly when
    `events` is a predicted-event list so the initial scan stays the same across sources.
    """
    b = MemoryBuilder(store, policy, embed, source)
    b.ingest_initial(initial if initial is not None else initial_states(events))
    for e in sorted(events, key=lambda e: e.t_place):
        if e.t_place <= t_query:
            b.ingest_event(e)
    return b
