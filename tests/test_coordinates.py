"""Coordinate sanity check (plan section 5.2). Skipped when the data is not on disk."""
import numpy as np
import pytest
from scipy.spatial import cKDTree

from dynmem.stage_b.data import DEFAULT_ROOT, SCAN_PLY, list_recordings, load_scan_points, load_trajectory

pytestmark = pytest.mark.skipif(not (DEFAULT_ROOT.exists() and SCAN_PLY.exists()), reason="data not downloaded")

BBOX_MARGIN = 0.3  # metres of slack around the scan point-cloud bounds


@pytest.fixture(scope="module")
def ends():
    pts = load_scan_points()
    lo, hi = pts.min(0) - BBOX_MARGIN, pts.max(0) + BBOX_MARGIN
    tree = cKDTree(pts[::4])
    starts, finals = [], []
    for r in list_recordings(DEFAULT_ROOT):
        _, x = load_trajectory(DEFAULT_ROOT, r, "gt")
        starts.append(x[0])
        finals.append(x[-1])
    return np.array(starts), np.array(finals), lo, hi, tree


def test_all_start_and_final_positions_inside_scan_bbox(ends):
    starts, finals, lo, hi, _ = ends
    for P in (starts, finals):
        assert np.all((P >= lo) & (P <= hi))


def test_start_poses_lie_on_the_scan_surface(ends):
    starts, _, _, _, tree = ends
    assert np.median(tree.query(starts)[0]) < 0.05  # objects are in the initial scan


def test_final_poses_are_near_surfaces(ends):
    _, finals, _, _, tree = ends
    d = tree.query(finals)[0]
    assert np.median(d) < 0.25 and d.max() < 0.6  # rigid-body origin is the object centre


def test_forward_icp_direction_would_fail(ends):
    """The stored transform is scan->recording; applying it forward misplaces the objects."""
    _, _, lo, hi, _ = ends
    inside = 0
    for r in list_recordings(DEFAULT_ROOT):
        import pandas as pd
        d = pd.read_csv(DEFAULT_ROOT / r / "gt_object.csv", comment="#")
        T = np.load(DEFAULT_ROOT / r / "icp_aligned_pose.npy")
        p = (np.r_[d[["tx", "ty", "tz"]].to_numpy()[-1], 1.0] @ T.T)[:3]
        inside += bool(np.all((p >= lo) & (p <= hi)))
    assert inside < 96 // 2
