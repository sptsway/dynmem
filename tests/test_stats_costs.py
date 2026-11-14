import numpy as np
import pytest

from dynmem.costs import build
from dynmem.llm import LLM, Response
from dynmem.stats import bootstrap_ci, mcnemar


def test_bootstrap_ci_brackets_mean_and_is_seeded():
    v = [1] * 70 + [0] * 30
    m, lo, hi = bootstrap_ci(v, n_boot=2000, seed=1)
    assert m == pytest.approx(0.7) and lo < 0.7 < hi and 0.55 < lo and hi < 0.85
    assert bootstrap_ci(v, n_boot=2000, seed=1) == (m, lo, hi)
    assert all(np.isnan(bootstrap_ci([])))


def test_mcnemar_known_case():
    a = [1] * 10 + [0] * 0 + [1] * 5
    b = [0] * 10 + [1] * 0 + [1] * 5
    r = mcnemar(a, b)
    assert (r["n_a_only"], r["n_b_only"]) == (10, 0)
    assert r["p_value"] == pytest.approx(2 * 0.5**10)
    assert r["acc_diff"] == pytest.approx(10 / 15)
    assert mcnemar([1, 0], [1, 0])["p_value"] == 1.0
    with pytest.raises(ValueError):
        mcnemar([1], [1, 0])


class Fake:
    provider = "fake"

    def call(self, model, messages, tools, params):
        return Response("x", [], 1000, 500)


def test_costs_table_uses_config_prices_only(tmp_path):
    db = tmp_path / "c.sqlite"
    llm = LLM(Fake(), "m1", cache_path=db, tag="t")
    llm.generate([{"role": "user", "text": "a"}])
    llm.generate([{"role": "user", "text": "a"}])  # cached
    (tmp_path / "models.yaml").write_text("prices:\n  m1: {input_per_m: 1.0, output_per_m: 2.0}\n")
    out = build(db, tmp_path / "models.yaml")
    assert "| fake | m1 | t | 1 | 1 | 1000 | 500 |" in out and "0.0020" in out
    assert "| - |" in build(db, tmp_path / "missing.yaml")
