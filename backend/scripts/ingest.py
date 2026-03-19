"""
Ingestion script — Phase 1 + fixes for quota safety.

Key improvements over original:
  - Store chunks to Supabase IMMEDIATELY after each embedding batch
    (if quota hits mid-run, already-processed chunks are safe)
  - Log every failed chunk to failed_chunks.log for retry
  - Running API call counter so you know exactly where you are
  - --retry-failed flag to re-process only previously failed chunks

Usage:
    python -m scripts.ingest --test-run
    python -m scripts.ingest --max-handbook 140 --max-direction 20
    python -m scripts.ingest --max-handbook 140 --max-direction 20 --force-reindex
    python -m scripts.ingest --retry-failed
"""

import asyncio
import argparse
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.crawler     import get_all_pages
from scraper.parser      import parse_page
from scraper.chunker     import create_chunks
from embeddings.embedder import configure, embed_chunks_with_progress
from database.supabase_client import (
    get_client,
    url_is_indexed,
    delete_chunks_for_url,
    insert_chunks,
)

load_dotenv()

logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt = "%H:%M:%S",
)
logger = logging.getLogger("ingest")

# Path to the failed chunks log — lives next to this script
FAILED_LOG = Path(__file__).parent / "failed_chunks.log"
PROGRESS_LOG = Path(__file__).parent / "ingest_progress.json"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GitLab Handbook ingestion pipeline")
    p.add_argument("--max-handbook",   type=int, default=None,
                   help="Max handbook pages to crawl")
    p.add_argument("--max-direction",  type=int, default=None,
                   help="Max direction pages to crawl")
    p.add_argument("--force-reindex",  action="store_true",
                   help="Delete existing chunks before re-ingesting")
    p.add_argument("--test-run",       action="store_true",
                   help="Quick test: 10 handbook + 5 direction pages")
    p.add_argument("--retry-failed",   action="store_true",
                   help="Re-process only URLs that failed in a previous run")
    return p.parse_args()


def _load_failed_urls() -> list[str]:
    """Read URLs from failed_chunks.log that need retry."""
    if not FAILED_LOG.exists():
        logger.info("No failed_chunks.log found — nothing to retry")
        return []
    urls = set()
    with open(FAILED_LOG) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    entry = json.loads(line)
                    urls.add(entry["url"])
                except (json.JSONDecodeError, KeyError):
                    pass
    logger.info(f"Found {len(urls)} URLs to retry from failed_chunks.log")
    return list(urls)


def _log_failed_chunk(url: str, chunk_index: int, error: str) -> None:
    """Append a failed chunk to the log file."""
    entry = {
        "timestamp":   datetime.utcnow().isoformat(),
        "url":         url,
        "chunk_index": chunk_index,
        "error":       error[:200],
    }
    with open(FAILED_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _clear_failed_log() -> None:
    """Clear the failed log after a successful retry run."""
    if FAILED_LOG.exists():
        FAILED_LOG.unlink()
        logger.info("Cleared failed_chunks.log (retry complete)")


def _save_progress(total_stored: int, total_api_calls: int) -> None:
    """Save running progress so you can see where you are if you re-run."""
    data = {
        "last_run":        datetime.utcnow().isoformat(),
        "total_stored":    total_stored,
        "total_api_calls": total_api_calls,
    }
    with open(PROGRESS_LOG, "w") as f:
        json.dump(data, f, indent=2)


async def main() -> None:
    args = _parse_args()

    # ── Validate env ──────────────────────────────────────────────────────────
    gemini_key    = os.getenv("GEMINI_API_KEY")
    supabase_url  = os.getenv("SUPABASE_URL")
    supabase_key  = os.getenv("SUPABASE_SERVICE_KEY")

    missing = [k for k, v in {
        "GEMINI_API_KEY":       gemini_key,
        "SUPABASE_URL":         supabase_url,
        "SUPABASE_SERVICE_KEY": supabase_key,
    }.items() if not v]

    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    configure(gemini_key)
    db = get_client(supabase_url, supabase_key)

    if args.test_run:
        args.max_handbook  = 10
        args.max_direction = 5
        logger.info("TEST RUN — limited to 10 handbook + 5 direction pages")

    # ── Step 1 · Crawl ────────────────────────────────────────────────────────
    _section("STEP 1 · CRAWL")

    if args.retry_failed:
        # Retry mode: load failed URLs from log, re-fetch their HTML
        failed_urls = _load_failed_urls()
        if not failed_urls:
            logger.info("Nothing to retry. Exiting.")
            return
        # We need to re-crawl these specific URLs
        # Split them by type based on URL pattern
        handbook_urls  = [u for u in failed_urls if "handbook.gitlab.com" in u]
        direction_urls = [u for u in failed_urls if "about.gitlab.com/direction" in u]
        from scraper.crawler import crawl_urls
        handbook_pages  = await crawl_urls(handbook_urls,  "handbook")
        direction_pages = await crawl_urls(direction_urls, "direction")
        all_pages = handbook_pages + direction_pages
        # Clear the failed log — we'll re-populate it with any new failures
        _clear_failed_log()
    else:
        all_pages = await get_all_pages(
            max_handbook  = args.max_handbook,
            max_direction = args.max_direction,
        )

    logger.info(f"Crawled {len(all_pages)} pages")

    # ── Step 2 · Parse ────────────────────────────────────────────────────────
    _section("STEP 2 · PARSE")
    parsed_pages: list[dict] = []
    skipped = 0

    for url, html, page_type in tqdm(all_pages, desc="Parsing", unit="page"):
        if not args.force_reindex and not args.retry_failed and url_is_indexed(db, url):
            skipped += 1
            continue
        if args.force_reindex:
            delete_chunks_for_url(db, url)

        parsed = parse_page(url, html, page_type)
        if parsed:
            parsed_pages.append(parsed)

    logger.info(
        f"Parsed {len(parsed_pages)} new pages | "
        f"Skipped {skipped} already-indexed pages"
    )

    if not parsed_pages:
        logger.info("Nothing new to index. Use --force-reindex to refresh.")
        return

    # ── Step 3 · Chunk ────────────────────────────────────────────────────────
    _section("STEP 3 · CHUNK")
    all_chunks: list[dict] = []
    for parsed in tqdm(parsed_pages, desc="Chunking", unit="page"):
        all_chunks.extend(create_chunks(parsed))
    logger.info(f"Created {len(all_chunks)} chunks from {len(parsed_pages)} pages")

    # Estimate API calls
    logger.info(
        f"\n{'─'*50}\n"
        f"  Chunks to embed : {len(all_chunks)}\n"
        f"  API calls needed: {len(all_chunks)}\n"
        f"  Daily free quota: 1,500\n"
        f"  Status          : {'OK — within quota' if len(all_chunks) <= 1500 else 'OVER QUOTA — will be rate limited, but will auto-retry'}\n"
        f"{'─'*50}"
    )

    # ── Step 4+5 · Embed and store immediately (interleaved) ──────────────────
    _section("STEP 4+5 · EMBED + STORE (interleaved — quota-safe)")
    logger.info(
        "Chunks are stored to Supabase immediately after each batch of 20 embeds.\n"
        "If quota is hit mid-run, all previously completed batches are already saved.\n"
        "Re-run with a new API key — already-indexed URLs will be skipped.\n"
    )

    total_stored    = 0
    total_api_calls = 0
    total_failed    = 0
    EMBED_BATCH     = 20

    for batch_start in range(0, len(all_chunks), EMBED_BATCH):
        batch       = all_chunks[batch_start : batch_start + EMBED_BATCH]
        batch_num   = batch_start // EMBED_BATCH + 1
        total_batches = (len(all_chunks) - 1) // EMBED_BATCH + 1

        logger.info(
            f"Batch {batch_num}/{total_batches} | "
            f"API calls so far: {total_api_calls} | "
            f"Stored so far: {total_stored}"
        )

        # Embed this batch — one API call per chunk
        embedded_batch = embed_chunks_with_progress(batch, batch_num, total_batches)

        total_api_calls += len(batch)   # each chunk = 1 call regardless of result

        # Count failures and log them
        failed_in_batch = [c for c in batch if "embedding" not in c]
        for chunk in failed_in_batch:
            total_failed += 1
            _log_failed_chunk(
                url         = chunk["source_url"],
                chunk_index = chunk.get("chunk_index", -1),
                error       = "embedding_failed",
            )

        # Store successfully embedded chunks to Supabase RIGHT NOW
        # This is the key fix — don't wait until the end
        if embedded_batch:
            stored = insert_chunks(db, embedded_batch, batch_size=50)
            total_stored += stored
            logger.info(
                f"  Stored {stored} chunks | "
                f"Running total: {total_stored} | "
                f"API calls used: {total_api_calls}/1500"
            )

        # Save progress file after every batch
        _save_progress(total_stored, total_api_calls)

    # ── Summary ───────────────────────────────────────────────────────────────
    _section("DONE")
    logger.info(f"Pages crawled   : {len(all_pages)}")
    logger.info(f"Pages parsed    : {len(parsed_pages)}")
    logger.info(f"Chunks created  : {len(all_chunks)}")
    logger.info(f"API calls used  : {total_api_calls}")
    logger.info(f"Chunks stored   : {total_stored}")
    logger.info(f"Chunks failed   : {total_failed}")

    if total_failed > 0:
        logger.warning(
            f"\n{total_failed} chunks failed to embed.\n"
            f"Failed chunks logged to: {FAILED_LOG}\n"
            f"To retry: python -m scripts.ingest --retry-failed"
        )
    else:
        logger.info("All chunks embedded and stored successfully.")

    if FAILED_LOG.exists() and total_failed == 0:
        _clear_failed_log()

    logger.info(f"\nProgress saved to: {PROGRESS_LOG}")
    logger.info("Your Supabase DB is ready for Phase 2 (FastAPI backend).")


def _section(title: str) -> None:
    logger.info("─" * 50)
    logger.info(title)
    logger.info("─" * 50)


if __name__ == "__main__":
    asyncio.run(main())