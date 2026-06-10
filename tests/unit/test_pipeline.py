from querymind.domain.contracts import QueryRequest, QueryStatus, QueryType
from querymind.services.pipeline import PipelineService


def test_pipeline_aov_success_with_raw() -> None:
    p = PipelineService()
    req = QueryRequest(query="Average order value by country", include_raw=True)
    res = p.run(req)

    assert res.status == QueryStatus.success
    assert res.query_type == QueryType.aggregation
    assert len(res.raw_results) > 0
    assert res.audit_log is not None
    assert "AVG(total_price) BY country" in res.audit_log.esql_generated
    assert res.fact_check_passed is True
    assert res.fact_check_warnings == []


def test_pipeline_hides_raw_when_include_raw_false() -> None:
    p = PipelineService()
    req = QueryRequest(query="Average order value by country", include_raw=False)
    res = p.run(req)

    assert res.status == QueryStatus.success
    assert res.raw_results == []


def test_pipeline_no_data_for_unmatched_query() -> None:
    p = PipelineService()
    req = QueryRequest(query="Tell me something impossible", include_raw=True)
    res = p.run(req)

    assert res.status == QueryStatus.no_data
    assert res.error_message == "No matching data in mock dataset"
