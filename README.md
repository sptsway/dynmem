# DynMem

Dynamic episodic memory for embodied agents: answering where-and-when questions after objects move.

This is a measurement study. It makes no claim of a new state of the art.

## Question

A robot with a long-term memory sees objects move. Which memory update policy keeps the answers correct?
Which retrieval design finds them?

Three memory update policies:

- **M0 static**: the initial scan only. Later events are ignored.
- **M1 overwrite**: one entry per object. A new event replaces it.
- **M2 versioned**: append-only entries with validity intervals.

Two retrieval designs:

- **R0 vector-only**: text similarity search.
- **R1 hybrid**: composed search with time, position and object filters, plus per-object history.

A **blind** baseline answers without any memory.

## Scope

Only the dynamic-memory study (Stage B) was run. The planned validation on NaVQA and CODa (Stage A) was not run. See `DEVIATIONS.md`.

## Method

- **Data**: the Lost & Found dataset (96 egocentric pick-and-place recordings, 9 objects, one scene).
- **Timelines**: each recording is one move. Recordings are placed on a synthetic clock with random gaps of 3 to 20 minutes. Timelines are constructed, not a real continuous log.
- **Events**: ground truth (`gt_event`) or Lost & Found predictions (`pred_event`). Answers are always scored against ground truth.
- **Questions**: five templated types. Current location, previous location, time of last move, move count and objects moved in an interval.
- **Scoring**: deterministic. Position within 0.25 m. Time within 10 s. Count exact. Interval by F1.
- **Splits**: by recording. 27 dev, 69 test. Prompts and tolerances were tuned on dev and frozen before the test run.
- **Agent**: tool-calling LLM, at most 3 retrieval rounds, strict JSON answers. A parse failure scores 0.
- **Memory store**: Qdrant (local mode). Embeddings: `mixedbread-ai/mxbai-embed-large-v1`.

## Benchmarks

<!-- BENCH:START -->
Split: `test`. Model: `qwen2.5:7b` (ollama). Score is accuracy (F1 for interval questions); brackets are 95% bootstrap CIs over questions.

**Event source: `gt_event`**

| cell | n | overall | overall_ex_prev | current_location | previous_location | when_moved | count | interval |
|---|---|---|---|---|---|---|---|---|
| M0_R0 | 180 | 0.20 [0.15, 0.26] | 0.01 [0.00, 0.03] | 0.00 [0.00, 0.00] | 0.97 [0.92, 1.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.01 [0.00, 0.04] |
| M0_R1 | 180 | 0.16 [0.11, 0.21] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.75 [0.61, 0.89] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |
| M1_R0 | 180 | 0.51 [0.44, 0.58] | 0.64 [0.57, 0.71] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.19 [0.08, 0.33] | 0.45 [0.37, 0.52] |
| M1_R1 | 180 | 0.55 [0.48, 0.62] | 0.69 [0.62, 0.76] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.25 [0.11, 0.39] | 0.60 [0.51, 0.69] |
| M2_R0 | 180 | 0.34 [0.28, 0.40] | 0.37 [0.30, 0.45] | 0.28 [0.14, 0.42] | 0.19 [0.08, 0.33] | 0.44 [0.28, 0.61] | 0.36 [0.22, 0.53] | 0.40 [0.32, 0.49] |
| M2_R1 | 180 | 0.56 [0.49, 0.63] | 0.61 [0.53, 0.69] | 0.58 [0.42, 0.75] | 0.36 [0.19, 0.53] | 0.72 [0.58, 0.86] | 0.25 [0.11, 0.39] | 0.90 [0.81, 0.97] |
| blind | 180 | 0.01 [0.00, 0.02] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |

**Event source: `pred_event`**

| cell | n | overall | overall_ex_prev | current_location | previous_location | when_moved | count | interval |
|---|---|---|---|---|---|---|---|---|
| M0_R0 | 180 | 0.20 [0.15, 0.26] | 0.01 [0.00, 0.03] | 0.00 [0.00, 0.00] | 0.97 [0.92, 1.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.01 [0.00, 0.04] |
| M0_R1 | 180 | 0.16 [0.11, 0.21] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.75 [0.61, 0.89] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |
| M1_R0 | 180 | 0.51 [0.44, 0.57] | 0.63 [0.57, 0.70] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.17 [0.06, 0.31] | 0.45 [0.38, 0.52] |
| M1_R1 | 180 | 0.53 [0.46, 0.60] | 0.67 [0.60, 0.73] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.17 [0.06, 0.31] | 0.59 [0.49, 0.68] |
| M2_R0 | 180 | 0.32 [0.26, 0.38] | 0.36 [0.29, 0.43] | 0.31 [0.17, 0.44] | 0.14 [0.03, 0.25] | 0.39 [0.25, 0.56] | 0.36 [0.22, 0.53] | 0.39 [0.30, 0.49] |
| M2_R1 | 180 | 0.55 [0.48, 0.62] | 0.61 [0.53, 0.69] | 0.61 [0.44, 0.78] | 0.31 [0.17, 0.47] | 0.81 [0.67, 0.92] | 0.08 [0.00, 0.19] | 0.93 [0.87, 0.99] |
| blind | 180 | 0.01 [0.00, 0.02] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |

`overall_ex_prev` leaves out previous-location questions. In these timelines the previous location is almost always the initial scan pose (see Limitations), so M0 scores high on that type without any history.

**Ground-truth versus predicted events (paired, same questions)**

| cell | n | acc gt_event | acc pred_event | diff (pred - gt) | pred only | gt only | McNemar p |
|---|---|---|---|---|---|---|---|
| M0_R0 | 180 | 0.20 | 0.20 | +0.00 | 0 | 0 | 1 |
| M0_R1 | 180 | 0.16 | 0.16 | +0.00 | 0 | 0 | 1 |
| M1_R0 | 180 | 0.42 | 0.42 | -0.01 | 1 | 2 | 1 |
| M1_R1 | 180 | 0.48 | 0.47 | -0.02 | 1 | 4 | 0.375 |
| M2_R0 | 180 | 0.26 | 0.24 | -0.02 | 6 | 9 | 0.607 |
| M2_R1 | 180 | 0.54 | 0.53 | -0.01 | 10 | 11 | 1 |
| blind | 180 | 0.01 | 0.01 | +0.00 | 0 | 0 | 1 |

<!-- BENCH:END -->

Paired differences use strict correctness (a question counts only at score 1). Cell scores are mean scores.

Full tables, paired tests, cost and latency, and failure cases: `figures/tables_test.md`. Figures: `figures/`. Reports: `REPORT.md`, `SUMMARY.md`.
Per-question traces: `results/stage_b_local/test/`.

## Reproduce

```
uv venv --python 3.11 .venv && uv pip install -e ".[dev]"
make test      # unit tests
make data      # scan archive and per-recording files (about 440 MB transferred)
make stage_b   # needs a running Ollama server with qwen2.5:7b
make report    # tables, figures, README benchmarks
```

API keys are read from environment variables only. The default agent runs locally.

## Limitations

- Timelines are constructed. They are not a continuous real-world log.
- One scene, nine objects, three timelines.
- Every recording of an object starts from nearly the same pose. The previous location is therefore usually the initial scan pose. Previous-location questions do not separate M0 from the other policies, so `overall_ex_prev` is reported.
- The agent is a local 7B model. Absolute accuracy is lower than for frontier models.
- Position and time tolerances were chosen on the dev split.
- Test size was cut to 60 questions per timeline.
- Stage A was not run, so the agent is not validated against published ReMEmbR results.
- No robot hardware is used.

## Data and licenses

| Dataset | Use | License |
|---|---|---|
| Lost & Found (Zenodo 14967441, arXiv 2411.19162) | Stage B trajectories | CC BY 4.0 |
| NaVQA / ReMEmbR (arXiv 2409.13682), CODa | cited as background, not used | NVIDIA non-commercial; CODa non-commercial |

Code: MIT (`LICENSE`). No dataset files are stored in this repository.
