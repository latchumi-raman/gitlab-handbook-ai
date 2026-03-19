"""
Crawler: fetches all pages from GitLab Handbook sitemap
and GitLab Direction pages. Respects rate limits.
"""

import asyncio
import httpx
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

HANDBOOK_SITEMAP  = "https://handbook.gitlab.com/sitemap.xml"
DIRECTION_BASE    = "https://about.gitlab.com/direction/"
REQUEST_DELAY     = 0.4   # seconds between requests — be polite
REQUEST_TIMEOUT   = 30.0

HEADERS = {
    "User-Agent": (
        "GitLabHandbookBot/1.0 "
        "(Educational AI chatbot; github.com/YOUR_USERNAME/gitlab-handbook-ai)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch a URL and return HTML text, or None on failure."""
    try:
        await asyncio.sleep(REQUEST_DELAY)
        resp = await client.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}")
        return None
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {type(e).__name__}: {e}")
        return None


async def _get_handbook_urls(client: httpx.AsyncClient) -> list[str]:
    """
    Parse the handbook sitemap (may be a sitemap index pointing to
    child sitemaps, or a direct urlset). Returns all page URLs.
    """
    logger.info("Fetching handbook sitemap ...")
    xml_text = await _fetch(client, HANDBOOK_SITEMAP)
    if not xml_text:
        logger.error("Could not fetch handbook sitemap — check your internet connection")
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"Sitemap XML parse error: {e}")
        return []

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls: list[str] = []

    # Check if it's a sitemap index (points to other sitemaps)
    child_sitemaps = root.findall(".//sm:sitemap/sm:loc", ns)
    if child_sitemaps:
        logger.info(f"Sitemap index found — expanding {len(child_sitemaps)} child sitemaps")
        for loc_elem in child_sitemaps:
            child_url = loc_elem.text.strip()
            child_xml = await _fetch(client, child_url)
            if child_xml:
                try:
                    child_root = ET.fromstring(child_xml)
                    for url_elem in child_root.findall(".//sm:url/sm:loc", ns):
                        urls.append(url_elem.text.strip())
                except ET.ParseError:
                    logger.warning(f"Could not parse child sitemap: {child_url}")
    else:
        # Direct urlset
        for url_elem in root.findall(".//sm:url/sm:loc", ns):
            urls.append(url_elem.text.strip())

    logger.info(f"Handbook: found {len(urls)} URLs in sitemap")
    return urls


async def _get_direction_urls(client: httpx.AsyncClient) -> list[str]:
    """
    Scrape the main direction page and discover all sub-page links
    within about.gitlab.com/direction/
    """
    logger.info("Fetching direction page links ...")
    html = await _fetch(client, DIRECTION_BASE)
    if not html:
        logger.warning("Could not fetch direction base page — using just the base URL")
        return [DIRECTION_BASE]

    soup = BeautifulSoup(html, "lxml")
    found: set[str] = {DIRECTION_BASE}

    for a_tag in soup.find_all("a", href=True):
        href = str(a_tag["href"]).strip()
        if not href or href.startswith("#") or href.startswith("mailto:"):
            continue

        full_url = urljoin(DIRECTION_BASE, href)
        parsed = urlparse(full_url)

        # Only keep direction sub-pages from about.gitlab.com
        if (
            parsed.netloc == "about.gitlab.com"
            and parsed.path.startswith("/direction/")
            and not full_url.endswith(".pdf")
            and not full_url.endswith(".zip")
        ):
            # Strip query params and fragments
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if not clean.endswith("/"):
                clean += "/"
            found.add(clean)

    logger.info(f"Direction: found {len(found)} URLs")
    return list(found)


async def crawl_urls(
    urls: list[str],
    page_type: str,
) -> list[tuple[str, str, str]]:
    """
    Crawl a list of URLs concurrently (with a small semaphore to avoid
    hammering the server). Returns list of (url, html, page_type).
    """
    results: list[tuple[str, str, str]] = []
    sem = asyncio.Semaphore(3)   # max 3 concurrent requests

    async def _bounded_fetch(client, url):
        async with sem:
            html = await _fetch(client, url)
            if html:
                results.append((url, html, page_type))

    async with httpx.AsyncClient() as client:
        tasks = [_bounded_fetch(client, url) for url in urls]
        total = len(tasks)
        for i, coro in enumerate(asyncio.as_completed(tasks), 1):
            await coro
            if i % 20 == 0 or i == total:
                logger.info(f"  {page_type}: {i}/{total} pages fetched")

    return results


async def get_all_pages(
    max_handbook: int | None = None,
    max_direction: int | None = None,
) -> list[tuple[str, str, str]]:
    """
    Main entry point for the crawler.
    Returns list of (url, html, page_type) tuples.
    page_type is either 'handbook' or 'direction'.
    """
    async with httpx.AsyncClient() as client:
        handbook_urls  = await _get_handbook_urls(client)
        direction_urls = await _get_direction_urls(client)

    if max_handbook is not None:
        handbook_urls = handbook_urls[:max_handbook]
        logger.info(f"Handbook limited to {max_handbook} pages")

    if max_direction is not None:
        direction_urls = direction_urls[:max_direction]
        logger.info(f"Direction limited to {max_direction} pages")

    logger.info(f"Crawling {len(handbook_urls)} handbook + {len(direction_urls)} direction pages ...")

    handbook_pages  = await crawl_urls(handbook_urls,  "handbook")
    direction_pages = await crawl_urls(direction_urls, "direction")

    all_pages = handbook_pages + direction_pages
    logger.info(f"Total fetched: {len(all_pages)} pages")
    return all_pages