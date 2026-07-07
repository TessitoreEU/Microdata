"""Builds summary statistics for a set of check results, for display in the report tab."""
from collections import Counter
from typing import Dict, List

from core.models import CheckResult


def summarize(results: List[CheckResult]) -> Dict[str, int]:
    counts = Counter(r.status for r in results)
    return {
        "total": len(results),
        "pass": counts.get("PASS", 0),
        "fail": counts.get("FAIL", 0),
        "na": counts.get("NA", 0),
        "error": counts.get("ERROR", 0),
    }


def to_table_rows(results: List[CheckResult]) -> List[dict]:
    return [
        {
            "Check ID": r.check_id,
            "Check Name": r.check_name,
            "Section": r.section_id,
            "Status": r.status,
            "Explanation": r.explanation,
            "Model": r.model,
            "Run ID": r.run_id,
            "Timestamp": r.timestamp,
        }
        for r in results
    ]
