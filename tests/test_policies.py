import numpy as np
import pytest

from dynmem.stage_b.events import Event
from dynmem.stage_b.policies import build_memory
from dynmem.store import QdrantStore

DIM = 16


def embed(texts):
    out = []
    for t in texts:
        rng = np.random.default_rng(abs(hash(t)) % (2**32))
        v = rng.normal(size=DIM)
        out.append(v / np.linalg.norm(v))
    return np.array(out)


A, B, C = (0, 0, 0), (1, 0, 0), (2, 0, 0)
EVENTS = [
    Event("mug", "r1", 100, 110, A, B, "gt_event"),
    Event("mug", "r2", 300, 310, B, C, "gt_event"),
    Event("book", "r3", 500, 510, (9, 9, 9), (8, 8, 8), "gt_event"),
]


def run(policy, t):
    s = QdrantStore(DIM)
    build_memory(s, policy, EVENTS, t, embed, "gt_event")
    return s


def mug_entries(s):
    return [e for e in s.all() if e.object == "mug"]


def test_m0_ignores_events():
    s = run("M0", 1000)
    assert s.count() == 2  # one initial entry per object
    assert mug_entries(s)[0].position == A


def test_m1_keeps_only_latest_pose():
    s = run("M1", 1000)
    assert s.count() == 2
    (mug,) = mug_entries(s)
    assert mug.position == C
    assert "(1.00, 0.00, 0.00)" not in mug.text  # previous pose is gone from the text


def test_m1_respects_query_time():
    (mug,) = mug_entries(run("M1", 200))
    assert mug.position == B


def test_m2_returns_previous_pose_for_before_question():
    s = run("M2", 1000)
    assert len(mug_entries(s)) == 3
    latest = s.search(None, 1, object="mug", valid_at=1000)[0][0]
    assert latest.position == C and "(1.00, 0.00, 0.00)" in latest.text  # moved from B
    at_200 = s.search(None, 1, object="mug", valid_at=200)[0][0]
    assert at_200.position == B


def test_m2_closes_previous_version():
    ents = sorted(mug_entries(run("M2", 1000)), key=lambda e: e.valid_from)
    assert ents[0].valid_to == 100 and ents[0].superseded_by == ents[1].id
    assert ents[1].valid_to == 300 and ents[1].superseded_by == ents[2].id
    assert ents[2].valid_to > 1e17


def test_unknown_policy():
    with pytest.raises(ValueError):
        build_memory(QdrantStore(DIM), "M9", EVENTS, 0, embed, "gt_event")
