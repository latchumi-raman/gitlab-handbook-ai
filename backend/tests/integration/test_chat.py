"""
Integration tests for the /chat and /chat/stream endpoints.

All Gemini + Supabase calls are mocked via conftest fixtures.
Tests verify: status codes, response shapes, guardrail behaviour,
streaming SSE format, session history persistence.
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from tests.conftest import MOCK_EMBEDDING, MOCK_CHUNKS, MOCK_GEMINI_ANSWER, MOCK_FOLLOW_UPS


# ── Helper ────────────────────────────────────────────────────────────────────

def mock_embed_and_generate(mock_supabase):
    """
    Context manager combination: patches both embed_content and GenerativeModel
    so the full /chat pipeline runs without touching external APIs.
    """
    rpc_result      = MagicMock()
    rpc_result.data = MOCK_CHUNKS
    mock_supabase.rpc.return_value.execute.return_value = rpc_result

    mock_response      = MagicMock()
    mock_response.text = MOCK_GEMINI_ANSWER

    words = MOCK_GEMINI_ANSWER.split()
    stream_chunks = []
    for w in words:
        c      = MagicMock()
        c.text = w + " "
        stream_chunks.append(c)

    return mock_response, stream_chunks


# ── Non-streaming /chat ───────────────────────────────────────────────────────

class TestChatSync:

    @pytest.mark.integration
    def test_chat_returns_200(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_chat_response_has_required_fields(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        data = resp.json()
        assert "answer"     in data
        assert "sources"    in data
        assert "confidence" in data
        assert "follow_ups" in data
        assert "session_id" in data

    @pytest.mark.integration
    def test_chat_answer_is_string(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        assert isinstance(resp.json()["answer"], str)
        assert len(resp.json()["answer"]) > 0

    @pytest.mark.integration
    def test_chat_sources_is_list(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        assert isinstance(resp.json()["sources"], list)

    @pytest.mark.integration
    def test_chat_confidence_between_0_and_1(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        conf = resp.json()["confidence"]
        assert 0.0 <= conf <= 1.0

    @pytest.mark.integration
    def test_chat_follow_ups_is_list_of_3(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        fu_response      = MagicMock()
        fu_response.text = json.dumps(MOCK_FOLLOW_UPS)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else (
                    fu_response if "follow" in str(msgs).lower()
                    else mock_response
                )
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        follow_ups = resp.json()["follow_ups"]
        assert isinstance(follow_ups, list)
        assert len(follow_ups) == 3

    @pytest.mark.integration
    def test_chat_session_id_echoed(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat", json=chat_payload)
        assert resp.json()["session_id"] == chat_payload["session_id"]

    @pytest.mark.integration
    def test_missing_query_returns_422(self, client):
        resp = client.post("/api/v1/chat", json={"session_id": "s1"})
        assert resp.status_code == 422

    @pytest.mark.integration
    def test_missing_session_id_returns_422(self, client):
        resp = client.post("/api/v1/chat", json={"query": "What are values?"})
        assert resp.status_code == 422

    @pytest.mark.integration
    def test_empty_query_returns_422(self, client):
        resp = client.post("/api/v1/chat", json={"query": "", "session_id": "s1"})
        assert resp.status_code == 422


# ── Guardrail behaviour ───────────────────────────────────────────────────────

class TestChatGuardrails:

    @pytest.mark.integration
    def test_off_topic_returns_200(self, client, off_topic_payload):
        resp = client.post("/api/v1/chat", json=off_topic_payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_off_topic_guardrail_triggered_flag(self, client, off_topic_payload):
        resp = client.post("/api/v1/chat", json=off_topic_payload)
        data = resp.json()
        assert data.get("guardrail_triggered") is True

    @pytest.mark.integration
    def test_off_topic_confidence_is_zero(self, client, off_topic_payload):
        resp = client.post("/api/v1/chat", json=off_topic_payload)
        assert resp.json()["confidence"] == 0.0

    @pytest.mark.integration
    def test_off_topic_sources_empty(self, client, off_topic_payload):
        resp = client.post("/api/v1/chat", json=off_topic_payload)
        assert resp.json()["sources"] == []

    @pytest.mark.integration
    def test_off_topic_answer_mentions_handbook(self, client, off_topic_payload):
        resp = client.post("/api/v1/chat", json=off_topic_payload)
        answer = resp.json()["answer"].lower()
        assert "handbook" in answer or "gitlab" in answer


# ── Streaming /chat/stream ────────────────────────────────────────────────────

class TestChatStream:

    @pytest.mark.integration
    def test_stream_returns_200(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat/stream", json=chat_payload)
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_stream_content_type_is_event_stream(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat/stream", json=chat_payload)
        assert "text/event-stream" in resp.headers.get("content-type", "")

    @pytest.mark.integration
    def test_stream_contains_done_event(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat/stream", json=chat_payload)
        # Collect all SSE events
        events = _parse_sse(resp.text)
        event_types = [e.get("type") for e in events]
        assert "done" in event_types

    @pytest.mark.integration
    def test_stream_contains_token_events(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat/stream", json=chat_payload)
        events     = _parse_sse(resp.text)
        token_evts = [e for e in events if e.get("type") == "token"]
        assert len(token_evts) > 0

    @pytest.mark.integration
    def test_stream_contains_sources_event(self, client, chat_payload, mock_supabase):
        mock_response, stream_chunks = mock_embed_and_generate(mock_supabase)
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}), \
             patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.side_effect = lambda msgs, stream=False, **kw: (
                iter(stream_chunks) if stream else mock_response
            )
            resp = client.post("/api/v1/chat/stream", json=chat_payload)
        events     = _parse_sse(resp.text)
        src_events = [e for e in events if e.get("type") == "sources"]
        assert len(src_events) >= 1

    @pytest.mark.integration
    def test_stream_guardrail_event_for_off_topic(self, client, off_topic_payload):
        resp   = client.post("/api/v1/chat/stream", json=off_topic_payload)
        events = _parse_sse(resp.text)
        guardrail_evts = [e for e in events if e.get("type") == "guardrail"]
        assert len(guardrail_evts) >= 1
        assert guardrail_evts[0]["triggered"] is True


# ── SSE parse helper ──────────────────────────────────────────────────────────

def _parse_sse(raw_text: str) -> list[dict]:
    """Parse raw SSE response text into a list of event dicts."""
    events = []
    for line in raw_text.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events