"""Load Lost & Found recordings into scan-frame trajectories.

Facts verified on disk (see DEVIATIONS.md): CSV timestamps are Unix epoch seconds at 30 Hz;
`icp_aligned_pose.npy` maps scan -> recording (vicon) frame, so its inverse maps a trajectory
into the scan frame.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from dynmem.stage_b.events import Event, extract_events
from dynmem.stage_b.timeline import Recording

DEFAULT_ROOT = Path("data/lostfound/Final_Dataset")
SCAN_PLY = Path("data/scan/Final_Scan/mesh_labeled.ply")


def list_recordings(root: str | Path = DEFAULT_ROOT) -> dict[str, str]:
    """recording id -> object name (folder name without the trailing index)."""
    return {p.name: re.sub(r"_\d+$", "", p.name) for p in sorted(Path(root).iterdir()) if p.is_dir()}


def load_trajectory(root: str | Path, rec: str, kind: str) -> tuple[np.ndarray, np.ndarray]:
    """(t, xyz): t in seconds from the first sample, xyz in the scan frame. kind: gt | pred."""
    d = pd.read_csv(Path(root) / rec / f"{kind}_object.csv", comment="#")
    T = np.load(Path(root) / rec / "icp_aligned_pose.npy")
    P = np.c_[d[["tx", "ty", "tz"]].to_numpy(float), np.ones(len(d))]
    xyz = (P @ np.linalg.inv(T).T)[:, :3]
    t = d["timestamp"].to_numpy(float)
    return t - t[0], xyz


def load_scan_points(path: str | Path = SCAN_PLY) -> np.ndarray:
    """Scan point cloud (binary little-endian PLY with double xyz + uchar rgb)."""
    raw = Path(path).read_bytes()
    off = raw.index(b"end_header\n") + len(b"end_header\n")
    dt = np.dtype([("x", "<f8"), ("y", "<f8"), ("z", "<f8"), ("rgb", "u1", 3)])
    a = np.frombuffer(raw, dtype=dt, offset=off)
    return np.stack([a["x"], a["y"], a["z"]], axis=1)


def load_recording(root: str | Path, rec: str, source: str, speed_thr: float) -> Recording:
    kind = {"gt_event": "gt", "pred_event": "pred"}[source]
    t, xyz = load_trajectory(root, rec, kind)
    obj = re.sub(r"_\d+$", "", rec)
    events = extract_events(t, xyz, object=obj, recording_id=rec, source=source, speed_thr=speed_thr)
    return Recording(rec, obj, float(t[-1]), tuple(events))
