"""Parses an uploaded JSON document into a flat dict of Section objects.

The primary shape (matching the real documents this app targets) is a nested dict keyed
by section id, where sub-sections are nested dict entries also keyed by section id:

    {
      "_metadata": {"document_title": "..."},
      "1": {
        "title": "Research Entity",
        "1.1": {
          "title": "Leading Research Entity",
          "tables": [{"label": "Entity name:", "value": "..."}]
        }
      },
      "3": {
        "title": "Purpose",
        "3.1": {"title": "...", "content": "free text..."}
      }
    }

A section's text can come from a "content" string, a "text"/"body" string, or a "tables"
list of {"label", "value"} pairs (rendered as "label value" lines). Keys that aren't
section-id-shaped (e.g. "_metadata", "title") are treated as metadata, not sections, and
are skipped/not recursed into as if they were sub-sections.

A flat dict of id -> text ({"1": "...", "1.1": "..."}) and a list of
[{"id", "title", "content"}, ...] are also accepted for convenience.
"""
import json
from typing import Dict, List, Union

from core.models import Section
from core.section_ids import is_section_id


def _tables_to_text(tables: List[dict]) -> str:
    lines = []
    for row in tables:
        label = row.get("label", "")
        value = row.get("value", "")
        lines.append(f"{label} {value}".strip())
    return "\n".join(lines)


def _content_of(value: Union[str, dict]) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("content", "text", "body"):
            if key in value and isinstance(value[key], str):
                return value[key]
        if isinstance(value.get("tables"), list):
            return _tables_to_text(value["tables"])
    return ""


def _title_of(section_id: str, value: Union[str, dict]) -> str:
    if isinstance(value, dict) and isinstance(value.get("title"), str):
        return value["title"]
    return section_id


def _flatten_dict(data: dict, sections: Dict[str, Section]) -> None:
    for key, value in data.items():
        if not is_section_id(key):
            continue
        section_id = str(key)
        sections[section_id] = Section(
            id=section_id,
            title=_title_of(section_id, value),
            content=_content_of(value),
        )
        if isinstance(value, dict):
            nested = {k: v for k, v in value.items() if is_section_id(k)}
            if nested:
                _flatten_dict(nested, sections)


def parse_sections(raw_text: str) -> Dict[str, Section]:
    data = json.loads(raw_text)
    sections: Dict[str, Section] = {}

    if isinstance(data, list):
        for item in data:
            section_id = str(item.get("id"))
            sections[section_id] = Section(
                id=section_id,
                title=item.get("title", section_id),
                content=item.get("content", item.get("text", "")),
            )
    elif isinstance(data, dict):
        _flatten_dict(data, sections)
    else:
        raise ValueError("Unsupported JSON structure: expected an object or a list")

    return sections
