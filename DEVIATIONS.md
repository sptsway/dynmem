# Deviations from the project plan

Each entry: what the plan said, what was found, what was done.

1. **Environment.** Plan: Python 3.11, `uv` or `venv`, `ffmpeg` via Homebrew. Found: none of
   `uv`, Python 3.11 or `ffmpeg` installed. Installed `uv` 0.13.8 and `ffmpeg` 9.0.2 with Homebrew;
   Python 3.11 provided by `uv venv --python 3.11`.
2. **Hardware.** Apple M4 Pro, 24 GB RAM, 188 GB free disk at start. No NVIDIA GPU.
3. **Scan labels (Final_Scan.zip, MD5 verified).** Plan: use `mesh_labeled.ply` / `pred_mask/` for instance
   labels. Found: `mesh_labeled.ply` is a coloured point cloud (4,140,377 points, 15 distinct colours) with
   no label names. `predictions.txt` lists mask files with numeric class ids and confidences only. No id-to-name
   table ships with the scan. Decision: Stage B uses coordinates only for now. `nearest_instance` stays
   optional (first item in the plan's cut order after interval questions and the second provider).
4. **Scan frame.** Point-cloud bounds: x [-2.28, 3.70], y [-0.56, 1.73], z [-1.96, 3.00] metres.
   y is the vertical axis. The sanity check for placed-object positions will use this box once
   `icp_aligned_pose.npy` files are available.
5. **No API keys.** Plan: Gemini primary, Anthropic optional, `GEMINI_API_KEY` required. Found: the user has
   subscriptions only. Decision (user's choice): the local backend is primary. Added `OllamaBackend`
   (Ollama HTTP API, no key). `claude -p` and subscription logins are still not used.
6. **Model.** The user mentioned Qwen2.5-7B; that model is not installed. Installed: `qwen3.5:9b`
   (9.7B, nvfp4, tools and vision), `qwen3.5:0.8b`, `tinyllama`. Using `qwen3.5:9b` for the agent,
   paraphrasing and (if Stage A runs) captioning. Thinking is disabled (`think: false`).
   Consequences: absolute accuracy is not comparable to the Gemini/GPT-4o numbers in ReMEmbR; the judge for
   free-text answers is the same model as the agent, so there is no independent judge.
7. **Ollama on this Mac.** The server log reported CPU compute (GPU discovery timed out) on first start.
   Probe latency was 2 to 6 s per question on a toy memory. To be re-measured on real runs.
8. **Dataset access.** Plan: download `Final_Dataset.zip` (30.2 GB) and verify its MD5. Download speed was
   about 0.8 MB/s (about 9 h). Stage B only needs six small files per recording (4.1 MB for all 96), so they are
   fetched with HTTP range requests (`remotezip`), which skips the 22 GB of `.vrs` data. Zip CRC32 is checked
   per member. The full download keeps running in the background so the archive MD5 can still be verified.
9. **Timestamps and frames (verified on disk).** `gt_object.csv` / `pred_object.csv` columns:
   `timestamp,tx,ty,tz,qx,qy,qz,qw`, three `#` header lines, parent frame `vicon`. Timestamps are Unix epoch
   seconds at 30 Hz. Recordings are short: object motion spans 1.3 to 7.6 s (median 3.5 s), so each
   recording is one pick-and-place. `icp_aligned_pose.npy` is a 4x4 matrix that maps scan -> recording. Applying
   its inverse puts 192 of 192 start/final positions inside the scan bounding box; applying it forward puts 40
   of 192 inside. Stage B uses the inverse.
10. **Sanity check results (tests/test_coordinates.py).** Distance to the nearest scan point: start poses
    median 0.016 m (max 0.341 m); final poses median 0.177 m (max 0.500 m). Final poses are object centres
    placed at new spots, so they sit further from the original scan surface. Test thresholds are descriptive
    (median < 0.25 m, max < 0.6 m), not tuned.
11. **Object counts.** 9 objects, 10 or 11 recordings each (96 total).
12. **Dev/test split.** Stratified by object, seed 0: 27 dev and 69 test recordings, no overlap (3 dev per object).
    Plan said 30% dev; rounding by object gives 28%.
13. **Dev tuning (see `configs/events.yaml`, `configs/scoring.yaml`).** Speed threshold 0.1 m/s. Position tolerance
    0.25 m, time tolerance 10 s, chosen from dev perception-error statistics. On dev, predicted place poses have
    median error 0.045 m and max 2.161 m, so some predicted events are wrong by more than the tolerance.
    Each recording contains one move, so every timeline event is one recording.
14. **Memory footprint.** With `num_ctx: 8192`, Ollama's MLX runner used 16 GB and pushed swap to 12.8 of 13.3 GB
    during the first dev run, which was stopped. The largest observed call was 3,076 input tokens, so `num_ctx`
    is now 5120 (7.7 GB resident). Backend settings are part of the cache key. Results from the stopped run were discarded.
