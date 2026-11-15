# Stage B tables (test)

## Accuracy by cell and question type, `gt_event`

| cell | n | overall | overall_ex_prev | current_location | previous_location | when_moved | count | interval |
|---|---|---|---|---|---|---|---|---|
| M0_R0 | 180 | 0.20 [0.15, 0.26] | 0.01 [0.00, 0.03] | 0.00 [0.00, 0.00] | 0.97 [0.92, 1.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.01 [0.00, 0.04] |
| M0_R1 | 180 | 0.16 [0.11, 0.21] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.75 [0.61, 0.89] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |
| M1_R0 | 180 | 0.51 [0.44, 0.58] | 0.64 [0.57, 0.71] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.19 [0.08, 0.33] | 0.45 [0.37, 0.52] |
| M1_R1 | 180 | 0.55 [0.48, 0.62] | 0.69 [0.62, 0.76] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.25 [0.11, 0.39] | 0.60 [0.51, 0.69] |
| M2_R0 | 180 | 0.34 [0.28, 0.40] | 0.37 [0.30, 0.45] | 0.28 [0.14, 0.42] | 0.19 [0.08, 0.33] | 0.44 [0.28, 0.61] | 0.36 [0.22, 0.53] | 0.40 [0.32, 0.49] |
| M2_R1 | 180 | 0.56 [0.49, 0.63] | 0.61 [0.53, 0.69] | 0.58 [0.42, 0.75] | 0.36 [0.19, 0.53] | 0.72 [0.58, 0.86] | 0.25 [0.11, 0.39] | 0.90 [0.81, 0.97] |
| blind | 180 | 0.01 [0.00, 0.02] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |

## Paired comparisons, `gt_event`

| A | B | n | acc A - acc B | A only | B only | McNemar p |
|---|---|---|---|---|---|---|
| M2_R1 | M1_R1 | 180 | +0.06 | 38 | 28 | 0.268 |
| M2_R1 | M0_R1 | 180 | +0.38 | 86 | 17 | 2.81e-12 |
| M2_R1 | M2_R0 | 180 | +0.28 | 68 | 17 | 2.18e-08 |
| M1_R1 | M1_R0 | 180 | +0.06 | 13 | 2 | 0.00739 |
| M2_R1 | blind | 180 | +0.53 | 96 | 0 | 2.52e-29 |

## Accuracy by cell and question type, `pred_event`

| cell | n | overall | overall_ex_prev | current_location | previous_location | when_moved | count | interval |
|---|---|---|---|---|---|---|---|---|
| M0_R0 | 180 | 0.20 [0.15, 0.26] | 0.01 [0.00, 0.03] | 0.00 [0.00, 0.00] | 0.97 [0.92, 1.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.01 [0.00, 0.04] |
| M0_R1 | 180 | 0.16 [0.11, 0.21] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.75 [0.61, 0.89] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |
| M1_R0 | 180 | 0.51 [0.44, 0.57] | 0.63 [0.57, 0.70] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.17 [0.06, 0.31] | 0.45 [0.38, 0.52] |
| M1_R1 | 180 | 0.53 [0.46, 0.60] | 0.67 [0.60, 0.73] | 0.92 [0.81, 1.00] | 0.00 [0.00, 0.00] | 1.00 [1.00, 1.00] | 0.17 [0.06, 0.31] | 0.59 [0.49, 0.68] |
| M2_R0 | 180 | 0.32 [0.26, 0.38] | 0.36 [0.29, 0.43] | 0.31 [0.17, 0.44] | 0.14 [0.03, 0.25] | 0.39 [0.25, 0.56] | 0.36 [0.22, 0.53] | 0.39 [0.30, 0.49] |
| M2_R1 | 180 | 0.55 [0.48, 0.62] | 0.61 [0.53, 0.69] | 0.61 [0.44, 0.78] | 0.31 [0.17, 0.47] | 0.81 [0.67, 0.92] | 0.08 [0.00, 0.19] | 0.93 [0.87, 0.99] |
| blind | 180 | 0.01 [0.00, 0.02] | 0.01 [0.00, 0.02] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.03 [0.00, 0.08] | 0.00 [0.00, 0.00] |

## Paired comparisons, `pred_event`

| A | B | n | acc A - acc B | A only | B only | McNemar p |
|---|---|---|---|---|---|---|
| M2_R1 | M1_R1 | 180 | +0.07 | 34 | 22 | 0.141 |
| M2_R1 | M0_R1 | 180 | +0.38 | 87 | 19 | 1.4e-11 |
| M2_R1 | M2_R0 | 180 | +0.29 | 72 | 19 | 1.97e-08 |
| M1_R1 | M1_R0 | 180 | +0.05 | 13 | 4 | 0.049 |
| M2_R1 | blind | 180 | +0.53 | 96 | 1 | 1.24e-27 |

## Ground-truth versus predicted events (RQ3), paired on the same questions

| cell | n | acc gt_event | acc pred_event | diff (pred - gt) | pred only | gt only | McNemar p |
|---|---|---|---|---|---|---|---|
| M0_R0 | 180 | 0.20 | 0.20 | +0.00 | 0 | 0 | 1 |
| M0_R1 | 180 | 0.16 | 0.16 | +0.00 | 0 | 0 | 1 |
| M1_R0 | 180 | 0.42 | 0.42 | -0.01 | 1 | 2 | 1 |
| M1_R1 | 180 | 0.48 | 0.47 | -0.02 | 1 | 4 | 0.375 |
| M2_R0 | 180 | 0.26 | 0.24 | -0.02 | 6 | 9 | 0.607 |
| M2_R1 | 180 | 0.54 | 0.53 | -0.01 | 10 | 11 | 1 |
| blind | 180 | 0.01 | 0.01 | +0.00 | 0 | 0 | 1 |

## Cost and latency (mean per question)

Retrieval latency covers the memory store and tools only. End-to-end time is dominated by the model. Only `gt_event` rows are shown: M0 and blind produce the same prompts for both sources, so their `pred_event` runs were cache hits.

| source | cell | n | tool_calls | input_tokens | output_tokens | retrieval_ms | end_to_end_s | parse_rate |
|---|---|---|---|---|---|---|---|---|
| gt_event | M0_R0 | 180 | 1.96 | 2350.88 | 114.81 | 119.18 | 5.82 | 0.93 |
| gt_event | M0_R1 | 180 | 2.29 | 4270.85 | 128.06 | 106.75 | 8.44 | 0.91 |
| gt_event | M1_R0 | 180 | 1.12 | 1371.59 | 97.66 | 58.55 | 3.31 | 0.99 |
| gt_event | M1_R1 | 180 | 1.36 | 2725.49 | 109.03 | 47.09 | 4.30 | 0.99 |
| gt_event | M2_R0 | 180 | 1.11 | 1469.62 | 93.40 | 61.73 | 3.30 | 0.99 |
| gt_event | M2_R1 | 180 | 1.29 | 2761.23 | 112.23 | 41.09 | 4.09 | 0.89 |
| gt_event | blind | 180 | 0.00 | 352.11 | 44.22 | 0.00 | 1.33 | 0.98 |

## Failures (up to 5 per cell)

### gt_event / M0_R0
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search_text({"query": "water", "k": 1})
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{"position": [1.71, 1.18, -1.04]}`
  - tool calls: search_text({"query": "organizer", "k": 1})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search_text({"k": 1, "query": "water"})
- `s1-current_location-003` (current_location): It is now t=12047 s. Where is the ball now?
  - ground truth: `{"position": [0.7353129367877614, -0.32523782002977264, -0.6111758583821705]}`
  - answer: `{"position": [1.45, -0.32, -0.48]}`
  - tool calls: search_text({"k": 1, "query": "ball", "object": "ball"}); search_text({"query": "ball", "k": 1})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search_text({"k": 1, "query": "carton"})
### gt_event / M0_R1
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search({"object": "water", "time_range": [0, 43398]})
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{}`
  - tool calls: search({"object": "organizer", "time_range": [0, 39135]})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search({"object": "water", "time_range": [0, 46602]})
- `s1-current_location-003` (current_location): It is now t=12047 s. Where is the ball now?
  - ground truth: `{"position": [0.7353129367877614, -0.32523782002977264, -0.6111758583821705]}`
  - answer: `{}`
  - tool calls: search({"object": "ball", "time_range": [0, 12047]})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search({"object": "carton", "time_range": [0, 38507]}); <empty reply, retried>({})
### gt_event / M1_R0
- `s1-previous_location-000` (previous_location): It is now t=2308 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.705678762902532, 1.1836474949511666, -1.0404429634453065]}`
  - answer: `{"position": [1.93, 0.53, 0.1], "time": 1653.0}`
  - tool calls: search_text({"k": 1, "query": "organizer before moved"})
- `s1-previous_location-001` (previous_location): It is now t=13352 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{"position": [1.86, 0.39, 0.12], "time": 7953.0, "objects": ["clock"]}`
  - tool calls: search_text({"query": "clock", "k": 1})
- `s1-previous_location-002` (previous_location): It is now t=34400 s. Where was the frame before it was last moved?
  - ground truth: `{"position": [1.2004572714836572, 0.5348049807823532, -1.0927757092301702]}`
  - answer: `{"position": [1.95, 0.43, 0.17]}`
  - tool calls: search_text({"k": 1, "query": "frame was last moved"})
- `s1-previous_location-003` (previous_location): It is now t=8500 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{"position": [1.86, 0.39, 0.12], "time": 7953.0, "objects": ["clock"]}`
  - tool calls: search_text({"k": 1, "query": "clock"})
- `s1-previous_location-004` (previous_location): It is now t=40621 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.7050900163387488, 1.1794429766032148, -1.0414010139656797]}`
  - answer: `{"position": [1.93, 0.83, 1.05], "time": 35687.0}`
  - tool calls: search_text({"query": "organizer moved", "k": 1})
### gt_event / M1_R1
- `s1-previous_location-000` (previous_location): It is now t=2308 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.705678762902532, 1.1836474949511666, -1.0404429634453065]}`
  - answer: `{"position": [1.93, 0.53, 0.1], "time": 1654.0}`
  - tool calls: search({"object": "organizer", "time_range": [0, 2308]})
- `s1-previous_location-001` (previous_location): It is now t=13352 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{}`
  - tool calls: <empty reply, retried>({}); search_time({"time_or_range": [0, 13352], "object": "clock"}); search_text({"query": "clock moved"})
- `s1-previous_location-002` (previous_location): It is now t=34400 s. Where was the frame before it was last moved?
  - ground truth: `{"position": [1.2004572714836572, 0.5348049807823532, -1.0927757092301702]}`
  - answer: `{"position": [1.95, 0.43, 0.17]}`
  - tool calls: search({"k": 1, "object": "frame", "time_range": [0, 34400]})
- `s1-previous_location-003` (previous_location): It is now t=8500 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{"position": [1.86, 0.39, 0.12], "objects": ["clock"]}`
  - tool calls: search_time({"time_or_range": [0, 8500], "object": "clock"}); search_text({"query": "clock"})
- `s1-previous_location-004` (previous_location): It is now t=40621 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.7050900163387488, 1.1794429766032148, -1.0414010139656797]}`
  - answer: `{"position": [1.93, 0.83, 1.05], "time": 35687.0}`
  - tool calls: search({"object": "organizer", "time_range": [0, 40621]})
### gt_event / M2_R0
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-0.83, -0.18, 2.17]}`
  - tool calls: search_text({"query": "water", "k": 1})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-0.83, -0.18, 2.17]}`
  - tool calls: search_text({"k": 1, "query": "water"})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search_text({"k": 1, "query": "carton"})
- `s1-current_location-005` (current_location): It is now t=35528 s. Where is the ball now?
  - ground truth: `{"position": [-1.2451422492372466, 0.9721417203013722, 0.7779724376761449]}`
  - answer: `{"position": [1.91, 0.46, 0.04], "time": 25913.0, "objects": ["ball"]}`
  - tool calls: search_text({"k": 1, "query": "ball", "object": "ball"}); search_text({"query": "ball", "k": 1})
- `s1-current_location-006` (current_location): It is now t=30395 s. Where is the frame now?
  - ground truth: `{"position": [-0.19233285208192763, 0.40698114834586596, -0.9989772241440174]}`
  - answer: `{"objects": ["frame"]}`
  - tool calls: search_text({"k": 1, "query": "frame"})
### gt_event / M2_R1
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-1.2, 1.01, 1.45], "time": 36513.0, "objects": ["water"]}`
  - tool calls: search({"object": "water", "time_range": [0, 43398]})
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{"position": [-0.34, 0.51, -0.95], "time": 35684.0, "objects": ["organizer"]}`
  - tool calls: search({"object": "organizer", "time_range": [0, 39135]})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-1.2, 1.01, 1.45], "objects": ["water"]}`
  - tool calls: search({"object": "water", "time_range": [0, 46602]})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.92, 0.53, 0.02], "objects": ["carton"]}`
  - tool calls: search({"object": "carton", "time_range": [0, 38507]})
- `s1-current_location-005` (current_location): It is now t=35528 s. Where is the ball now?
  - ground truth: `{"position": [-1.2451422492372466, 0.9721417203013722, 0.7779724376761449]}`
  - answer: `{"position": [-0.58, -0.24, 0.68], "objects": ["ball"]}`
  - tool calls: search({"object": "ball", "time_range": [0, 35528]})
### gt_event / blind
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: none
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{}`
  - tool calls: none
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: none
- `s1-current_location-003` (current_location): It is now t=12047 s. Where is the ball now?
  - ground truth: `{"position": [0.7353129367877614, -0.32523782002977264, -0.6111758583821705]}`
  - answer: `{"objects": ["ball"]}`
  - tool calls: none
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"objects": ["carton"]}`
  - tool calls: none
### pred_event / M0_R0
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search_text({"query": "water", "k": 1})
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{"position": [1.71, 1.18, -1.04]}`
  - tool calls: search_text({"query": "organizer", "k": 1})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search_text({"k": 1, "query": "water"})
- `s1-current_location-003` (current_location): It is now t=12047 s. Where is the ball now?
  - ground truth: `{"position": [0.7353129367877614, -0.32523782002977264, -0.6111758583821705]}`
  - answer: `{"position": [1.45, -0.32, -0.48]}`
  - tool calls: search_text({"k": 1, "query": "ball", "object": "ball"}); search_text({"query": "ball", "k": 1})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search_text({"k": 1, "query": "carton"})
### pred_event / M0_R1
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search({"object": "water", "time_range": [0, 43398]})
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{}`
  - tool calls: search({"object": "organizer", "time_range": [0, 39135]})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: search({"object": "water", "time_range": [0, 46602]})
- `s1-current_location-003` (current_location): It is now t=12047 s. Where is the ball now?
  - ground truth: `{"position": [0.7353129367877614, -0.32523782002977264, -0.6111758583821705]}`
  - answer: `{}`
  - tool calls: search({"object": "ball", "time_range": [0, 12047]})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search({"object": "carton", "time_range": [0, 38507]}); <empty reply, retried>({})
### pred_event / M1_R0
- `s1-previous_location-000` (previous_location): It is now t=2308 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.705678762902532, 1.1836474949511666, -1.0404429634453065]}`
  - answer: `{"position": [2.01, 0.48, 0.1], "time": 1653.0}`
  - tool calls: search_text({"k": 1, "query": "organizer before moved"})
- `s1-previous_location-001` (previous_location): It is now t=13352 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{"position": [1.86, 0.39, 0.11], "time": 7953.0, "objects": ["clock"]}`
  - tool calls: search_text({"query": "clock", "k": 1})
- `s1-previous_location-002` (previous_location): It is now t=34400 s. Where was the frame before it was last moved?
  - ground truth: `{"position": [1.2004572714836572, 0.5348049807823532, -1.0927757092301702]}`
  - answer: `{"position": [1.94, 0.43, 0.16]}`
  - tool calls: search_text({"k": 1, "query": "frame was last moved"})
- `s1-previous_location-003` (previous_location): It is now t=8500 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{"position": [1.86, 0.39, 0.11], "time": 7953.0, "objects": ["clock"]}`
  - tool calls: search_text({"k": 1, "query": "clock"})
- `s1-previous_location-004` (previous_location): It is now t=40621 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.7050900163387488, 1.1794429766032148, -1.0414010139656797]}`
  - answer: `{"position": [2.0, 0.79, 1.07], "time": 35687.0}`
  - tool calls: search_text({"query": "organizer moved", "k": 1})
### pred_event / M1_R1
- `s1-previous_location-000` (previous_location): It is now t=2308 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.705678762902532, 1.1836474949511666, -1.0404429634453065]}`
  - answer: `{"position": [2.01, 0.48, 0.1]}`
  - tool calls: search({"object": "organizer", "time_range": [0, 2308]})
- `s1-previous_location-001` (previous_location): It is now t=13352 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{}`
  - tool calls: <empty reply, retried>({}); search_time({"time_or_range": [0, 13352], "object": "clock"}); search_text({"query": "clock moved"})
- `s1-previous_location-002` (previous_location): It is now t=34400 s. Where was the frame before it was last moved?
  - ground truth: `{"position": [1.2004572714836572, 0.5348049807823532, -1.0927757092301702]}`
  - answer: `{"position": [1.94, 0.43, 0.16]}`
  - tool calls: search({"k": 1, "object": "frame", "time_range": [0, 34400]})
- `s1-previous_location-003` (previous_location): It is now t=8500 s. Where was the clock before it was last moved?
  - ground truth: `{"position": [-1.3363284778669142, 0.9105460115551363, 1.0025199026249407]}`
  - answer: `{"position": [1.86, 0.39, 0.11], "objects": ["clock"]}`
  - tool calls: search_time({"time_or_range": [0, 8500], "object": "clock"}); search_text({"query": "clock"})
- `s1-previous_location-004` (previous_location): It is now t=40621 s. Where was the organizer before it was last moved?
  - ground truth: `{"position": [1.7050900163387488, 1.1794429766032148, -1.0414010139656797]}`
  - answer: `{"position": [2.0, 0.79, 1.07], "time": 35687.0}`
  - tool calls: search({"object": "organizer", "time_range": [0, 40621]})
### pred_event / M2_R0
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-0.83, -0.18, 2.17]}`
  - tool calls: search_text({"query": "water", "k": 1})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-0.83, -0.18, 2.17]}`
  - tool calls: search_text({"k": 1, "query": "water"})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search_text({"k": 1, "query": "carton"})
- `s1-current_location-005` (current_location): It is now t=35528 s. Where is the ball now?
  - ground truth: `{"position": [-1.2451422492372466, 0.9721417203013722, 0.7779724376761449]}`
  - answer: `{"position": [1.89, 0.45, -0.0], "time": 25913.0, "objects": ["ball"]}`
  - tool calls: search_text({"k": 1, "query": "ball", "object": "ball"}); search_text({"query": "ball", "k": 1})
- `s1-current_location-008` (current_location): It is now t=6966 s. Where is the carton now?
  - ground truth: `{"position": [1.9071528835762317, 0.5293741052178336, 0.025593448623421056]}`
  - answer: `{"position": [1.97, 0.53, 0.46]}`
  - tool calls: search_text({"k": 1, "query": "carton"})
### pred_event / M2_R1
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-1.18, 0.99, 1.45], "objects": ["water"]}`
  - tool calls: search({"object": "water", "time_range": [0, 43398]})
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{"position": [-0.37, 0.54, -0.96], "time": 35684.0, "objects": ["organizer"]}`
  - tool calls: search({"object": "organizer", "time_range": [0, 39135]})
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{"position": [-1.18, 0.99, 1.45], "objects": ["water"]}`
  - tool calls: search({"object": "water", "time_range": [0, 46602]})
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"position": [1.92, 0.55, 0.02], "objects": ["carton"]}`
  - tool calls: search({"object": "carton", "time_range": [0, 38507]})
- `s1-current_location-005` (current_location): It is now t=35528 s. Where is the ball now?
  - ground truth: `{"position": [-1.2451422492372466, 0.9721417203013722, 0.7779724376761449]}`
  - answer: `{"position": [-0.59, -0.23, 0.67], "time": 30871.0, "objects": ["ball"]}`
  - tool calls: search({"object": "ball", "time_range": [0, 35528]})
### pred_event / blind
- `s1-current_location-000` (current_location): It is now t=43398 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: none
- `s1-current_location-001` (current_location): It is now t=39135 s. Where is the organizer now?
  - ground truth: `{"position": [1.9269349575361328, 0.8284455801643671, 1.0489356802412264]}`
  - answer: `{}`
  - tool calls: none
- `s1-current_location-002` (current_location): It is now t=46602 s. Where is the water now?
  - ground truth: `{"position": [-0.28639056778275684, 0.5078889867896158, -0.852927978499961]}`
  - answer: `{}`
  - tool calls: none
- `s1-current_location-003` (current_location): It is now t=12047 s. Where is the ball now?
  - ground truth: `{"position": [0.7353129367877614, -0.32523782002977264, -0.6111758583821705]}`
  - answer: `{"objects": ["ball"]}`
  - tool calls: none
- `s1-current_location-004` (current_location): It is now t=38507 s. Where is the carton now?
  - ground truth: `{"position": [0.1032096501609906, 0.5487470012776599, -0.9873959501444936]}`
  - answer: `{"objects": ["carton"]}`
  - tool calls: none