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
