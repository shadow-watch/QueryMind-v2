from typing import Protocol

from querymind.adapters.contracts import AdapterResult
from querymind.domain.contracts import QueryType


class AnalyticsAdapter(Protocol):
    def run(self, query: str, query_type: QueryType, max_results: int) -> AdapterResult:
        ...