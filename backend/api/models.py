"""
All Pydantic schemas for request/response validation.
These are the contracts between the React frontend and FastAPI backend.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ── Shared types ─────────────────────────────────────────────────────────────

class PageType(str, Enum):
    handbook  = "handbook"
    direction = "direction"
    both      = "both"


class SourceChunk(BaseModel):
    """A single retrieved context chunk — sent to the frontend for transparency."""
    id:            int
    content:       str
    source_url:    str
    page_type:     str
    page_title:    str
    section_title: str
    similarity:    float = Field(ge=0.0, le=1.0)


# ── Chat ─────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    """A single turn in a conversation."""
    role:    str   # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Sent by the React frontend on every message."""
    query:      str = Field(
        min_length=1,
        max_length=2000,
        description="The user's question",
    )
    session_id: str = Field(
        description="UUID generated once per browser session — persists history",
    )
    history: list[Message] = Field(
        default=[],
        max_length=20,          # keep context window manageable
        description="Previous turns in this conversation",
    )
    page_type_filter: PageType = Field(
        default=PageType.both,
        description="Restrict search to handbook, direction, or both",
    )
    match_count: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of chunks to retrieve",
    )


class ChatResponse(BaseModel):
    """
    Returned as the final JSON object after streaming completes.
    The stream sends text tokens; this is the metadata envelope.
    """
    answer:          str
    sources:         list[SourceChunk]
    confidence:      float = Field(ge=0.0, le=1.0)
    follow_ups:      list[str]
    session_id:      str
    guardrail_triggered: bool = False
    guardrail_reason:    Optional[str] = None


# ── Feedback ─────────────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    session_id: str
    query:      str
    response:   str
    rating:     int  = Field(..., description="1 = helpful, -1 = not helpful")
    comment:    str  = Field(default="", max_length=1000)


class FeedbackResponse(BaseModel):
    success: bool
    message: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:        str
    version:       str
    db_connected:  bool
    chunks_indexed: int


class PingResponse(BaseModel):
    status: str = "alive"