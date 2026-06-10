from querymind.domain.contracts import QueryType


class QueryClassifier:
    TREND_KEYWORDS = {
        "trend",
        "declining",
        "increasing",
        "over time",
        "monthly",
        "weekly",
        "daily",
        "quarterly",
        "yearly",
    }
    AGG_KEYWORDS = {
        "sum",
        "average",
        "avg",
        "mean",
        "max",
        "min",
        "total",
        "count",
        "top",
        "bottom",
        "revenue",
        "aov",
    }
    COMP_KEYWORDS = {"compare", "vs", "versus", "difference", "split by", "comparison"}
    LOOKUP_KEYWORDS = {"what is", "find", "show", "get", "list", "details"}

    def classify(self, query: str) -> QueryType:
        q = query.lower().strip()
        if len(q.split()) < 3:
            return QueryType.unknown

        if any(k in q for k in self.TREND_KEYWORDS):
            return QueryType.trend
        if any(k in q for k in self.COMP_KEYWORDS):
            return QueryType.comparison
        if any(k in q for k in self.AGG_KEYWORDS):
            return QueryType.aggregation
        if any(k in q for k in self.LOOKUP_KEYWORDS):
            return QueryType.lookup
        return QueryType.unknown