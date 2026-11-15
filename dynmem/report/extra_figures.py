"""Readable, self-explaining figures for Stage B. Everything is drawn from result files.

Colour = memory policy (validated 3-slot categorical palette: blue, orange, aqua; grey for no memory).
Texture = retrieval design (hatched = text search only, solid = hybrid). Dashed = predicted events.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
POLICY_COLOR = {"M0": "#2a78d6", "M1": "#eb6834", "M2": "#1baf7a", "blind": "#8b8a85"}
CELLS = ["M0_R0", "M0_R1", "M1_R0", "M1_R1", "M2_R0", "M2_R1", "blind"]
MEMORY_CELLS = CELLS[:-1]
LABEL = {"M0_R0": "Static · text", "M0_R1": "Static · hybrid", "M1_R0": "Overwrite · text",
         "M1_R1": "Overwrite · hybrid", "M2_R0": "Versioned · text", "M2_R1": "Versioned · hybrid",
         "blind": "No memory"}
POLICY_NAME = {"M0": "Static (initial scan only)", "M1": "Overwrite (latest pose only)",
               "M2": "Versioned (full history)", "blind": "No memory"}
QTYPES = ["current_location", "previous_location", "when_moved", "count", "interval"]
QLABEL = {"current_location": "Where is it\nnow?", "previous_location": "Where was it\nbefore?",
          "when_moved": "When was it\nlast moved?", "count": "How many\nmoves?", "interval": "What moved in\na time window?"}


def style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK2, "text.color": INK, "xtick.color": INK2,
        "ytick.color": INK2, "font.size": 10.5, "axes.titlesize": 12.5, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "legend.frameon": False, "font.family": "DejaVu Sans",
    })


def bar_kwargs(cell: str) -> dict:
    pol = cell.split("_")[0]
    c = POLICY_COLOR[pol]
    if cell == "blind":
        return dict(color=c, edgecolor=c)
    if cell.endswith("R0"):  # text search only: hatched, light fill
        return dict(facecolor=SURFACE, edgecolor=c, hatch="////", linewidth=1.4)
    return dict(color=c, edgecolor=c)  # hybrid: solid


def design_legend(ax, loc="upper left", extra=()):
    h = [Patch(facecolor=POLICY_COLOR[p], label=POLICY_NAME[p]) for p in ("M0", "M1", "M2")]
    h += [Patch(facecolor=SURFACE, edgecolor=INK2, hatch="////", label="Text search only"),
          Patch(facecolor=INK2, edgecolor=INK2, label="Hybrid search")] + list(extra)
    ax.legend(handles=h, loc=loc, fontsize=9)


def get(s, src, cell, qt="overall"):
    r = s[(s.source == src) & (s.cell == cell) & (s.qtype == qt)].iloc[0]
    return r["mean"], r["ci_lo"], r["ci_hi"]


def save(fig, out: Path, name: str) -> None:
    out.mkdir(exist_ok=True)
    fig.savefig(out / name, dpi=170, bbox_inches="tight")
    plt.close(fig)


# 0. What each memory keeps (schematic, no data)
def fig_policies(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5.2); ax.axis("off"); ax.grid(False)
    ax.set_title("What each memory keeps when an object is moved twice", pad=14)
    ax.annotate("", xy=(9.8, 4.55), xytext=(0.2, 4.55), arrowprops=dict(arrowstyle="->", color=INK2))
    ax.text(0.2, 4.8, "time", color=INK2, fontsize=10)
    for x, lab in ((3.2, "moved"), (6.4, "moved again")):
        ax.plot([x, x], [0.35, 4.55], color=GRID, lw=1.5, zorder=0)
        ax.text(x, 4.8, lab, ha="center", color=INK2, fontsize=10)
    rows = [("Static", "M0", [(0.2, 9.8, "Start: at A  (never updated)")]),
            ("Overwrite", "M1", [(6.4, 9.8, "Now: at C")]),
            ("Versioned", "M2", [(0.2, 3.2, "At A"), (3.2, 6.4, "At B"), (6.4, 9.8, "At C")])]
    for k, (name, pol, segs) in enumerate(rows):
        y = 3.3 - k * 1.45
        ax.text(0.0, y + 0.25, name, ha="right", va="center", fontsize=11, fontweight="bold", color=INK)
        for a, b, txt in segs:
            ax.add_patch(plt.Rectangle((a + 0.04, y), b - a - 0.08, 0.5, color=POLICY_COLOR[pol]))
            ax.text((a + b) / 2, y + 0.25, txt, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    ax.text(0.0, 0.05, "", fontsize=1)
    ax.text(5.0, -0.25, "Static fails \"where is it now\"; Overwrite fails \"where was it before\"; "
            "Versioned keeps both.", ha="center", color=INK2, fontsize=10.5)
    ax.set_xlim(-1.3, 10)
    save(fig, out, "00_memory_policies.png")


# 1. Hero heatmap
def fig_heatmap(s, out: Path, src="gt_event", split="test") -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    M = np.array([[get(s, src, c, q)[0] for q in QTYPES] for c in CELLS])
    im = ax.imshow(M, vmin=0, vmax=1, cmap="YlGnBu", aspect="auto")
    ax.grid(False)
    ax.set_xticks(range(len(QTYPES)), [QLABEL[q] for q in QTYPES], fontsize=10)
    ax.set_yticks(range(len(CELLS)), [LABEL[c] for c in CELLS], fontsize=10.5)
    ax.xaxis.tick_top()
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.0%}", ha="center", va="center", fontsize=12, fontweight="bold",
                    color="white" if M[i, j] > 0.55 else INK)
    j = QTYPES.index("previous_location")
    ax.add_patch(plt.Rectangle((j - .5, -.5), 1, len(CELLS) - 1, fill=False, ec=POLICY_COLOR["M1"], lw=2.5, ls="--"))
    ax.set_title("Share of questions answered correctly, by memory and question", pad=40, loc="left")
    ax.text(j, len(CELLS) - 0.35, "dashed: previous pose = start pose\nin most timelines, so Static scores high",
            ha="center", va="top", fontsize=9, color=POLICY_COLOR["M1"])
    for sp in ax.spines.values():
        sp.set_visible(False)
    save(fig, out, f"01_accuracy_heatmap_{split}.png")


# 2. Overall bars with and without previous-location
def fig_overall(s, out: Path, src="gt_event", split="test") -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    xs = {"M0_R0": 0, "M0_R1": 1, "M1_R0": 2.5, "M1_R1": 3.5, "M2_R0": 5, "M2_R1": 6, "blind": 8.1}
    for ax, qt, ttl in zip(axes, ("overall", "overall_ex_prev"),
                           ("All question types", "Without \"where was it before?\"")):
        for c in CELLS:
            m, lo, hi = get(s, src, c, qt)
            ax.bar(xs[c], m, 0.85, **bar_kwargs(c))
            ax.errorbar(xs[c], m, yerr=[[m - lo], [hi - m]], color=INK, lw=1.3, capsize=3)
            ax.text(xs[c], hi + 0.025, f"{m:.0%}", ha="center", fontsize=10.5, fontweight="bold")
        ax.set_xticks([xs[c] for c in CELLS], [("text" if c.endswith("R0") else "hybrid") if c != "blind" else "" for c in CELLS], fontsize=9.5)
        for name, x in (("Static", 0.5), ("Overwrite", 3.0), ("Versioned", 5.5), ("No memory", 8.1)):
            ax.text(x, -0.115, name, transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=10.5,
                    fontweight="bold", color=INK)
        ax.set_ylim(0, 1.0); ax.set_title(ttl)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Questions answered correctly")
    design_legend(axes[0], loc="upper left")
    fig.suptitle("Overall accuracy per memory setting (error bars: 95% confidence interval)", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", y=1.02)
    save(fig, out, f"02_overall_accuracy_{split}.png")


# 3. Does hybrid search help? dumbbell per question type
def fig_hybrid(s, out: Path, src="gt_event", split="test") -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2), sharey=True)
    for ax, pol in zip(axes, ("M0", "M1", "M2")):
        for k, q in enumerate(QTYPES + ["overall"]):
            a, b = get(s, src, f"{pol}_R0", q)[0], get(s, src, f"{pol}_R1", q)[0]
            y = len(QTYPES) - k
            ax.plot([a, b], [y, y], color=GRID, lw=3, zorder=1)
            ax.scatter(a, y, s=70, facecolor=SURFACE, edgecolor=POLICY_COLOR[pol], lw=2, zorder=3)
            ax.scatter(b, y, s=70, color=POLICY_COLOR[pol], zorder=3)
            if abs(b - a) >= 0.08:
                ax.text(max(a, b) + 0.04, y, f"{b - a:+.0%}", va="center", fontsize=9.5, color=INK)
        ax.set_xlim(-0.02, 1.15); ax.set_title(POLICY_NAME[pol].split(" (")[0])
        ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        ax.set_yticks(range(len(QTYPES), -1, -1), [QLABEL[q].replace("\n", " ") for q in QTYPES] + ["Overall"])
        ax.grid(axis="y", visible=False)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=INK2, mew=2, ms=9, label="Text search only"),
                        Line2D([], [], marker="o", ls="", color=INK2, ms=9, label="Hybrid search")],
               loc="lower center", ncol=2, fontsize=10, bbox_to_anchor=(0.5, -0.07))
    fig.suptitle("Does hybrid search help? Accuracy with text search only (open) vs hybrid (filled)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", y=1.02)
    save(fig, out, f"03_hybrid_vs_text_{split}.png")


# 4. Ground truth vs predicted events: accuracy and perception error
def fig_pred(s, out: Path, split="test", perception: Path = Path("results/perception_error.csv")) -> None:
    has_p = perception.exists()
    fig, axes = plt.subplots(1, 2 if has_p else 1, figsize=(12 if has_p else 6, 4.7))
    axes = np.atleast_1d(axes)
    ax = axes[0]
    ax.plot([0, 1], [0, 1], color=GRID, lw=2, zorder=0)
    gaps = []
    for c in MEMORY_CELLS:
        g, p = get(s, "gt_event", c)[0], get(s, "pred_event", c)[0]
        gaps.append(abs(p - g))
        col = POLICY_COLOR[c.split("_")[0]]
        ax.scatter(g, p, s=110, **(dict(color=col) if c.endswith("R1") else dict(facecolor=SURFACE, edgecolor=col, linewidth=2.2)))
    ax.set_xlim(0, 0.8); ax.set_ylim(0, 0.8)
    ax.set_xlabel("Accuracy with ground-truth events"); ax.set_ylabel("Accuracy with predicted events")
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}"); ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_title(f"Predicted events score within {max(gaps):.0%} of ground truth")
    ax.text(0.78, 0.03, "on the line = no loss", ha="right", fontsize=9, color=INK2)
    design_legend(ax, loc="upper left")
    if has_p:
        df = pd.read_csv(perception)
        ax = axes[1]
        for sp, col in (("test", POLICY_COLOR["M2"]), ("dev", POLICY_COLOR["M1"])):
            v = np.sort(df[df.split == sp].place_error_m.to_numpy())
            ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=col, lw=2.4,
                    label=f"{sp} recordings (n={len(v)})")
        ax.axvline(0.25, color=INK2, ls="--", lw=1.4)
        ax.text(0.28, 0.5, "scoring tolerance\n0.25 m", fontsize=9, color=INK2)
        ax.set_xscale("log"); ax.set_xlim(0.004, 3)
        ax.set_xlabel("Error of the predicted placement position (m, log scale)")
        ax.set_ylabel("Share of recordings with error ≤ x"); ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
        ax.set_title("Perception error of the tracker"); ax.legend(loc="upper left", fontsize=9)
    save(fig, out, f"04_predicted_vs_ground_truth_{split}.png")


# 5. Tolerance sensitivity from stored answers
def tolerance_table(d: pd.DataFrame) -> pd.DataFrame:
    rows = []
    pos_tol = np.round(np.geomspace(0.05, 2.0, 15), 3)
    time_tol = np.round(np.geomspace(1, 600, 15), 1)
    for (src, cell), g in d.groupby(["source", "cell"]):
        for kind, qts, tols in (("position_m", ("current_location", "previous_location"), pos_tol),
                                ("time_s", ("when_moved",), time_tol)):
            gg = g[g.qtype.isin(qts)]
            err = []
            for _, r in gg.iterrows():
                a = r["answer"] if isinstance(r["answer"], dict) else {}
                if kind == "position_m":
                    p = a.get("position")
                    err.append(math.dist(p, r["gt"]["position"]) if p and len(p) == 3 else math.inf)
                else:
                    t = a.get("time")
                    err.append(abs(t - r["gt"]["time"]) if t is not None else math.inf)
            err = np.array(err)
            for tol in tols:
                rows.append({"source": src, "cell": cell, "kind": kind, "tolerance": tol,
                             "accuracy": float((err <= tol).mean()) if len(err) else float("nan"), "n": len(err)})
    return pd.DataFrame(rows)


def fig_tolerance(d: pd.DataFrame, out: Path, split="test") -> pd.DataFrame:
    t = tolerance_table(d)
    t.to_csv(f"results/benchmark_tolerance_{split}.csv", index=False)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    for ax, kind, xl, chosen in zip(axes, ("position_m", "time_s"),
                                    ("Position tolerance (m, log scale)", "Time tolerance (s, log scale)"), (0.25, 10)):
        for cell in ("M1_R1", "M2_R1"):
            for src, ls in (("gt_event", "-"), ("pred_event", "--")):
                g = t[(t.cell == cell) & (t.source == src) & (t.kind == kind)]
                ax.plot(g.tolerance, g.accuracy, ls=ls, lw=2.4, color=POLICY_COLOR[cell[:2]])
        ax.axvline(chosen, color=INK2, ls=":", lw=1.4)
        ax.text(chosen * 1.06, 0.03, f"chosen\n{chosen:g}", fontsize=9, color=INK2)
        ax.set_xscale("log"); ax.set_ylim(0, 1.02); ax.set_xlabel(xl)
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    axes[0].set_ylabel("Questions answered within tolerance")
    axes[0].set_title("Position questions (now / before)"); axes[1].set_title("Time question (last moved)")
    axes[1].legend(handles=[Line2D([], [], color=POLICY_COLOR["M1"], lw=2.4, label="Overwrite · hybrid"),
                            Line2D([], [], color=POLICY_COLOR["M2"], lw=2.4, label="Versioned · hybrid"),
                            Line2D([], [], color=INK2, lw=2.4, label="ground-truth events"),
                            Line2D([], [], color=INK2, lw=2.4, ls="--", label="predicted events")],
                   loc="lower right", fontsize=9)
    fig.suptitle("Would a different tolerance change the picture? Answers re-scored at other tolerances",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", y=1.02)
    save(fig, out, f"05_tolerance_sensitivity_{split}.png")
    return t


# 6. Cost and latency
def fig_cost(d: pd.DataFrame, out: Path, split="test") -> None:
    g = d[d.source == "gt_event"].groupby("cell").agg(
        tokens=("input_tokens", "mean"), out_tokens=("output_tokens", "mean"), calls=("n_tool_calls", "mean"),
        retr=("retrieval_s", lambda x: 1000 * x.mean()), e2e=("total_s", "mean")).reindex(CELLS)
    g["tok"] = g.tokens + g.out_tokens
    fig, axes = plt.subplots(1, 4, figsize=(14, 4.2), sharey=True)
    spec = [("tok", "Tokens per question", "{:,.0f}"), ("calls", "Tool calls per question", "{:.1f}"),
            ("e2e", "End-to-end seconds", "{:.1f}"), ("retr", "Memory lookup (ms)", "{:.0f}")]
    for ax, (col, ttl, fmt) in zip(axes, spec):
        for i, c in enumerate(CELLS):
            ax.barh(i, g.loc[c, col], 0.7, **bar_kwargs(c))
            ax.text(g.loc[c, col], i, " " + fmt.format(g.loc[c, col]), va="center", fontsize=9.5)
        ax.set_title(ttl, fontsize=11); ax.set_xlim(0, g[col].max() * 1.28); ax.grid(axis="y", visible=False)
    axes[0].set_yticks(range(len(CELLS)), [LABEL[c] for c in CELLS]); axes[0].invert_yaxis()
    fig.suptitle("Cost per question (local model, no API cost). Memory lookup is a tiny part of the time",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", y=1.02)
    save(fig, out, f"06_cost_and_latency_{split}.png")


# 7. Reliability
def reliability_table(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["tool_error"] = d.steps.apply(lambda ss: any(str(x["result"]).startswith("error") for x in ss))
    d["retried"] = d.steps.apply(lambda ss: any(str(x["tool"]).startswith("<empty") for x in ss))
    d["unparsed"] = ~d.parsed
    return d.groupby(["source", "cell"])[["unparsed", "tool_error", "retried"]].mean().reset_index()


def fig_reliability(d: pd.DataFrame, out: Path, split="test") -> pd.DataFrame:
    r = reliability_table(d)
    r.to_csv(f"results/benchmark_reliability_{split}.csv", index=False)
    g = r[r.source == "gt_event"].set_index("cell").reindex(CELLS)
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.0), sharey=True)
    for ax, (col, ttl) in zip(axes, (("unparsed", "Final answer not valid JSON\n(scored 0)"),
                                     ("tool_error", "Tool call rejected\n(argument the tool lacks)"),
                                     ("retried", "Empty model reply\n(retried once)"))):
        for i, c in enumerate(CELLS):
            ax.barh(i, g.loc[c, col], 0.7, **bar_kwargs(c))
            ax.text(g.loc[c, col], i, f" {g.loc[c, col]:.0%}", va="center", fontsize=9.5)
        ax.set_title(ttl, fontsize=11); ax.set_xlim(0, max(0.2, g[col].max() * 1.35)); ax.grid(axis="y", visible=False)
        ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    axes[0].set_yticks(range(len(CELLS)), [LABEL[c] for c in CELLS]); axes[0].invert_yaxis()
    fig.suptitle("How often did the 7B model slip? Share of questions affected", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", y=1.02)
    save(fig, out, f"07_model_reliability_{split}.png")
    return r


# 8. Per-timeline spread
def fig_timelines(d: pd.DataFrame, out: Path, split="test") -> pd.DataFrame:
    g = d[d.source == "gt_event"].groupby(["cell", "timeline"]).score.mean().reset_index()
    g.to_csv(f"results/benchmark_per_timeline_{split}.csv", index=False)
    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    marks = dict(zip(sorted(g.timeline.unique()), "osD"))
    for i, c in enumerate(MEMORY_CELLS):
        v = g[g.cell == c]
        ax.plot([v.score.min(), v.score.max()], [i, i], color=GRID, lw=4, zorder=1)
        for _, r in v.iterrows():
            ax.scatter(r.score, i, marker=marks[r.timeline], s=70, color=POLICY_COLOR[c[:2]], zorder=3)
    ax.set_yticks(range(len(MEMORY_CELLS)), [LABEL[c] for c in MEMORY_CELLS]); ax.invert_yaxis()
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}"); ax.set_xlim(0, 0.9); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Overall accuracy on one timeline (60 questions)")
    ax.legend(handles=[Line2D([], [], marker=m, ls="", color=INK2, label=f"timeline {t}") for t, m in marks.items()],
              loc="lower right", fontsize=9)
    ax.set_title("Accuracy on each of the three constructed timelines")
    save(fig, out, f"08_per_timeline_{split}.png")
    return g


# 9. Effect of the one dev tuning round
def fig_tuning(root: str, out: Path) -> None:
    def load(name):
        rows = [json.loads(l) for f in sorted(Path(root, name).glob("*.jsonl")) for l in f.read_text().splitlines() if l.strip()]
        return pd.DataFrame(rows).groupby("cell").score.mean().reindex(CELLS) if rows else None
    a, b = load("dev_round1"), load("dev")
    if a is None or b is None:
        return
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for i, c in enumerate(CELLS):
        ax.plot([a[c], b[c]], [i, i], color=GRID, lw=4, zorder=1)
        ax.scatter(a[c], i, s=70, facecolor=SURFACE, edgecolor=POLICY_COLOR[c.split("_")[0]], lw=2, zorder=3)
        ax.scatter(b[c], i, s=70, color=POLICY_COLOR[c.split("_")[0]], zorder=3)
        if abs(b[c] - a[c]) >= 0.05:
            ax.text(max(a[c], b[c]) + 0.03, i, f"{b[c] - a[c]:+.0%}", va="center", fontsize=9.5)
    ax.set_yticks(range(len(CELLS)), [LABEL[c] for c in CELLS]); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}"); ax.set_xlim(0, 0.95)
    ax.set_xlabel("Overall accuracy on the dev timeline (60 questions)")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", mfc=SURFACE, mec=INK2, mew=2, label="Before tuning (round 1)"),
                       Line2D([], [], marker="o", ls="", color=INK2, label="After tuning (round 2, frozen)")],
              loc="lower right", fontsize=9)
    ax.set_title("What the single dev tuning round changed (dev split only)")
    save(fig, out, "09_dev_tuning_effect.png")


# 10. Approach overview (schematic, no data)
def fig_pipeline(out: Path) -> None:
    fig, ax = plt.subplots(figsize=(14.4, 3.6))
    ax.set_xlim(0, 14.4); ax.set_ylim(0, 3.6); ax.axis("off"); ax.grid(False)
    boxes = [("Lost & Found\nrecordings", "96 pick-and-place\nvideos, 9 objects"),
             ("Move events", "pick / place pose\nand time"),
             ("Constructed\ntimeline", "one synthetic clock,\n3 to 20 min gaps"),
             ("Memory policy", "static · overwrite ·\nversioned"),
             ("Agent + search", "text only or hybrid,\nup to 3 rounds"),
             ("Scored answer", "checked against\nground truth")]
    w, gap = 1.95, 0.46
    for i, (t, sub) in enumerate(boxes):
        x = 0.15 + i * (w + gap)
        ax.add_patch(plt.Rectangle((x, 0.9), w, 1.9, fc=SURFACE, ec=INK2, lw=1.6, zorder=2))
        ax.text(x + w / 2, 2.35, t, ha="center", va="center", fontsize=11.5, fontweight="bold", color=INK)
        ax.text(x + w / 2, 1.5, sub, ha="center", va="center", fontsize=9.2, color=INK2)
        if i < len(boxes) - 1:
            ax.annotate("", xy=(x + w + gap - 0.05, 1.85), xytext=(x + w + 0.05, 1.85),
                        arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.6))
    x4 = 0.15 + 3 * (w + gap)
    for k, pol in enumerate(("M0", "M1", "M2")):
        ax.add_patch(plt.Rectangle((x4 + 0.12 + k * 0.6, 0.98), 0.54, 0.16, color=POLICY_COLOR[pol], zorder=3))
    ax.text(0.15 + 1.5 * (w + gap) - gap / 2, 0.45, "events come from ground-truth trajectories\nor from Lost & Found predictions",
            ha="center", fontsize=9.5, color=INK2, va="center")
    ax.set_title("Approach: from recordings to a scored answer", pad=6)
    save(fig, out, "10_approach_pipeline.png")


def now_failure_analysis(d: pd.DataFrame, cell: str = "M2_R1", split: str = "test") -> dict:
    """Why did a cell fail 'where is it now?' questions? Counts from the stored traces. Writes a CSV."""
    import re
    c = {"questions": 0, "failed": 0, "retrieved_right_object_still_wrong": 0, "no_position_given": 0,
         "retrieved_nothing_about_object": 0}
    g = d[(d.source == "gt_event") & (d.cell == cell) & (d.qtype == "current_location")]
    for _, r in g.iterrows():
        c["questions"] += 1
        if r["score"] >= 1:
            continue
        c["failed"] += 1
        a = r["answer"] if isinstance(r["answer"], dict) else {}
        if not a.get("position"):
            c["no_position_given"] += 1
            continue
        obj = re.search(r"the (\w+) now", r["question"]).group(1)
        seen = any(f"object={obj}" in str(st["result"]) for st in r["steps"])
        c["retrieved_right_object_still_wrong" if seen else "retrieved_nothing_about_object"] += 1
    pd.DataFrame([c]).to_csv(f"results/benchmark_now_failures_{cell}_{split}.csv", index=False)
    return c


def make_all(d, s, out: Path, split: str, dev_root: str) -> None:
    style()
    fig_policies(out)
    fig_pipeline(out)
    for src in sorted(d.source.unique()):
        if src == "gt_event":
            fig_heatmap(s, out, src, split)
    fig_overall(s, out, "gt_event", split)
    fig_hybrid(s, out, "gt_event", split)
    if "pred_event" in set(d.source):
        fig_pred(s, out, split)
    fig_tolerance(d, out, split)
    fig_cost(d, out, split)
    fig_reliability(d, out, split)
    fig_timelines(d, out, split)
    fig_tuning(dev_root, out)
    now_failure_analysis(d, "M2_R1", split)
