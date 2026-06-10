from unittest.mock import patch

from fastapi.testclient import TestClient

from querymind.main import app

client = TestClient(app)


def test_ui_root_endpoint() -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "QueryMind v2" in res.text
    assert "Run Query" in res.text


def test_health_endpoint() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "env" in data
    assert "mock_mode" in data


def test_diagnostics_endpoint() -> None:
    res = client.get("/diagnostics")
    assert res.status_code == 200
    data = res.json()
    assert "app_name" in data
    assert "env" in data
    assert "mock_mode" in data
    assert "gemini_model" in data
    assert "query_timeout_ms" in data
    assert "max_results_limit" in data
    assert "elastic_configured" in data
    assert "gemini_configured" in data


def test_query_endpoint_aov() -> None:
    res = client.post(
        "/query",
        json={"query": "Average order value by country", "include_raw": True, "max_results": 10},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["query_type"] == "aggregation"
    assert len(data["raw_results"]) > 0
    assert "AVG(total_price) BY country" in data["audit_log"]["esql_generated"]


def test_query_endpoint_validation_error_for_short_query() -> None:
    res = client.post("/query", json={"query": "hi", "include_raw": True})
    assert res.status_code == 422


def test_request_id_header_is_returned() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers


def test_request_id_header_is_echoed_when_provided() -> None:
    req_id = "test-request-id-123"
    res = client.get("/health", headers={"X-Request-ID": req_id})
    assert res.status_code == 200
    assert res.headers["X-Request-ID"] == req_id


def test_ready_endpoint_in_mock_mode() -> None:
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert "checks" in data


def test_ready_endpoint_not_ready_when_live_mode_missing_keys() -> None:
    with patch("querymind.main.settings.mock_mode", False), patch(
        "querymind.main.settings.elastic_api_key", ""
    ), patch("querymind.main.settings.gemini_api_key", ""):
        res = client.get("/ready")

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_ready"
