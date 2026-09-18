"""
app.schemas.chatbot — ClassPulse AI Assistant API Request & Response Schemas

The chatbot is stateless on the backend: instead of a server-side session
store, each response returns a small `context` object which the frontend
echoes back on the next turn. This lets the assistant support basic
multi-turn conversation ("Only Grade 10." / "Which of those...?") without
any new infrastructure, while authorization is always re-derived fresh from
the caller's Firebase-verified identity on every single request — the
client-supplied context can narrow a query, but it can never widen access
beyond what `resolve_scope()` grants the authenticated user.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatContext(BaseModel):
    """Carries the resolved filters/results from the previous turn.

    This is opaque state from the frontend's point of view — it should just
    store whatever the last response returned and send it back unmodified
    unless the user explicitly starts a new conversation.
    """

    categories: List[str] = Field(default_factory=list)

    attendance_threshold: Optional[float] = None
    attendance_cmp: Optional[str] = None  # "lt" | "gt"
    attendance_trend: Optional[str] = None  # "DECLINING" | "IMPROVING"

    homework_filter: Optional[str] = None  # "NOT_COMPLETED" | "LATE" | "POOR"
    homework_trend: Optional[str] = None  # "DECLINING" | "IMPROVING"

    academic_trend: Optional[str] = None  # "DECLINING" | "IMPROVING"
    academic_lowest: bool = False

    risk_level: Optional[str] = None  # "HIGH" | "MEDIUM" | "LOW"
    risk_level_exclude: Optional[str] = None
    risk_trend: Optional[str] = None  # "WORSENING" | "IMPROVING"

    intervention_filter: Optional[str] = None  # "NONE" | "ONGOING" | "OVERDUE" | "COMPLETED" | "ANY"

    grade: Optional[str] = None
    section: Optional[str] = None
    class_id: Optional[str] = None

    last_student_ids: List[str] = Field(default_factory=list)
    last_student_id: Optional[str] = None

    wants_school_wide: bool = False


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    context: Optional[ChatContext] = None


class ChatMessageResponse(BaseModel):
    reply: str
    data: Optional[Any] = None
    context: ChatContext
    suggestions: List[str] = Field(default_factory=list)


class ChatCapabilitiesResponse(BaseModel):
    """Describes what the authenticated user's chatbot can do — used by the
    frontend to render a helpful empty-state / onboarding hint, and to decide
    whether the floating button should render at all (backend is still the
    authority on actual data access, per-request)."""

    role: str
    is_principal: bool
    school_id: Optional[str] = None
    authorized_class_count: int = 0
    example_questions: List[str] = Field(default_factory=list)
