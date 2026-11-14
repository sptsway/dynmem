# DynMem

Dynamic episodic memory for embodied agents: answering where-and-when questions after objects move.

This is a measurement and systems study, not a state-of-the-art claim. Every number in the
reports is produced by a script that reads files under `results/`.

Terms used throughout:

- **memory store**: the vector database plus its metadata.
- **scene graph**: object-level structure of the scene (nodes = static instances and movable objects, edges = spatial relations).
- **episode**: one continuous recording or one task run.

## Status

Work in progress. See `DEVIATIONS.md` for every place where the plan was changed and `COSTS.md` for API spend.

## Setup

```
uv venv --python 3.11 .venv && uv pip install -e ".[dev]"
export GEMINI_API_KEY=...        # read from the environment only, never written to disk
make test
```

## Datasets and licenses

| Dataset | Use | License |
|---|---|---|
| NaVQA (from ReMEmbR, arXiv 2409.13682) | Stage A questions | to be confirmed |
| CODa (UT Austin) | Stage A video and poses | to be confirmed |
| Lost & Found (Zenodo 14967441, arXiv 2411.19162) | Stage B trajectories | CC BY 4.0 |

No dataset files are stored in this repository.

## License

MIT for code (see `LICENSE`).
