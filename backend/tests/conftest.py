"""
Shared pytest fixtures for all tests.

Key design decisions:
- All Supabase calls are mocked → tests run offline, no DB needed
- All Gemini API calls are mocked → tests run without API key
- The FastAPI test client uses the real app with mocked dependencies
- Each fixture is documented with what it provides and why
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

# ── Minimal env setup so imports don't crash ─────────────────────────────────
import os
os.environ.setdefault("GEMINI_API_KEY",       "test-gemini-key-fake")
os.environ.setdefault("SUPABASE_URL",          "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY",     "test-anon-key-fake")
os.environ.setdefault("SUPABASE_SERVICE_KEY",  "test-service-key-fake")
os.environ.setdefault("ALLOWED_ORIGINS",       "http://localhost:5173")


# ── Reusable mock data ─────────────────────────────────────────────────────────

MOCK_EMBEDDING = [0.01] * 768   # 768-dim zero vector for text-embedding-004

MOCK_CHUNKS = [
    {
        "id":            1,
        "content":       "GitLab's CREDIT values stand for Collaboration, Results, "
                         "Efficiency, Diversity, Iteration, and Transparency.",
        "source_url":    "https://handbook.gitlab.com/handbook/values/",
        "page_type":     "handbook",
        "page_title":    "GitLab Values",
        "section_title": "CREDIT Values",
        "similarity":    0.92,
    },
    {
        "id":            2,
        "content":       "Transparency is one of GitLab's most unique values. "
                         "GitLab publishes its strategy, handbook, and roadmap publicly.",
        "source_url":    "https://handbook.gitlab.com/handbook/values/#transparency",
        "page_type":     "handbook",
        "page_title":    "GitLab Values",
        "section_title": "Transparency",
        "similarity":    0.87,
    },
    {
        "id":            3,
        "content":       "GitLab is an all-remote company. All team members work remotely "
                         "and communicate asynchronously.",
        "source_url":    "https://handbook.gitlab.com/handbook/company/culture/all-remote/",
        "page_type":     "handbook",
        "page_title":    "All-Remote",
        "section_title": "Remote Work",
        "similarity":    0.78,
    },
]

MOCK_GEMINI_ANSWER = (
    "GitLab's core values are represented by the acronym **CREDIT**:\n\n"
    "- **Collaboration** — work together across teams\n"
    "- **Results** — focus on outcomes, not activity\n"
    "- **Efficiency** — make the most of everyone's time\n"
    "- **Diversity** — include all perspectives\n"
    "- **Iteration** — ship small and improve continuously\n"
    "- **Transparency** — default to public and open\n\n"
    "These values shape everything from how GitLab runs meetings to "
    "how it makes product decisions."
)

MOCK_FOLLOW_UPS = [
    "How does GitLab apply the iteration value in practice?",
    "What does transparency mean concretely at GitLab?",
    "How are CREDIT values measured or evaluated?",
]


# ── Supabase mock ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_supabase():
    """
    Returns a fully mocked Supabase client.
    Covers: rpc (vector search), table insert/select, execute chain.
    """
    mock_client = MagicMock()

    # Vector search via RPC
    mock_rpc_result       = MagicMock()
    mock_rpc_result.data  = MOCK_CHUNKS
    mock_client.rpc.return_value.execute.return_value = mock_rpc_result

    # Table operations — chainable: .table().select().eq().limit().execute()
    mock_table_result        = MagicMock()
    mock_table_result.data   = []
    mock_table_result.count  = 42
    mock_chain = MagicMock()
    mock_chain.execute.return_value   = mock_table_result
    mock_chain.limit.return_value     = mock_chain
    mock_chain.eq.return_value        = mock_chain
    mock_chain.gte.return_value       = mock_chain
    mock_chain.order.return_value     = mock_chain
    mock_chain.select.return_value    = mock_chain
    mock_chain.insert.return_value    = mock_chain
    mock_chain.delete.return_value    = mock_chain
    mock_chain.filter.return_value    = mock_chain
    mock_client.table.return_value    = mock_chain

    return mock_client


# ── Gemini mock ────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_gemini_embed():
    """Mocks genai.embed_content to return a fixed 768-dim vector."""
    with patch("google.generativeai.embed_content") as mock:
        mock.return_value = {"embedding": MOCK_EMBEDDING}
        yield mock


@pytest.fixture
def mock_gemini_generate():
    """
    Mocks genai.GenerativeModel().generate_content for both
    streaming (iter of chunks) and non-streaming (single response) use.
    """
    with patch("google.generativeai.GenerativeModel") as MockModel:
        instance = MockModel.return_value

        # Non-streaming response
        mock_response      = MagicMock()
        mock_response.text = MOCK_GEMINI_ANSWER

        # Streaming response — iterate over word-by-word chunks
        words = MOCK_GEMINI_ANSWER.split()
        stream_chunks = []
        for word in words:
            chunk      = MagicMock()
            chunk.text = word + " "
            stream_chunks.append(chunk)

        instance.generate_content.return_value = mock_response
        # When called with stream=True, return an iterable
        instance.generate_content.side_effect = lambda msgs, stream=False, **kw: (
            iter(stream_chunks) if stream else mock_response
        )
        yield MockModel


# ── FastAPI test app ───────────────────────────────────────────────────────────

@pytest.fixture
def app(mock_supabase):
    """
    Creates the FastAPI app with mocked external dependencies.
    The Supabase client is injected via app.state.db.
    Gemini is configured but calls are expected to be mocked in each test.
    """
    from api.main import create_app

    with patch("database.supabase_client.create_client", return_value=mock_supabase):
        with patch("google.generativeai.configure"):
            test_app = create_app()
            # Inject mock DB directly so routes get it via request.app.state.db
            test_app.state.db = mock_supabase
            yield test_app


@pytest.fixture
def client(app):
    """Synchronous TestClient — use for simple endpoint tests."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
async def async_client(app):
    """Async HTTPX client — use for streaming endpoint tests."""
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c


# ── Common request payloads ────────────────────────────────────────────────────

@pytest.fixture
def chat_payload():
    return {
        "query":            "What are GitLab's CREDIT values?",
        "session_id":       "test-session-abc123",
        "history":          [],
        "page_type_filter": "both",
        "match_count":      5,
    }


@pytest.fixture
def off_topic_payload():
    return {
        "query":      "What is the weather in Bangalore today?",
        "session_id": "test-session-off-topic",
        "history":    [],
    }


@pytest.fixture
def feedback_payload():
    return {
        "session_id": "test-session-abc123",
        "query":      "What are GitLab CREDIT values?",
        "response":   "GitLab values are CREDIT: Collaboration, Results...",
        "rating":     1,
        "comment":    "Very helpful, thanks!",
    }