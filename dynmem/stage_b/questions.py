"""Template-based Stage B question generation. Ground truth comes from gt_event only.

Answer definitions (query time T, object o, moves = events of o with t_place <= T):
  current_location : p_place of the latest move, or the initial pose if there is none.
  previous_location: p_pick of the latest move (needs >= 1 move).
  when_moved       : t_place of the latest move (needs >= 1 move).
  count            : number of moves.
  interval         : objects with a move whose t_place lies in (t1, t2].
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from dynmem.stage_b.events import Event
from dynmem.stage_b.policies import initial_states
from dynmem.stage_b.timeline import Timeline

TEMPLATES = {
    "current_location": "It is now t={t:.0f} s. Where is the {obj} now?",
    "previous_location": "It is now t={t:.0f} s. Where was the {obj} before it was last moved?",
    "when_moved": "It is now t={t:.0f} s. When was the {obj} last moved?",
    "count": "It is now t={t:.0f} s. How many times has the {obj} been moved so far?",
    "interval": "It is now t={t:.0f} s. Which objects were moved between t={t1:.0f} s and t={t2:.0f} s?",
}


@dataclass(frozen=True)
class Question:
    id: str
    qtype: str
    text: str
    t_query: float
    obj: str | None
    gt: dict

    def to_dict(self) -> dict:
        return asdict(self)


def split_recordings(rec_objects: dict[str, str], seed: int = 0, dev_frac: float = 0.3):
    """Split recording ids into (dev, test), stratified by object. Disjoint by construction."""
    rng = np.random.default_rng(seed)
    dev, test = [], []
    for obj in sorted(set(rec_objects.values())):
        ids = sorted(r for r, o in rec_objects.items() if o == obj)
        rng.shuffle(ids)
        n_dev = max(1, round(len(ids) * dev_frac)) if len(ids) > 1 else 0
        dev += ids[:n_dev]
        test += ids[n_dev:]
    return sorted(dev), sorted(test)


def _moves(events, obj, t):
    return sorted((e for e in events if e.object == obj and e.t_place <= t), key=lambda e: e.t_place)


def answer_for(events: list[Event], qtype: str, obj: str | None, t: float, t1=None, t2=None) -> dict | None:
    """Ground-truth answer, or None when the question is not well defined."""
    if qtype == "interval":
        objs = sorted({e.object for e in events if t1 < e.t_place <= t2})
        return {"objects": objs} if objs else None
    moves = _moves(events, obj, t)
    if qtype == "current_location":
        pos = moves[-1].p_place if moves else initial_states(events)[obj].p_pick
        return {"position": list(pos)}
    if qtype == "count":
        return {"count": len(moves)}
    if not moves:
        return None
    if qtype == "previous_location":
        return {"position": list(moves[-1].p_pick)}
    if qtype == "when_moved":
        return {"time": moves[-1].t_place}
    raise ValueError(qtype)


def generate_questions(tl: Timeline, n_per_type: int = 36, seed: int = 0,
                       qtypes=tuple(TEMPLATES)) -> list[Question]:
    events = list(tl.events)
    if not events:
        return []
    rng = np.random.default_rng([seed, tl.seed])
    objects = sorted({e.object for e in events})
    t_lo, t_hi = events[0].t_place, tl.t_end
    out: list[Question] = []
    for qtype in qtypes:
        made, tries = 0, 0
        while made < n_per_type and tries < n_per_type * 50:
            tries += 1
            t = float(rng.uniform(t_lo, t_hi))
            obj = None if qtype == "interval" else str(rng.choice(objects))
            t1 = t2 = None
            if qtype == "interval":
                t1 = float(rng.uniform(t_lo, t))
                t2 = float(min(t, t1 + rng.uniform(600, 3600)))
            gt = answer_for(events, qtype, obj, t, t1, t2)
            if gt is None:
                continue
            text = TEMPLATES[qtype].format(t=t, obj=obj, t1=t1, t2=t2)
            out.append(Question(f"s{tl.seed}-{qtype}-{made:03d}", qtype, text, t, obj, gt))
            made += 1
    return out
