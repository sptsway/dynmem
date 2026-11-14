import os
from pathlib import Path

import pytest

from dynmem.llm import LLM, Response, RetryableError, cache_key


class FakeBackend:
    provider = "fake"

    def __init__(self, fail_times=0, exc=RetryableError("429")):
        self.calls, self.fail_times, self.exc = 0, fail_times, exc

    def call(self, model, messages, tools, params):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc
        return Response(text=f"answer-{self.calls}", input_tokens=10, output_tokens=3)


def make(tmp_path, backend=None, **kw):
    return LLM(backend or FakeBackend(), "m1", cache_path=tmp_path / "c.sqlite", sleep=lambda s: None, **kw)


MSG = [{"role": "user", "text": "where is the mug?"}]


def test_identical_call_is_cached(tmp_path):
    llm = make(tmp_path)
    a, b = llm.generate(MSG), llm.generate(MSG)
    assert a.text == b.text == "answer-1"
    assert not a.cached and b.cached
    assert llm.backend.calls == 1


def test_cache_persists_across_instances(tmp_path):
    make(tmp_path).generate(MSG)
    llm2 = make(tmp_path)
    assert llm2.generate(MSG).cached


def test_key_depends_on_model_params_and_image_content(tmp_path):
    img1, img2 = tmp_path / "a.jpg", tmp_path / "b.jpg"
    img1.write_bytes(b"AAA")
    img2.write_bytes(b"BBB")
    k = lambda **kw: cache_key("p", kw.get("model", "m"), kw.get("messages", MSG), None, kw.get("params", {"t": 0}))
    assert k() == k()
    assert k() != k(model="m2")
    assert k() != k(params={"t": 1})
    with_img = lambda p: [{"role": "user", "text": "x", "images": [p]}]
    assert k(messages=with_img(img1)) != k(messages=with_img(img2))
    # same content under another filename hashes the same
    img3 = tmp_path / "c.jpg"
    img3.write_bytes(b"AAA")
    assert k(messages=with_img(img1)) == k(messages=with_img(img3))


def test_retries_then_succeeds(tmp_path):
    llm = make(tmp_path, FakeBackend(fail_times=2))
    assert llm.generate(MSG).text == "answer-3"


def test_retry_is_bounded(tmp_path):
    llm = make(tmp_path, FakeBackend(fail_times=99))
    with pytest.raises(RetryableError):
        llm.generate(MSG)
    assert llm.backend.calls == 6


def test_non_retryable_error_raises_immediately(tmp_path):
    llm = make(tmp_path, FakeBackend(fail_times=1, exc=ValueError("bad request")))
    with pytest.raises(ValueError):
        llm.generate(MSG)
    assert llm.backend.calls == 1


def test_token_log_records_cached_and_fresh(tmp_path):
    llm = make(tmp_path, tag="t")
    llm.generate(MSG)
    llm.generate(MSG)
    rows = llm.db.execute("SELECT input_tokens, output_tokens, cached, tag FROM call_log").fetchall()
    assert rows == [(10, 3, 0, "t"), (10, 3, 1, "t")]


def test_api_key_never_reaches_cache_file(tmp_path, monkeypatch):
    secret = "SECRET-KEY-DO-NOT-LEAK-123"
    monkeypatch.setenv("GEMINI_API_KEY", secret)
    llm = make(tmp_path)
    llm.generate(MSG)
    llm.db.commit()
    assert secret.encode() not in Path(tmp_path / "c.sqlite").read_bytes()
