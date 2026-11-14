"""Bootstrap confidence intervals and paired tests."""
from __future__ import annotations

import numpy as np
from scipy.stats import binomtest


def bootstrap_ci(values, n_boot: int = 10_000, alpha: float = 0.05, seed: int = 0) -> tuple[float, float, float]:
    """Mean and (1 - alpha) percentile bootstrap CI over items."""
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), size=(n_boot, len(v)))].mean(axis=1)
    return float(v.mean()), float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def mcnemar(a, b) -> dict:
    """Exact McNemar test on paired binary outcomes (same questions, methods a and b).

    Returns discordant counts, the exact two-sided p-value, the paired accuracy
    difference (a - b) and the discordant-pair odds ratio.
    """
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    if a.shape != b.shape:
        raise ValueError("paired outcomes must have equal length")
    n10 = int((a & ~b).sum())  # a right, b wrong
    n01 = int((~a & b).sum())
    n = n10 + n01
    p = 1.0 if n == 0 else float(binomtest(n10, n, 0.5).pvalue)
    return {"n_a_only": n10, "n_b_only": n01, "p_value": p,
            "acc_diff": float(a.mean() - b.mean()) if len(a) else float("nan"),
            "odds_ratio": (n10 / n01) if n01 else (float("inf") if n10 else float("nan"))}
