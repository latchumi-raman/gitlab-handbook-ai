"""
Integration tests for the /feedback endpoint.

Tests cover:
- Valid feedback saved successfully
- Invalid rating (not 1 or -1) returns 400
- Missing required fields returns 422
- Optional comment field works
"""

import pytest


class TestFeedbackEndpoint:

    @pytest.mark.integration
    def test_positive_feedback_returns_200(self, client, feedback_payload):
        resp = client.post("/api/v1/feedback", json=feedback_payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_feedback_response_success_true(self, client, feedback_payload):
        resp = client.post("/api/v1/feedback", json=feedback_payload)
        data = resp.json()
        assert data.get("success") is True

    @pytest.mark.integration
    def test_feedback_response_has_message(self, client, feedback_payload):
        resp = client.post("/api/v1/feedback", json=feedback_payload)
        assert "message" in resp.json()

    @pytest.mark.integration
    def test_negative_feedback_returns_200(self, client, feedback_payload):
        payload = {**feedback_payload, "rating": -1, "comment": "Not accurate"}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_feedback_without_comment_returns_200(self, client, feedback_payload):
        payload = {k: v for k, v in feedback_payload.items() if k != "comment"}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_invalid_rating_zero_returns_400(self, client, feedback_payload):
        payload = {**feedback_payload, "rating": 0}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 400

    @pytest.mark.integration
    def test_invalid_rating_two_returns_400(self, client, feedback_payload):
        payload = {**feedback_payload, "rating": 2}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 400

    @pytest.mark.integration
    def test_missing_session_id_returns_422(self, client, feedback_payload):
        payload = {k: v for k, v in feedback_payload.items() if k != "session_id"}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 422

    @pytest.mark.integration
    def test_missing_rating_returns_422(self, client, feedback_payload):
        payload = {k: v for k, v in feedback_payload.items() if k != "rating"}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 422

    @pytest.mark.integration
    def test_empty_comment_accepted(self, client, feedback_payload):
        payload = {**feedback_payload, "comment": ""}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_long_comment_accepted(self, client, feedback_payload):
        payload = {**feedback_payload, "comment": "A" * 999}
        resp    = client.post("/api/v1/feedback", json=payload)
        assert resp.status_code == 200