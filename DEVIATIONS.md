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
