from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryStatus(str, Enum):
    success = "success"
    no_data = "no_data"
    error = "error"
    timeout = "timeout"


class QueryType(str, Enum):
    aggregation = "aggregation"
    trend = "trend"
    comparison = "comparison"
    lookup = "lookup"
    unknown = "unknown"


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    include_raw: bool = False
    max_results: int = Field(default=10, ge=1, le=100)


class AuditLog(BaseModel):
    esql_generated: str = ""
    retries: int = 0
    fallback_applied: bool = False
    fallback_distance: int = 0
    confidence: int = 0


class QueryResponse(BaseModel):
    query: str
    status: QueryStatus
    query_type: QueryType = QueryType.unknown

    insight_title: str | None = None
    insight_text: str | None = None

    raw_results: list[dict[str, Any]] = []
    fact_check_passed: bool | None = None
    fact_check_warnings: list[str] = []

    audit_log: AuditLog | None = None
    error_message: str | None = None