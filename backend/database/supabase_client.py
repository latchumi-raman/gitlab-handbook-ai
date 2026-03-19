"""
Supabase client: handles all vector DB operations —
inserting chunks, similarity search, feedback, and analytics.
"""

import logging
from typing import Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client(url: str, key: str) -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        _client = create_client(url, key)
        logger.info("Supabase client initialised")
    return _client


# ── Ingestion helpers ────────────────────────────────────────────────────────

def url_is_indexed(client: Client, url: str) -> bool:
    result = (
        client.table("documents")
        .select("id")
        .eq("source_url", url)
        .limit(1)
        .execute()
    )
    return len(result.data) > 0


def delete_chunks_for_url(client: Client, url: str) -> None:
    client.table("documents").delete().eq("source_url", url).execute()
    logger.info(f"Deleted existing chunks for {url}")


def insert_chunks(
    client: Client,
    chunks: list[dict],
    batch_size: int = 50,
) -> int:
    total_inserted = 0

    for i in range(0, len(chunks), batch_size):
        batch   = chunks[i : i + batch_size]
        records = []

        for chunk in batch:
            if "embedding" not in chunk:
                continue
            records.append({
                "content":       chunk["content"],
                "embedding":     chunk["embedding"],
                "source_url":    chunk["source_url"],
                "page_type":     chunk["page_type"],
                "page_title":    chunk.get("page_title", ""),
                "section_title": chunk.get("section_title", ""),
                "chunk_index":   chunk.get("chunk_index", 0),
                "token_count":   chunk.get("token_count", 0),
                "metadata": {
                    "page_type":     chunk["page_type"],
                    "page_title":    chunk.get("page_title", ""),
                    "section_title": chunk.get("section_title", ""),
                },
            })

        if not records:
            continue

        try:
            client.table("documents").insert(records).execute()
            total_inserted += len(records)
            logger.info(f"Inserted batch {i // batch_size + 1}: {len(records)} chunks")
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")

    return total_inserted


# ── Search ───────────────────────────────────────────────────────────────────

def search_similar(
    client: Client,
    query_embedding: list[float],
    match_count:      int   = 5,
    match_threshold:  float = 0.50,
    page_type_filter: Optional[str] = None,
) -> list[dict]:
    try:
        params: dict = {
            "query_embedding":  query_embedding,
            "match_threshold":  match_threshold,
            "match_count":      match_count,
            "filter_page_type": page_type_filter,
        }
        result = client.rpc("match_documents", params).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"search_similar failed: {e}")
        return []


# ── Feedback ─────────────────────────────────────────────────────────────────

def save_feedback(
    client:     Client,
    session_id: str,
    query:      str,
    response:   str,
    rating:     int,
    comment:    str = "",
) -> bool:
    try:
        client.table("feedback").insert({
            "session_id": session_id,
            "query":      query,
            "response":   response,
            "rating":     rating,
            "comment":    comment,
        }).execute()
        return True
    except Exception as e:
        logger.error(f"save_feedback failed: {e}")
        return False


# ── Analytics ────────────────────────────────────────────────────────────────

def log_query(
    client:             Client,
    session_id:         str,
    query:              str,
    page_type_filter:   str,
    confidence:         float,
    source_count:       int,
    response_time_ms:   int,
    guardrail_triggered: bool,
) -> None:
    """Log every chat query for the analytics dashboard."""
    try:
        client.table("query_logs").insert({
            "session_id":          session_id,
            "query":               query[:500],    # trim very long queries
            "page_type_filter":    page_type_filter,
            "confidence":          round(confidence, 4),
            "source_count":        source_count,
            "response_time_ms":    response_time_ms,
            "guardrail_triggered": guardrail_triggered,
        }).execute()
    except Exception as e:
        # Non-critical — don't let analytics failure affect chat
        logger.warning(f"log_query failed (non-critical): {e}")


def get_analytics_summary(client: Client) -> dict:
    """
    Fetch aggregated analytics for the admin dashboard.
    Returns a single dict with all metrics.
    """
    summary = {
        "total_queries":        0,
        "queries_last_7_days":  0,
        "avg_confidence":       0.0,
        "guardrail_rate":       0.0,
        "positive_feedback":    0,
        "negative_feedback":    0,
        "total_feedback":       0,
        "chunks_indexed":       0,
        "handbook_chunks":      0,
        "direction_chunks":     0,
        "queries_per_day":      [],
        "top_queries":          [],
    }

    try:
        # Total queries + last 7 days
        total_result = client.table("query_logs").select("id", count="exact").execute()
        summary["total_queries"] = total_result.count or 0

        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
        week_result = (
            client.table("query_logs")
            .select("id", count="exact")
            .gte("created_at", cutoff)
            .execute()
        )
        summary["queries_last_7_days"] = week_result.count or 0

        # Average confidence + guardrail rate
        stats_result = client.table("query_logs").select(
            "confidence, guardrail_triggered"
        ).execute()
        rows = stats_result.data or []
        if rows:
            confs      = [r["confidence"] for r in rows if r["confidence"] is not None]
            guardrails = [r for r in rows if r.get("guardrail_triggered")]
            summary["avg_confidence"]  = round(sum(confs) / len(confs), 3) if confs else 0.0
            summary["guardrail_rate"]  = round(len(guardrails) / len(rows), 3)

        # Feedback summary
        fb_result = client.table("feedback").select("rating").execute()
        fb_rows   = fb_result.data or []
        summary["positive_feedback"] = sum(1 for r in fb_rows if r["rating"] ==  1)
        summary["negative_feedback"] = sum(1 for r in fb_rows if r["rating"] == -1)
        summary["total_feedback"]    = len(fb_rows)

        # Chunks indexed
        chunk_result = client.table("documents").select("page_type").execute()
        chunk_rows   = chunk_result.data or []
        summary["chunks_indexed"]   = len(chunk_rows)
        summary["handbook_chunks"]  = sum(1 for r in chunk_rows if r["page_type"] == "handbook")
        summary["direction_chunks"] = sum(1 for r in chunk_rows if r["page_type"] == "direction")

        # Queries per day (last 14 days)
        try:
            qpd_result = client.table("queries_per_day").select("*").execute()
            summary["queries_per_day"] = qpd_result.data or []
        except Exception:
            pass   # view may not exist yet

        # Top queries
        try:
            tq_result = client.table("top_queries").select("*").limit(10).execute()
            summary["top_queries"] = tq_result.data or []
        except Exception:
            pass

    except Exception as e:
        logger.error(f"get_analytics_summary failed: {e}")

    return summary


def get_confidence_distribution(client: Client) -> list[dict]:
    """
    Returns confidence score bucketed into ranges for the histogram.
    Buckets: 0-20%, 20-40%, 40-60%, 60-80%, 80-100%
    """
    try:
        result = client.table("query_logs").select("confidence").execute()
        rows   = result.data or []
        confs  = [r["confidence"] for r in rows if r["confidence"] is not None]

        buckets = [
            {"range": "0–20%",  "min": 0.0,  "max": 0.2,  "count": 0},
            {"range": "20–40%", "min": 0.2,  "max": 0.4,  "count": 0},
            {"range": "40–60%", "min": 0.4,  "max": 0.6,  "count": 0},
            {"range": "60–80%", "min": 0.6,  "max": 0.8,  "count": 0},
            {"range": "80–100%","min": 0.8,  "max": 1.01, "count": 0},
        ]
        for c in confs:
            for b in buckets:
                if b["min"] <= c < b["max"]:
                    b["count"] += 1
                    break

        return [{"range": b["range"], "count": b["count"]} for b in buckets]

    except Exception as e:
        logger.error(f"get_confidence_distribution failed: {e}")
        return []