"""
Chunker: splits parsed pages into token-sized chunks
with overlap, preserving section context in each chunk.
"""

import re
import logging
import tiktoken

logger = logging.getLogger(__name__)

CHUNK_SIZE    = 512   # max tokens per chunk
CHUNK_OVERLAP = 64    # overlap between consecutive chunks
MIN_CHUNK_LEN = 60    # discard chunks shorter than this (chars)

# cl100k_base is the GPT-4 tokenizer — a good proxy for Gemini
_ENCODER = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


def _split_into_units(text: str) -> list[str]:
    """
    Split document text into logical units (paragraphs / sections).
    We try to honour paragraph boundaries so chunks stay coherent.
    """
    # Split on blank lines
    units = re.split(r"\n{2,}", text)
    return [u.strip() for u in units if u.strip()]


def create_chunks(parsed_page: dict) -> list[dict]:
    """
    Split a parsed page dict into a list of chunk dicts.
    Each chunk inherits metadata from its parent page.

    Chunk dict keys:
        content, source_url, page_type, page_title,
        section_title, chunk_index, token_count
    """
    url        = parsed_page["url"]
    page_type  = parsed_page["page_type"]
    title      = parsed_page["title"]
    content    = parsed_page["content"]

    units = _split_into_units(content)

    chunks: list[dict] = []
    current_units: list[str] = []
    current_token_count: int = 0
    chunk_index: int = 0
    current_section: str = title   # tracks the last heading we passed

    def _flush(units_to_flush: list[str], token_count: int) -> None:
        """Save current buffer as a chunk."""
        nonlocal chunk_index
        chunk_text = "\n\n".join(units_to_flush)
        if len(chunk_text) < MIN_CHUNK_LEN:
            return
        chunks.append(
            {
                "content":       chunk_text,
                "source_url":    url,
                "page_type":     page_type,
                "page_title":    title,
                "section_title": current_section,
                "chunk_index":   chunk_index,
                "token_count":   token_count,
            }
        )
        chunk_index += 1

    for unit in units:
        # Track which section we're in
        heading_match = re.match(r"^#{1,4}\s+(.+)$", unit)
        if heading_match:
            current_section = heading_match.group(1).strip()

        unit_tokens = _count_tokens(unit)

        # If a single unit is larger than CHUNK_SIZE, split it by sentences
        if unit_tokens > CHUNK_SIZE:
            # Flush current buffer first
            if current_units:
                _flush(current_units, current_token_count)
                # Keep overlap from tail of current_units
                current_units, current_token_count = _build_overlap(current_units)

            # Split oversized unit by sentences
            sentences = re.split(r"(?<=[.!?])\s+", unit)
            for sentence in sentences:
                s_tokens = _count_tokens(sentence)
                if current_token_count + s_tokens > CHUNK_SIZE and current_units:
                    _flush(current_units, current_token_count)
                    current_units, current_token_count = _build_overlap(current_units)
                current_units.append(sentence)
                current_token_count += s_tokens
            continue

        # Normal case: check if adding this unit would overflow the chunk
        if current_token_count + unit_tokens > CHUNK_SIZE and current_units:
            _flush(current_units, current_token_count)
            current_units, current_token_count = _build_overlap(current_units)

        current_units.append(unit)
        current_token_count += unit_tokens

    # Flush any remaining content
    if current_units:
        _flush(current_units, current_token_count)

    return chunks


def _build_overlap(units: list[str]) -> tuple[list[str], int]:
    """
    From the tail of the current buffer, keep units that fit within
    CHUNK_OVERLAP tokens. Returns (overlap_units, overlap_token_count).
    """
    overlap_units: list[str] = []
    overlap_tokens: int = 0

    for unit in reversed(units):
        t = _count_tokens(unit)
        if overlap_tokens + t <= CHUNK_OVERLAP:
            overlap_units.insert(0, unit)
            overlap_tokens += t
        else:
            break

    return overlap_units, overlap_tokens