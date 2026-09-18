"""
app.services.chatbot.responder — Natural-Language Response Generation

Turns the structured, already-authorized data produced by tools.py into a
concise English reply. This is fully deterministic template logic by
default, so the assistant works with zero external dependencies.

If `settings.chatbot_llm_enabled` is True (an ANTHROPIC_API_KEY is
configured), `polish()` makes one best-effort call to the Anthropic Messages
API to rephrase the already-computed template reply more conversationally.
The model is given ONLY the template reply and the structured data behind it
— never raw credentials, tokens, or unfiltered database access — and is
explicitly instructed not to introduce any numbers that aren't already
present in the data. Any failure (missing key, timeout, network error) falls
back to the deterministic template reply silently, so the chatbot is never
dependent on the LLM being reachable.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_LLM_TIMEOUT_SECONDS = 6.0

_SYSTEM_PROMPT = (
    "You are the ClassPulse Assistant, a school-analytics chat helper for teachers and "
    "principals. You will be given a JSON object with already-retrieved, already-authorized "
    "ClassPulse data, plus a draft reply that already states the correct facts. "
    "Rewrite the draft reply so it reads naturally and concisely (2-5 sentences, plain text, "
    "no markdown headings). "
    "Rules: never invent a number, name, or fact that is not present in the JSON data or the "
    "draft reply; never mention students, classes, or figures that are not in the JSON; keep it "
    "factual and professional; do not apologize or add disclaimers; do not mention that you are "
    "an AI or that a draft was rewritten."
)


def polish(draft_reply: str, structured_data: Optional[Any]) -> str:
    """Best-effort LLM rephrasing of an already-correct template reply."""
    settings = get_settings()
    if not settings.chatbot_llm_enabled:
        return draft_reply

    try:
        import httpx

        payload = {
            "model": settings.CHATBOT_LLM_MODEL,
            "max_tokens": 400,
            "system": _SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(
                        {"draft_reply": draft_reply, "data": _safe_truncate(structured_data)},
                        default=str,
                    ),
                }
            ],
        }
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=_LLM_TIMEOUT_SECONDS) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            resp.raise_for_status()
            body = resp.json()
            text_parts = [block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"]
            polished = "".join(text_parts).strip()
            return polished or draft_reply
    except Exception as exc:  # noqa: BLE001 — this is a best-effort enhancement only
        logger.warning("Chatbot LLM phrasing skipped (falling back to template reply): %s", type(exc).__name__)
        return draft_reply


def _safe_truncate(data: Optional[Any], max_items: int = 25) -> Any:
    """Keep the payload sent to the LLM small and bounded."""
    if isinstance(data, list):
        return data[:max_items]
    if isinstance(data, dict):
        out = {}
        for k, v in data.items():
            if isinstance(v, list):
                out[k] = v[:max_items]
            else:
                out[k] = v
        return out
    return data


# ---------------------------------------------------------------------------
# Template building blocks
# ---------------------------------------------------------------------------

NO_DATA_MESSAGE = "I couldn't find sufficient data in ClassPulse to answer that."
OUT_OF_SCOPE_MESSAGE = (
    "I can help you analyze authorized ClassPulse student, attendance, academic, risk, "
    "and intervention information. I'm not able to help with that."
)
HELP_MESSAGE = (
    "I'm the ClassPulse Assistant. Ask me things like: \"Who has attendance below 75%?\", "
    "\"Which students are currently high risk?\", \"Who has not completed homework?\", or "
    "\"Give me a summary of <student name>.\" I only answer using verified ClassPulse data "
    "you're authorized to see."
)
SCOPE_DENIED_MESSAGE = "I can only provide information for the students/classes you are authorized to access."


def name_list(items: List[Dict[str, Any]], key: str = "student_name", limit: int = 10) -> str:
    names = [i.get(key, "?") for i in items[:limit]]
    text = ", ".join(names)
    if len(items) > limit:
        text += f", and {len(items) - limit} more"
    return text


def scope_phrase(grade: Optional[str], section: Optional[str], class_name: Optional[str], scope_label: str) -> str:
    if class_name:
        return f" in {class_name}"
    if grade and section:
        return f" in Grade {grade} Section {section}"
    if grade:
        return f" in Grade {grade}"
    return f" in {scope_label}"
