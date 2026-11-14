"""Constructed timelines: independent recordings placed on one synthetic clock.

These are constructed, not a continuous real-world log. Gaps between recordings are drawn
uniformly from [gap_min, gap_max] seconds with a fixed seed.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from dynmem.stage_b.events import Event


@dataclass(frozen=True)
class Recording:
    id: str
    object: str
    duration: float          # seconds
    events: tuple[Event, ...]  # times relative to the recording start


@dataclass(frozen=True)
class Timeline:
    seed: int
    order: tuple[str, ...]
    starts: dict[str, float]
    events: tuple[Event, ...]  # absolute times, sorted by t_place
    t_end: float


def build_timeline(recordings: list[Recording], seed: int,
                   gap_min: float = 180.0, gap_max: float = 1200.0) -> Timeline:
    rng = np.random.default_rng(seed)
    recs = sorted(recordings, key=lambda r: r.id)  # canonical order before shuffling
    order = [recs[i] for i in rng.permutation(len(recs))]
    t, starts, events = 0.0, {}, []
    for r in order:
        t += float(rng.uniform(gap_min, gap_max))
        starts[r.id] = t
        events += [replace(e, t_pick=e.t_pick + t, t_place=e.t_place + t) for e in r.events]
        t += r.duration
    events.sort(key=lambda e: (e.t_place, e.recording_id))
    return Timeline(seed, tuple(r.id for r in order), starts, tuple(events), t)


def remap_events(tl: Timeline, recordings: list[Recording]) -> tuple[Event, ...]:
    """Place another event source (e.g. predicted events) on the same timeline `tl`.

    Recording start times come from `tl`, so both sources share one clock.
    """
    out = []
    for r in recordings:
        s = tl.starts[r.id]
        out += [replace(e, t_pick=e.t_pick + s, t_place=e.t_place + s) for e in r.events]
    return tuple(sorted(out, key=lambda e: (e.t_place, e.recording_id)))
