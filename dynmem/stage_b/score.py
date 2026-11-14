"""Deterministic scoring for Stage B questions. No LLM judge."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

import yaml

QTYPES = ("current_location", "previous_location", "when_moved", "count", "interval")


def load_scoring(path: str | Path = "configs/scoring.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text())


def position_correct(pred: Sequence[float] | None, gt: Sequence[float], tol_m: float) -> bool:
    if pred is None or len(pred) != 3:
        return False
    return math.dist(pred, gt) <= tol_m


def time_correct(pred: float | None, gt: float, tol_s: float) -> bool:
    return pred is not None and abs(pred - gt) <= tol_s


def count_correct(pred: int | None, gt: int) -> bool:
    return pred is not None and int(pred) == int(gt)


def set_f1(pred: Sequence[str] | None, gt: Sequence[str]) -> float:
    p, g = {s.lower() for s in (pred or [])}, {s.lower() for s in gt}
    if not p and not g:
        return 1.0
    tp = len(p & g)
    if tp == 0:
        return 0.0
    prec, rec = tp / len(p), tp / len(g)
    return 2 * prec * rec / (prec + rec)


def score_answer(qtype: str, answer: dict | None, gt: dict, cfg: dict) -> float:
    """Score in [0, 1]. A missing answer (parse failure) scores 0."""
    if answer is None:
        return 0.0
    if qtype in ("current_location", "previous_location"):
        return float(position_correct(answer.get("position"), gt["position"], cfg["position_tolerance_m"]))
    if qtype == "when_moved":
        return float(time_correct(answer.get("time"), gt["time"], cfg["time_tolerance_s"]))
    if qtype == "count":
        return float(count_correct(answer.get("count"), gt["count"]))
    if qtype == "interval":
        return set_f1(answer.get("objects"), gt["objects"])
    raise ValueError(f"unknown question type {qtype!r}")
