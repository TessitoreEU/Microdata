"""Persists check-run results to, and loads them back from, results/results.json."""
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from core.models import CheckResult

RESULTS_FILE = Path("results/results.json")


def save_run(results: List[CheckResult]) -> None:
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = load_all()
    existing.extend(results)
    RESULTS_FILE.write_text(json.dumps([asdict(r) for r in existing], indent=2))


def load_all() -> List[CheckResult]:
    if not RESULTS_FILE.exists():
        return []
    raw = json.loads(RESULTS_FILE.read_text())
    return [CheckResult(**item) for item in raw]


def list_run_ids() -> List[str]:
    seen = []
    for result in load_all():
        if result.run_id not in seen:
            seen.append(result.run_id)
    return seen
