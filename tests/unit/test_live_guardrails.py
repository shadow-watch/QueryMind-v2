from typing import Any

from querymind.adapters.live_adapter import LiveAnalyticsAdapter
from querymind.domain.contracts import QueryRequest, QueryStatus, QueryType
from querymind.services.pipeline import PipelineService


class FailingLiveAdapter:
    def run(self, query: str, query_type: QueryType, max_results: int) -> Any:
        raise RuntimeError("Live mode requires ELASTIC_API_KEY and GEMINI_API_KEY to be configured.")


def test_live_adapter_requires_keys() -> None:
    adapter = LiveAnalyticsAdapter()

    try:
        adapter.run("Average order value by country", QueryType.aggregation, 10)
        assert False, "Expected missing-key runtime error"
    except RuntimeError as exc:
        assert "requires ELASTIC_API_KEY and GEMINI_API_KEY" in str(exc)


def test_pipeline_maps_live_adapter_errors_to_api_error_response() -> None:
    pipeline = PipelineService(adapter=FailingLiveAdapter())

    res = pipeline.run(QueryRequest(query="Average order value by country", include_raw=True))

    assert res.status == QueryStatus.error
    assert res.query_type == QueryType.aggregation
    assert res.error_message is not None
    assert "requires ELASTIC_API_KEY and GEMINI_API_KEY" in res.error_message
    assert res.audit_log is not None
    assert res.audit_log.confidence == 0
