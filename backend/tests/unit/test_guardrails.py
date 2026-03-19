"""
Unit tests for the guardrails service.

Tests cover:
- Off-topic queries are blocked
- GitLab-related queries pass through
- Edge cases: empty queries, very short queries, ambiguous queries
- Confidence-based low-confidence note logic
"""

import pytest
from api.services.guardrails import (
    check_guardrails,
    check_confidence,
    get_off_topic_response,
    OFF_TOPIC_RESPONSE,
    LOW_CONFIDENCE_ADDENDUM,
)


# ── check_guardrails ──────────────────────────────────────────────────────────

class TestCheckGuardrails:

    @pytest.mark.unit
    def test_gitlab_values_passes(self):
        blocked, reason = check_guardrails("What are GitLab's CREDIT values?")
        assert blocked is False
        assert reason is None

    @pytest.mark.unit
    def test_hiring_process_passes(self):
        blocked, reason = check_guardrails("How does GitLab's hiring process work?")
        assert blocked is False

    @pytest.mark.unit
    def test_remote_work_passes(self):
        blocked, reason = check_guardrails("Tell me about GitLab all-remote culture")
        assert blocked is False

    @pytest.mark.unit
    def test_okrs_passes(self):
        blocked, reason = check_guardrails("How do GitLab OKRs work?")
        assert blocked is False

    @pytest.mark.unit
    def test_weather_is_blocked(self):
        blocked, reason = check_guardrails("What is the weather in Bangalore?")
        assert blocked is True

    @pytest.mark.unit
    def test_sports_is_blocked(self):
        blocked, reason = check_guardrails("Who won the cricket match yesterday?")
        assert blocked is True

    @pytest.mark.unit
    def test_recipe_is_blocked(self):
        blocked, reason = check_guardrails("Write me a recipe for chocolate cake")
        assert blocked is True

    @pytest.mark.unit
    def test_competitor_comparison_blocked(self):
        blocked, reason = check_guardrails("GitHub vs GitLab which is better?")
        # Pattern: competitor + compare
        assert blocked is True

    @pytest.mark.unit
    def test_stock_price_blocked(self):
        blocked, reason = check_guardrails("Should I buy or sell GitLab stock GTLB?")
        assert blocked is True

    @pytest.mark.unit
    def test_empty_query_blocked(self):
        blocked, reason = check_guardrails("")
        assert blocked is True
        assert reason == "Query too short"

    @pytest.mark.unit
    def test_single_char_blocked(self):
        blocked, reason = check_guardrails("a")
        assert blocked is True

    @pytest.mark.unit
    def test_two_char_blocked(self):
        blocked, reason = check_guardrails("hi")
        assert blocked is True

    @pytest.mark.unit
    def test_whitespace_only_blocked(self):
        blocked, reason = check_guardrails("   ")
        assert blocked is True

    @pytest.mark.unit
    def test_returns_tuple(self):
        """check_guardrails always returns a 2-tuple."""
        result = check_guardrails("test query about gitlab")
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.unit
    def test_reason_is_string_or_none(self):
        blocked, reason = check_guardrails("What is the weather?")
        if blocked:
            # reason can be a string or None — both valid
            assert reason is None or isinstance(reason, str)


# ── check_confidence ──────────────────────────────────────────────────────────

class TestCheckConfidence:

    @pytest.mark.unit
    def test_high_confidence_no_note(self):
        from api.models import SourceChunk
        sources = [
            SourceChunk(id=1, content="x", source_url="http://a.com",
                        page_type="handbook", page_title="", section_title="",
                        similarity=0.92),
        ]
        needs_note, note = check_confidence(0.92, sources)
        assert needs_note is False
        assert note is None

    @pytest.mark.unit
    def test_low_confidence_adds_note(self):
        from api.models import SourceChunk
        sources = [
            SourceChunk(id=1, content="x", source_url="http://a.com",
                        page_type="handbook", page_title="", section_title="",
                        similarity=0.40),
        ]
        needs_note, note = check_confidence(0.40, sources)
        assert needs_note is True
        assert note is not None
        assert len(note) > 10

    @pytest.mark.unit
    def test_no_sources_adds_note(self):
        needs_note, note = check_confidence(0.90, [])
        assert needs_note is True

    @pytest.mark.unit
    def test_boundary_exactly_0_55_no_note(self):
        from api.models import SourceChunk
        sources = [
            SourceChunk(id=1, content="x", source_url="http://a.com",
                        page_type="handbook", page_title="", section_title="",
                        similarity=0.55),
        ]
        needs_note, _ = check_confidence(0.55, sources)
        assert needs_note is False

    @pytest.mark.unit
    def test_below_0_55_adds_note(self):
        from api.models import SourceChunk
        sources = [
            SourceChunk(id=1, content="x", source_url="http://a.com",
                        page_type="handbook", page_title="", section_title="",
                        similarity=0.54),
        ]
        needs_note, _ = check_confidence(0.54, sources)
        assert needs_note is True


# ── Response templates ────────────────────────────────────────────────────────

class TestOffTopicResponse:

    @pytest.mark.unit
    def test_off_topic_response_is_string(self):
        resp = get_off_topic_response()
        assert isinstance(resp, str)
        assert len(resp) > 50

    @pytest.mark.unit
    def test_off_topic_response_mentions_handbook(self):
        resp = get_off_topic_response()
        assert "handbook" in resp.lower() or "gitlab" in resp.lower()

    @pytest.mark.unit
    def test_low_confidence_addendum_is_string(self):
        assert isinstance(LOW_CONFIDENCE_ADDENDUM, str)
        assert "confidence" in LOW_CONFIDENCE_ADDENDUM.lower()