"""Tool-calling agent with a bounded retrieval loop, a strict answer schema and full traces."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, ConfigDict, ValidationError

from dynmem.llm import LLM
from dynmem.tools import Toolbox

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
MAX_ITERATIONS = 3
MAX_EMPTY_RETRIES = 1  # per question


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    position: list[float] | None = None
    time: float | None = None
    duration: float | None = None
    count: int | None = None
    objects: list[str] | None = None

    def model_post_init(self, _ctx) -> None:
        if self.position is not None and len(self.position) != 3:
            raise ValueError("position must have 3 numbers")


def parse_answer(raw: str | None) -> Answer | None:
    """Strict parse. A single JSON object, optionally inside a code fence. Anything else is None."""
    if not raw:
        return None
    s = raw.strip()
    m = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", s, flags=re.S)
    if m:
        s = m.group(1)
    try:
        return Answer.model_validate(json.loads(s))
    except (json.JSONDecodeError, ValidationError, ValueError):
        return None


@dataclass
class AgentResult:
    answer: Answer | None
    raw: str | None
    steps: list[dict] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    n_tool_calls: int = 0
    retrieval_s: float = 0.0   # time inside the memory store and tools only
    total_s: float = 0.0       # end-to-end, dominated by the API

    def to_dict(self) -> dict:
        return {"answer": self.answer.model_dump() if self.answer else None, "raw": self.raw,
                "steps": self.steps, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
                "n_tool_calls": self.n_tool_calls, "retrieval_s": self.retrieval_s, "total_s": self.total_s}


class Agent:
    def __init__(self, llm: LLM, toolbox: Toolbox | None, tool_names: Sequence[str],
                 system_prompt: str | None = None, max_calls_per_iteration: int = 3,
                 max_output_tokens: int = 1024):
        self.llm, self.toolbox, self.tool_names = llm, toolbox, list(tool_names)
        self.system = system_prompt or (PROMPTS / "agent_system.md").read_text()
        self.force = (PROMPTS / "agent_force_answer.md").read_text()
        self.retry = (PROMPTS / "agent_retry.md").read_text()
        self.k_calls, self.max_out = max_calls_per_iteration, max_output_tokens

    def run(self, question: str) -> AgentResult:
        t0 = time.perf_counter()
        msgs = [{"role": "system", "text": self.system}, {"role": "user", "text": question}]
        res = AgentResult(None, None)
        specs = self.toolbox.specs(self.tool_names) if (self.toolbox and self.tool_names) else None
        rounds = empty_retries = 0
        while True:
            use_tools = specs if (specs and rounds < MAX_ITERATIONS) else None
            if specs and not use_tools:
                msgs.append({"role": "user", "text": self.force})
            r = self.llm.generate(msgs, tools=use_tools, max_output_tokens=self.max_out)
            res.input_tokens += r.input_tokens
            res.output_tokens += r.output_tokens
            if not r.tool_calls and not (r.text or "").strip() and empty_retries < MAX_EMPTY_RETRIES:
                empty_retries += 1  # some local models return an empty turn when their tool call fails to parse
                res.steps.append({"round": rounds, "tool": "<empty reply, retried>", "args": {},
                                  "retrieved_ids": [], "result": "", "retrieval_s": 0.0})
                msgs.append({"role": "user", "text": self.retry})
                continue
            if not (use_tools and r.tool_calls):
                res.raw = r.text
                res.answer = parse_answer(r.text)
                break
            rounds += 1
            msgs.append({"role": "assistant", "text": r.text, "tool_calls": r.tool_calls})
            results = []
            for i, tc in enumerate(r.tool_calls):
                if i >= self.k_calls:
                    out, ids, dt = "skipped: too many calls in one round", [], 0.0
                else:
                    ts = time.perf_counter()
                    out, ids = self.toolbox.call(tc["name"], tc["args"])
                    dt = time.perf_counter() - ts
                    res.n_tool_calls += 1
                    res.retrieval_s += dt
                results.append({"id": tc["id"], "name": tc["name"], "content": out})
                res.steps.append({"round": rounds, "tool": tc["name"], "args": tc["args"],
                                  "retrieved_ids": ids, "result": out, "retrieval_s": dt})
            msgs.append({"role": "user", "tool_results": results})
        res.total_s = time.perf_counter() - t0
        return res
