"""Write SUMMARY.md and REPORT.md. Every number is read from result files.

Usage: python -m dynmem.report.make_summary [--root results/stage_b_local] [--split test]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from dynmem.report.make_figures import load, summarise
from dynmem.stats import mcnemar


def build(root: str, split: str) -> tuple[str, str]:
    d = load(split, root)
    s = summarise(d)
    csv = f"results/summary_stage_b_{split}.csv"
    model = f"{d['model'].iloc[0]} ({d['provider'].iloc[0]})"

    def m(src, cell, qt="overall"):
        r = s[(s.source == src) & (s.cell == cell) & (s.qtype == qt)].iloc[0]
        return r["mean"], r["ci_lo"], r["ci_hi"]

    def f(src, cell, qt="overall"):
        a, lo, hi = m(src, cell, qt)
        return f"{a:.2f} [{lo:.2f}, {hi:.2f}]"

    def pair(src, a, b, qtypes=None):
        t = d[d.source == src]
        if qtypes is not None:
            t = t[t.qtype.isin(qtypes)]
        ga, gb = t[t.cell == a].set_index("qid"), t[t.cell == b].set_index("qid")
        ids = ga.index.intersection(gb.index)
        r = mcnemar(ga.loc[ids, "correct"].to_numpy(), gb.loc[ids, "correct"].to_numpy())
        return r, len(ids)

    g = "gt_event"
    n_q = int(s[(s.source == g) & (s.cell == "M2_R1") & (s.qtype == "overall")]["n"].iloc[0])
    r_m2h, _ = pair(g, "M2_R1", "M2_R0")
    r_m1h, _ = pair(g, "M1_R1", "M1_R0")
    r_21, _ = pair(g, "M2_R1", "M1_R1")
    temporal = ["when_moved", "interval"]
    r_t, nt = pair(g, "M2_R1", "M2_R0", temporal)
    max_gap, worst, min_p = 0.0, None, 1.0
    for cell in ["M0_R0", "M0_R1", "M1_R0", "M1_R1", "M2_R0", "M2_R1"]:
        diff = abs(m("pred_event", cell)[0] - m(g, cell)[0])
        if diff >= max_gap:
            max_gap, worst = diff, cell
        a = d[(d.source == "pred_event") & (d.cell == cell)].set_index("qid")["correct"]
        b = d[(d.source == g) & (d.cell == cell)].set_index("qid")["correct"]
        ids = a.index.intersection(b.index)
        min_p = min(min_p, mcnemar(a.loc[ids].to_numpy(), b.loc[ids].to_numpy())["p_value"])
    sig = "No cell differs significantly in a paired test" if min_p >= 0.05 else "At least one cell differs significantly in a paired test"
    parse = d.groupby("cell")["parsed"].mean()
    tl = sorted(d["timeline"].unique())

    summary = f"""# Summary

Five findings from `{csv}` and the per-question traces in `{root}/{split}/`. Model: `{model}`.
{n_q} questions per cell (3 constructed timelines, seeds {", ".join(map(str, tl))}). Scores are accuracy, F1 for interval questions, with 95% bootstrap CIs.

1. **A static memory cannot answer "where is X now".** M0 scores {f(g, "M0_R1", "current_location")} on current-location questions with hybrid retrieval. M1 scores {f(g, "M1_R1", "current_location")}. Source: `{csv}`.
2. **An overwrite memory cannot answer "where was X before".** M1 scores {f(g, "M1_R1", "previous_location")} on previous-location questions. M2 scores {f(g, "M2_R1", "previous_location")}. M0 scores {f(g, "M0_R0", "previous_location")} on the same type because the previous location equals the initial scan pose in most constructed timelines, so this type does not separate M0 from the others. Source: `{csv}`.
3. **Hybrid retrieval helps most with the versioned memory.** M2 overall: R1 {f(g, "M2_R1")}, R0 {f(g, "M2_R0")}; paired difference {r_m2h["acc_diff"]:+.2f}, McNemar p = {r_m2h["p_value"]:.3g}. On when-moved and interval questions only, the paired difference is {r_t["acc_diff"]:+.2f} (n = {nt}, p = {r_t["p_value"]:.3g}). For M1 the difference is {r_m1h["acc_diff"]:+.2f} (p = {r_m1h["p_value"]:.3g}). Source: `{root}/{split}/`.
4. **The versioned memory did not beat the overwrite memory overall.** M2 with hybrid retrieval scores {f(g, "M2_R1")} against {f(g, "M1_R1")} for M1 (paired difference {r_21["acc_diff"]:+.2f}, p = {r_21["p_value"]:.3g}). Without previous-location questions, M1 scores {f(g, "M1_R1", "overall_ex_prev")} and M2 {f(g, "M2_R1", "overall_ex_prev")}. Source: `{csv}`.
5. **Predicted trajectories cost little accuracy.** The largest overall gap between `pred_event` and `gt_event` over the six memory cells is {max_gap:.2f} ({worst}). {sig} (smallest McNemar p = {min_p:.3g}). Source: `figures/tables_{split}.md`.

Paired differences and McNemar p-values use strict correctness (a question is correct only at score 1, so an interval question needs F1 = 1). Cell scores above are mean scores, so the two can differ.

The memory-less baseline scores {f(g, "blind")} overall. Parse failures count as wrong: parse rate is between {parse.min():.2f} and {parse.max():.2f} across cells.
"""

    report = f"""# DynMem: memory update policies for where-and-when questions

## Problem
An agent with a long-term memory sees objects move. A static memory goes stale. This study measures how
three memory update policies and two retrieval designs change the accuracy of where-and-when questions
after objects move. It is a measurement study. It makes no claim of a new state of the art.

## Method
**Data.** The Lost & Found dataset: 96 egocentric pick-and-place recordings of 9 objects in one scene.
Each recording holds one move. Trajectories are mapped into the scan frame with the inverse of the stored
ICP transform. Moves are found by a speed threshold chosen on the dev split.

**Constructed timelines.** Recordings are placed on a synthetic clock with random gaps of 3 to 20 minutes.
Timelines are constructed. They are not a continuous real-world log. Three timelines (seeds {", ".join(map(str, tl))}) were built from
the 69 test recordings. 27 recordings form the dev split. No recording is in both.

**Memory policies.** M0 static (initial scan only). M1 overwrite (one entry per object). M2 versioned
(append-only entries with validity intervals).

**Retrieval designs.** R0 vector-only (text similarity). R1 hybrid (composed search with time, position and
object filters, plus per-object history). A blind baseline uses no memory.

**Questions and scoring.** Five templated types: current location, previous location, time of last move,
move count, objects moved in an interval. Scoring is deterministic: position within 0.25 m, time within 10 s,
count exact, interval by F1. Answers are always scored against ground truth. Event sources: ground truth
(`gt_event`) and Lost & Found predictions (`pred_event`).

**Agent.** `{model}` with tool calling, at most 3 retrieval rounds, strict JSON answers. A parse failure scores 0.
Temperature 0. Every call is cached on disk. Prompts, tools and tolerances were tuned on dev in one round and
frozen (hashes in `configs/frozen_hashes.json`) before the test run.

## Results
Per cell and question type: `figures/tables_{split}.md` and `figures/stage_b_heatmap_{split}.png`.
Test set, {n_q} questions per cell, `gt_event`:

| cell | overall | overall without previous location |
|---|---|---|
""" + "\n".join(f"| {c} | {f(g, c)} | {f(g, c, 'overall_ex_prev')} |" for c in ["M0_R0", "M0_R1", "M1_R0", "M1_R1", "M2_R0", "M2_R1", "blind"]) + f"""

Hybrid retrieval raises the versioned memory from {m(g, "M2_R0")[0]:.2f} to {m(g, "M2_R1")[0]:.2f} overall (p = {r_m2h["p_value"]:.3g}).
The versioned memory is not better than the overwrite memory overall (p = {r_21["p_value"]:.3g}).
Predicted events change accuracy by at most {max_gap:.2f} in any memory cell ({sig.lower()}; smallest p = {min_p:.3g}).
Paired differences and p-values use strict correctness (score 1); cell scores are mean scores.

## Hypotheses
- **H1** (rebuilt ReMEmbR-style agent matches published correctness): not tested. Stage A was not run.
- **H2** (static fails on "now", overwrite fails on "before", versioned answers both): the first two held
  (M0 current location {m(g, "M0_R1", "current_location")[0]:.2f}; M1 previous location {m(g, "M1_R1", "previous_location")[0]:.2f}).
  The third did not hold for this model: M2 current location {m(g, "M2_R1", "current_location")[0]:.2f}, previous location {m(g, "M2_R1", "previous_location")[0]:.2f}.
- **H3** (hybrid beats vector-only mostly on temporal questions): held for M2 (largest gains on when-moved and
  interval questions, paired difference {r_t["acc_diff"]:+.2f}), weak for M1 ({r_m1h["acc_diff"]:+.2f}).
- **H4** (predicted trajectories lower accuracy only slightly): {'held' if max_gap < 0.05 and min_p >= 0.05 else 'did not hold'}. Largest overall gap {max_gap:.2f}; smallest paired p = {min_p:.3g}.

## Limitations
- Timelines are constructed. They are not a continuous real-world log.
- One scene and nine objects. Three timelines.
- Every recording of an object starts from nearly the same pose, so the previous location is usually the initial
  scan pose. Previous-location questions do not separate M0 from the other policies. Chaining recordings so
  that one move ends where the next begins would remove this.
- The agent is a local 7B model. Absolute accuracy is lower than for frontier models. It often returned the
  current position for previous-location questions and struggled with counts.
- Position and time tolerances were chosen on the dev split.
- Stage A (validation on NaVQA) was not run: it needs hundreds of GB of CODa video and a vision captioner.
- Test size was cut from 150 to 60 questions per timeline (see `DEVIATIONS.md`).
- No robot hardware is used.

## Data and licenses
Lost & Found (Zenodo 14967441, arXiv 2411.19162): CC BY 4.0. Code: MIT. No dataset files are in the repository.
ReMEmbR (arXiv 2409.13682) and CODa are cited as background; neither dataset was used.
"""
    return summary, report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/stage_b_local")
    ap.add_argument("--split", default="test")
    a = ap.parse_args(argv)
    summary, report = build(a.root, a.split)
    Path("SUMMARY.md").write_text(summary)
    Path("REPORT.md").write_text(report)
    print("wrote SUMMARY.md, REPORT.md")


if __name__ == "__main__":
    main()
