"""
Embedder: generates vector embeddings using Google's
embedding-001 model (768 dimensions, free tier, works on v1beta).
"""

import time
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

EMBEDDING_MODEL   = "models/gemini-embedding-001"
EMBEDDING_DIMS    = 768  
BATCH_SIZE        = 20
RETRY_ATTEMPTS    = 3
BASE_RETRY_WAIT   = 10.0
INTER_REQ_DELAY   = 0.15
INTER_BATCH_DELAY = 2.0


def configure(api_key: str) -> None:
    genai.configure(api_key=api_key)


def _embed_single(text: str, task_type: str = "retrieval_document") -> list[float] | None:
    """Embed one piece of text. Returns None on permanent failure."""
    if len(text) > 8_000:
        text = text[:8_000]

    for attempt in range(RETRY_ATTEMPTS):
        try:
            result = genai.embed_content(
                model      = EMBEDDING_MODEL,
                content    = text,
                task_type  = task_type,
                output_dimensionality=EMBEDDING_DIMS,
            )
            return result["embedding"]
        except Exception as e:
            err = str(e).lower()
            is_rate_limit = "429" in err or "quota" in err or "rate" in err
            if is_rate_limit:
                wait = BASE_RETRY_WAIT * (2 ** attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{RETRY_ATTEMPTS}). "
                    f"Waiting {wait:.0f}s ..."
                )
                time.sleep(wait)
            else:
                logger.error(f"Embedding error (non-retriable): {e}")
                return None

    logger.error("Embedding failed after all retry attempts")
    return None


def embed_chunks_with_progress(
    chunks:       list[dict],
    batch_num:    int,
    total_batches: int,
) -> list[dict]:
    """
    Embed a single batch of chunks.
    Called by ingest.py once per batch so storage can happen immediately after.
    Mutates each chunk dict in-place by adding 'embedding' key.
    Returns only successfully embedded chunks.
    """
    embedded = []
    for chunk in chunks:
        embedding = _embed_single(chunk["content"])
        time.sleep(INTER_REQ_DELAY)

        if embedding:
            chunk["embedding"] = embedding
            embedded.append(chunk)
        else:
            logger.warning(
                f"  Batch {batch_num}/{total_batches} — "
                f"failed chunk {chunk.get('chunk_index')} "
                f"from {chunk['source_url']}"
            )

    # Pause between batches to respect rate limits
    time.sleep(INTER_BATCH_DELAY)
    return embedded


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Original bulk embed — kept for backward compatibility.
    For new runs use embed_chunks_with_progress in ingest.py instead.
    """
    total   = len(chunks)
    success = 0
    failed  = 0
    embedded = []

    logger.info(f"Embedding {total} chunks (batch size {BATCH_SIZE}) ...")
    logger.info(
        f"Estimated API calls: {total} | "
        f"Daily free quota: 1,500 | "
        f"{'OK' if total <= 1500 else 'OVER QUOTA — run in multiple sessions'}"
    )

    for batch_start in range(0, total, BATCH_SIZE):
        batch       = chunks[batch_start : batch_start + BATCH_SIZE]
        batch_n     = batch_start // BATCH_SIZE + 1
        total_batches = (total - 1) // BATCH_SIZE + 1

        logger.info(f"Batch {batch_n}/{total_batches} ({len(batch)} chunks) ...")

        for chunk in batch:
            embedding = _embed_single(chunk["content"])
            time.sleep(INTER_REQ_DELAY)
            if embedding:
                chunk["embedding"] = embedding
                embedded.append(chunk)
                success += 1
            else:
                failed += 1
                logger.warning(f"  ✗ Failed: {chunk['source_url']} [chunk {chunk['chunk_index']}]")

        if batch_start + BATCH_SIZE < total:
            time.sleep(INTER_BATCH_DELAY)

    logger.info(
        f"Embedding done — {success} succeeded, {failed} failed "
        f"({success/total*100:.1f}% success rate)"
    )
    return embedded