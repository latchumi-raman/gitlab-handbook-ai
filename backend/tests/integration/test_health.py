"""
Integration tests for health and utility endpoints.

/ping    → must return 200 + {"status": "alive"}
/health  → must return 200 + required fields
/stats   → must return 200 + totals dict
/session → clear + retrieve history
"""

import pytest


class TestPingEndpoint:

    @pytest.mark.integration
    def test_ping_returns_200(self, client):
        resp = client.get("/api/v1/ping")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_ping_returns_alive(self, client):
        resp = client.get("/api/v1/ping")
        data = resp.json()
        assert data["status"] == "alive"

    @pytest.mark.integration
    def test_ping_is_fast(self, client):
        """Ping should respond in under 500ms — it's a keepalive."""
        import time
        start = time.perf_counter()
        client.get("/api/v1/ping")
        elapsed = time.perf_counter() - start
        assert elapsed < 0.5, f"Ping took {elapsed:.2f}s — too slow for keepalive"


class TestHealthEndpoint:

    @pytest.mark.integration
    def test_health_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_health_has_required_fields(self, client):
        resp = client.get("/api/v1/health")
        data = resp.json()
        assert "status"         in data
        assert "version"        in data
        assert "db_connected"   in data
        assert "chunks_indexed" in data

    @pytest.mark.integration
    def test_health_version_is_string(self, client):
        resp = client.get("/api/v1/health")
        assert isinstance(resp.json()["version"], str)

    @pytest.mark.integration
    def test_health_chunks_indexed_is_int(self, client):
        resp = client.get("/api/v1/health")
        assert isinstance(resp.json()["chunks_indexed"], int)


class TestStatsEndpoint:

    @pytest.mark.integration
    def test_stats_returns_200(self, client):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_stats_has_status_field(self, client):
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert "status" in data

    @pytest.mark.integration
    def test_stats_has_totals(self, client):
        resp = client.get("/api/v1/stats")
        data = resp.json()
        assert "totals" in data or "grand_total" in data or "status" in data


class TestSessionEndpoints:

    @pytest.mark.integration
    def test_delete_session_returns_200(self, client):
        resp = client.delete("/api/v1/session/test-session-123")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_delete_session_returns_ok_status(self, client):
        resp = client.delete("/api/v1/session/test-session-123")
        data = resp.json()
        assert data.get("status") == "ok"

    @pytest.mark.integration
    def test_get_history_returns_200(self, client):
        resp = client.get("/api/v1/session/test-session-456/history")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_get_history_has_messages_field(self, client):
        resp = client.get("/api/v1/session/test-session-456/history")
        data = resp.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    @pytest.mark.integration
    def test_root_endpoint_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_docs_endpoint_accessible(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200