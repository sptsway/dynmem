import numpy as np
import pytest

from dynmem.store import Entry, QdrantStore

DIM = 8


def vec(i):
    v = np.zeros(DIM)
    v[i % DIM] = 1.0
    return v


def entries():
    return [
        Entry(0, "mug on table", 0, 10, (0, 0, 0), vec(0), object="mug"),
        Entry(1, "mug on shelf", 100, 110, (5, 0, 0), vec(0), object="mug", valid_from=100),
        Entry(2, "book on desk", 50, 60, (1, 0, 0), vec(1), object="book"),
    ]


@pytest.fixture
def store():
    s = QdrantStore(DIM)
    s.add(entries())
    return s


def test_vector_search_ranks_by_similarity(store):
    hits = store.search(vec(1), 3)
    assert hits[0][0].id == 2


def test_time_overlap_filter(store):
    ids = {e.id for e, _ in store.search(vec(0), 10, time_range=(55, 105))}
    assert ids == {1, 2}


def test_radial_filter_is_exact(store):
    # entry 2 at distance 1 lies in the bounding box of radius 1.2, entry 1 at distance 5 does not
    ids = {e.id for e, _ in store.search(vec(0), 10, position=(0, 0, 0), radius=1.2)}
    assert ids == {0, 2}
    # corner of the box but outside the sphere
    s = QdrantStore(DIM)
    s.add([Entry(0, "corner", 0, 1, (0.9, 0.9, 0.9), vec(0))])
    assert s.search(vec(0), 5, position=(0, 0, 0), radius=1.0) == []


def test_object_and_filter_only_search_sorted_by_time(store):
    hits = store.search(None, 10, object="mug")
    assert [e.id for e, s in hits] == [0, 1] and all(s is None for _, s in hits)


def test_valid_at(store):
    store.update(0, valid_to=100.0)
    assert {e.id for e, _ in store.search(None, 10, object="mug", valid_at=50)} == {0}
    assert {e.id for e, _ in store.search(None, 10, object="mug", valid_at=150)} == {1}


def test_update_position_delete_count(store):
    store.update(2, position=(9, 9, 9))
    assert next(e for e in store.all() if e.id == 2).position == (9, 9, 9)
    store.delete([0])
    assert store.count() == 2


def test_requires_embedding_of_right_dim():
    s = QdrantStore(DIM)
    with pytest.raises(ValueError):
        s.add([Entry(0, "x", 0, 1, (0, 0, 0))])
