"""Tables and figures from result files only. Nothing here is typed by hand.

Usage: python -m dynmem.report.make_figures [--split test] [--readme]
Reads results/stage_b/<split>/*.jsonl. Writes results/summary_stage_b_<split>.csv,
figures/*.png and figures/tables_<split>.md. With --readme it fills the benchmark block of README.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from dynmem.stats import bootstrap_ci, mcnemar

QTYPES = ["current_location", "previous_location", "when_moved", "count", "interval"]
CELL_ORDER = ["M0_R0", "M0_R1", "M1_R0", "M1_R1", "M2_R0", "M2_R1", "blind"]
PAIRS = [("M2_R1", "M1_R1"), ("M2_R1", "M0_R1"), ("M2_R1", "M2_R0"), ("M1_R1", "M1_R0"), ("M2_R1", "blind")]
README_START, README_END = "<!-- BENCH:START -->", "<!-- BENCH:END -->"


def load(split: str, root="results/stage_b") -> pd.DataFrame:
    rows = [json.loads(l) for f in sorted(Path(root, split).glob("*.jsonl")) for l in f.read_text().splitlines() if l.strip()]
    if not rows:
        raise SystemExit(f"no results under {root}/{split}")
    d = pd.DataFrame(rows)
    d["correct"] = d["score"] >= 1.0  # binary view; interval questions need F1 = 1
    return d


def summarise(d: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (src, cell), g in d.groupby(["source", "cell"]):
        ex = g[g.qtype != "previous_location"]
        for qt, gg in [("overall", g), ("overall_ex_prev", ex)] + list(g.groupby("qtype")):
            m, lo, hi = bootstrap_ci(gg["score"].to_numpy())
            out.append({"source": src, "cell": cell, "qtype": qt, "n": len(gg), "mean": m, "ci_lo": lo, "ci_hi": hi})
    return pd.DataFrame(out)


def fmt(r) -> str:
    return f"{r['mean']:.2f} [{r['ci_lo']:.2f}, {r['ci_hi']:.2f}]"


def accuracy_table(s: pd.DataFrame, source: str) -> str:
    t = s[s.source == source]
    cols = ["overall", "overall_ex_prev"] + QTYPES
    lines = [f"| cell | n | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    for cell in CELL_ORDER:
        g = t[t.cell == cell].set_index("qtype")
        if g.empty:
            continue
        lines.append(f"| {cell} | {int(g.loc['overall', 'n'])} | " + " | ".join(fmt(g.loc[c]) if c in g.index else "-" for c in cols) + " |")
    return "\n".join(lines)


def paired_table(d: pd.DataFrame, source: str) -> str:
    lines = ["| A | B | n | acc A - acc B | A only | B only | McNemar p |", "|---|---|---|---|---|---|---|"]
    t = d[d.source == source]
    for a, b in PAIRS:
        ga, gb = t[t.cell == a].set_index("qid"), t[t.cell == b].set_index("qid")
        ids = ga.index.intersection(gb.index)
        if len(ids) == 0:
            continue
        r = mcnemar(ga.loc[ids, "correct"].to_numpy(), gb.loc[ids, "correct"].to_numpy())
        lines.append(f"| {a} | {b} | {len(ids)} | {r['acc_diff']:+.2f} | {r['n_a_only']} | {r['n_b_only']} | {r['p_value']:.3g} |")
    return "\n".join(lines)


def source_table(d: pd.DataFrame) -> str:
    lines = ["| cell | n | acc gt_event | acc pred_event | diff (pred - gt) | pred only | gt only | McNemar p |",
             "|---|---|---|---|---|---|---|---|"]
    for cell in CELL_ORDER:
        g = d[(d.cell == cell) & (d.source == "gt_event")].set_index("qid")
        p = d[(d.cell == cell) & (d.source == "pred_event")].set_index("qid")
        ids = g.index.intersection(p.index)
        if len(ids) == 0:
            continue
        r = mcnemar(p.loc[ids, "correct"].to_numpy(), g.loc[ids, "correct"].to_numpy())
        lines.append(f"| {cell} | {len(ids)} | {g.loc[ids, 'correct'].mean():.2f} | {p.loc[ids, 'correct'].mean():.2f} | "
                     f"{r['acc_diff']:+.2f} | {r['n_a_only']} | {r['n_b_only']} | {r['p_value']:.3g} |")
    return "\n".join(lines)


def cost_table(d: pd.DataFrame) -> pd.DataFrame:
    d = d[d.source == "gt_event"]  # pred_event rows for M0 and blind are cache hits (wall time about 0)
    g = d.groupby(["source", "cell"]).agg(
        n=("qid", "size"), tool_calls=("n_tool_calls", "mean"), input_tokens=("input_tokens", "mean"),
        output_tokens=("output_tokens", "mean"), retrieval_ms=("retrieval_s", lambda x: 1000 * x.mean()),
        end_to_end_s=("total_s", "mean"), parse_rate=("parsed", "mean")).reset_index()
    g["cell"] = pd.Categorical(g["cell"], CELL_ORDER, ordered=True)
    return g.sort_values(["source", "cell"])


def md(df: pd.DataFrame, floatfmt="{:.2f}") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(floatfmt.format(v) if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(lines)


def failure_table(d: pd.DataFrame, per_cell: int = 5) -> str:
    out = []
    for (src, cell), g in d[d.score < 1.0].groupby(["source", "cell"]):
        out.append(f"### {src} / {cell}")
        for _, r in g.head(per_cell).iterrows():
            ans = (r["answer"] or {}) if isinstance(r["answer"], dict) else {}
            calls = "; ".join(f"{s['tool']}({json.dumps(s['args'])})" for s in r["steps"]) or "none"
            out.append(f"- `{r['qid']}` ({r['qtype']}): {r['question']}\n  - ground truth: `{json.dumps(r['gt'])}`\n"
                       f"  - answer: `{json.dumps({k: v for k, v in ans.items() if v is not None and k != 'text'})}`\n  - tool calls: {calls}")
    return "\n".join(out)


def figures(s: pd.DataFrame, outdir: Path, split: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    outdir.mkdir(exist_ok=True)
    sources = sorted(s.source.unique())
    cols = QTYPES + ["overall", "overall_ex_prev"]
    fig, axes = plt.subplots(1, len(sources), figsize=(6.2 * len(sources), 3.6), squeeze=False)
    for ax, src in zip(axes[0], sources):
        t = s[s.source == src]
        M = np.array([[t[(t.cell == c) & (t.qtype == q)]["mean"].mean() for q in cols] for c in CELL_ORDER])
        im = ax.imshow(M, vmin=0, vmax=1, cmap="viridis", aspect="auto")
        ax.set_xticks(range(len(cols)), [c.replace("_", "\n") for c in cols], fontsize=7)
        ax.set_yticks(range(len(CELL_ORDER)), CELL_ORDER, fontsize=8)
        for i in range(M.shape[0]):
            for j in range(M.shape[1]):
                if not np.isnan(M[i, j]):
                    ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=7, color="w" if M[i, j] < 0.6 else "k")
        ax.set_title(src)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.8, label="score")
    fig.savefig(outdir / f"stage_b_heatmap_{split}.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    if len(sources) > 1:
        o = s[s.qtype == "overall"]
        fig, ax = plt.subplots(figsize=(7, 3.4))
        w = 0.38
        for k, src in enumerate(sources):
            t = o[o.source == src].set_index("cell").reindex(CELL_ORDER)
            x = np.arange(len(CELL_ORDER)) + (k - 0.5) * w
            ax.bar(x, t["mean"], w, yerr=[t["mean"] - t["ci_lo"], t["ci_hi"] - t["mean"]], label=src, capsize=2)
        ax.set_xticks(range(len(CELL_ORDER)), CELL_ORDER, fontsize=8)
        ax.set_ylabel("overall score")
        ax.legend()
        fig.savefig(outdir / f"stage_b_gt_vs_pred_{split}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)


def bench_block(d: pd.DataFrame, s: pd.DataFrame, split: str) -> str:
    parts = [f"Split: `{split}`. Model: `{d['model'].iloc[0]}` ({d['provider'].iloc[0]}). Score is accuracy (F1 for interval questions); "
             "brackets are 95% bootstrap CIs over questions.", ""]
    for src in sorted(d.source.unique()):
        parts += [f"**Event source: `{src}`**", "", accuracy_table(s, src), ""]
    parts += ["`overall_ex_prev` leaves out previous-location questions. In these timelines the previous location is "
              "almost always the initial scan pose (see Limitations), so M0 scores high on that type without any history.", ""]
    if len(d.source.unique()) > 1:
        parts += ["**Ground-truth versus predicted events (paired, same questions)**", "", source_table(d), ""]
    return "\n".join(parts)


def fill_readme(block: str, path="README.md") -> None:
    p = Path(path)
    txt = p.read_text()
    if README_START not in txt:
        raise SystemExit("README.md has no benchmark markers")
    pre, rest = txt.split(README_START)
    _, post = rest.split(README_END)
    p.write_text(f"{pre}{README_START}\n{block}\n{README_END}{post}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="test")
    ap.add_argument("--root", default="results/stage_b_local", help="results directory holding <split>/*.jsonl")
    ap.add_argument("--readme", action="store_true")
    a = ap.parse_args(argv)
    d = load(a.split, a.root)
    s = summarise(d)
    s.to_csv(f"results/summary_stage_b_{a.split}.csv", index=False)
    cost_table(d).to_csv(f"results/cost_latency_{a.split}.csv", index=False)
    figures(s, Path("figures"), a.split)
    tables = [f"# Stage B tables ({a.split})", ""]
    for src in sorted(d.source.unique()):
        tables += [f"## Accuracy by cell and question type, `{src}`", "", accuracy_table(s, src), "",
                   f"## Paired comparisons, `{src}`", "", paired_table(d, src), ""]
    if len(d.source.unique()) > 1:
        tables += ["## Ground-truth versus predicted events (RQ3), paired on the same questions", "", source_table(d), ""]
    tables += ["## Cost and latency (mean per question)", "",
               "Retrieval latency covers the memory store and tools only. End-to-end time is dominated by the model. "
               "Only `gt_event` rows are shown: M0 and blind produce the same prompts for both sources, so their "
               "`pred_event` runs were cache hits.", "",
               md(cost_table(d)), "", "## Failures (up to 5 per cell)", "", failure_table(d)]
    Path(f"figures/tables_{a.split}.md").write_text("\n".join(tables))
    if a.readme:
        fill_readme(bench_block(d, s, a.split))
    print(f"wrote results/summary_stage_b_{a.split}.csv, figures/ and tables_{a.split}.md")


if __name__ == "__main__":
    main()
