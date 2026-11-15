import pytest

from dynmem.stage_b.events import Event
from dynmem.stage_b.questions import answer_for, generate_questions, split_recordings
from dynmem.stage_b.timeline import Recording, build_timeline

A, B, C = (0, 0, 0), (1, 0, 0), (2, 0, 0)
EV = [Event("mug", "r1", 100, 110, A, B, "gt_event"),
      Event("mug", "r2", 300, 310, B, C, "gt_event"),
      Event("book", "r3", 500, 510, (9, 9, 9), (8, 8, 8), "gt_event")]


def test_answers_at_different_times():
    assert answer_for(EV, "current_location", "mug", 50) == {"position": [0, 0, 0]}  # initial pose
    assert answer_for(EV, "current_location", "mug", 200) == {"position": [1, 0, 0]}
    assert answer_for(EV, "previous_location", "mug", 400) == {"position": [1, 0, 0]}
    assert answer_for(EV, "when_moved", "mug", 400) == {"time": 310}
    assert answer_for(EV, "count", "mug", 400) == {"count": 2}
    assert answer_for(EV, "count", "mug", 50) == {"count": 0}
    assert answer_for(EV, "interval", None, 0, 200, 600) == {"objects": ["book", "mug"]}
    assert answer_for(EV, "interval", None, 0, 320, 400) is None


def test_undefined_before_first_move():
    assert answer_for(EV, "previous_location", "mug", 50) is None
    assert answer_for(EV, "when_moved", "mug", 50) is None


def test_split_has_no_overlap_and_covers_all():
    recs = {f"r{i}": ("mug" if i % 3 else "book") for i in range(30)}
    dev, test = split_recordings(recs, seed=1)
    assert not set(dev) & set(test)
    assert set(dev) | set(test) == set(recs)
    assert 0.2 < len(dev) / len(recs) < 0.4
    assert split_recordings(recs, seed=1) == (dev, test)


def timeline():
    recs = [Recording(f"r{i}", o, 40.0, (Event(o, f"r{i}", 5, 15, (i, 0, 0), (i + 1, 0, 0), "gt_event"),))
            for i, o in enumerate(["mug", "book", "mug", "cup", "book", "mug", "cup", "mug"])]
    return build_timeline(recs, seed=2)


def test_generation_is_deterministic_and_well_formed():
    tl = timeline()
    from dynmem.stage_b.questions import CORE_QTYPES
    a, b = generate_questions(tl, 10, seed=0), generate_questions(tl, 10, seed=0)
    assert a == b
    core = [q for q in a if q.qtype in CORE_QTYPES]
    assert len(core) == 50 and len({q.id for q in a}) == len(a)
    assert all(q.text.startswith("It is now t=") for q in a)
    assert {q.qtype for q in a} <= set(CORE_QTYPES) | {"previous_place"}


def test_previous_place_needs_two_moves_and_uses_the_earlier_place():
    assert answer_for(EV, "previous_place", "mug", 200) is None           # one move so far
    assert answer_for(EV, "previous_place", "mug", 400) == {"position": [1, 0, 0]}  # placed at B before moving to C


def test_adding_the_new_type_leaves_earlier_questions_unchanged():
    from dynmem.stage_b.questions import CORE_QTYPES
    tl = timeline()
    core_only = generate_questions(tl, 10, seed=0, qtypes=CORE_QTYPES)
    with_new = generate_questions(tl, 10, seed=0, n_override={"previous_place": 5})
    assert [q for q in with_new if q.qtype in CORE_QTYPES] == core_only
