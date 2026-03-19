"""
Unit tests for RAG utility functions:
- embed_query: calls Gemini embed_content correctly
- _build_context_block: formats chunks into a context string
- enhance_query: rewrites short queries (mocked Gemini)
- generate_follow_ups: returns 3 suggestions (mocked Gemini)
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from api.models import SourceChunk
from api.services.rag import (
    embed_query,
    _build_context_block,
    calculate_confidence,
)

MOCK_EMBEDDING = [0.01] * 768

SAMPLE_CHUNKS = [
    SourceChunk(
        id=1,
        content="GitLab values are CREDIT: Collaboration, Results, Efficiency, Diversity, Iteration, Transparency.",
        source_url="https://handbook.gitlab.com/values/",
        page_type="handbook",
        page_title="GitLab Values",
        section_title="CREDIT",
        similarity=0.92,
    ),
    SourceChunk(
        id=2,
        content="GitLab is an all-remote company. All team members work remotely.",
        source_url="https://handbook.gitlab.com/remote/",
        page_type="handbook",
        page_title="All-Remote",
        section_title="Remote Work",
        similarity=0.85,
    ),
]


class TestEmbedQuery:

    @pytest.mark.unit
    def test_returns_list_of_floats(self):
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}):
            result = embed_query("What are GitLab values?")
        assert isinstance(result, list)
        assert len(result) == 768
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.unit
    def test_uses_retrieval_query_task_type(self):
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}) as mock:
            embed_query("What are GitLab values?")
            call_kwargs = mock.call_args[1]
            assert call_kwargs.get("task_type") == "retrieval_query"

    @pytest.mark.unit
    def test_returns_none_on_api_error(self):
        with patch("google.generativeai.embed_content", side_effect=Exception("API error")):
            result = embed_query("What are GitLab values?")
        assert result is None

    @pytest.mark.unit
    def test_truncates_very_long_query(self):
        long_query = "a " * 5000   # ~10,000 chars
        with patch("google.generativeai.embed_content", return_value={"embedding": MOCK_EMBEDDING}) as mock:
            embed_query(long_query)
            call_kwargs  = mock.call_args[1]
            sent_content = call_kwargs.get("content", "")
            assert len(sent_content) <= 4_001   # 4,000 chars + tiny margin


class TestBuildContextBlock:

    @pytest.mark.unit
    def test_returns_string(self):
        context = _build_context_block(SAMPLE_CHUNKS)
        assert isinstance(context, str)

    @pytest.mark.unit
    def test_empty_chunks_returns_empty_string(self):
        context = _build_context_block([])
        assert context == ""

    @pytest.mark.unit
    def test_contains_source_urls(self):
        context = _build_context_block(SAMPLE_CHUNKS)
        for chunk in SAMPLE_CHUNKS:
            assert chunk.source_url in context

    @pytest.mark.unit
    def test_contains_chunk_content(self):
        context = _build_context_block(SAMPLE_CHUNKS)
        for chunk in SAMPLE_CHUNKS:
            # At least the start of each chunk's content should appear
            assert chunk.content[:30] in context

    @pytest.mark.unit
    def test_source_labels_numbered(self):
        context = _build_context_block(SAMPLE_CHUNKS)
        assert "[SOURCE 1]" in context
        assert "[SOURCE 2]" in context

    @pytest.mark.unit
    def test_respects_max_context_chars(self):
        from api.services.rag import MAX_CONTEXT_CHARS
        # Create a chunk with very large content
        big_chunk = SourceChunk(
            id=99,
            content="x " * 10_000,
            source_url="https://handbook.gitlab.com/big/",
            page_type="handbook",
            page_title="Big Page",
            section_title="Big Section",
            similarity=0.90,
        )
        context = _build_context_block([big_chunk])
        assert len(context) <= MAX_CONTEXT_CHARS + 200   # small buffer for label


class TestEnhanceQuery:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_short_query_gets_enhanced(self):
        from api.services.rag import enhance_query
        enhanced_text = "What are GitLab CREDIT values and how do they guide work?"
        mock_response      = MagicMock()
        mock_response.text = enhanced_text

        with patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response
            result, was_enhanced = await enhance_query("values")

        # Short query (1 word) should be enhanced
        assert was_enhanced is True
        assert result == enhanced_text

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_long_query_not_enhanced(self):
        from api.services.rag import enhance_query
        long_query = "How does GitLab handle the performance review process for individual contributors?"
        result, was_enhanced = await enhance_query(long_query)
        # >8 words → skip enhancement entirely (no Gemini call)
        assert was_enhanced is False
        assert result == long_query

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_enhancement_falls_back_on_error(self):
        from api.services.rag import enhance_query
        with patch("google.generativeai.GenerativeModel", side_effect=Exception("API error")):
            result, was_enhanced = await enhance_query("hiring")
        assert was_enhanced is False
        assert result == "hiring"


class TestGenerateFollowUps:

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_three_suggestions(self):
        from api.services.rag import generate_follow_ups
        suggestions = ["Q1?", "Q2?", "Q3?"]
        mock_response      = MagicMock()
        mock_response.text = json.dumps(suggestions)

        with patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response
            result = await generate_follow_ups("What are GitLab values?", "They are CREDIT...")

        assert len(result) == 3
        assert all(isinstance(s, str) for s in result)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_defaults_on_json_error(self):
        from api.services.rag import generate_follow_ups
        mock_response      = MagicMock()
        mock_response.text = "not valid json at all!!!"

        with patch("google.generativeai.GenerativeModel") as MockModel:
            MockModel.return_value.generate_content.return_value = mock_response
            result = await generate_follow_ups("values", "answer")

        assert len(result) == 3
        assert all(isinstance(s, str) for s in result)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_defaults_on_api_error(self):
        from api.services.rag import generate_follow_ups
        with patch("google.generativeai.GenerativeModel", side_effect=Exception("API down")):
            result = await generate_follow_ups("values", "answer")
        assert len(result) == 3