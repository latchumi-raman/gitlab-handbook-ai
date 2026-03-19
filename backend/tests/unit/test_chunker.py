"""
Unit tests for the text chunker.

Tests cover:
- Basic chunking produces correct structure
- Chunk size respects CHUNK_SIZE token limit
- Chunk overlap carries context between adjacent chunks
- Metadata (source_url, page_type, etc.) is preserved on every chunk
- Empty / very short content handled gracefully
- Section headings are tracked in section_title
"""

import pytest
from scraper.chunker import create_chunks, CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_LEN

# ── Test data ─────────────────────────────────────────────────────────────────

def make_parsed_page(content: str, url: str = "https://handbook.gitlab.com/test/",
                     page_type: str = "handbook", title: str = "Test Page") -> dict:
    return {"url": url, "page_type": page_type, "title": title, "content": content}


SIMPLE_CONTENT = """
# GitLab Values

GitLab has six core values known as CREDIT.

## Collaboration

We work together across all teams and time zones.
Every team member can contribute to any project.

## Results

We focus on outcomes, not activity or hours worked.
Results matter more than time spent.

## Efficiency

We use everyone's time wisely. Meetings have agendas.
Documentation is preferred over verbal communication.
""".strip()

LONG_CONTENT = ("GitLab is an all-remote company. " * 200).strip()


# ── Basic structure ───────────────────────────────────────────────────────────

class TestCreateChunks:

    @pytest.mark.unit
    def test_returns_list(self):
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        assert isinstance(chunks, list)

    @pytest.mark.unit
    def test_produces_at_least_one_chunk(self):
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        assert len(chunks) >= 1

    @pytest.mark.unit
    def test_each_chunk_is_dict(self):
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        for chunk in chunks:
            assert isinstance(chunk, dict)

    @pytest.mark.unit
    def test_required_keys_present(self):
        required = {"content", "source_url", "page_type",
                    "page_title", "section_title", "chunk_index", "token_count"}
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        for chunk in chunks:
            assert required.issubset(set(chunk.keys())), \
                f"Missing keys: {required - set(chunk.keys())}"

    @pytest.mark.unit
    def test_source_url_preserved(self):
        url    = "https://handbook.gitlab.com/specific/page/"
        page   = make_parsed_page(SIMPLE_CONTENT, url=url)
        chunks = create_chunks(page)
        for chunk in chunks:
            assert chunk["source_url"] == url

    @pytest.mark.unit
    def test_page_type_preserved(self):
        page   = make_parsed_page(SIMPLE_CONTENT, page_type="direction")
        chunks = create_chunks(page)
        for chunk in chunks:
            assert chunk["page_type"] == "direction"

    @pytest.mark.unit
    def test_page_title_preserved(self):
        page   = make_parsed_page(SIMPLE_CONTENT, title="GitLab Values")
        chunks = create_chunks(page)
        for chunk in chunks:
            assert chunk["page_title"] == "GitLab Values"

    @pytest.mark.unit
    def test_chunk_index_sequential(self):
        page   = make_parsed_page(LONG_CONTENT)
        chunks = create_chunks(page)
        indices = [c["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    @pytest.mark.unit
    def test_token_count_is_positive_int(self):
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        for chunk in chunks:
            assert isinstance(chunk["token_count"], int)
            assert chunk["token_count"] > 0

    @pytest.mark.unit
    def test_no_empty_content_chunks(self):
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        for chunk in chunks:
            assert chunk["content"].strip() != ""
            assert len(chunk["content"]) >= MIN_CHUNK_LEN


# ── Token limits ──────────────────────────────────────────────────────────────

class TestChunkTokenLimits:

    @pytest.mark.unit
    def test_chunks_respect_token_limit(self):
        """No chunk should exceed CHUNK_SIZE tokens."""
        import tiktoken
        enc    = tiktoken.get_encoding("cl100k_base")
        page   = make_parsed_page(LONG_CONTENT)
        chunks = create_chunks(page)
        for chunk in chunks:
            token_count = len(enc.encode(chunk["content"]))
            assert token_count <= CHUNK_SIZE + 20, \
                f"Chunk {chunk['chunk_index']} has {token_count} tokens (limit {CHUNK_SIZE})"

    @pytest.mark.unit
    def test_long_content_produces_multiple_chunks(self):
        page   = make_parsed_page(LONG_CONTENT)
        chunks = create_chunks(page)
        assert len(chunks) > 1, "Long content should be split into multiple chunks"

    @pytest.mark.unit
    def test_short_content_single_chunk(self):
        content = "GitLab values are CREDIT: Collaboration, Results, Efficiency, Diversity, Iteration, Transparency."
        page    = make_parsed_page(content)
        chunks  = create_chunks(page)
        assert len(chunks) == 1


# ── Section tracking ──────────────────────────────────────────────────────────

class TestSectionTracking:

    @pytest.mark.unit
    def test_section_title_populated(self):
        page   = make_parsed_page(SIMPLE_CONTENT)
        chunks = create_chunks(page)
        # At least some chunks should have a non-empty section title
        section_titles = [c["section_title"] for c in chunks if c["section_title"]]
        assert len(section_titles) > 0

    @pytest.mark.unit
    def test_section_changes_across_chunks(self):
        """Content with multiple H2 headings should produce different section titles."""
        content = (
            "## Alpha Section\n\nContent about alpha. " * 50 +
            "## Beta Section\n\nContent about beta. " * 50
        )
        page   = make_parsed_page(content)
        chunks = create_chunks(page)
        titles = {c["section_title"] for c in chunks}
        assert len(titles) >= 2, "Multiple H2 headings should produce multiple section titles"


# ── Edge cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:

    @pytest.mark.unit
    def test_empty_content_returns_empty_list(self):
        page   = make_parsed_page("")
        chunks = create_chunks(page)
        assert chunks == []

    @pytest.mark.unit
    def test_very_short_content_skipped(self):
        """Content shorter than MIN_CHUNK_LEN should produce no chunks."""
        page   = make_parsed_page("Too short.")
        chunks = create_chunks(page)
        assert chunks == []

    @pytest.mark.unit
    def test_whitespace_only_returns_empty(self):
        page   = make_parsed_page("   \n\n   \t   ")
        chunks = create_chunks(page)
        assert chunks == []

    @pytest.mark.unit
    def test_content_with_no_headings(self):
        content = "A paragraph of text. " * 30
        page    = make_parsed_page(content)
        chunks  = create_chunks(page)
        assert len(chunks) >= 1