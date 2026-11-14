import json
from pathlib import Path

import pytest
import yaml

from dynmem.freeze import OUT, current

PROMPTS = sorted(Path("prompts").glob("*.md"))


def test_frozen_files_match_recorded_hashes():
    cfg = yaml.safe_load(Path("configs/scoring.yaml").read_text())
    if not cfg["frozen"]:
        pytest.skip("not frozen yet")
    assert json.loads(OUT.read_text()) == current(), "frozen prompt/config changed after the freeze"


def test_prompts_contain_no_ground_truth_answers():
    """No GT position or time from any generated question set may appear in any prompt file."""
    from dynmem.stage_b.data import DEFAULT_ROOT, list_recordings, load_recording
    from dynmem.stage_b.questions import generate_questions, split_recordings
    from dynmem.stage_b.timeline import build_timeline

    if not DEFAULT_ROOT.exists():
        pytest.skip("data not downloaded")
    text = "\n".join(p.read_text() for p in PROMPTS)
    ids = list(list_recordings(DEFAULT_ROOT))
    recs = [load_recording(DEFAULT_ROOT, r, "gt_event", 0.1) for r in ids]
    for seed in (1, 2, 3, 100):
        for q in generate_questions(build_timeline(recs, seed), 30):
            if "position" in q.gt:
                for v in q.gt["position"]:
                    assert f"{v:.2f}" not in text
            if "time" in q.gt:
                assert f"{q.gt['time']:.0f}" not in text
