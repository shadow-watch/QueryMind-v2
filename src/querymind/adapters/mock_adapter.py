from querymind.adapters.contracts import AdapterResult
from querymind.domain.contracts import QueryType


class MockAnalyticsAdapter:
    def run(self, query: str, query_type: QueryType, max_results: int) -> AdapterResult:
        q = query.lower()

        if "revenue" in q or "top" in q:
            return AdapterResult(
                esql=(
                    "FROM orders_index | STATS revenue = SUM(total_price) "
                    "BY product_id | SORT revenue DESC | LIMIT 10"
                ),
                rows=[
                    {"product_id": "P001", "revenue": 95000.50},
                    {"product_id": "P002", "revenue": 82300.00},
                    {"product_id": "P003", "revenue": 64150.20},
                ][:max_results],
                insight_title="Top Products by Revenue",
                insight_text="Top products are contributing most of total revenue.",
                confidence=95,
            )

        if "average order value" in q or "aov" in q:
            return AdapterResult(
                esql=(
                    "FROM orders_index | STATS aov = AVG(total_price) "
                    "BY country | SORT aov DESC | LIMIT 10"
                ),
                rows=[
                    {"country": "DE", "aov": 124.4},
                    {"country": "FR", "aov": 118.9},
                    {"country": "IN", "aov": 94.2},
                ][:max_results],
                insight_title="Average Order Value by Country",
                insight_text="AOV is highest in DE in this mock sample.",
                confidence=92,
            )

        if "declining" in q or (query_type == QueryType.trend and "review" in q):
            return AdapterResult(
                esql=(
                    "FROM reviews_index | STATS avg_rating = AVG(rating) "
                    "BY product_id, created_date | SORT created_date ASC | LIMIT 10"
                ),
                rows=[
                    {"product_id": "P001", "created_date": "2024-01-10", "avg_rating": 4.2},
                    {"product_id": "P001", "created_date": "2024-02-15", "avg_rating": 3.0},
                    {"product_id": "P001", "created_date": "2024-03-31", "avg_rating": 2.1},
                ][:max_results],
                insight_title="Declining Review Trend",
                insight_text="Ratings for P001 decline across the sampled dates.",
                confidence=90,
            )

        if "less than 3 star" in q or "rating" in q:
            return AdapterResult(
                esql="FROM reviews_index | WHERE rating < 3 | LIMIT 10",
                rows=[
                    {"product_id": "P004", "country": "DE", "rating": 2.4},
                    {"product_id": "P005", "country": "IT", "rating": 2.7},
                ][:max_results],
                insight_title="Low-Rating Products",
                insight_text="These products are below 3 stars in the sample.",
                confidence=88,
            )

        if "most reviewed" in q:
            return AdapterResult(
                esql=(
                    "FROM reviews_index | STATS review_count = COUNT(review_id) "
                    "BY product_id | SORT review_count DESC | LIMIT 10"
                ),
                rows=[
                    {"product_id": "P001", "review_count": 140},
                    {"product_id": "P002", "review_count": 115},
                ][:max_results],
                insight_title="Most Reviewed Products",
                insight_text="P001 and P002 have the highest review volume in sample data.",
                confidence=89,
            )

        return AdapterResult(
            esql="FROM products_index | LIMIT 10",
            rows=[],
            insight_title="No Data",
            insight_text="No matching pattern in deterministic mock rules.",
            confidence=60,
        )