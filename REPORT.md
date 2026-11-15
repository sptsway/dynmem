# DynMem: memory update policies for where-and-when questions

## Problem
An agent with a long-term memory sees objects move. A static memory goes stale. This study measures how
three memory update policies and two retrieval designs change the accuracy of where-and-when questions
after objects move.

## Method
**Data.** The Lost & Found dataset: 96 egocentric pick-and-place recordings of 9 objects in one scene.
Each recording holds one move. Trajectories are mapped into the scan frame with the inverse of the stored
ICP transform. Moves are found by a speed threshold chosen on the dev split.

**Constructed timelines.** Recordings are placed on a synthetic clock with random gaps of 3 to 20 minutes.
Timelines are constructed. They are not a continuous real-world log. Three timelines (seeds 1, 2, 3) were built from
the 69 test recordings. 27 recordings form the dev split. No recording is in both.

**Memory policies.** M0 static (initial scan only). M1 overwrite (one entry per object). M2 versioned
(append-only entries with validity intervals).

**Retrieval designs.** R0 vector-only (text similarity). R1 hybrid (composed search with time, position and
object filters, plus per-object history). A blind baseline uses no memory.

**Questions and scoring.** Five templated types: current location, previous location, time of last move,
move count, objects moved in an interval. Scoring is deterministic: position within 0.25 m, time within 10 s,
count exact, interval by F1. Answers are always scored against ground truth. Event sources: ground truth
(`gt_event`) and Lost & Found predictions (`pred_event`).

**Agent.** `qwen2.5:7b (ollama)` with tool calling, at most 3 retrieval rounds, strict JSON answers. A parse failure scores 0.
Temperature 0. Every call is cached on disk. Prompts, tools and tolerances were tuned on dev in one round and
frozen (hashes in `configs/frozen_hashes.json`) before the test run.

## Results
Per cell and question type: `figures/tables_test.md` and `figures/stage_b_heatmap_test.png`.
Test set, 180 questions per cell, `gt_event`:

| cell | overall | overall without previous location |
|---|---|---|
| M0_R0 | 0.20 [0.15, 0.26] | 0.01 [0.00, 0.03] |
| M0_R1 | 0.16 [0.11, 0.21] | 0.01 [0.00, 0.02] |
| M1_R0 | 0.51 [0.44, 0.58] | 0.64 [0.57, 0.71] |
| M1_R1 | 0.55 [0.48, 0.62] | 0.69 [0.62, 0.76] |
| M2_R0 | 0.34 [0.28, 0.40] | 0.37 [0.30, 0.45] |
| M2_R1 | 0.56 [0.49, 0.63] | 0.61 [0.53, 0.69] |
| blind | 0.01 [0.00, 0.02] | 0.01 [0.00, 0.02] |

Hybrid retrieval raises the versioned memory from 0.34 to 0.56 overall (p = 2.18e-08).
The versioned memory is not better than the overwrite memory overall (p = 0.268).
Predicted events change accuracy by at most 0.02 in any memory cell (no cell differs significantly in a paired test; smallest p = 0.375).
Paired differences and p-values use strict correctness (score 1); cell scores are mean scores.

## Hypotheses
- **H1** (rebuilt ReMEmbR-style agent matches published correctness): not tested. Stage A was not run.
- **H2** (static fails on "now", overwrite fails on "before", versioned answers both): the first two held
  (M0 current location 0.00; M1 previous location 0.00).
  The third did not hold for this model: M2 current location 0.58, previous location 0.36.
- **H3** (hybrid beats vector-only mostly on temporal questions): held for M2 (largest gains on when-moved and
  interval questions, paired difference +0.53), weak for M1 (+0.06).
- **H4** (predicted trajectories lower accuracy only slightly): held. Largest overall gap 0.02; smallest paired p = 0.375.

## Limitations
- Timelines are constructed. They are not a continuous real-world log.
- One scene and nine objects. Three timelines.
- Every recording of an object starts from nearly the same pose, so the previous location is usually the initial
  scan pose. Previous-location questions do not separate M0 from the other policies. Chaining recordings so
  that one move ends where the next begins would remove this.
- The agent is a local 7B model. Absolute accuracy is lower than for frontier models. It often returned the
  current position for previous-location questions and struggled with counts.
- In the text-only design the model often passed an `object` filter that `search_text` does not accept
  (11% of Overwrite · text questions). The tool returned an error and the model retried. This may
  understate text-only accuracy and so part of the hybrid gain.
- Position and time tolerances were chosen on the dev split.
- Stage A (validation on NaVQA) was not run: it needs hundreds of GB of CODa video and a vision captioner.
- Test size was cut from 150 to 60 questions per timeline (see `DEVIATIONS.md`).
- No robot hardware is used.

## Data and licenses
Lost & Found (Zenodo 14967441, arXiv 2411.19162): CC BY 4.0. Code: MIT. No dataset files are in the repository.
ReMEmbR (arXiv 2409.13682) and CODa are cited as background; neither dataset was used.
