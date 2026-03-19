"""
Analytics routes for the admin dashboard.

GET /analytics/summary       → all key metrics in one call
GET /analytics/confidence    → confidence score histogram
GET /analytics/feedback      → detailed feedback records
"""

import logging
from fastapi import APIRouter, Request

from database.supabase_client import (
    get_analytics_summary,
    get_confidence_distribution,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/analytics/summary", tags=["Analytics"])
async def analytics_summary(request: Request):
    """
    Returns all dashboard metrics in a single call.
    Includes: query counts, confidence averages, feedback totals,
    chunks indexed, queries per day, and top queries.
    """
    db = request.app.state.db
    summary = get_analytics_summary(db)
    return {"status": "ok", "data": summary}


@router.get("/analytics/confidence", tags=["Analytics"])
async def confidence_distribution(request: Request):
    """
    Returns confidence score distribution bucketed into 5 ranges.
    Used to render the histogram in the dashboard.
    """
    db   = request.app.state.db
    data = get_confidence_distribution(db)
    return {"status": "ok", "data": data}


@router.get("/analytics/feedback", tags=["Analytics"])
async def recent_feedback(request: Request, limit: int = 20):
    """
    Returns the most recent feedback records with query and comment.
    """
    db = request.app.state.db
    try:
        result = (
            db.table("feedback")
            .select("id, session_id, query, rating, comment, created_at")
            .order("created_at", desc=True)
            .limit(min(limit, 100))
            .execute()
        )
        return {"status": "ok", "data": result.data or []}
    except Exception as e:
        logger.error(f"Recent feedback query failed: {e}")
        return {"status": "error", "message": str(e)}