"""
Integration tests for analytics endpoints.

/analytics/summary     → aggregated metrics dict
/analytics/confidence  → list of bucketed confidence scores
/analytics/feedback    → recent feedback records
"""

import pytest


class TestAnalyticsSummary:

    @pytest.mark.integration
    def test_summary_returns_200(self, client):
        resp = client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_summary_has_status_ok(self, client):
        resp = client.get("/api/v1/analytics/summary")
        assert resp.json().get("status") == "ok"

    @pytest.mark.integration
    def test_summary_has_data_key(self, client):
        resp = client.get("/api/v1/analytics/summary")
        assert "data" in resp.json()

    @pytest.mark.integration
    def test_summary_data_has_required_keys(self, client):
        resp = client.get("/api/v1/analytics/summary")
        data = resp.json()["data"]
        required = {
            "total_queries", "queries_last_7_days",
            "avg_confidence", "guardrail_rate",
            "positive_feedback", "negative_feedback",
            "chunks_indexed",
        }
        for key in required:
            assert key in data, f"Missing key in analytics summary: {key}"

    @pytest.mark.integration
    def test_summary_numeric_fields_are_numbers(self, client):
        resp = client.get("/api/v1/analytics/summary")
        data = resp.json()["data"]
        for field in ["total_queries", "avg_confidence", "guardrail_rate"]:
            assert isinstance(data[field], (int, float)), \
                f"{field} should be numeric, got {type(data[field])}"

    @pytest.mark.integration
    def test_summary_queries_per_day_is_list(self, client):
        resp = client.get("/api/v1/analytics/summary")
        data = resp.json()["data"]
        assert isinstance(data.get("queries_per_day", []), list)

    @pytest.mark.integration
    def test_summary_top_queries_is_list(self, client):
        resp = client.get("/api/v1/analytics/summary")
        data = resp.json()["data"]
        assert isinstance(data.get("top_queries", []), list)


class TestAnalyticsConfidence:

    @pytest.mark.integration
    def test_confidence_returns_200(self, client):
        resp = client.get("/api/v1/analytics/confidence")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_confidence_has_data_list(self, client):
        resp = client.get("/api/v1/analytics/confidence")
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    @pytest.mark.integration
    def test_confidence_data_has_range_and_count(self, client):
        resp    = client.get("/api/v1/analytics/confidence")
        buckets = resp.json()["data"]
        for bucket in buckets:
            assert "range" in bucket
            assert "count" in bucket
            assert isinstance(bucket["count"], int)
            assert bucket["count"] >= 0

    @pytest.mark.integration
    def test_confidence_returns_five_buckets(self, client):
        """Should always return exactly 5 buckets regardless of data."""
        resp    = client.get("/api/v1/analytics/confidence")
        buckets = resp.json()["data"]
        assert len(buckets) == 5


class TestAnalyticsFeedback:

    @pytest.mark.integration
    def test_feedback_returns_200(self, client):
        resp = client.get("/api/v1/analytics/feedback")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_feedback_has_data_key(self, client):
        resp = client.get("/api/v1/analytics/feedback")
        assert "data" in resp.json()

    @pytest.mark.integration
    def test_feedback_data_is_list(self, client):
        resp = client.get("/api/v1/analytics/feedback")
        assert isinstance(resp.json()["data"], list)

    @pytest.mark.integration
    def test_feedback_limit_param_accepted(self, client):
        resp = client.get("/api/v1/analytics/feedback?limit=5")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_feedback_limit_max_100(self, client):
        """Limit is capped at 100 — requesting 200 should still return 200."""
        resp = client.get("/api/v1/analytics/feedback?limit=200")
        assert resp.status_code == 200