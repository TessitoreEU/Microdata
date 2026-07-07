"""Shared helper for recognising section-id keys (e.g. "1", "1.1", "6.2.3") inside
nested JSON documents, so that metadata keys like "_metadata" or "title" are not
mistaken for sections while walking the tree.
"""
import re

_SECTION_ID_RE = re.compile(r"^\d+(\.\d+)*$")


def is_section_id(key: str) -> bool:
    return bool(_SECTION_ID_RE.match(str(key)))
