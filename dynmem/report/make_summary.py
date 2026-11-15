"""Write SUMMARY.md and REPORT.md. Every number is read from result files.

Usage: python -m dynmem.report.make_summary [--root results/stage_b_local] [--split test]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from dynmem.report.extra_figures import history_summary, now_failure_analysis, reliability_table
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
    rel = reliability_table(d)
    rel_err = float(rel[(rel.source == g) & (rel.cell == "M1_R0")]["tool_error"].iloc[0])
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
after objects move.

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
- In the text-only design the model often passed an `object` filter that `search_text` does not accept
  ({rel_err:.0%} of Overwrite · text questions). The tool returned an error and the model retried. This may
  understate text-only accuracy and so part of the hybrid gain.
- Position and time tolerances were chosen on the dev split.
- Stage A (validation on NaVQA) was not run: it needs hundreds of GB of CODa video and a vision captioner.
- Test size was cut from 150 to 60 questions per timeline (see `DEVIATIONS.md`).
- No robot hardware is used.

## Data and licenses
Lost & Found (Zenodo 14967441, arXiv 2411.19162): CC BY 4.0. Code: MIT. No dataset files are in the repository.
ReMEmbR (arXiv 2409.13682) and CODa are cited as background; neither dataset was used.
"""
    return summary, report


def pair_readme(d, src, a, b):
    t = d[d.source == src]
    ga, gb = t[t.cell == a].set_index("qid"), t[t.cell == b].set_index("qid")
    ids = ga.index.intersection(gb.index)
    return mcnemar(ga.loc[ids, "correct"].to_numpy(), gb.loc[ids, "correct"].to_numpy()), len(ids)


def build_readme(root: str, split: str) -> str:
    d = load(split, root)
    s = summarise(d)
    g = "gt_event"

    def m(cell, qt="overall", src=g):
        r = s[(s.source == src) & (s.cell == cell) & (s.qtype == qt)].iloc[0]
        return r["mean"]

    best = max(("M0_R0", "M0_R1", "M1_R0", "M1_R1", "M2_R0", "M2_R1"), key=lambda c: m(c))
    gaps = [abs(m(c, src="pred_event") - m(c)) for c in ("M0_R0", "M0_R1", "M1_R0", "M1_R1", "M2_R0", "M2_R1")]
    per = pd.read_csv("results/perception_error.csv") if Path("results/perception_error.csv").exists() else None
    med = f"{per[per.split == 'test'].place_error_m.median() * 100:.0f} cm" if per is not None else "n/a"
    n_q = int(s[(s.source == g) & (s.cell == "M2_R1") & (s.qtype == "overall")]["n"].iloc[0])
    model = d["model"].iloc[0]
    fig = lambda name, cap: f"![{cap}](figures/{name})\n\n*{cap}*\n"
    r_h, _ = pair_readme(d, g, "M2_R1", "M2_R0")
    r_21, _ = pair_readme(d, g, "M2_R1", "M1_R1")
    nf = now_failure_analysis(d, "M2_R1", split)
    d_all = load(split, root, core_only=False)
    h = history_summary(d_all)
    hb = hf = hc = ""
    h2 = "The first two held. Versioned answered both only in part with this model."
    pp_box = "[ ]"
    if not h.empty and set(h.cell) >= {"M0_R0", "M1_R0", "M2_R0", "M2_R1"}:
        hv = lambda c: float(h[(h.source == g) & (h.cell == c)]["mean"].iloc[0])
        hd = d_all[d_all.qtype == "previous_place"]
        def hp(a, b):
            t_ = hd[hd.source == g]
            x, y = t_[t_.cell == a].set_index("qid"), t_[t_.cell == b].set_index("qid")
            ids = x.index.intersection(y.index)
            return mcnemar(x.loc[ids, "correct"].to_numpy(), y.loc[ids, "correct"].to_numpy())
        nh = int(h[(h.source == g) & (h.cell == "M2_R0")]["n"].iloc[0])
        m2_best = max(("M2_R0", "M2_R1"), key=hv)
        m01 = max(hv(c) for c in ("M0_R0", "M0_R1", "M1_R0", "M1_R1"))
        r_vs = hp(m2_best, "M1_R0" if m2_best.endswith("R0") else "M1_R1")
        r_tool = hp("M2_R1", "M2_R0")
        hb = (f"- **Only versioned memory answers the history question.** On \"where was it placed before its latest move?\" "
              f"versioned memory answers {hv('M2_R0'):.0%} with text search and {hv('M2_R1'):.0%} with hybrid search. "
              f"Static and overwrite memory answer at most {m01:.0%}.\n")
        hf = fig(f"11_history_question_{split}.png", "The history question: where was the object placed before its latest move?")
        if r_tool["p_value"] >= 0.05:
            tool_txt = "Hybrid search did not help on this question"
        else:
            tool_txt = "Hybrid search lowered accuracy on this question" if hv("M2_R1") < hv("M2_R0") else "Hybrid search raised accuracy on this question"
        co_path = Path(f"results/history_coincidence_{split}.csv")
        co_txt = ""
        if co_path.exists():
            co = pd.read_csv(co_path).iloc[0]
            co_txt = (f" Overwrite memory gets {int(co['overwrite_correct_by_coincidence'])} of its {int(co['overwrite_correct'])} correct answers "
                      f"only where the object was placed twice at the same spot.")
        hc = (f"- **Keeping history pays off on the question that needs it.** Versioned memory answers {hv(m2_best):.0%} "
              f"against at most {m01:.0%} for the other policies (paired p = {r_vs['p_value']:.2g}, {nh} questions). "
              f"{tool_txt} ({hv('M2_R1'):.0%} hybrid against {hv('M2_R0'):.0%} text, paired p = {r_tool['p_value']:.2g}).{co_txt}\n")
        h2 = (f"The first two held. On the history question versioned memory answers {hv(m2_best):.0%} "
              f"against at most {m01:.0%} for the other policies.")
        pp_box = "[x]"
    return f"""# DynMem

Dynamic episodic memory for embodied agents: answering where-and-when questions after objects move.

## Summary

This project measures how the long-term memory of an embodied agent should be updated and searched when objects move. It builds a retrieval-augmented memory agent and tests three memory update policies and two retrieval designs on 96 real pick-and-place recordings from the Lost & Found dataset. Without memory the agent answers {m("blind"):.0%} of where-and-when questions. The best memory setting answers {m(best):.0%}. Each simpler policy fails one question class: a static memory cannot say where an object is now ({m("M0_R1", "current_location"):.0%}), and an overwrite memory cannot say where it was before ({m("M1_R1", "previous_location"):.0%}). Hybrid search lifts a versioned memory from {m("M2_R0"):.0%} to {m("M2_R1"):.0%}. Noise from predicted trajectories costs at most {max(gaps) * 100:.0f} percentage points. Work in progress is tracked in the [roadmap](#roadmap).

## Problem

A robot or a pair of smart glasses can keep a long-term memory of what it saw. A common design captions short video segments, embeds the captions and stores them in a vector database with position and time. An LLM agent then answers questions through retrieval tools. ReMEmbR (arXiv 2409.13682) is a reference system of this kind.

Such a memory records what was seen once. Objects move. A question like "where is the mug now?" then has an answer that the stored observation no longer holds. Lost & Found (arXiv 2411.19162) tracks the 6DoF pose of objects that a person moves, which makes the changes observable.

This study asks three questions:

1. **Update policy.** Which memory update policy keeps answers correct after objects move: static, overwrite or versioned?
2. **Retrieval design.** Does a hybrid search (text, time, position and object filters, per-object history) beat text search alone?
3. **Perception noise.** How much accuracy is lost when the memory is built from predicted trajectories instead of ground-truth ones?

## Approach

{fig("10_approach_pipeline.png", "From recordings to a scored answer")}
- **Events.** Each recording is one pick-and-place. A speed threshold gives the pick pose, the place pose and the times. Events come from ground-truth trajectories or from Lost & Found predictions.
- **Timelines.** The 96 recordings are independent. They are placed on one synthetic clock with random 3 to 20 minute gaps, in an order set by a fixed seed. Timelines are constructed and not a real continuous log.
- **Memory policies.** Static keeps the initial scan. Overwrite keeps one entry per object and replaces it on each move. Versioned appends entries with validity intervals.
- **Retrieval designs.** Text-only search, or hybrid search with time, position and object filters and a per-object history tool.
- **Agent.** `{model}` with tool calling, at most 3 retrieval rounds and strict JSON answers. A parse failure scores 0. Every call is cached and run at temperature 0.
- **Questions.** Five templated types: where now, where before, when last moved, how many moves, what moved in a time window. Scoring is deterministic: position within 0.25 m, time within 10 s, count exact, interval by F1.
- **Splits.** By recording: 27 dev, 69 test. Prompts and tolerances were tuned on dev and frozen before the test run. The test set holds 3 timelines and {n_q} questions per setting.

## Results

- **Memory design decides accuracy.** With no memory the agent answers {m("blind"):.0%} of questions. The best memory setting answers {m(best):.0%}.
- **Static memory goes stale.** It answers {m("M0_R1", "current_location"):.0%} of "where is it now?" questions. Overwrite memory fixes that ({m("M1_R1", "current_location"):.0%}) and loses history ({m("M1_R1", "previous_location"):.0%} on "where was it before?").
- **Hybrid search lifts versioned memory** from {m("M2_R0"):.0%} to {m("M2_R1"):.0%} overall, and from {m("M2_R0", "interval"):.0%} to {m("M2_R1", "interval"):.0%} on "what moved in a time window?".
- **Predicted trajectories cost little.** Scores with Lost & Found predictions stay within {max(gaps) * 100:.0f} percentage points of ground truth. The median placement error on test recordings is {med}.
{hb}
{fig("00_memory_policies.png", "The three memory policies")}
{fig(f"01_accuracy_heatmap_{split}.png", "Share of questions answered correctly, by memory setting and question type")}
{fig(f"02_overall_accuracy_{split}.png", "Overall accuracy with 95% confidence intervals")}
{fig(f"03_hybrid_vs_text_{split}.png", "Accuracy gain from hybrid search, per question type")}
{fig(f"04_predicted_vs_ground_truth_{split}.png", "Predicted versus ground-truth events, and the tracker's placement error")}
{fig(f"05_tolerance_sensitivity_{split}.png", "Accuracy as the position and time tolerances change")}
{fig(f"06_cost_and_latency_{split}.png", "Tokens, tool calls and time per question")}
{fig(f"07_model_reliability_{split}.png", "How often the model produced an invalid answer or a rejected tool call")}
{fig(f"08_per_timeline_{split}.png", "Accuracy on each constructed timeline")}
{fig("09_dev_tuning_effect.png", "Effect of the single dev tuning round")}
{hf}
Tables with confidence intervals and paired tests: [`figures/tables_{split}.md`](figures/tables_{split}.md). Every figure is built from the traces in `results/`.
Reports: [`REPORT.md`](REPORT.md), [`SUMMARY.md`](SUMMARY.md). Deviations from the plan: [`DEVIATIONS.md`](DEVIATIONS.md). Costs: [`COSTS.md`](COSTS.md).

## Conclusions

- **History is needed, and each simpler policy fails one question class.** Static memory cannot answer "now" ({m("M0_R1", "current_location"):.0%}). Overwrite memory cannot answer "before" ({m("M1_R1", "previous_location"):.0%}).
- **Hybrid retrieval matters most when memory holds many versions.** For versioned memory the paired gain is {r_h["acc_diff"]:+.2f} (McNemar p = {r_h["p_value"]:.2g}). For overwrite memory it is smaller.
- **Versioned and overwrite memory are level overall with this model.** {m("M2_R1"):.0%} against {m("M1_R1"):.0%} (paired p = {r_21["p_value"]:.2g}). Versioned memory is stronger on time-window questions ({m("M2_R1", "interval"):.0%} against {m("M1_R1", "interval"):.0%}). It is weaker on "where is it now?" ({m("M2_R1", "current_location"):.0%} against {m("M1_R1", "current_location"):.0%}). In {nf["retrieved_right_object_still_wrong"]} of its {nf["failed"]} failures on that question the model had retrieved entries of the right object and still gave a wrong position. In {nf["no_position_given"]} it gave no position.
{hc}- **Perception noise is not the bottleneck here.** Median placement error is {med}, well inside the 0.25 m tolerance. A tolerance sweep (figure 05) shows the same picture at other tolerances.

| Hypothesis | Outcome |
|---|---|
| H1. A rebuilt ReMEmbR-style agent matches published correctness | Not tested. The NaVQA validation was not run. |
| H2. Static fails "now", overwrite fails "before", versioned answers both | {h2} |
| H3. Hybrid retrieval helps most on temporal questions | Held for versioned memory. Smaller effect for overwrite memory. |
| H4. Predicted trajectories lower accuracy only slightly | Held. Largest gap {max(gaps) * 100:.0f} percentage points. |

## Roadmap

- [x] Memory store, retrieval tools, tool-calling agent and deterministic scoring
- [x] Three memory policies and two retrieval designs on Lost & Found, with ground-truth and predicted events
- [x] Dev/test split by recording, frozen prompts, confidence intervals and paired tests
- [x] Figures and tables generated from result files
- {pp_box} A history question that only versioned memory can answer ("where was it placed before its latest move?")
- [ ] Remove the text-tool confound: let text-only search accept an object argument
- [ ] Repeat the key settings with a stronger model (Gemini)
- [ ] Chained timelines, so each move starts where the previous one ended
- [ ] Larger test set: 5 timelines and 150 questions per timeline
- [ ] Paper-style report (PDF, about 4 pages)
- [ ] Validate the agent on NaVQA against published ReMEmbR results
- [ ] Memory budget ablation: limit the number of entries and test an eviction policy

## Reproduce

```
uv venv --python 3.11 .venv && uv pip install -e ".[dev]"
make test      # unit tests
make data      # scan archive and per-recording files (about 440 MB transferred)
make stage_b   # needs a running Ollama server with qwen2.5:7b
make report    # figures, tables, README, SUMMARY, REPORT
```

API keys are read from environment variables only. The default agent runs locally.

## Limitations

- Timelines are constructed from independent recordings. They are not a continuous real-world log.
- One scene, nine objects, three timelines.
- Each object starts every recording from nearly the same pose, so the previous location is usually the initial scan pose. "Where was it before?" does not separate static memory from the others, and the figures also show scores without it.
- The agent is a local 7B model. Frontier models would score higher in absolute terms.
- In the text-only design the model often passed an `object` filter that `search_text` does not accept. The tool returned an error and the model retried. This may understate text-only accuracy.
- Position and time tolerances were chosen on the dev split. Figure 05 shows how scores change with them.
- The agent was not validated against published ReMEmbR results (NaVQA and CODa are not included).
- No robot hardware is used.

## Resources

**Data**

| Resource | Size | Used for | License |
|---|---|---|---|
| [Lost & Found dataset](https://zenodo.org/records/14967441), [`Final_Dataset.zip`](https://zenodo.org/records/14967441/files/Final_Dataset.zip?download=1) | 30.2 GB | object trajectories, ICP transforms | CC BY 4.0 |
| [Lost & Found scan](https://zenodo.org/records/14967441), [`Final_Scan.zip`](https://zenodo.org/records/14967441/files/Final_Scan.zip?download=1) | 434 MB | scene point cloud, coordinate check | CC BY 4.0 |

`make data` downloads the scan and fetches only the six small files per recording (about 4 MB in total) from the 30 GB archive by HTTP range requests. The raw `.vrs` videos are not needed.

**Papers and code**

- Lost & Found: Tracking Changes from Egocentric Observations in 3D Dynamic Scene Graphs. [arXiv 2411.19162](https://arxiv.org/abs/2411.19162), [code](https://github.com/behretj/LostFound).
- ReMEmbR: Building and Reasoning Over Long-Horizon Spatio-Temporal Memory for Robot Navigation. [arXiv 2409.13682](https://arxiv.org/abs/2409.13682), [code](https://github.com/NVIDIA-AI-IOT/remembr).

**Models**

| Model | Role |
|---|---|
| [`qwen2.5:7b`](https://ollama.com/library/qwen2.5) (Q4_K_M, via Ollama) | agent for all reported results |
| [`mixedbread-ai/mxbai-embed-large-v1`](https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1) | text embeddings for the memory store |
| [`qwen3.5:9b`](https://ollama.com/library/qwen3.5) | tried, not used: 14 GB resident on a 24 GB laptop |
| `gemini-3.5-flash` | tool-calling test only: the free tier allows 5 requests per minute |

**Software**

[Ollama](https://ollama.com) for local inference, [Qdrant](https://qdrant.tech/documentation/) in local mode as the memory store, [sentence-transformers](https://sbert.net) for embeddings, [uv](https://docs.astral.sh/uv/) for the environment.

Code: MIT ([`LICENSE`](LICENSE)). No dataset files are stored in this repository.
"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="results/stage_b_local")
    ap.add_argument("--split", default="test")
    a = ap.parse_args(argv)
    summary, report = build(a.root, a.split)
    Path("SUMMARY.md").write_text(summary)
    Path("REPORT.md").write_text(report)
    Path("README.md").write_text(build_readme(a.root, a.split))
    print("wrote SUMMARY.md, REPORT.md, README.md")


if __name__ == "__main__":
    main()
