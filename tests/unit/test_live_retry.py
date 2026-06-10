from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import httpx

from querymind.adapters.live_adapter import LiveAnalyticsAdapter


class RetryFakeResponse:
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


class RetryFakeClient:
    def __init__(self, response_factory: Callable[[], RetryFakeResponse]) -> None:
        self.response_factory = response_factory

    def __enter__(self) -> "RetryFakeClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        return None

    def post(self, *args: Any, **kwargs: Any) -> RetryFakeResponse:
        return self.response_factory()


def test_post_with_retry_succeeds_after_transient_failures() -> None:
    attempts = {"count": 0}

    def response_factory() -> RetryFakeResponse:
        attempts["count"] += 1
        if attempts["count"] < 3:
            return RetryFakeResponse({}, status_code=502)
        return RetryFakeResponse({"ok": True}, status_code=200)

    with patch("querymind.adapters.live_adapter.httpx.Client", return_value=RetryFakeClient(response_factory)), patch(
        "querymind.adapters.live_adapter.time.sleep", return_value=None
    ), patch("querymind.adapters.live_adapter.settings.live_max_retries", 3), patch(
        "querymind.adapters.live_adapter.settings.live_backoff_base_ms", 1
    ):
        adapter = LiveAnalyticsAdapter()
        resp = adapter._post_with_retry(
            url="https://example.local",
            json_payload={"x": 1},
            timeout_s=1.0,
            headers=None,
            error_prefix="test",
        )

    assert resp.json() == {"ok": True}
    assert attempts["count"] == 3


def test_post_with_retry_raises_after_max_attempts() -> None:
    attempts = {"count": 0}

    def response_factory() -> RetryFakeResponse:
        attempts["count"] += 1
        return RetryFakeResponse({}, status_code=503)

    with patch("querymind.adapters.live_adapter.httpx.Client", return_value=RetryFakeClient(response_factory)), patch(
        "querymind.adapters.live_adapter.time.sleep", return_value=None
    ), patch("querymind.adapters.live_adapter.settings.live_max_retries", 2), patch(
        "querymind.adapters.live_adapter.settings.live_backoff_base_ms", 1
    ):
        adapter = LiveAnalyticsAdapter()
        try:
            adapter._post_with_retry(
                url="https://example.local",
                json_payload={"x": 1},
                timeout_s=1.0,
                headers=None,
                error_prefix="retry failed",
            )
            assert False, "Expected retry exhaustion error"
        except RuntimeError as exc:
            assert "retry failed" in str(exc)

    assert attempts["count"] == 3
