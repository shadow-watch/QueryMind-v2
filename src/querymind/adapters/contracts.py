from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdapterResult:
    esql: str
    rows: list[dict[str, Any]]
    insight_title: str | None
    insight_text: str | None
    confidence: int