"""Loads check definitions from every JSON file in a directory.

Each check-definition file mirrors the shape of the section tree it targets. A section
entry can carry an "elements_to_be_included_or_confirmed" list; every item's "text" becomes
one check to run against that section id:

    {
      "6": {
        "6.2": {
          "title": "Anonymisation of results",
          "elements_to_be_included_or_confirmed": [
            {"text": "The specific confidentiality thresholds ... will be applied."},
            {"text": "No confidential information can be inferred ..."}
          ]
        }
      }
    }

Keys that aren't section-id-shaped (e.g. "title", "elements_to_be_included_or_confirmed"
itself) are not recursed into as sub-sections.
"""
import json
from pathlib import Path
from typing import List

from core.models import Check
from core.section_ids import is_section_id

ELEMENTS_KEY = "elements_to_be_included_or_confirmed"


def _walk(data: dict, source_file: str, checks: List[Check]) -> None:
    for key, value in data.items():
        if not is_section_id(key) or not isinstance(value, dict):
            continue
        section_id = str(key)

        for i, element in enumerate(value.get(ELEMENTS_KEY, []), start=1):
            text = element.get("text", "") if isinstance(element, dict) else str(element)
            checks.append(
                Check(
                    id=f"{section_id}-{i}",
                    section=section_id,
                    text=text,
                    source_file=source_file,
                )
            )

        nested = {k: v for k, v in value.items() if is_section_id(k)}
        if nested:
            _walk(nested, source_file, checks)


def load_checks(checks_dir: str) -> List[Check]:
    checks: List[Check] = []
    directory = Path(checks_dir)
    if not directory.is_dir():
        return checks

    for file_path in sorted(directory.glob("*.json")):
        try:
            data = json.loads(file_path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {file_path.name}: {exc}") from exc

        if isinstance(data, dict):
            _walk(data, file_path.name, checks)

    return checks
