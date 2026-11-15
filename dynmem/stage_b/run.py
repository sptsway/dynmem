"""Run Stage B cells: (event source) x (memory policy) x (retrieval design), plus the blind baseline.

Usage: python -m dynmem.stage_b.run --split dev --timelines 100 --n-per-type 3 --sources gt_event
Output: results/stage_b/<split>/<source>__<cell>.jsonl, one line per question. Re-running resumes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import yaml

from dynmem.agent import Agent
from dynmem.embed import Embedder
from dynmem.llm import make_llm
from dynmem.stage_b.data import DEFAULT_ROOT, list_recordings, load_recording
from dynmem.stage_b.policies import POLICIES, build_memory, initial_states
from dynmem.stage_b.questions import generate_questions, split_recordings
from dynmem.stage_b.score import load_scoring, score_answer
from dynmem.stage_b.timeline import build_timeline, remap_events
from dynmem.store import QdrantStore
from dynmem.tools import Toolbox

DESIGNS = {
    "R0": ["search_text"],
    "R1": ["search", "search_text", "search_time", "search_position", "object_history"],
}


def git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _locked(lock, fn, x):
    with lock:
        return fn(x)


def done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(l)["qid"] for l in path.read_text().splitlines() if l.strip()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--timelines", type=int, nargs="+", required=True, help="timeline seeds")
    ap.add_argument("--n-per-type", type=int, default=36)
    ap.add_argument("--sources", nargs="+", default=["gt_event"])
    ap.add_argument("--policies", nargs="+", default=list(POLICIES))
    ap.add_argument("--designs", nargs="+", default=list(DESIGNS))
    ap.add_argument("--blind", action="store_true", help="also run the no-memory baseline")
    ap.add_argument("--qtypes", nargs="+", default=None)
    ap.add_argument("--n-override", nargs="*", default=[], help="per-type counts, e.g. previous_place=30")
    ap.add_argument("--limit", type=int, default=None, help="questions per timeline (smoke tests)")
    ap.add_argument("--agent", default="agent", help="key in configs/models.yaml: agent or local_baseline")
    ap.add_argument("--workers", type=int, default=1, help="questions in flight (API backends)")
    ap.add_argument("--out", default="results/stage_b")
    a = ap.parse_args(argv)

    models, ev_cfg, sc_cfg = (yaml.safe_load(Path(p).read_text()) for p in
                              ("configs/models.yaml", "configs/events.yaml", "configs/scoring.yaml"))
    scoring = load_scoring()
    recs = list_recordings(DEFAULT_ROOT)
    dev, test = split_recordings(recs, **ev_cfg["split"])
    ids = dev if a.split == "dev" else test
    thr = ev_cfg["speed_thr_mps"]
    gt_recs = [load_recording(DEFAULT_ROOT, r, "gt_event", thr) for r in ids]
    pred_recs = {r.id: r for r in (load_recording(DEFAULT_ROOT, i, "pred_event", thr) for i in ids)}

    emb = Embedder()
    emb_lock = threading.Lock()  # torch/MPS encode is not shared across threads
    text_cache: dict[str, "np.ndarray"] = {}  # event texts repeat across questions: embed each text once

    def embed_docs(texts):
        with emb_lock:
            missing = [x for x in dict.fromkeys(texts) if x not in text_cache]
            if missing:
                text_cache.update(zip(missing, emb.embed_docs(missing)))
            return np.array([text_cache[x] for x in texts])

    embed_query = lambda x: _locked(emb_lock, emb.embed_query, x)
    ag = models[a.agent]
    llm = make_llm(ag["provider"], ag["model"], tag=f"stage_b_{a.split}",
                   extra_params=models.get(ag["provider"]))
    meta = {"git": git_hash(), "model": ag["model"], "provider": ag["provider"], "split": a.split}
    out_dir = Path(a.out) / a.split
    out_dir.mkdir(parents=True, exist_ok=True)

    cells = [(p, d) for p in a.policies for d in a.designs]
    for seed in a.timelines:
        tl = build_timeline(gt_recs, seed)
        # Always generate every type, then filter, so a question's id and content never depend on --qtypes.
        overrides = dict(x.split("=") for x in a.n_override)
        qs = generate_questions(tl, a.n_per_type, seed=0, n_override={k: int(v) for k, v in overrides.items()})
        if a.qtypes:
            qs = [q for q in qs if q.qtype in a.qtypes]
        if a.limit:
            # keep a balanced subset: round-robin over question types
            by = {}
            for q in qs:
                by.setdefault(q.qtype, []).append(q)
            qs = [q for grp in zip(*by.values()) for q in grp][: a.limit]
        initial = initial_states(tl.events)
        for source in a.sources:
            events = tl.events if source == "gt_event" else remap_events(tl, [pred_recs[i] for i in ids])
            runs = [(f"{p}_{d}", p, d) for p, d in cells] + ([("blind", None, None)] if a.blind else [])
            for name, pol, design in runs:
                path = out_dir / f"{source}__{name}.jsonl"
                have = done_ids(path)
                todo = [q for q in qs if q.id not in have]

                def run_one(q, pol=pol, design=design, name=name, source=source, events=events, seed=seed):
                    if pol is None:
                        agent = Agent(llm, None, [])
                    else:
                        store = QdrantStore(emb.dim)
                        build_memory(store, pol, list(events), q.t_query, embed_docs, source, initial=initial)
                        agent = Agent(llm, Toolbox(store, embed_query), DESIGNS[design])
                    r = agent.run(q.text)
                    s = score_answer(q.qtype, r.answer.model_dump() if r.answer else None, q.gt, scoring)
                    return {"qid": q.id, "timeline": seed, "source": source, "cell": name,
                            "qtype": q.qtype, "question": q.text, "gt": q.gt, "score": s,
                            "parsed": r.answer is not None, **r.to_dict(), **meta}

                with path.open("a") as f, ThreadPoolExecutor(a.workers) as pool:
                    for row in pool.map(run_one, todo):  # results come back in question order
                        f.write(json.dumps(row) + "\n")
                        f.flush()
                print(f"seed {seed} {source} {name}: done ({len(qs)} questions)", flush=True)


if __name__ == "__main__":
    main()
