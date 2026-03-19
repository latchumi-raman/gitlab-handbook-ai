"""
Health and utility endpoints.

GET /ping      → keepalive for Render (hit every 10 min by cron-job.org)
GET /health    → full health check including DB connectivity
GET /stats     → total chunks indexed, by page type
DELETE /session/{id} → clear conversation history
"""

import os
import logging
from fastapi import APIRouter, Depends, Request

from ..models import HealthResponse, PingResponse
from ..services.rag import clear_session, get_session_history

router = APIRouter()
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"


@router.get("/ping", response_model=PingResponse, tags=["Health"])
async def ping():
    """
    Lightweight keepalive endpoint.
    cron-job.org hits this every 10 minutes to prevent Render sleep.
    """
    return PingResponse(status="alive")


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health(request: Request):
    """
    Full health check — verifies DB is reachable and returns indexed chunk count.
    """
    db            = request.app.state.db
    db_connected  = False
    chunks_indexed = 0

    try:
        result = db.table("documents").select("id", count="exact").limit(1).execute()
        db_connected   = True
        chunks_indexed = result.count or 0
    except Exception as e:
        logger.warning(f"Health check DB query failed: {e}")

    return HealthResponse(
        status="ok" if db_connected else "degraded",
        version=APP_VERSION,
        db_connected=db_connected,
        chunks_indexed=chunks_indexed,
    )


@router.get("/stats", tags=["Health"])
async def stats(request: Request):
    """
    Returns chunk count breakdown by page_type.
    Useful for the admin dashboard (Phase 4 bonus feature).
    """
    db = request.app.state.db
    try:
        result = (
            db.table("documents")
            .select("page_type")
            .execute()
        )
        rows = result.data or []
        counts: dict[str, int] = {}
        for row in rows:
            pt = row.get("page_type", "unknown")
            counts[pt] = counts.get(pt, 0) + 1
        return {"status": "ok", "totals": counts, "grand_total": len(rows)}
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    """Clear all conversation history for a session (new chat button)."""
    clear_session(session_id)
    return {"status": "ok", "message": f"Session {session_id} cleared"}


@router.get("/session/{session_id}/history", tags=["Session"])
async def get_history(session_id: str):
    """Return the conversation history for a session."""
    history = get_session_history(session_id)
    return {"session_id": session_id, "messages": [m.dict() for m in history]}