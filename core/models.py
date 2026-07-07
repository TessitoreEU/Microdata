from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Section:
    id: str
    title: str
    content: str


@dataclass
class Check:
    id: str
    section: str
    text: str
    source_file: str

    @property
    def name(self) -> str:
        return self.text if len(self.text) <= 80 else self.text[:77] + "..."


@dataclass
class CheckResult:
    run_id: str
    timestamp: str
    check_id: str
    check_name: str
    section_id: str
    section_found: bool
    model: str
    status: str  # PASS | FAIL | NA | ERROR
    explanation: str
    raw_response: Optional[str] = field(default=None)
