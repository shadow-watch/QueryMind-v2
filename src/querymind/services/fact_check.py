from typing import Any


class FactChecker:
    def validate(self, insight_title: str | None, rows: list[dict[str, Any]]) -> tuple[bool, list[str]]:
        if not rows:
            return True, []

        warnings: list[str] = []
        row_text = " ".join(str(v).lower() for r in rows for v in r.values() if v is not None)

        if insight_title and "revenue" in insight_title.lower() and "revenue" not in row_text:
            warnings.append("Insight mentions revenue but raw rows do not include revenue field.")

        return len(warnings) == 0, warnings
