"""
Chat route — updated for Phase 4.
New: query enhancement (auto-rewrite), query logging for analytics.
"""

import json
import time
import logging
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from ..models import ChatRequest, ChatResponse, FeedbackRequest, FeedbackResponse
from ..services.guardrails import check_guardrails, get_off_topic_response
from ..services.rag import (
    embed_query,
    retrieve_chunks,
    calculate_confidence,
    stream_answer,
    generate_follow_ups,
    save_to_history,
    get_session_history,
    _build_context_block,
    enhance_query,
    DEFAULT_MATCH_THRESHOLD,
)
from database.supabase_client import save_feedback, log_query

router  = APIRouter()
logger  = logging.getLogger(__name__)


@router.post("/chat/stream", tags=["Chat"])
async def chat_stream(req: ChatRequest, request: Request):
    """
    Main streaming chat endpoint (Server-Sent Events).
    Phase 4 additions: query enhancement event, query logging.
    """
    db = request.app.state.db

    async def event_generator():
        start_time          = time.time()
        final_confidence    = 0.0
        final_source_count  = 0
        guardrail_hit       = False

        try:
            # ── 1. Guardrail check ──────────────────────────────────────
            is_blocked, reason = check_guardrails(req.query)
            if is_blocked:
                guardrail_hit = True
                off_topic_msg = get_off_topic_response()
                words = off_topic_msg.split(" ")
                for i, word in enumerate(words):
                    sep = " " if i < len(words) - 1 else ""
                    yield _sse({"type": "token", "content": word + sep})
                    await asyncio.sleep(0.02)
                yield _sse({"type": "guardrail", "triggered": True, "reason": reason or "off_topic"})
                yield _sse({"type": "done"})
                return

            # ── 2. Query enhancement ────────────────────────────────────
            # Rewrite vague/short queries to improve retrieval quality
            enhanced_query, was_enhanced = await enhance_query(req.query)

            if was_enhanced:
                yield _sse({
                    "type":             "query_enhanced",
                    "original":         req.query,
                    "enhanced":         enhanced_query,
                    "message":          "Query enhanced for better search",
                })

            # ── 3. History ──────────────────────────────────────────────
            session_history = get_session_history(req.session_id)
            history_to_use  = session_history if session_history else req.history

            # ── 4. Embed ────────────────────────────────────────────────
            query_embedding = await asyncio.to_thread(embed_query, enhanced_query)
            if not query_embedding:
                yield _sse({"type": "error", "message": "Embedding service unavailable"})
                yield _sse({"type": "done"})
                return

            # ── 5. Retrieve ─────────────────────────────────────────────
            page_filter = (
                req.page_type_filter.value
                if req.page_type_filter.value != "both"
                else None
            )
            chunks = await asyncio.to_thread(
                retrieve_chunks,
                db,
                query_embedding,
                req.match_count,
                DEFAULT_MATCH_THRESHOLD,
                page_filter,
            )

            # ── 6. Confidence + sources ─────────────────────────────────
            final_confidence   = calculate_confidence(chunks)
            final_source_count = len(chunks)

            yield _sse({
                "type":    "sources",
                "sources": [c.dict() for c in chunks],
            })

            # ── 7. Build context ────────────────────────────────────────
            context = _build_context_block(chunks)
            if not context:
                context = (
                    "No directly relevant content found in the GitLab handbook. "
                    "State that clearly in your answer."
                )

            # ── 8. Stream answer ────────────────────────────────────────
            full_answer_parts: list[str] = []

            async for token in stream_answer(req.query, context, history_to_use):
                full_answer_parts.append(token)
                yield _sse({"type": "token", "content": token})
                await asyncio.sleep(0)

            full_answer = "".join(full_answer_parts)

            # Low-confidence note
            if final_confidence < 0.55 and chunks:
                note = (
                    "\n\n---\n*Note: Confidence is low. "
                    "Please verify by checking the linked sources directly.*"
                )
                full_answer += note
                yield _sse({"type": "token", "content": note})

            # ── 9. Save history ─────────────────────────────────────────
            save_to_history(req.session_id, "user",      req.query)
            save_to_history(req.session_id, "assistant", full_answer)

            # ── 10. Follow-ups ──────────────────────────────────────────
            follow_ups = await generate_follow_ups(req.query, full_answer)

            # ── 11. Metadata event ──────────────────────────────────────
            yield _sse({
                "type":       "metadata",
                "confidence": final_confidence,
                "follow_ups": follow_ups,
                "session_id": req.session_id,
            })

            yield _sse({"type": "done"})

        except asyncio.CancelledError:
            logger.debug(f"Stream cancelled for session {req.session_id}")

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield _sse({"type": "error", "message": str(e)[:100]})
            yield _sse({"type": "done"})

        finally:
            # ── 12. Log query for analytics ─────────────────────────────
            elapsed_ms = int((time.time() - start_time) * 1000)
            try:
                log_query(
                    client              = db,
                    session_id          = req.session_id,
                    query               = req.query,
                    page_type_filter    = req.page_type_filter.value,
                    confidence          = final_confidence,
                    source_count        = final_source_count,
                    response_time_ms    = elapsed_ms,
                    guardrail_triggered = guardrail_hit,
                )
            except Exception as log_err:
                logger.warning(f"Analytics log failed (non-critical): {log_err}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_sync(req: ChatRequest, request: Request):
    """Non-streaming JSON fallback — unchanged from Phase 2, adds logging."""
    db         = request.app.state.db
    start_time = time.time()

    is_blocked, reason = check_guardrails(req.query)
    if is_blocked:
        log_query(
            db, req.session_id, req.query,
            req.page_type_filter.value,
            0.0, 0, 0, True,
        )
        return ChatResponse(
            answer              = get_off_topic_response(),
            sources             = [],
            confidence          = 0.0,
            follow_ups          = [],
            session_id          = req.session_id,
            guardrail_triggered = True,
            guardrail_reason    = reason,
        )

    enhanced_query, _ = await enhance_query(req.query)
    query_embedding   = await asyncio.to_thread(embed_query, enhanced_query)
    if not query_embedding:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")

    page_filter = (
        req.page_type_filter.value
        if req.page_type_filter.value != "both"
        else None
    )
    chunks     = await asyncio.to_thread(
        retrieve_chunks, db, query_embedding,
        req.match_count, DEFAULT_MATCH_THRESHOLD, page_filter,
    )
    confidence = calculate_confidence(chunks)
    context    = _build_context_block(chunks)
    history    = get_session_history(req.session_id) or req.history

    answer_parts: list[str] = []
    async for token in stream_answer(req.query, context or "No context found.", history):
        answer_parts.append(token)
    answer = "".join(answer_parts)

    if confidence < 0.55 and chunks:
        answer += "\n\n---\n*Note: Confidence is low — verify via linked sources.*"

    save_to_history(req.session_id, "user",      req.query)
    save_to_history(req.session_id, "assistant", answer)
    follow_ups = await generate_follow_ups(req.query, answer)

    elapsed_ms = int((time.time() - start_time) * 1000)
    log_query(db, req.session_id, req.query,
              req.page_type_filter.value,
              confidence, len(chunks), elapsed_ms, False)

    return ChatResponse(
        answer=answer, sources=chunks,
        confidence=confidence, follow_ups=follow_ups,
        session_id=req.session_id,
    )


@router.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(req: FeedbackRequest, request: Request):
    db = request.app.state.db
    if req.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 or -1")
    success = save_feedback(
        db, req.session_id, req.query,
        req.response[:2000], req.rating, req.comment,
    )
    if success:
        return FeedbackResponse(success=True, message="Feedback saved — thank you!")
    raise HTTPException(status_code=500, detail="Failed to save feedback")


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"