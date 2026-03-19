"""
Unit tests for the RAG confidence score calculation.

The scoring formula:
  - Single chunk: score = chunk.similarity
  - Multiple chunks: weighted = 0.4 * top + 0.6 * avg(rest)
  - Result is clamped to [0.0, 1.0] and rounded to 3dp
"""

import pytest
from api.models import SourceChunk
from api.services.rag import calculate_confidence


def make_chunk(similarity: float, idx: int = 0) -> SourceChunk:
    return SourceChunk(
        id=idx,
        content="test content",
        source_url="https://handbook.gitlab.com/test/",
        page_type="handbook",
        page_title="Test",
        section_title="Test Section",
        similarity=similarity,
    )


class TestCalculateConfidence:

    @pytest.mark.unit
    def test_empty_list_returns_zero(self):
        assert calculate_confidence([]) == 0.0

    @pytest.mark.unit
    def test_single_chunk_returns_its_similarity(self):
        chunk  = make_chunk(0.85)
        result = calculate_confidence([chunk])
        assert result == 0.85

    @pytest.mark.unit
    def test_two_chunks_weighted_formula(self):
        """Result = 0.4 * top + 0.6 * avg(rest)"""
        chunks = [make_chunk(0.90, 0), make_chunk(0.70, 1)]
        result = calculate_confidence(chunks)
        expected = round(0.4 * 0.90 + 0.6 * 0.70, 3)
        assert result == expected

    @pytest.mark.unit
    def test_five_chunks_weighted_formula(self):
        sims   = [0.92, 0.85, 0.78, 0.70, 0.60]
        chunks = [make_chunk(s, i) for i, s in enumerate(sims)]
        result = calculate_confidence(chunks)
        expected = round(0.4 * 0.92 + 0.6 * (sum(sims[1:]) / len(sims[1:])), 3)
        assert result == expected

    @pytest.mark.unit
    def test_result_clamped_to_one(self):
        """Should never exceed 1.0 even with perfect scores."""
        chunks = [make_chunk(1.0), make_chunk(1.0), make_chunk(1.0)]
        result = calculate_confidence(chunks)
        assert result <= 1.0

    @pytest.mark.unit
    def test_result_rounded_to_3dp(self):
        chunks = [make_chunk(0.876543), make_chunk(0.765432)]
        result = calculate_confidence(chunks)
        assert result == round(result, 3)

    @pytest.mark.unit
    def test_low_similarity_stays_low(self):
        chunks = [make_chunk(0.35), make_chunk(0.30), make_chunk(0.25)]
        result = calculate_confidence(chunks)
        assert result < 0.55   # should correctly reflect low confidence

    @pytest.mark.unit
    def test_high_similarity_stays_high(self):
        chunks = [make_chunk(0.95), make_chunk(0.92), make_chunk(0.90)]
        result = calculate_confidence(chunks)
        assert result >= 0.80

    @pytest.mark.unit
    def test_returns_float(self):
        chunks = [make_chunk(0.80)]
        result = calculate_confidence(chunks)
        assert isinstance(result, float)