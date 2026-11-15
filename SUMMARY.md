# Summary

Five findings from `results/summary_stage_b_test.csv` and the per-question traces in `results/stage_b_local/test/`. Model: `qwen2.5:7b (ollama)`.
180 questions per cell (3 constructed timelines, seeds 1, 2, 3). Scores are accuracy, F1 for interval questions, with 95% bootstrap CIs.

1. **A static memory cannot answer "where is X now".** M0 scores 0.00 [0.00, 0.00] on current-location questions with hybrid retrieval. M1 scores 0.92 [0.81, 1.00]. Source: `results/summary_stage_b_test.csv`.
2. **An overwrite memory cannot answer "where was X before".** M1 scores 0.00 [0.00, 0.00] on previous-location questions. M2 scores 0.36 [0.19, 0.53]. M0 scores 0.97 [0.92, 1.00] on the same type because the previous location equals the initial scan pose in most constructed timelines, so this type does not separate M0 from the others. Source: `results/summary_stage_b_test.csv`.
3. **Hybrid retrieval helps most with the versioned memory.** M2 overall: R1 0.56 [0.49, 0.63], R0 0.34 [0.28, 0.40]; paired difference +0.28, McNemar p = 2.18e-08. On when-moved and interval questions only, the paired difference is +0.53 (n = 72, p = 4.11e-10). For M1 the difference is +0.06 (p = 0.00739). Source: `results/stage_b_local/test/`.
4. **The versioned memory did not beat the overwrite memory overall.** M2 with hybrid retrieval scores 0.56 [0.49, 0.63] against 0.55 [0.48, 0.62] for M1 (paired difference +0.06, p = 0.268). Without previous-location questions, M1 scores 0.69 [0.62, 0.76] and M2 0.61 [0.53, 0.69]. Source: `results/summary_stage_b_test.csv`.
5. **Predicted trajectories cost little accuracy.** The largest overall gap between `pred_event` and `gt_event` over the six memory cells is 0.02 (M1_R1). No cell differs significantly in a paired test (smallest McNemar p = 0.375). Source: `figures/tables_test.md`.

Paired differences and McNemar p-values use strict correctness (a question is correct only at score 1, so an interval question needs F1 = 1). Cell scores above are mean scores, so the two can differ.

The memory-less baseline scores 0.01 [0.00, 0.02] overall. Parse failures count as wrong: parse rate is between 0.91 and 1.00 across cells.
