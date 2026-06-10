from querymind.domain.contracts import QueryType
from querymind.services.classifier import QueryClassifier


def test_classify_aggregation() -> None:
    c = QueryClassifier()
    assert c.classify("Average order value by country") == QueryType.aggregation


def test_classify_trend() -> None:
    c = QueryClassifier()
    assert c.classify("Which products have declining reviews over time?") == QueryType.trend


def test_classify_comparison() -> None:
    c = QueryClassifier()
    assert c.classify("Compare revenue vs rating by country") == QueryType.comparison


def test_classify_unknown_for_short_query() -> None:
    c = QueryClassifier()
    assert c.classify("hi there") == QueryType.unknown
