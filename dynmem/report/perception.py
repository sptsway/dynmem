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


if __name__ == "__main__":
    print(build().groupby("split")[["place_error_m", "pick_error_m", "place_time_error_s"]].describe().T.round(3))
