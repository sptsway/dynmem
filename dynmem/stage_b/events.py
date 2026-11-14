"""Object-move events extracted from an object trajectory.

A trajectory is (t, xyz) with t in seconds from the start of the recording. Motion is
segmented by a speed threshold; each moving segment is one move (pick pose -> place pose).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Event:
    object: str
    recording_id: str
    t_pick: float
    t_place: float
    p_pick: tuple[float, float, float]
    p_place: tuple[float, float, float]
    source: str  # gt_event | pred_event
    instance_pick: str | None = None
    instance_place: str | None = None


def segment_moves(t: np.ndarray, xyz: np.ndarray, speed_thr: float,
                  min_duration: float = 0.5, merge_gap: float = 1.0) -> list[tuple[int, int]]:
    """Return (start_idx, end_idx) pairs of moving segments.

    Speed is the finite-difference norm. Segments closer than `merge_gap` seconds are merged;
    segments shorter than `min_duration` seconds are dropped.
    """
    t, xyz = np.asarray(t, float), np.asarray(xyz, float)
    if len(t) < 2:
        return []
    speed = np.linalg.norm(np.diff(xyz, axis=0), axis=1) / np.maximum(np.diff(t), 1e-9)
    moving = speed > speed_thr  # moving[i] covers interval i -> i+1
    segs: list[list[int]] = []
    i = 0
    while i < len(moving):
        if moving[i]:
            j = i
            while j + 1 < len(moving) and moving[j + 1]:
                j += 1
            segs.append([i, j + 1])
            i = j + 1
        else:
            i += 1
    merged: list[list[int]] = []
    for s in segs:
        if merged and t[s[0]] - t[merged[-1][1]] < merge_gap:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return [(a, b) for a, b in merged if t[b] - t[a] >= min_duration]


def extract_events(t, xyz, *, object: str, recording_id: str, source: str, speed_thr: float,
                   min_duration: float = 0.5, merge_gap: float = 1.0) -> list[Event]:
    t, xyz = np.asarray(t, float), np.asarray(xyz, float)
    return [
        Event(object, recording_id, float(t[a]), float(t[b]),
              tuple(map(float, xyz[a])), tuple(map(float, xyz[b])), source)
        for a, b in segment_moves(t, xyz, speed_thr, min_duration, merge_gap)
    ]
