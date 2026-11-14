import numpy as np

from dynmem.agent import Agent, parse_answer
from dynmem.llm import LLM, Response
from dynmem.store import Entry, QdrantStore
from dynmem.tools import Toolbox

DIM = 4
FINAL = '{"text": "on the shelf", "position": [1, 2, 3]}'


class Script:
    """Backend that replays scripted responses and records what it was sent."""
    provider = "script"

    def __init__(self, responses):
        self.responses, self.seen = list(responses), []

    def call(self, model, messages, tools, params):
        self.seen.append((messages, tools))
        return self.responses.pop(0)


def tool_call(name="search_text", **args):
    return Response(None, [{"id": "c1", "name": name, "args": args}], 5, 1)


def setup(tmp_path, responses, tool_names=("search_text",)):
    store = QdrantStore(DIM)
    v = np.eye(DIM)[0]
    store.add([Entry(0, "mug on shelf", 0, 1, (1, 2, 3), v, object="mug")])
    tb = Toolbox(store, lambda q: v)
    be = Script(responses)
    llm = LLM(be, "m", cache_path=tmp_path / "c.sqlite", sleep=lambda s: None)
    return Agent(llm, tb, tool_names), be


def test_parse_answer_strict():
    assert parse_answer(FINAL).position == [1, 2, 3]
    assert parse_answer("```json\n" + FINAL + "\n```").text == "on the shelf"
    assert parse_answer("Sure! " + FINAL) is None          # prose around the JSON
    assert parse_answer('{"text": "x", "extra": 1}') is None  # unknown key
    assert parse_answer('{"text": "x", "position": [1, 2]}') is None
    assert parse_answer(None) is None


def test_agent_retrieves_then_answers(tmp_path):
    ag, be = setup(tmp_path, [tool_call(query="mug"), Response(FINAL, [], 7, 3)])
    r = ag.run("Where is the mug?")
    assert r.answer.position == [1, 2, 3]
    assert r.n_tool_calls == 1 and r.steps[0]["retrieved_ids"] == [0]
    assert (r.input_tokens, r.output_tokens) == (12, 4)
    assert be.seen[1][0][-1]["tool_results"][0]["name"] == "search_text"


def test_agent_stops_after_three_rounds_and_forces_answer(tmp_path):
    ag, be = setup(tmp_path, [tool_call(query="a")] * 3 + [Response(FINAL, [], 1, 1)])
    r = ag.run("q")
    assert r.n_tool_calls == 3 and r.answer is not None
    last_msgs, last_tools = be.seen[-1]
    assert last_tools is None and "used all retrieval rounds" in last_msgs[-1]["text"]


def test_parse_failure_gives_no_answer(tmp_path):
    ag, _ = setup(tmp_path, [Response("I think it is on the shelf.", [], 1, 1)])
    r = ag.run("q")
    assert r.answer is None and r.raw.startswith("I think")


def test_bad_tool_args_do_not_crash(tmp_path):
    ag, _ = setup(tmp_path, [tool_call(wrong=1), Response(FINAL, [], 1, 1)])
    r = ag.run("q")
    assert r.steps[0]["result"].startswith("error") and r.answer is not None


def test_extra_calls_in_a_round_are_skipped(tmp_path):
    many = Response(None, [{"id": f"c{i}", "name": "search_text", "args": {"query": "x"}} for i in range(5)], 1, 1)
    ag, _ = setup(tmp_path, [many, Response(FINAL, [], 1, 1)])
    r = ag.run("q")
    assert r.n_tool_calls == 3 and sum(s["result"].startswith("skipped") for s in r.steps) == 2


def test_blind_baseline_has_no_tools(tmp_path):
    be = Script([Response(FINAL, [], 1, 1)])
    llm = LLM(be, "m", cache_path=tmp_path / "c.sqlite")
    r = Agent(llm, None, []).run("q")
    assert be.seen[0][1] is None and r.n_tool_calls == 0
