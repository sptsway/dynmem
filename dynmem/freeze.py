"""Freeze prompts and configs before any test run: record SHA-256 hashes and enforce them in tests."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

FROZEN_FILES = ["prompts/agent_system.md", "prompts/agent_force_answer.md", "prompts/agent_retry.md",
                "configs/scoring.yaml", "configs/events.yaml", "dynmem/tools.py", "dynmem/agent.py"]
OUT = Path("configs/frozen_hashes.json")


def digest(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def current() -> dict[str, str]:
    return {p: digest(p) for p in FROZEN_FILES}


if __name__ == "__main__":
    OUT.write_text(json.dumps(current(), indent=2) + "\n")
    print("wrote", OUT, file=sys.stderr)
