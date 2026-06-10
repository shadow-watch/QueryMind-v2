import json
import time
from typing import Any

import httpx

from querymind.adapters.contracts import AdapterResult
from querymind.core.settings import settings
from querymind.domain.contracts import QueryType


class LiveAnalyticsAdapter:
    def run(self, query: str, query_type: QueryType, max_results: int) -> AdapterResult:
        if not settings.elastic_api_key or not settings.gemini_api_key:
            raise RuntimeError(
                "Live mode requires ELASTIC_API_KEY and GEMINI_API_KEY to be configured."
            )

        timeout_s = settings.query_timeout_ms / 1000
        esql = self._translate_to_esql(query, query_type, max_results, timeout_s)
        rows = self._execute_esql(esql, timeout_s)

        insight_title, insight_text, confidence = self._build_basic_insight(query, rows)

        return AdapterResult(
            esql=esql,
            rows=rows,
            insight_title=insight_title,
            insight_text=insight_text,
            confidence=confidence,
        )

    def _translate_to_esql(
        self,
        query: str,
        query_type: QueryType,
        max_results: int,
        timeout_s: float,
    ) -> str:
        prompt = (
            "Convert the user analytics question into Elasticsearch ES|QL. "
            "Return JSON only with shape {\"esql\": \"...\"}. "
            f"Ensure the query has LIMIT {max_results}. "
            f"Query type hint: {query_type.value}. "
            f"Question: {query}"
        )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
        }

        resp = self._post_with_retry(
            url=url,
            json_payload=payload,
            timeout_s=timeout_s,
            headers=None,
            error_prefix="Gemini translation call failed",
        )

        raw_text = self._extract_gemini_text(resp.json())
        parsed = self._parse_json_maybe_fenced(raw_text)

        esql = str(parsed.get("esql", "")).strip()
        if not esql:
            raise RuntimeError("Gemini translation did not return an ES|QL query.")
        return esql

    def _execute_esql(self, esql: str, timeout_s: float) -> list[dict[str, Any]]:
        headers = {
            "Authorization": f"ApiKey {settings.elastic_api_key}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true",
        }
        url = f"{settings.elastic_endpoint.rstrip('/')}/_query"

        resp = self._post_with_retry(
            url=url,
            json_payload={"query": esql, "format": "json"},
            timeout_s=timeout_s,
            headers=headers,
            error_prefix="Elasticsearch query execution failed",
        )

        data = resp.json()
        columns = [str(col.get("name", "")) for col in data.get("columns", [])]
        values = data.get("values", [])
        rows: list[dict[str, Any]] = [dict(zip(columns, row)) for row in values]
        return rows

    def _build_basic_insight(
        self, user_query: str, rows: list[dict[str, Any]]
    ) -> tuple[str, str, int]:
        if not rows:
            return "No Data Found", "Live query returned no rows for the selected filters.", 50

        title = f"Live Results: {user_query[:60]}"
        if len(rows) == 1:
            detail = "1 row returned from Elasticsearch."
        else:
            detail = f"{len(rows)} rows returned from Elasticsearch."

        return title, detail, 85

    def _extract_gemini_text(self, body: dict[str, Any]) -> str:
        candidates = body.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini response had no candidates.")

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts or "text" not in parts[0]:
            raise RuntimeError("Gemini response had no text part.")
        return str(parts[0]["text"]).strip()

    def _parse_json_maybe_fenced(self, raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Gemini translation output was not valid JSON.") from exc

        if not isinstance(parsed, dict):
            raise RuntimeError("Gemini translation output must be a JSON object.")
        return parsed

    def _post_with_retry(
        self,
        url: str,
        json_payload: dict[str, Any],
        timeout_s: float,
        headers: dict[str, str] | None,
        error_prefix: str,
    ) -> httpx.Response:
        max_retries = max(0, settings.live_max_retries)
        base_ms = max(1, settings.live_backoff_base_ms)
        attempts = max_retries + 1

        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=timeout_s) as client:
                    resp = client.post(url, headers=headers, json=json_payload)
                    resp.raise_for_status()
                    return resp
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                sleep_s = (base_ms * (2**attempt)) / 1000.0
                time.sleep(sleep_s)

        raise RuntimeError(f"{error_prefix}: {last_error}") from last_error