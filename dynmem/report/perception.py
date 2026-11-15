"""Perception error of the Lost & Found predictions, per recording, written to results/perception_error.csv.

Needs the dataset on disk (`make data`). The figure is drawn from the CSV, so a clean clone can reproduce it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from dynmem.stage_b.data import DEFAULT_ROOT, list_recordings, load_recording
from dynmem.stage_b.questions import split_recordings


def build(out: str = "results/perception_error.csv") -> pd.DataFrame:
    ev = yaml.safe_load(open("configs/events.yaml"))
    recs = list_recordings(DEFAULT_ROOT)
    dev, test = split_recordings(recs, **ev["split"])
    split_of = {r: "dev" for r in dev} | {r: "test" for r in test}
    rows = []
    for r, obj in recs.items():
        g = load_recording(DEFAULT_ROOT, r, "gt_event", ev["speed_thr_mps"]).events[0]
        p = load_recording(DEFAULT_ROOT, r, "pred_event", ev["speed_thr_mps"]).events[0]
        rows.append({"recording": r, "object": obj, "split": split_of[r],
                     "move_distance_m": float(np.linalg.norm(np.array(g.p_place) - g.p_pick)),
                     "place_error_m": float(np.linalg.norm(np.array(g.p_place) - p.p_place)),
                     "pick_error_m": float(np.linalg.norm(np.array(g.p_pick) - p.p_pick)),
                     "place_time_error_s": abs(g.t_place - p.t_place)})
    df = pd.DataFrame(rows).sort_values("recording")
    df.to_csv(out, index=False)
    return df




def history_coincidence(split: str = "test", root: str = "results/stage_b_local") -> dict:
    """How often is the previous place within tolerance of the current place? Overwrite memory can only answer
    the history question in those cases. Needs the dataset on disk; writes a CSV the README reads."""
    import json
    import math
    from pathlib import Path

    from dynmem.stage_b.questions import answer_for
    from dynmem.stage_b.timeline import build_timeline

    ev = yaml.safe_load(open("configs/events.yaml"))
    tol = yaml.safe_load(open("configs/scoring.yaml"))["position_tolerance_m"]
    recs = list_recordings(DEFAULT_ROOT)
    dev, test = split_recordings(recs, **ev["split"])
    ids = test if split == "test" else dev
    R = [load_recording(DEFAULT_ROOT, r, "gt_event", ev["speed_thr_mps"]) for r in ids]
    tls = {}
    out = {"questions": 0, "previous_equals_current": 0, "overwrite_correct": 0, "overwrite_correct_by_coincidence": 0}
    for l in Path(root, split, "gt_event__M1_R1.jsonl").read_text().splitlines():
        r = json.loads(l)
        if r["qtype"] != "previous_place":
            continue
        tl = tls.setdefault(r["timeline"], build_timeline(R, r["timeline"]))
        obj = r["question"].split("the ", 1)[1].split(" placed")[0]
        t = float(r["question"].split("t=")[1].split(" s")[0])
        same = math.dist(answer_for(list(tl.events), "current_location", obj, t)["position"], r["gt"]["position"]) <= tol
        out["questions"] += 1
        out["previous_equals_current"] += same
        if r["score"] >= 1:
            out["overwrite_correct"] += 1
            out["overwrite_correct_by_coincidence"] += same
    pd.DataFrame([out]).to_csv(f"results/history_coincidence_{split}.csv", index=False)
    return out


if __name__ == "__main__":
    print(build().groupby("split")[["place_error_m", "pick_error_m", "place_time_error_s"]].describe().T.round(3))
    print(history_coincidence())
