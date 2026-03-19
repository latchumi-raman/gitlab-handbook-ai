"""
RAG service — updated to match gemini-embedding-001 at 768 dimensions
and gemini-2.5-flash for generation.
"""

import os
import logging
import asyncio
import json
import re
from typing import AsyncIterator, Optional

import google.generativeai as genai
from supabase import Client

from ..models import Message, SourceChunk
from .guardrails import check_confidence

logger = logging.getLogger(__name__)

# ── Model names — must match exactly what embedder.py uses ───────────────────
GEMINI_MODEL     = "gemini-2.5-flash"
EMBEDDING_MODEL  = "models/gemini-embedding-001"
EMBEDDING_DIMS   = 768    # must match the vector(768) column in Supabase

DEFAULT_MATCH_COUNT     = 5
DEFAULT_MATCH_THRESHOLD = 0.45
MAX_CONTEXT_CHARS       = 12_000

GENERATION_CONFIG = {
    "temperature":       0.3,
    "top_p":             0.85,
    "top_k":             40,
    "max_output_tokens": 2048,
}

SYSTEM_PROMPT = """You are GitLab's Handbook AI — a knowledgeable, helpful assistant \
for GitLab employees and aspiring employees. You answer questions exclusively using \
content from GitLab's official Handbook (handbook.gitlab.com) and Direction pages \
(about.gitlab.com/direction).

RULES:
1. Base your answer ONLY on the provided context chunks. Do not use outside knowledge.
2. If the context doesn't contain enough information, say so clearly rather than guessing.
3. Always cite which part of the handbook or direction page you're drawing from.
4. Be concise but complete. Use markdown formatting for clarity.
5. Maintain a professional, friendly tone.
6. If asked about something not in the context, say so and recommend handbook.gitlab.com.

CONTEXT FROM GITLAB HANDBOOK/DIRECTION:
{context}
"""

FOLLOW_UP_PROMPT = """Based on this GitLab handbook Q&A exchange, suggest exactly 3 \
natural follow-up questions a GitLab employee might ask next.

Original question: {query}
Answer summary: {answer_summary}

Rules:
- Questions must be answerable from the GitLab handbook or direction pages
- Keep each question under 12 words
- Make them genuinely useful and specific
- Return ONLY a valid JSON array of exactly 3 strings
- No markdown, no backticks, no preamble, no explanation
- Example: ["How does X work?", "What is Y policy?", "Where can I find Z?"]"""

QUERY_ENHANCE_PROMPT = """You are helping improve a search query against GitLab's \
employee handbook. Rewrite the following query to be more specific and informative \
for semantic search, while preserving the original intent.

Rules:
- Keep it under 60 words
- Add relevant GitLab-specific context if the query is vague
- If the query is already specific and clear (>8 words), return it unchanged
- Return ONLY the rewritten query string, nothing else, no quotes

Original query: {query}

Rewritten query:"""


# ── Session history ───────────────────────────────────────────────────────────
_session_history: dict[str, list[Message]] = {}
_MAX_HISTORY_TURNS = 10


def configure_gemini(api_key: str) -> None:
    genai.configure(api_key=api_key)
    logger.info("Gemini configured")


def get_session_history(session_id: str) -> list[Message]:
    return _session_history.get(session_id, [])


def save_to_history(session_id: str, role: str, content: str) -> None:
    if session_id not in _session_history:
        _session_history[session_id] = []
    _session_history[session_id].append(Message(role=role, content=content))
    max_messages = _MAX_HISTORY_TURNS * 2
    if len(_session_history[session_id]) > max_messages:
        _session_history[session_id] = _session_history[session_id][-max_messages:]


def clear_session(session_id: str) -> None:
    _session_history.pop(session_id, None)


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_query(query: str) -> list[float] | None:
    """
    Embed the user query.
    IMPORTANT: must use same model AND same output_dimensionality as ingestion.
    gemini-embedding-001 default is 3072 dims — we force 768 to match Supabase schema.
    """
    try:
        result = genai.embed_content(
            model                = EMBEDDING_MODEL,
            content              = query[:4_000],
            task_type            = "retrieval_query",
            output_dimensionality = EMBEDDING_DIMS,   # ← critical: must match stored vectors
        )
        return result["embedding"]
    except Exception as e:
        logger.error(f"Query embedding failed: {e}")
        return None


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve_chunks(
    db:              Client,
    query_embedding: list[float],
    match_count:     int   = DEFAULT_MATCH_COUNT,
    threshold:       float = DEFAULT_MATCH_THRESHOLD,
    page_type:       Optional[str] = None,
) -> list[SourceChunk]:
    try:
        params = {
            "query_embedding":  query_embedding,
            "match_threshold":  threshold,
            "match_count":      match_count,
            "filter_page_type": page_type if page_type != "both" else None,
        }
        result = db.rpc("match_documents", params).execute()
        rows   = result.data or []
        return [
            SourceChunk(
                id            = row["id"],
                content       = row["content"],
                source_url    = row["source_url"],
                page_type     = row["page_type"],
                page_title    = row.get("page_title", ""),
                section_title = row.get("section_title", ""),
                similarity    = round(float(row["similarity"]), 4),
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Vector retrieval failed: {e}")
        return []


# ── Confidence ────────────────────────────────────────────────────────────────

def calculate_confidence(chunks: list[SourceChunk]) -> float:
    if not chunks:
        return 0.0
    sims = [c.similarity for c in chunks]
    if len(sims) == 1:
        return round(sims[0], 3)
    top        = sims[0]
    avg_others = sum(sims[1:]) / len(sims[1:])
    return round(min(0.4 * top + 0.6 * avg_others, 1.0), 3)


# ── Prompt builder ────────────────────────────────────────────────────────────

def _build_context_block(chunks: list[SourceChunk]) -> str:
    parts       = []
    total_chars = 0
    for i, chunk in enumerate(chunks, 1):
        label = (
            f"[SOURCE {i}] {chunk.page_title or 'GitLab Handbook'} "
            f"— {chunk.section_title} ({chunk.source_url})\n"
        )
        block = f"{label}{chunk.content.strip()}\n"
        if total_chars + len(block) > MAX_CONTEXT_CHARS:
            break
        parts.append(block)
        total_chars += len(block)
    return "\n---\n".join(parts)


def _build_gemini_messages(
    query:   str,
    context: str,
    history: list[Message],
) -> tuple[str, list[dict]]:
    system   = SYSTEM_PROMPT.format(context=context)
    messages = []
    for msg in history[-8:]:
        role = "user" if msg.role == "user" else "model"
        messages.append({"role": role, "parts": [msg.content]})
    messages.append({"role": "user", "parts": [query]})
    return system, messages


# ── Streaming generation ──────────────────────────────────────────────────────
# ── Streaming generation ──────────────────────────────────────────────────────

async def stream_answer(
    query:   str,
    context: str,
    history: list[Message],
) -> AsyncIterator[str]:
    system, messages = _build_gemini_messages(query, context, history)
    model = genai.GenerativeModel(
        model_name         = GEMINI_MODEL,
        system_instruction = system,
        generation_config  = GENERATION_CONFIG,
    )
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    def _sync_stream() -> None:
        try:
            response = model.generate_content(messages, stream=True)
            for chunk in response:
                # ── FIXED: safely access chunk text ──────────────────────────
                # gemini-2.5-flash throws if you access .text on a blocked chunk
                # instead of returning empty string like 1.5-flash did
                try:
                    text = chunk.text
                    if text:
                        queue.put_nowait(text)
                except Exception:
                    # Chunk was blocked by safety filter — check finish reason
                    try:
                        candidate = chunk.candidates[0] if chunk.candidates else None
                        if candidate:
                            finish = str(candidate.finish_reason)
                            if "SAFETY" in finish or "RECITATION" in finish:
                                logger.warning(
                                    f"Chunk blocked by safety filter: "
                                    f"finish_reason={finish}"
                                )
                                # Send a soft message rather than crashing
                                queue.put_nowait(
                                    "\n\n*This response was partially filtered. "
                                    "Please rephrase your question.*"
                                )
                            elif "STOP" in finish or "MAX_TOKENS" in finish:
                                pass  # normal end of stream — no action needed
                    except Exception as inner:
                        logger.debug(f"Could not read finish_reason: {inner}")
                    # Either way, continue to next chunk — don't crash the stream

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            queue.put_nowait(
                "\n\nI encountered an issue generating a response. "
                "Please try rephrasing your question."
            )
        finally:
            # Always send the sentinel — stream must always terminate
            queue.put_nowait(None)

    asyncio.get_event_loop().run_in_executor(None, _sync_stream)

    while True:
        token = await queue.get()
        if token is None:
            break
        yield token

# ── Query enhancement ─────────────────────────────────────────────────────────

async def enhance_query(query: str) -> tuple[str, bool]:
    word_count = len(query.strip().split())
    if word_count > 8:
        return query, False

    try:
        prompt   = QUERY_ENHANCE_PROMPT.format(query=query)
        model    = genai.GenerativeModel(GEMINI_MODEL)
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={"temperature": 0.2, "max_output_tokens": 80},
        )
        enhanced = response.text.strip().strip('"').strip("'").strip()
        if not enhanced or len(enhanced) < len(query) or len(enhanced) > 400:
            return query, False
        if enhanced.lower() == query.lower():
            return query, False
        logger.info(f"Query enhanced: '{query}' → '{enhanced}'")
        return enhanced, True
    except Exception as e:
        logger.warning(f"Query enhancement failed (using original): {e}")
        return query, False


# ── Follow-ups ────────────────────────────────────────────────────────────────

def _extract_json_array(text: str) -> list | None:
    """
    Robustly extract a JSON array from model output.
    Handles: plain JSON, markdown fences, leading/trailing whitespace,
    extra text before/after the array, and gemini-2.5-flash quirks.
    """
    # Strip markdown code fences (```json...``` or ```...```)
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()

    # Try parsing the whole thing first
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try finding a JSON array anywhere in the response using regex
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None

# ── Follow-ups ────────────────────────────────────────────────────────────────

async def generate_follow_ups(query: str, answer: str) -> list[str]:
    default = [
        "What are GitLab's core values?",
        "How does GitLab handle remote work?",
        "Where can I find the engineering handbook?",
    ]

    try:
        summary  = answer[:500] + ("..." if len(answer) > 500 else "")
        prompt   = FOLLOW_UP_PROMPT.format(query=query, answer_summary=summary)
        model    = genai.GenerativeModel(GEMINI_MODEL)

        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={
                "temperature":       0.7,
                "max_output_tokens": 800,   # ← increased from 200/300 — fixes truncation
            },
        )

        text        = response.text.strip()
        suggestions = _extract_json_array(text)

        if suggestions and len(suggestions) >= 3:
            return [str(s).strip() for s in suggestions[:3]]

        logger.warning(
            f"Follow-up parse failed — raw response was: {repr(text[:200])}"
        )

    except Exception as e:
        logger.warning(f"Follow-up generation failed: {e}")

    return default