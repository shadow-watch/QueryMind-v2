from querymind.adapters.interfaces import AnalyticsAdapter
from querymind.adapters.live_adapter import LiveAnalyticsAdapter
from querymind.adapters.mock_adapter import MockAnalyticsAdapter
from querymind.core.settings import settings
from querymind.domain.contracts import AuditLog, QueryRequest, QueryResponse, QueryStatus
from querymind.services.classifier import QueryClassifier
from querymind.services.fact_check import FactChecker


class PipelineService:
    def __init__(self, adapter: AnalyticsAdapter | None = None) -> None:
        self.classifier = QueryClassifier()
        self.fact_checker = FactChecker()
        self.adapter = adapter or self._build_default_adapter()

    def _build_default_adapter(self) -> AnalyticsAdapter:
        if settings.mock_mode:
            return MockAnalyticsAdapter()
        return LiveAnalyticsAdapter()

    def run(self, request: QueryRequest) -> QueryResponse:
        q = request.query.strip()
        query_type = self.classifier.classify(q)

        try:
            result = self.adapter.run(q, query_type, request.max_results)
        except Exception as exc:
            return QueryResponse(
                query=q,
                status=QueryStatus.error,
                query_type=query_type,
                raw_results=[],
                fact_check_passed=None,
                fact_check_warnings=[],
                audit_log=AuditLog(
                    esql_generated="",
                    retries=0,
                    fallback_applied=False,
                    fallback_distance=0,
                    confidence=0,
                ),
                error_message=str(exc),
            )

        fact_passed, fact_warnings = self.fact_checker.validate(result.insight_title, result.rows)

        return QueryResponse(
            query=q,
            status=QueryStatus.success if result.rows else QueryStatus.no_data,
            query_type=query_type,
            insight_title=result.insight_title,
            insight_text=result.insight_text,
            raw_results=result.rows if request.include_raw else [],
            fact_check_passed=fact_passed,
            fact_check_warnings=fact_warnings,
            audit_log=AuditLog(
                esql_generated=result.esql,
                retries=0,
                fallback_applied=False,
                fallback_distance=0,
                confidence=result.confidence,
            ),
            error_message=None if result.rows else "No matching data in mock dataset",
        )
