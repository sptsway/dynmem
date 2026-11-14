import numpy as np

from dynmem.store import Entry, QdrantStore
from dynmem.tools import Toolbox

DIM = 4
V = np.eye(DIM)


def toolbox(instances=None):
    s = QdrantStore(DIM)
    s.add([Entry(0, "mug at table", 0, 10, (0, 0, 0), V[0], object="mug"),
           Entry(1, "mug at shelf", 100, 110, (5, 0, 0), V[0], object="mug", valid_from=100),
           Entry(2, "book at desk", 50, 60, (1, 0, 0), V[1], object="book")])
    return Toolbox(s, lambda q: V[0], instances=instances)


def test_search_time_overlap_and_nearest_fallback():
    tb = toolbox()
    _, ids = tb.call("search_time", {"time_or_range": [55]})
    assert ids == [2]
    _, ids = tb.call("search_time", {"time_or_range": [1000], "k": 1})
    assert ids == [1]  # nothing overlaps t=1000, so the nearest entry is returned


def test_composed_search_applies_all_filters():
    tb = toolbox()
    _, ids = tb.call("search", {"query": "mug", "object": "mug", "time_range": [90, 120]})
    assert ids == [1]
    out, ids = tb.call("search", {"position": [0, 0, 0]})
    assert out.startswith("error") and ids == []


def test_object_history_ordered_by_time():
    _, ids = toolbox().call("object_history", {"object": "mug"})
    assert ids == [0, 1]


def test_nearest_instance():
    tb = toolbox([("table", (0, 0, 0)), ("shelf", (5, 0, 0))])
    out, _ = tb.call("nearest_instance", {"xyz": [4.5, 0, 0]})
    assert "shelf" in out
    assert "no static instances" in toolbox().call("nearest_instance", {"xyz": [0, 0, 0]})[0]


def test_unknown_tool_and_specs():
    tb = toolbox()
    assert tb.call("nope", {})[0].startswith("error")
    assert [s["name"] for s in tb.specs(["search", "object_history"])] == ["search", "object_history"]


def test_single_value_time_range_is_a_point_range():
    _, ids = toolbox().call("search", {"query": "mug", "time_range": [105]})
    assert ids == [1]


def test_malformed_arguments_return_errors_not_exceptions():
    tb = toolbox()
    for args in ({"time_range": [1, 2, 3]}, {"time_range": ["a"]}, {"position": [0, 0], "radius": 1.0},
                 {"k": "many"}):
        out, ids = tb.call("search", args)
        assert ids == [] or isinstance(out, str)  # never raises
    assert tb.call("search", {"time_range": [1, 2, 3]})[0].startswith("error")
    assert tb.call("search_time", {"time_or_range": []})[0].startswith("error")


def test_null_arguments_are_treated_as_absent():
    tb = toolbox()
    _, ids = tb.call("search", {"query": "mug", "object": "mug", "position": [None, None, None],
                                "radius": None, "time_range": None, "k": 5})
    assert set(ids) == {0, 1}
    out, _ = tb.call("search_time", {"time_or_range": [0, 200], "k": None})
    assert not out.startswith("error")
