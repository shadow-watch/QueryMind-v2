from typing import Any
from unittest.mock import patch

import httpx

from querymind.adapters.live_adapter import LiveAnalyticsAdapter
from querymind.domain.contracts import QueryType


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            req = httpx.Request("POST", "https://example.invalid")
            resp = httpx.Response(self.status_code, request=req)
            raise httpx.HTTPStatusError("error", request=req, response=resp)


class FakeClient:
    def __init__(self, responses: list[FakeResponse]) -> None:
        self._responses = responses
        self._index = 0

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        return None

    def post(self, *args: Any, **kwargs: Any) -> FakeResponse:
        if self._index >= len(self._responses):
            raise RuntimeError("No more fake responses configured")
        res = self._responses[self._index]
        self._index += 1
        return res


def test_live_adapter_success_with_mocked_http_calls() -> None:
    gemini_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"esql":"FROM orders_index | STATS aov = AVG(total_price) BY country | LIMIT 10"}'
                        }
                    ]
                }
            }
        ]
    }
    elastic_payload = {
        "columns": [{"name": "country"}, {"name": "aov"}],
        "values": [["DE", 124.4], ["FR", 118.9]],
    }

    fake_client = FakeClient([FakeResponse(gemini_payload), FakeResponse(elastic_payload)])

    with patch("querymind.adapters.live_adapter.settings.gemini_api_key", "g-key"), patch(
        "querymind.adapters.live_adapter.settings.elastic_api_key", "e-key"
    ), patch("querymind.adapters.live_adapter.settings.elastic_endpoint", "https://elastic.local"), patch(
        "querymind.adapters.live_adapter.httpx.Client", return_value=fake_client
    ):
        adapter = LiveAnalyticsAdapter()
        result = adapter.run("Average order value by country", QueryType.aggregation, 10)

    assert "AVG(total_price)" in result.esql
    assert len(result.rows) == 2
    assert result.rows[0]["country"] == "DE"
    assert result.confidence == 85


def test_live_adapter_raises_for_invalid_gemini_json() -> None:
    gemini_payload = {
        "candidates": [{"content": {"parts": [{"text": "not-json"}]}}],
    }

    fake_client = FakeClient([FakeResponse(gemini_payload)])

    with patch("querymind.adapters.live_adapter.settings.gemini_api_key", "g-key"), patch(
        "querymind.adapters.live_adapter.settings.elastic_api_key", "e-key"
    ), patch("querymind.adapters.live_adapter.httpx.Client", return_value=fake_client):
        adapter = LiveAnalyticsAdapter()

        try:
            adapter.run("Average order value by country", QueryType.aggregation, 10)
            assert False, "Expected invalid Gemini JSON to raise runtime error"
        except RuntimeError as exc:
            assert "not valid JSON" in str(exc)


def test_live_adapter_raises_for_elastic_http_error() -> None:
    gemini_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '{"esql":"FROM orders_index | STATS revenue = SUM(total_price) BY product_id | LIMIT 10"}'
                        }
                    ]
                }
            }
        ]
    }
    fake_client = FakeClient(
        [
            FakeResponse(gemini_payload),
            FakeResponse({}, status_code=500),
            FakeResponse({}, status_code=500),
            FakeResponse({}, status_code=500),
        ]
    )

    with patch("querymind.adapters.live_adapter.settings.gemini_api_key", "g-key"), patch(
        "querymind.adapters.live_adapter.settings.elastic_api_key", "e-key"
    ), patch("querymind.adapters.live_adapter.settings.elastic_endpoint", "https://elastic.local"), patch(
        "querymind.adapters.live_adapter.httpx.Client", return_value=fake_client
    ):
        adapter = LiveAnalyticsAdapter()

        try:
            adapter.run("Top products by revenue", QueryType.aggregation, 10)
            assert False, "Expected Elasticsearch HTTP error to raise runtime error"
        except RuntimeError as exc:
            assert "Elasticsearch query execution failed" in str(exc)
