"""
Guardrails service — keeps the chatbot focused on GitLab content.

Strategy: lightweight keyword + pattern check first (fast, no API call).
If the query passes that but still seems off-topic after retrieval,
the RAG service will catch it via low similarity scores.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ── Allow-listed topics ───────────────────────────────────────────────────────
# Anything clearly about GitLab or the handbook passes immediately.

GITLAB_KEYWORDS = {
    # Company / product
    "gitlab", "handbook", "direction", "strategy", "roadmap",
    # Values / culture
    "credit", "collaboration", "results", "efficiency", "diversity",
    "iteration", "transparency", "values", "culture", "mission",
    # Work topics
    "hiring", "onboarding", "offboarding", "career", "promotion",
    "performance", "review", "okr", "goal", "kpi", "metric",
    "remote", "async", "asynchronous", "all-remote", "distributed",
    "compensation", "benefits", "equity", "salary",
    # Engineering
    "devops", "devsecops", "ci/cd", "pipeline", "deployment",
    "kubernetes", "docker", "kubernetes", "observability",
    "security", "compliance", "soc2", "gdpr",
    # Product
    "issue", "merge request", "mr", "milestone", "epic", "label",
    "sprint", "agile", "scrum", "kanban",
    # People
    "manager", "ic", "individual contributor", "vp", "cto", "ceo",
    "people ops", "talent", "recruiter",
    # General work
    "meeting", "1:1", "team", "department", "division",
    "communication", "feedback", "recognition",
}

# ── Block-listed patterns ─────────────────────────────────────────────────────
# Clearly off-topic requests that should be politely declined.

BLOCKED_PATTERNS = [
    # Competitor info requests
    r"\b(github|bitbucket|jira|confluence|azure devops|jenkins)\b.*\b(vs|versus|compare|better|worse)\b",
    # Personal tasks unrelated to work
    r"\b(write (me )?(a |an )?(poem|song|story|essay|joke|recipe))\b",
    r"\b(homework|assignment|essay for)\b",
    # Financial / investment advice
    r"\b(stock|share price|invest|buy|sell|trade)\b.*\b(gitlab|gtlb)\b",
    # Harmful content
    r"\b(hack|exploit|vulnerability|bypass|injection|xss|sql injection)\b",
    # Completely unrelated domains
    r"\b(weather|sports|movie|celebrity|recipe|cook|food|game|fifa|nfl|cricket)\b",
    r"\b(medical advice|diagnos|prescription|symptom|cure)\b",
    r"\b(politics|election|vote|democrat|republican|president)\b",
]

# ── Compiled patterns (do this once at import time) ───────────────────────────
_COMPILED_BLOCKS = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

# ── Response templates ────────────────────────────────────────────────────────
OFF_TOPIC_RESPONSE = (
    "I'm GitLab's Handbook AI, so I can only answer questions about GitLab's "
    "internal handbook, company direction, values, processes, and ways of working. "
    "\n\nYour question doesn't appear to be related to GitLab. "
    "Try asking about topics like:\n"
    "- GitLab's CREDIT values\n"
    "- Hiring and onboarding processes\n"
    "- Engineering culture and practices\n"
    "- Remote work policies\n"
    "- Career development at GitLab"
)

LOW_CONFIDENCE_ADDENDUM = (
    "\n\n---\n"
    "*Note: Due to low confidence, I couldn't find highly relevant content in the GitLab handbook for this specific question "
    "for this specific question. The answer above is based on the closest "
    "available content — please verify by checking the linked sources directly.*"
)


def check_guardrails(query: str) -> tuple[bool, str | None]:
    """
    Returns (is_blocked, reason_or_None).

    Call this BEFORE embedding/retrieval to save API calls.
    Fast: keyword + regex only, no LLM call required.
    """
    query_lower = query.lower().strip()

    # 1. Empty or trivially short query
    if len(query_lower) < 3:
        return True, "Query too short"

    # 2. Check explicit block patterns first
    for pattern in _COMPILED_BLOCKS:
        if pattern.search(query_lower):
            logger.info(f"Guardrail blocked query (pattern match): '{query[:80]}...'")
            return True, "off_topic_pattern"

    # 3. Very short queries with no GitLab keywords — flag for low-confidence
    #    (don't hard-block, let retrieval try — handled by confidence score)
    words = set(re.findall(r"\b\w+\b", query_lower))
    has_gitlab_keyword = bool(words & GITLAB_KEYWORDS)

    if not has_gitlab_keyword and len(query_lower) < 80:
        # Short query with no recognisable GitLab terms — soft flag
        # We'll still run RAG but flag it so the UI can show a warning
        logger.debug(f"Guardrail soft flag (no keywords): '{query[:80]}'")
        # Don't block — return not blocked, let confidence score handle it
        return False, None

    return False, None


def check_confidence(confidence: float, sources: list) -> tuple[bool, str | None]:
    """
    Post-retrieval confidence gate.
    Returns (should_add_low_confidence_note, note_text).
    """
    if confidence < 0.55 or len(sources) == 0:
        return True, LOW_CONFIDENCE_ADDENDUM
    return False, None


def get_off_topic_response() -> str:
    return OFF_TOPIC_RESPONSE