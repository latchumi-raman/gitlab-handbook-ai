"""
Parser: extracts clean, structured text from raw HTML pages.
Handles both handbook.gitlab.com and about.gitlab.com layouts.
"""

import re
import logging
from bs4 import BeautifulSoup, NavigableString, Tag

logger = logging.getLogger(__name__)

# Tags to completely remove before extracting text
_REMOVE_TAGS = {
    "script", "style", "nav", "header", "footer", "aside",
    "noscript", "iframe", "form", "button", "meta", "link",
    "svg", "canvas", "figure",               # decorative
}

# CSS selectors for site-specific chrome to remove
_REMOVE_SELECTORS = [
    ".breadcrumb", ".breadcrumbs",
    ".pagination",
    ".edit-this-page", ".edit-page",
    "#table-of-contents", ".toc", ".sidebar-toc",
    '[class*="sidebar"]',
    '[class*="cookie"]',
    '[class*="banner"]',
    '[class*="announcement"]',
    '[class*="newsletter"]',
    ".feedback",
    "#feedback",
]

# Selectors tried in order to find the main content block
_MAIN_CONTENT_SELECTORS = [
    "main",
    "article",
    '[role="main"]',
    ".content",
    ".main-content",
    "#content",
    ".handbook-content",
    ".documentation",
    ".markdown-content",
]


def _clean_whitespace(text: str) -> str:
    """Collapse runs of whitespace, trim each line, drop blank lines."""
    lines = []
    for line in text.splitlines():
        stripped = re.sub(r"[ \t]+", " ", line).strip()
        if stripped:
            lines.append(stripped)
    # Reduce 3+ consecutive blank separators to 2
    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _extract_text(element: Tag) -> str:
    """
    Recursively extract text from a BeautifulSoup element,
    preserving headings, lists, paragraphs and code blocks as
    markdown-flavoured plain text.
    """
    if isinstance(element, NavigableString):
        return str(element)

    name = element.name
    if not name or name in _REMOVE_TAGS:
        return ""

    parts: list[str] = []

    # Headings
    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        level = int(name[1])
        text = element.get_text(" ", strip=True)
        if text:
            parts.append(f"\n{'#' * level} {text}\n")
        return "".join(parts)

    # Paragraphs
    if name == "p":
        text = element.get_text(" ", strip=True)
        if text:
            parts.append(f"\n{text}\n")
        return "".join(parts)

    # Code / pre
    if name in ("code", "pre"):
        code = element.get_text(strip=True)
        if code:
            parts.append(f"\n```\n{code}\n```\n")
        return "".join(parts)

    # Lists
    if name in ("ul", "ol"):
        for li in element.find_all("li", recursive=False):
            item_text = li.get_text(" ", strip=True)
            if item_text:
                parts.append(f"• {item_text}")
        parts.append("\n")
        return "\n".join(parts)

    # Tables — flatten to pipe-separated rows
    if name == "table":
        for row in element.find_all("tr"):
            cells = [
                cell.get_text(" ", strip=True)
                for cell in row.find_all(["td", "th"])
            ]
            if any(cells):
                parts.append(" | ".join(cells))
        parts.append("\n")
        return "\n".join(parts)

    # Horizontal rules / dividers — act as section separator
    if name == "hr":
        return "\n"

    # Everything else: recurse into children
    for child in element.children:
        child_text = _extract_text(child)
        if child_text.strip():
            parts.append(child_text)

    return " ".join(p for p in parts if p.strip())


def parse_page(url: str, html: str, page_type: str) -> dict | None:
    """
    Parse a raw HTML page and return a structured dict:
        {url, page_type, title, content}

    Returns None if the page is too short or fails to parse.
    """
    try:
        soup = BeautifulSoup(html, "lxml")

        # ── Remove unwanted chrome ───────────────────────
        for tag_name in _REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for selector in _REMOVE_SELECTORS:
            for elem in soup.select(selector):
                elem.decompose()

        # ── Extract title ────────────────────────────────
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        elif soup.find("title"):
            raw = soup.find("title").get_text(strip=True)
            # Strip " | GitLab" suffix common on these pages
            title = re.sub(r"\s*[|\-–—]\s*GitLab.*$", "", raw, flags=re.IGNORECASE).strip()

        # ── Find main content block ──────────────────────
        content_block = None
        for selector in _MAIN_CONTENT_SELECTORS:
            content_block = soup.select_one(selector)
            if content_block:
                break

        if not content_block:
            content_block = soup.find("body")

        if not content_block:
            logger.warning(f"No body found for {url}")
            return None

        # ── Extract and clean text ───────────────────────
        raw_text = _extract_text(content_block)
        content = _clean_whitespace(raw_text)

        # Prepend title so every chunk carries context about the page
        if title and not content.startswith("#"):
            content = f"# {title}\n\n{content}"

        # Skip error pages, very short pages, or 404s
        if len(content) < 200:
            logger.debug(f"Skipping {url} — too short ({len(content)} chars)")
            return None

        return {
            "url":       url,
            "page_type": page_type,
            "title":     title,
            "content":   content,
        }

    except Exception as e:
        logger.error(f"parse_page failed for {url}: {type(e).__name__}: {e}")
        return None