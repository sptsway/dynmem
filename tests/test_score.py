import pytest

from dynmem.stage_b.score import (count_correct, position_correct, score_answer,
                                  set_f1, time_correct)

CFG = {"position_tolerance_m": 0.5, "time_tolerance_s": 60.0}


def test_position_inside_and_outside_tolerance():
    assert position_correct([0.3, 0, 0], [0, 0, 0], 0.5)
    assert position_correct([0.5, 0, 0], [0, 0, 0], 0.5)  # boundary counts
    assert not position_correct([0.6, 0, 0], [0, 0, 0], 0.5)
    assert not position_correct(None, [0, 0, 0], 0.5)
    assert not position_correct([0, 0], [0, 0, 0], 0.5)


def test_time_tolerance():
    assert time_correct(100, 150, 60)
    assert not time_correct(100, 200, 60)
    assert not time_correct(None, 200, 60)


def test_count_exact():
    assert count_correct(3, 3)
    assert not count_correct(2, 3)
    assert not count_correct(None, 0)


def test_set_f1():
    assert set_f1(["a", "b"], ["a", "b"]) == 1.0
    assert set_f1(["A"], ["a"]) == 1.0  # case-insensitive
    assert set_f1(["a"], ["b"]) == 0.0
    assert set_f1([], []) == 1.0
    assert set_f1(None, ["a"]) == 0.0
    assert set_f1(["a", "b"], ["a", "c"]) == pytest.approx(0.5)
    assert set_f1(["a"], ["a", "b"]) == pytest.approx(2 / 3)


def test_score_answer_dispatch_and_parse_failure():
    gt = {"position": [1, 1, 1], "time": 500.0, "count": 2, "objects": ["cup"]}
    assert score_answer("current_location", {"position": [1, 1, 1.2]}, gt, CFG) == 1.0
    assert score_answer("previous_location", {"position": [5, 5, 5]}, gt, CFG) == 0.0
    assert score_answer("when_moved", {"time": 530}, gt, CFG) == 1.0
    assert score_answer("count", {"count": 2}, gt, CFG) == 1.0
    assert score_answer("interval", {"objects": ["cup", "mug"]}, gt, CFG) == pytest.approx(2 / 3)
    assert score_answer("count", None, gt, CFG) == 0.0
    with pytest.raises(ValueError):
        score_answer("bogus", {}, gt, CFG)
