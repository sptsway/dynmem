"""Provider interface for LLM/VLM calls with a disk cache, retries and a token log.

Every call goes through `LLM.generate`. The cache key is a hash of
(provider, model, messages, images, tools, params); API keys are read from the
environment by the backend and never enter the key, the cache or the log.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

KEY_ENV = {"gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}
DEFAULT_CACHE = Path("cache/llm.sqlite")
MAX_ATTEMPTS = 6


class MissingKeyError(RuntimeError):
    pass


class RetryableError(RuntimeError):
    """Raised by a backend for rate limits and transient server errors."""


@dataclass
class Response:
    text: str | None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)  # {id, name, args}
    input_tokens: int = 0
    output_tokens: int = 0
    latency_s: float = 0.0
    cached: bool = False

    def to_json(self) -> str:
        return json.dumps(
            {"text": self.text, "tool_calls": self.tool_calls,
             "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
             "latency_s": self.latency_s}
        )

    @classmethod
    def from_json(cls, s: str, cached: bool) -> "Response":
        d = json.loads(s)
        return cls(d["text"], d["tool_calls"], d["input_tokens"], d["output_tokens"],
                   d["latency_s"], cached)


class Backend(Protocol):
    provider: str

    def call(self, model: str, messages: list[dict], tools: list[dict] | None,
             params: dict) -> Response: ...


def _image_digest(img: str | Path | bytes) -> str:
    data = img if isinstance(img, bytes) else Path(img).read_bytes()
    return hashlib.sha256(data).hexdigest()


def cache_key(provider: str, model: str, messages: list[dict],
              tools: list[dict] | None, params: dict) -> str:
    """Hash of everything that determines the output. Images are hashed by content."""
    norm = []
    for m in messages:
        m = dict(m)
        m["images"] = [_image_digest(i) for i in m.get("images", [])]
        norm.append(m)
    blob = json.dumps(
        {"provider": provider, "model": model, "messages": norm,
         "tools": tools, "params": params},
        sort_keys=True, default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


def is_retryable(exc: Exception) -> bool:
    if isinstance(exc, RetryableError):
        return True
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return isinstance(code, int) and (code == 429 or 500 <= code < 600)


class LLM:
    """Cached, retrying, logging wrapper around one backend."""

    def __init__(self, backend: Backend, model: str, cache_path: str | Path = DEFAULT_CACHE,
                 tag: str = "", sleep=time.sleep):
        self.backend, self.model, self.tag, self._sleep = backend, model, tag, sleep
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.cache_path)
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS calls (
                key TEXT PRIMARY KEY, provider TEXT, model TEXT, response TEXT);
            CREATE TABLE IF NOT EXISTS call_log (
                ts REAL, key TEXT, provider TEXT, model TEXT, tag TEXT,
                input_tokens INTEGER, output_tokens INTEGER,
                latency_s REAL, cached INTEGER);
            """
        )

    def generate(self, messages: list[dict], tools: list[dict] | None = None,
                 temperature: float = 0.0, max_output_tokens: int = 2048,
                 **extra) -> Response:
        params = {"temperature": temperature, "max_output_tokens": max_output_tokens, **extra}
        provider = self.backend.provider
        key = cache_key(provider, self.model, messages, tools, params)
        row = self.db.execute("SELECT response FROM calls WHERE key=?", (key,)).fetchone()
        if row:
            resp = Response.from_json(row[0], cached=True)
            self._log(key, resp)
            return resp

        t0 = time.perf_counter()
        resp = self._call_with_backoff(messages, tools, params)
        resp.latency_s = time.perf_counter() - t0
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO calls VALUES (?,?,?,?)",
                            (key, provider, self.model, resp.to_json()))
        self._log(key, resp)
        return resp

    def _call_with_backoff(self, messages, tools, params) -> Response:
        for attempt in range(MAX_ATTEMPTS):
            try:
                return self.backend.call(self.model, messages, tools, params)
            except Exception as exc:  # noqa: BLE001 - classified below
                if not is_retryable(exc) or attempt == MAX_ATTEMPTS - 1:
                    raise
                self._sleep(min(60.0, 2.0 ** attempt) * (0.5 + random.random() / 2))
        raise AssertionError("unreachable")

    def _log(self, key: str, resp: Response) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO call_log VALUES (?,?,?,?,?,?,?,?,?)",
                (time.time(), key, self.backend.provider, self.model, self.tag,
                 resp.input_tokens, resp.output_tokens, resp.latency_s, int(resp.cached)),
            )


def _require_key(provider: str) -> str:
    var = KEY_ENV[provider]
    key = os.environ.get(var)
    if not key:
        raise MissingKeyError(f"{var} is not set. Create a key and export it; it is read from the environment only.")
    return key


class GeminiBackend:
    provider = "gemini"

    def __init__(self):
        from google import genai
        self._genai = genai
        self.client = genai.Client(api_key=_require_key("gemini"))

    def call(self, model, messages, tools, params) -> Response:
        from google.genai import errors, types

        contents, system = [], None
        for m in messages:
            if m["role"] == "system":
                system = m["text"]
                continue
            parts = [types.Part.from_bytes(
                        data=i if isinstance(i, bytes) else Path(i).read_bytes(),
                        mime_type="image/jpeg") for i in m.get("images", [])]
            if m.get("text"):
                parts.append(types.Part.from_text(text=m["text"]))
            for tc in m.get("tool_calls", []):
                parts.append(types.Part(function_call=types.FunctionCall(name=tc["name"], args=tc["args"])))
            if m.get("tool_result"):
                tr = m["tool_result"]
                parts.append(types.Part.from_function_response(
                    name=tr["name"], response={"result": tr["content"]}))
            contents.append(types.Content(role="model" if m["role"] == "assistant" else "user", parts=parts))

        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=params["temperature"],
            max_output_tokens=params["max_output_tokens"],
            seed=params.get("seed", 0),
            tools=[types.Tool(function_declarations=[types.FunctionDeclaration(**t) for t in tools])] if tools else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        try:
            r = self.client.models.generate_content(model=model, contents=contents, config=cfg)
        except errors.APIError as exc:
            if exc.code == 429 or (isinstance(exc.code, int) and exc.code >= 500):
                raise RetryableError(str(exc)) from exc
            raise
        calls = []
        for i, fc in enumerate(r.function_calls or []):
            calls.append({"id": f"call_{i}", "name": fc.name, "args": dict(fc.args or {})})
        u = r.usage_metadata
        return Response(
            text=r.text if not calls else None, tool_calls=calls,
            input_tokens=(u.prompt_token_count or 0) if u else 0,
            output_tokens=(u.candidates_token_count or 0) if u else 0,
        )


class AnthropicBackend:
    provider = "anthropic"

    def __init__(self):
        import anthropic
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=_require_key("anthropic"))

    def call(self, model, messages, tools, params) -> Response:
        import base64

        system, out = None, []
        for m in messages:
            if m["role"] == "system":
                system = m["text"]
                continue
            blocks: list[dict] = []
            for i in m.get("images", []):
                data = i if isinstance(i, bytes) else Path(i).read_bytes()
                blocks.append({"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg",
                    "data": base64.b64encode(data).decode()}})
            if m.get("text"):
                blocks.append({"type": "text", "text": m["text"]})
            for tc in m.get("tool_calls", []):
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["args"]})
            if m.get("tool_result"):
                tr = m["tool_result"]
                blocks.append({"type": "tool_result", "tool_use_id": tr["id"], "content": tr["content"]})
            out.append({"role": "assistant" if m["role"] == "assistant" else "user", "content": blocks})

        kwargs: dict[str, Any] = dict(model=model, messages=out,
                                      max_tokens=params["max_output_tokens"],
                                      temperature=params["temperature"])
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [{"name": t["name"], "description": t["description"],
                                "input_schema": t["parameters"]} for t in tools]
        try:
            r = self.client.messages.create(**kwargs)
        except self._anthropic.APIStatusError as exc:
            if exc.status_code == 429 or exc.status_code >= 500:
                raise RetryableError(str(exc)) from exc
            raise
        text = "".join(b.text for b in r.content if b.type == "text") or None
        calls = [{"id": b.id, "name": b.name, "args": dict(b.input)} for b in r.content if b.type == "tool_use"]
        return Response(text=text, tool_calls=calls,
                        input_tokens=r.usage.input_tokens, output_tokens=r.usage.output_tokens)


def make_llm(provider: str, model: str, tag: str = "", cache_path=DEFAULT_CACHE) -> LLM:
    backends = {"gemini": GeminiBackend, "anthropic": AnthropicBackend}
    if provider not in backends:
        raise ValueError(f"unknown provider {provider!r}; 'local' is only added if the user asks")
    return LLM(backends[provider](), model, cache_path=cache_path, tag=tag)
