"""
app.services.chatbot.nlu — Intent / Query Understanding

Deterministic, rule-based natural-language understanding for the ClassPulse
Assistant. This module ONLY extracts intent and filters from text — it never
touches Firestore, never sees credentials, and never makes an authorization
decision. That keeps "understanding the question" fully separate from
"deciding what the user is allowed to see" (see scope.py) and "fetching the
answer" (see tools.py), exactly as required by section 15 of the chatbot
spec: deterministic calculations and data access must never be delegated to
a language model.

Why rule-based instead of calling an LLM for intent extraction? Tool
selection and filter extraction are deterministic, auditable decisions with
real access-control consequences — a misread intent here could ask a tool
for data outside the caller's scope. Keeping this step as plain, testable
Python means every question in the product spec resolves to the same
filters every time, with zero dependency on an external API key. The one
place an LLM *is* optionally used is `responder.py`, purely to phrase the
sentence around numbers this module and tools.py already computed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Set

from app.schemas.chatbot import ChatContext

GREETING_WORDS = {"hi", "hello", "hey", "hiya", "yo", "good morning", "good afternoon", "good evening"}

HELP_PHRASES = ("what can you do", "help me", "how does this work", "who are you", "what are you")

FOLLOWUP_LEAD_WORDS = (
    "only", "just", "and ", "what about", "of those", "of them", "among them",
    "which of", "now show", "narrow", "filter to", "also show",
)

RESET_PHRASES = ("start over", "new question", "reset", "clear filters", "forget that")

DECLINE_WORDS = {"declining", "dropping", "decreasing", "worsening", "falling", "fallen", "dropped", "worse", "down"}
IMPROVE_WORDS = {"improving", "increasing", "rising", "risen", "better", "improved", "up"}
LOW_WORDS = {"low", "poor", "lowest", "worst"}

CATEGORY_KEYWORDS = {
    "attendance": ("attendance", "absent", "absentee", "absenteeism", "present", "absences"),
    "homework": ("homework", "assignment completion", "submit homework", "submitting homework"),
    "academic": ("test score", "test scores", "marks", "exam", "academic", "performance", "grade average", "grades"),
    "risk": ("risk",),
    "intervention": ("intervention",),
    "summary": ("summary", "profile", "overview", "360", "complete summary", "full picture", "tell me about"),
}

# Grade like "grade 10" / "class 10" / "10th grade"
_GRADE_RE = re.compile(r"\b(?:grade|class|standard)\s*[- ]?(\d{1,2})\b|\b(\d{1,2})(?:th|st|nd|rd)\s*grade\b", re.I)
# Combined grade+section like "10a" / "10-a" / "10 a" / "class 10a"
_GRADE_SECTION_RE = re.compile(r"\b(\d{1,2})\s*[- ]?([a-dA-D])\b")
_SECTION_RE = re.compile(r"\bsection\s+([a-dA-D])\b", re.I)
_PERCENT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
_BELOW_WORDS = ("below", "under", "less than", "lower than", "<")
_ABOVE_WORDS = ("above", "over", "more than", "greater than", "higher than", ">")

_QUOTED_NAME_RE = re.compile(r'"([^"]{2,60})"|\'([^\']{2,60})\'')
_PROPER_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\b")
_STUDENT_CODE_RE = re.compile(r"\b([A-Z]{2,6}\d{2,6})\b")

SCHOOL_WIDE_PHRASES = (
    "entire school", "whole school", "across the school", "school-wide", "school wide",
    "all students in the school", "the entire student body",
)
OWN_SCOPE_PHRASES = ("my class", "my classes", "my students", "students i teach")

# Words that don't indicate a real student name even though they're Title-cased
# (mostly sentence-leading question words and domain nouns from the product's
# own example questions — see docs/CHATBOT.md for the NLU's known limits).
_NAME_STOPWORDS = {
    "Show", "Which", "Who", "What", "Give", "Find", "List", "Tell", "Does", "Do",
    "Is", "Are", "How", "Why", "When", "Where", "Can", "Grade", "Class", "Section",
    "The", "This", "That", "Those", "Them", "Students", "Student", "High", "Low",
    "Attendance", "Homework", "Academic", "Risk", "Test", "Tests", "Complete",
    "Full", "My", "Our", "All", "Currently", "Only", "Just",
}


@dataclass
class ParsedQuery:
    raw_text: str
    categories: Set[str] = field(default_factory=set)

    attendance_threshold: Optional[float] = None
    attendance_cmp: Optional[str] = None  # "lt" | "gt"
    attendance_trend: Optional[str] = None  # "DECLINING" | "IMPROVING"
    wants_count_only: bool = False

    homework_filter: Optional[str] = None  # NOT_COMPLETED | LATE | POOR
    homework_trend: Optional[str] = None  # DECLINING | IMPROVING

    academic_trend: Optional[str] = None
    academic_lowest: bool = False

    risk_level: Optional[str] = None
    risk_level_exclude: Optional[str] = None
    risk_trend: Optional[str] = None  # WORSENING | IMPROVING
    risk_why: bool = False

    intervention_filter: Optional[str] = None  # NONE | ONGOING | OVERDUE | COMPLETED | ANY
    has_prior_intervention: Optional[bool] = None

    grade: Optional[str] = None
    section: Optional[str] = None

    student_query: Optional[str] = None
    refers_to_last_student: bool = False

    wants_school_wide: bool = False
    is_followup: bool = False
    is_reset: bool = False
    is_greeting: bool = False
    is_help: bool = False
    is_out_of_scope: bool = False

    restrict_to_previous_results: bool = False

    wants_breakdown_by_class: bool = False
    wants_class_comparison: bool = False
    class_comparison_metric: Optional[str] = None  # "attendance" | "homework" | "academic" | "risk_high"
    class_comparison_direction: Optional[str] = None  # "max" | "min"


def _find_comparison(lower: str) -> Optional[str]:
    if any(w in lower for w in _BELOW_WORDS):
        return "lt"
    if any(w in lower for w in _ABOVE_WORDS):
        return "gt"
    return None


def _extract_grade_section(lower: str, original: str):
    grade = None
    section = None

    m = _GRADE_SECTION_RE.search(original)
    if m:
        grade, section = m.group(1), m.group(2).upper()
        return grade, section

    m = _GRADE_RE.search(lower)
    if m:
        grade = m.group(1) or m.group(2)

    m = _SECTION_RE.search(lower)
    if m:
        section = m.group(1).upper()

    return grade, section


def _extract_student_reference(original: str, lower: str) -> Optional[str]:
    m = _QUOTED_NAME_RE.search(original)
    if m:
        return (m.group(1) or m.group(2)).strip()

    m = _STUDENT_CODE_RE.search(original)
    if m:
        return m.group(1)

    # Scan every Title-Case run in the sentence (not just the first — a
    # sentence-leading question word like "Give"/"Which" is Title-Case too,
    # but isn't a student name) and return the first one that isn't entirely
    # made of known non-name words (e.g. "Grade Ten").
    for m in _PROPER_NAME_RE.finditer(original):
        candidate = m.group(1)
        words = candidate.split()
        if all(w in _NAME_STOPWORDS for w in words):
            continue
        return candidate

    return None


def parse_message(message: str, previous_context: Optional[ChatContext] = None) -> ParsedQuery:
    original = (message or "").strip()
    lower = original.lower()
    parsed = ParsedQuery(raw_text=original)

    if not lower:
        parsed.is_out_of_scope = True
        return parsed

    if lower in GREETING_WORDS or any(lower.startswith(g) for g in GREETING_WORDS):
        parsed.is_greeting = True
        return parsed

    if any(p in lower for p in HELP_PHRASES):
        parsed.is_help = True
        return parsed

    if any(p in lower for p in RESET_PHRASES):
        parsed.is_reset = True
        return parsed

    # --- category detection -------------------------------------------------
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in lower for k in keywords):
            parsed.categories.add(category)

    is_followup_phrase = any(lower.startswith(w) or f" {w}" in f" {lower}" for w in FOLLOWUP_LEAD_WORDS)
    very_short = len(lower.split()) <= 6

    if not parsed.categories and previous_context and previous_context.categories and (is_followup_phrase or very_short):
        parsed.is_followup = True
        parsed.categories = set(previous_context.categories)
    elif parsed.categories and previous_context and previous_context.categories and is_followup_phrase:
        # Adds a category on top of a previous one ("Which of those have attendance below 75%?")
        parsed.is_followup = True
        parsed.categories |= set(previous_context.categories)

    if any(p in lower for p in ("of those", "of them", "among them", "which of those", "which of them")):
        parsed.restrict_to_previous_results = True
        parsed.is_followup = True

    if not parsed.categories and not parsed.is_followup:
        parsed.is_out_of_scope = True
        return parsed

    # --- school-wide / own-scope phrases -------------------------------------
    if any(p in lower for p in SCHOOL_WIDE_PHRASES):
        parsed.wants_school_wide = True
    if any(p in lower for p in OWN_SCOPE_PHRASES):
        parsed.wants_school_wide = False

    # --- grade / section ------------------------------------------------------
    grade, section = _extract_grade_section(lower, original)
    parsed.grade = grade
    parsed.section = section

    # --- attendance -------------------------------------------------------
    if "attendance" in parsed.categories:
        pct_match = _PERCENT_RE.search(lower)
        if pct_match:
            parsed.attendance_threshold = float(pct_match.group(1))
            parsed.attendance_cmp = _find_comparison(lower) or "lt"
        elif any(w in lower for w in LOW_WORDS):
            parsed.attendance_threshold = 75.0
            parsed.attendance_cmp = "lt"

        if any(w in lower for w in DECLINE_WORDS):
            parsed.attendance_trend = "DECLINING"
        elif any(w in lower for w in IMPROVE_WORDS):
            parsed.attendance_trend = "IMPROVING"

        if lower.startswith("how many") and ("absent" in lower or "attendance" in lower):
            parsed.wants_count_only = True

    # --- homework -----------------------------------------------------------
    if "homework" in parsed.categories:
        if any(p in lower for p in ("not completed", "haven't completed", "have not completed", "didn't complete", "did not complete", "incomplete", "not done", "not turned in", "not submitted")):
            parsed.homework_filter = "NOT_COMPLETED"
        elif "late" in lower:
            parsed.homework_filter = "LATE"
        elif any(w in lower for w in LOW_WORDS):
            parsed.homework_filter = "POOR"
        elif "frequently" in lower or "often" in lower:
            parsed.homework_filter = parsed.homework_filter or "LATE"

        if any(w in lower for w in DECLINE_WORDS):
            parsed.homework_trend = "DECLINING"
        elif any(w in lower for w in IMPROVE_WORDS):
            parsed.homework_trend = "IMPROVING"

    # --- academic performance ------------------------------------------------
    if "academic" in parsed.categories:
        if any(w in lower for w in DECLINE_WORDS) or "dropped" in lower or "drop in" in lower:
            parsed.academic_trend = "DECLINING"
        elif any(w in lower for w in IMPROVE_WORDS):
            parsed.academic_trend = "IMPROVING"
        if any(p in lower for p in ("lowest", "lowest-performing", "lowest performing", "worst")):
            parsed.academic_lowest = True

    # --- risk -----------------------------------------------------------------
    if "risk" in parsed.categories:
        if "high" in lower or "high-risk" in lower:
            parsed.risk_level = "HIGH"
        elif "medium" in lower:
            parsed.risk_level = "MEDIUM"
        elif "low risk" in lower or "low-risk" in lower:
            parsed.risk_level = "LOW"

        if "not high risk" in lower or "not currently high risk" in lower or ("not " in lower and "high risk" in lower):
            parsed.risk_level_exclude = "HIGH"
            parsed.risk_level = None

        if any(w in lower for w in DECLINE_WORDS) or any(w in lower for w in IMPROVE_WORDS):
            # For risk specifically, "increasing"/"rising" means getting WORSE.
            if any(w in lower for w in IMPROVE_WORDS) and "risk" in lower:
                parsed.risk_trend = "WORSENING"
            elif any(w in lower for w in DECLINE_WORDS) and "risk" in lower:
                parsed.risk_trend = "IMPROVING"

        if lower.startswith("why"):
            parsed.risk_why = True

    # --- interventions ---------------------------------------------------------
    if "intervention" in parsed.categories:
        if any(p in lower for p in ("no intervention", "without intervention", "not have an intervention", "have no intervention")):
            parsed.intervention_filter = "NONE"
        elif "overdue" in lower:
            parsed.intervention_filter = "OVERDUE"
        elif any(p in lower for p in ("ongoing", "in progress", "in-progress", "currently active")):
            parsed.intervention_filter = "ONGOING"
        elif "completed" in lower or "after intervention" in lower or "remain high risk" in lower:
            parsed.intervention_filter = "COMPLETED"
            if "remain high risk" in lower or "still high risk" in lower:
                parsed.risk_level = "HIGH"
                parsed.has_prior_intervention = True

    # --- per-class breakdown / comparison ("by class", "which class has...") --
    if any(p in lower for p in ("by class", "each class", "per class", "by section")):
        parsed.wants_breakdown_by_class = True

    if "which class" in lower or "which section" in lower:
        parsed.wants_class_comparison = True
        if "absenteeism" in lower or ("attendance" in lower and any(w in lower for w in ("lowest", "worst"))):
            parsed.class_comparison_metric = "attendance"
            parsed.class_comparison_direction = "min"
        elif "attendance" in lower and any(w in lower for w in ("highest", "best")):
            parsed.class_comparison_metric = "attendance"
            parsed.class_comparison_direction = "max"
        elif any(w in lower for w in ("test", "academic", "performance", "marks")) and any(w in lower for w in ("lowest", "worst")):
            parsed.class_comparison_metric = "academic"
            parsed.class_comparison_direction = "min"
        elif any(w in lower for w in ("test", "academic", "performance", "marks")) and any(w in lower for w in ("highest", "best")):
            parsed.class_comparison_metric = "academic"
            parsed.class_comparison_direction = "max"
        elif "homework" in lower and any(w in lower for w in ("lowest", "worst")):
            parsed.class_comparison_metric = "homework"
            parsed.class_comparison_direction = "min"
        elif "homework" in lower and any(w in lower for w in ("highest", "best")):
            parsed.class_comparison_metric = "homework"
            parsed.class_comparison_direction = "max"
        elif "risk" in lower:
            parsed.class_comparison_metric = "risk_high"
            parsed.class_comparison_direction = "max"
        else:
            parsed.wants_class_comparison = False

    # --- student reference ------------------------------------------------------
    if any(p in lower for p in ("this student", "that student", "them", "him", "her", "this kid")):
        parsed.refers_to_last_student = True
    else:
        ref = _extract_student_reference(original, lower)
        if ref:
            parsed.student_query = ref

    return parsed


def merge_with_context(parsed: ParsedQuery, previous: Optional[ChatContext]) -> ParsedQuery:
    """Fill in gaps in a follow-up query using the previous turn's resolved context.

    Only ever narrows/extends filters the user already had — never grants a
    wider scope than what `resolve_scope()` allows.
    """
    if not previous or not parsed.is_followup:
        return parsed

    if parsed.attendance_threshold is None:
        parsed.attendance_threshold = previous.attendance_threshold
        parsed.attendance_cmp = parsed.attendance_cmp or previous.attendance_cmp
    if parsed.attendance_trend is None:
        parsed.attendance_trend = previous.attendance_trend
    if parsed.homework_filter is None:
        parsed.homework_filter = previous.homework_filter
    if parsed.homework_trend is None:
        parsed.homework_trend = previous.homework_trend
    if parsed.academic_trend is None:
        parsed.academic_trend = previous.academic_trend
    if not parsed.academic_lowest:
        parsed.academic_lowest = previous.academic_lowest
    if parsed.risk_level is None:
        parsed.risk_level = previous.risk_level
    if parsed.risk_level_exclude is None:
        parsed.risk_level_exclude = previous.risk_level_exclude
    if parsed.risk_trend is None:
        parsed.risk_trend = previous.risk_trend
    if parsed.intervention_filter is None:
        parsed.intervention_filter = previous.intervention_filter
    if parsed.grade is None:
        parsed.grade = previous.grade
    if parsed.section is None:
        parsed.section = previous.section

    return parsed
