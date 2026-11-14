import numpy as np

from dynmem.stage_b.events import Event, extract_events, segment_moves
from dynmem.stage_b.timeline import Recording, build_timeline


def traj():
    # still 0-5s, moves 5-8s at 1 m/s along x, still 8-12s, then moves 12-14s along y
    t = np.arange(0, 15, 1.0)
    xyz = np.zeros((len(t), 3))
    for i, ti in enumerate(t):
        xyz[i, 0] = min(max(ti - 5, 0), 3)
        xyz[i, 1] = min(max(ti - 12, 0), 2)
    return t, xyz


def test_segment_moves_finds_two_moves():
    t, xyz = traj()
    assert segment_moves(t, xyz, speed_thr=0.5) == [(5, 8), (12, 14)]


def test_segment_threshold_and_min_duration():
    t, xyz = traj()
    assert segment_moves(t, xyz, speed_thr=2.0) == []
    assert segment_moves(t, xyz, speed_thr=0.5, min_duration=2.5) == [(5, 8)]


def test_merge_gap_joins_close_segments():
    t, xyz = traj()
    assert segment_moves(t, xyz, speed_thr=0.5, merge_gap=10.0) == [(5, 14)]


def test_extract_events_poses():
    t, xyz = traj()
    ev = extract_events(t, xyz, object="mug", recording_id="r1", source="gt_event", speed_thr=0.5)
    assert len(ev) == 2
    assert ev[0].p_pick == (0, 0, 0) and ev[0].p_place == (3, 0, 0)
    assert ev[0].t_pick == 5 and ev[0].t_place == 8


def make_recs():
    mk = lambda i, o: Recording(f"r{i}", o, 30.0, (Event(o, f"r{i}", 5, 10, (0, 0, 0), (i, 0, 0), "gt_event"),))
    return [mk(i, "mug" if i % 2 else "book") for i in range(6)]


def test_timeline_is_deterministic_for_fixed_seed():
    a, b = build_timeline(make_recs(), seed=7), build_timeline(make_recs(), seed=7)
    assert a == b
    assert build_timeline(make_recs(), seed=8).order != a.order


def test_timeline_independent_of_input_order():
    recs = make_recs()
    assert build_timeline(recs, 3) == build_timeline(recs[::-1], 3)


def test_timeline_gaps_in_range_and_no_overlap():
    tl = build_timeline(make_recs(), seed=1)
    prev_end = 0.0
    for rid in tl.order:
        gap = tl.starts[rid] - prev_end
        assert 180 <= gap <= 1200
        prev_end = tl.starts[rid] + 30.0
    assert tl.t_end == prev_end
    assert [e.t_place for e in tl.events] == sorted(e.t_place for e in tl.events)
