# DynMem

Dynamic episodic memory for embodied agents: answering where-and-when questions after objects move.

## Problem

A robot or a pair of smart glasses can keep a long-term memory of what it saw. A common design captions short video segments, embeds the captions and stores them in a vector database with position and time. An LLM agent then answers questions through retrieval tools. ReMEmbR (arXiv 2409.13682) is a reference system of this kind.

Such a memory records what was seen once. Objects move. A question like "where is the mug now?" then has an answer that the stored observation no longer holds. Lost & Found (arXiv 2411.19162) tracks the 6DoF pose of objects that a person moves, which makes the changes observable.

This study asks three questions:

1. **Update policy.** Which memory update policy keeps answers correct after objects move: static, overwrite or versioned?
2. **Retrieval design.** Does a hybrid search (text, time, position and object filters, per-object history) beat text search alone?
3. **Perception noise.** How much accuracy is lost when the memory is built from predicted trajectories instead of ground-truth ones?

## Approach

![From recordings to a scored answer](figures/10_approach_pipeline.png)

*From recordings to a scored answer*

- **Events.** Each recording is one pick-and-place. A speed threshold gives the pick pose, the place pose and the times. Events come from ground-truth trajectories or from Lost & Found predictions.
- **Timelines.** The 96 recordings are independent. They are placed on one synthetic clock with random 3 to 20 minute gaps, in an order set by a fixed seed. Timelines are constructed and not a real continuous log.
- **Memory policies.** Static keeps the initial scan. Overwrite keeps one entry per object and replaces it on each move. Versioned appends entries with validity intervals.
- **Retrieval designs.** Text-only search, or hybrid search with time, position and object filters and a per-object history tool.
- **Agent.** `qwen2.5:7b` with tool calling, at most 3 retrieval rounds and strict JSON answers. A parse failure scores 0. Every call is cached and run at temperature 0.
- **Questions.** Five templated types: where now, where before, when last moved, how many moves, what moved in a time window. Scoring is deterministic: position within 0.25 m, time within 10 s, count exact, interval by F1.
- **Splits.** By recording: 27 dev, 69 test. Prompts and tolerances were tuned on dev and frozen before the test run. The test set holds 3 timelines and 180 questions per setting.

## Results

- **Memory design decides accuracy.** With no memory the agent answers 1% of questions. The best memory setting answers 56%.
- **Static memory goes stale.** It answers 0% of "where is it now?" questions. Overwrite memory fixes that (92%) and loses history (0% on "where was it before?").
- **Hybrid search lifts versioned memory** from 34% to 56% overall, and from 40% to 90% on "what moved in a time window?".
- **Predicted trajectories cost little.** Scores with Lost & Found predictions stay within 2 percentage points of ground truth. The median placement error on test recordings is 3 cm.

![The three memory policies](figures/00_memory_policies.png)

*The three memory policies*

![Share of questions answered correctly, by memory setting and question type](figures/01_accuracy_heatmap_test.png)

*Share of questions answered correctly, by memory setting and question type*

![Overall accuracy with 95% confidence intervals](figures/02_overall_accuracy_test.png)

*Overall accuracy with 95% confidence intervals*

![Accuracy gain from hybrid search, per question type](figures/03_hybrid_vs_text_test.png)

*Accuracy gain from hybrid search, per question type*

![Predicted versus ground-truth events, and the tracker's placement error](figures/04_predicted_vs_ground_truth_test.png)

*Predicted versus ground-truth events, and the tracker's placement error*

![Accuracy as the position and time tolerances change](figures/05_tolerance_sensitivity_test.png)

*Accuracy as the position and time tolerances change*

![Tokens, tool calls and time per question](figures/06_cost_and_latency_test.png)

*Tokens, tool calls and time per question*

![How often the model produced an invalid answer or a rejected tool call](figures/07_model_reliability_test.png)

*How often the model produced an invalid answer or a rejected tool call*

![Accuracy on each constructed timeline](figures/08_per_timeline_test.png)

*Accuracy on each constructed timeline*

![Effect of the single dev tuning round](figures/09_dev_tuning_effect.png)

*Effect of the single dev tuning round*


Tables with confidence intervals and paired tests: [`figures/tables_test.md`](figures/tables_test.md). Every figure is built from the traces in `results/`.
Reports: [`REPORT.md`](REPORT.md), [`SUMMARY.md`](SUMMARY.md). Deviations from the plan: [`DEVIATIONS.md`](DEVIATIONS.md). Costs: [`COSTS.md`](COSTS.md).

## Conclusions

- **History is needed, and each simpler policy fails one question class.** Static memory cannot answer "now" (0%). Overwrite memory cannot answer "before" (0%).
- **Hybrid retrieval matters most when memory holds many versions.** For versioned memory the paired gain is +0.28 (McNemar p = 2.2e-08). For overwrite memory it is smaller.
- **Versioned and overwrite memory are level overall with this model.** 56% against 55% (paired p = 0.27). Versioned memory is stronger on time-window questions (90% against 60%). It is weaker on "where is it now?" (58% against 92%). In 12 of its 15 failures on that question the model had retrieved entries of the right object and still gave a wrong position. In 3 it gave no position.
- **Perception noise is not the bottleneck here.** Median placement error is 3 cm, well inside the 0.25 m tolerance. A tolerance sweep (figure 05) shows the same picture at other tolerances.

| Hypothesis | Outcome |
|---|---|
| H1. A rebuilt ReMEmbR-style agent matches published correctness | Not tested. The NaVQA validation was not run. |
| H2. Static fails "now", overwrite fails "before", versioned answers both | The first two held. Versioned answered both only in part with this model. |
| H3. Hybrid retrieval helps most on temporal questions | Held for versioned memory. Smaller effect for overwrite memory. |
| H4. Predicted trajectories lower accuracy only slightly | Held. Largest gap 2 percentage points. |

## Next steps

- Chain recordings so that each move starts where the previous one ended. "Where was it before?" would then separate the policies.
- Let the text-only tool accept an object filter, to separate retrieval quality from tool-signature errors.
- Repeat with a stronger model through a paid API tier.
- Add the NaVQA validation of the agent.

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

## Data and licenses

| Dataset | Use | License |
|---|---|---|
| Lost & Found (Zenodo 14967441, arXiv 2411.19162) | trajectories | CC BY 4.0 |

Code: MIT ([`LICENSE`](LICENSE)). No dataset files are stored in this repository.
