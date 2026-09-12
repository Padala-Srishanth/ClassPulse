"""
app.services.chatbot.orchestrator — ClassPulse AI Assistant Orchestrator

Glues together, in order:
    1. scope.resolve_scope()      — WHO the caller is and WHAT they may see
    2. nlu.parse_message()        — WHAT the caller is asking
    3. tools.py                   — controlled, read-only data retrieval
    4. responder.py                — turning results into a reply

This is the only module that both understands a question AND is allowed to
call the data tools — nlu.py and tools.py never talk to each other directly.
Authorization (scope) is resolved once per request straight from the
Firebase-verified identity and is never widened by conversational context.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.security import CurrentUser
from app.schemas.chatbot import ChatContext, ChatMessageResponse
from app.services.chatbot import responder, tools
from app.services.chatbot.nlu import ParsedQuery, merge_with_context, parse_message
from app.services.chatbot.scope import ChatbotAuthorizationError, ChatbotDataError, ChatScope, resolve_scope
from app.services.student_service import StudentService


def handle_message(user: CurrentUser, message: str, context: Optional[ChatContext]) -> ChatMessageResponse:
    try:
        scope = resolve_scope(user)
    except ChatbotAuthorizationError as exc:
        return ChatMessageResponse(reply=str(exc), data=None, context=ChatContext(), suggestions=_default_suggestions(None))

    parsed = parse_message(message, context)

    if parsed.is_greeting:
        return ChatMessageResponse(
            reply=f"Hello! {responder.HELP_MESSAGE}",
            data=None,
            context=context or ChatContext(),
            suggestions=_default_suggestions(scope),
        )
    if parsed.is_help:
        return ChatMessageResponse(reply=responder.HELP_MESSAGE, data=None, context=context or ChatContext(), suggestions=_default_suggestions(scope))
    if parsed.is_reset:
        return ChatMessageResponse(reply="Sure, let's start fresh. What would you like to know?", data=None, context=ChatContext(), suggestions=_default_suggestions(scope))
    if parsed.is_out_of_scope:
        return ChatMessageResponse(reply=responder.OUT_OF_SCOPE_MESSAGE, data=None, context=context or ChatContext(), suggestions=_default_suggestions(scope))

    if parsed.is_followup:
        parsed = merge_with_context(parsed, context)

    # A teacher explicitly asking for whole-school data is denied outright —
    # their scope never includes classes they don't teach, regardless of phrasing.
    if parsed.wants_school_wide and not scope.is_principal:
        return ChatMessageResponse(
            reply=responder.SCOPE_DENIED_MESSAGE,
            data=None,
            context=context or ChatContext(),
            suggestions=_default_suggestions(scope),
        )

    try:
        return _route(scope, parsed, context)
    except ChatbotAuthorizationError as exc:
        return ChatMessageResponse(reply=str(exc), data=None, context=context or ChatContext(), suggestions=_default_suggestions(scope))
    except ChatbotDataError as exc:
        return ChatMessageResponse(reply=str(exc), data=None, context=context or ChatContext(), suggestions=_default_suggestions(scope))


def _default_suggestions(scope: Optional[ChatScope]) -> List[str]:
    if scope is None:
        return []
    if scope.is_principal:
        return [
            "Show all high-risk students.",
            "Which class has the lowest attendance?",
            "Show students with attendance below 75% and declining test scores.",
        ]
    return [
        "Show students with attendance below 75%.",
        "Who has not completed homework?",
        "Which students in my class are currently high risk?",
    ]


# ---------------------------------------------------------------------------
# Candidate resolution
# ---------------------------------------------------------------------------

def _candidate_students(scope: ChatScope, parsed: ParsedQuery, context: Optional[ChatContext]):
    students = scope.students()

    if parsed.grade:
        students = [s for s in students if s.grade.strip().lower() == parsed.grade.strip().lower()]
    if parsed.section:
        students = [s for s in students if s.section.strip().lower() == parsed.section.strip().lower()]

    if parsed.restrict_to_previous_results and context and context.last_student_ids:
        allowed = set(context.last_student_ids)
        students = [s for s in students if s.id in allowed]

    return students


def _resolve_target_student(scope: ChatScope, parsed: ParsedQuery, context: Optional[ChatContext]):
    if parsed.refers_to_last_student:
        if not context or not context.last_student_id:
            raise ChatbotDataError("I'm not sure which student you mean — could you name them?")
        student = StudentService.get_student(context.last_student_id)
        return scope.require_student(student)

    if parsed.student_query:
        matches = tools.find_students_by_query(scope, parsed.student_query)
        if not matches:
            raise ChatbotDataError(
                f"I couldn't find a student matching \"{parsed.student_query}\" among the students you are authorized to access."
            )
        return matches[0]

    return None


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route(scope: ChatScope, parsed: ParsedQuery, context: Optional[ChatContext]) -> ChatMessageResponse:
    target_student = _resolve_target_student(scope, parsed, context)

    if target_student is not None:
        return _handle_individual_student(scope, parsed, target_student)

    if parsed.wants_class_comparison and parsed.class_comparison_metric:
        return _handle_class_comparison(scope, parsed)

    if "intervention" in parsed.categories and len(parsed.categories) == 1 and not any(
        [parsed.risk_level, parsed.attendance_threshold, parsed.homework_filter, parsed.academic_trend]
    ):
        return _handle_interventions_only(scope, parsed, context)

    return _handle_aggregate_query(scope, parsed, context)


# ---------------------------------------------------------------------------
# Individual student handling
# ---------------------------------------------------------------------------

def _handle_individual_student(scope: ChatScope, parsed: ParsedQuery, student) -> ChatMessageResponse:
    new_context = ChatContext(categories=list(parsed.categories), last_student_id=student.id, last_student_ids=[student.id])

    if parsed.risk_why or ("risk" in parsed.categories and not parsed.categories - {"risk"}):
        data = tools.get_student_risk(scope, student)
        if data["risk_level"] == "INSUFFICIENT_DATA":
            reply = f"{student.name} doesn't have enough historical data yet for a risk assessment."
        elif not data["reasons"]:
            reply = f"{student.name} is currently {data['risk_level']} risk (score {data['risk_score']}), with no specific decline signals flagged."
        else:
            reasons_text = " ".join(data["reasons"])
            reply = f"{student.name} is currently {data['risk_level']} risk (score {data['risk_score']}). Reasons: {reasons_text}"
        return _finish(reply, data, new_context, scope, parsed)

    if "attendance" in parsed.categories and len(parsed.categories) == 1:
        data = tools.get_student_attendance(scope, student)
        if data["total_days"] == 0:
            reply = responder.NO_DATA_MESSAGE
        else:
            trend_txt = _trend_phrase(data["trend"])
            reply = f"{student.name} has {data['attendance_pct']}% attendance ({data['present']} present, {data['absent']} absent, {data['late']} late out of {data['total_days']} days).{trend_txt}"
        return _finish(reply, data, new_context, scope, parsed)

    if "academic" in parsed.categories and len(parsed.categories) == 1:
        data = tools.get_student_test_scores(scope, student)
        if data["test_count"] == 0:
            reply = responder.NO_DATA_MESSAGE
        else:
            trend_txt = _trend_phrase(data["trend"])
            reply = f"{student.name}'s average test score is {data['average_pct']}% across {data['test_count']} assessments.{trend_txt}"
        return _finish(reply, data, new_context, scope, parsed)

    if "homework" in parsed.categories and len(parsed.categories) == 1:
        data = tools.get_student_summary(scope, student)
        reply = f"{student.name}'s homework completion rate is {_fmt_pct(data['homework_completion_pct'])}."
        return _finish(reply, data, new_context, scope, parsed)

    if "intervention" in parsed.categories and len(parsed.categories) == 1:
        data = tools.get_interventions(scope, student=student)
        if not data:
            reply = f"{student.name} has no interventions on record."
        else:
            statuses = ", ".join(f"{i['type']} ({i['status']})" for i in data)
            reply = f"{student.name} has {len(data)} intervention(s): {statuses}."
        return _finish(reply, data, new_context, scope, parsed)

    # Default: full 360-degree summary
    data = tools.get_student_summary(scope, student)
    reply = _format_summary_reply(data)
    return _finish(reply, data, new_context, scope, parsed)


def _format_summary_reply(data: Dict[str, Any]) -> str:
    s = data["student"]
    parts = [f"Summary for {s['name']} (Grade {s['grade']}{s['section']}):"]
    parts.append(f"Attendance: {_fmt_pct(data['attendance_pct'])} ({_trend_word(data['attendance_trend'])}).")
    parts.append(f"Homework completion: {_fmt_pct(data['homework_completion_pct'])}.")
    parts.append(f"Academic average: {_fmt_pct(data['academic_avg'])} ({_trend_word(data['academic_trend'])}).")
    parts.append(f"Risk level: {data['risk_level']}" + (f" (score {data['risk_score']})." if data["risk_score"] else "."))
    if data["risk_reasons"]:
        parts.append("Risk factors: " + " ".join(data["risk_reasons"]))
    if data["interventions"]:
        parts.append(f"{len(data['interventions'])} intervention(s) on record.")
    else:
        parts.append("No interventions on record.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Interventions-only aggregate handling
# ---------------------------------------------------------------------------

def _handle_interventions_only(scope: ChatScope, parsed: ParsedQuery, context: Optional[ChatContext]) -> ChatMessageResponse:
    data = tools.get_interventions(scope, status_filter=parsed.intervention_filter)
    new_context = ChatContext(categories=list(parsed.categories), intervention_filter=parsed.intervention_filter)

    label = {
        "ONGOING": "ongoing",
        "OVERDUE": "overdue",
        "COMPLETED": "completed",
        "NONE": "with no intervention",
    }.get(parsed.intervention_filter or "", "")

    if not data:
        reply = f"There are no {label} interventions recorded in {scope.scope_label()} right now." if label else "There are no interventions recorded."
    else:
        reply = f"There are {len(data)} {label} intervention(s) in {scope.scope_label()}.".replace("  ", " ")

    return _finish(reply, data, new_context, scope, parsed)


# ---------------------------------------------------------------------------
# Class comparison handling ("Which class has the highest/lowest ...")
# ---------------------------------------------------------------------------

def _handle_class_comparison(scope: ChatScope, parsed: ParsedQuery) -> ChatMessageResponse:
    rollups = _class_rollups(scope)
    metric = parsed.class_comparison_metric
    metric_key = {"attendance": "avg_attendance", "homework": "avg_homework", "academic": "avg_academic", "risk_high": "high_risk_count"}[metric]

    valid = [r for r in rollups if r[metric_key] is not None]
    if not valid:
        return _finish(responder.NO_DATA_MESSAGE, None, ChatContext(), scope, parsed)

    reverse = parsed.class_comparison_direction == "max"
    valid.sort(key=lambda r: r[metric_key], reverse=reverse)
    top = valid[0]

    metric_label = {
        "attendance": f"{top['avg_attendance']}% average attendance",
        "homework": f"{top['avg_homework']}% average homework completion",
        "academic": f"{top['avg_academic']}% average test performance",
        "risk_high": f"{top['high_risk_count']} high-risk student(s)",
    }[metric]

    reply = f"{top['class_name']} (Grade {top['grade']}{top['section']}) — {metric_label}."
    return _finish(reply, {"classes": rollups, "answer": top}, ChatContext(categories=list(parsed.categories)), scope, parsed)


def _class_rollups(scope: ChatScope) -> List[Dict[str, Any]]:
    rollups = []
    for c in scope.classes:
        students = StudentService.list_class_students(c.id, limit=tools.MAX_STUDENTS_PER_QUERY)
        metrics = tools.gather_metrics(scope, students)
        att_vals = [m.attendance_pct for m in metrics if m.attendance_pct is not None]
        hw_vals = [m.homework_completion_pct for m in metrics if m.homework_completion_pct is not None]
        ac_vals = [m.academic_avg for m in metrics if m.academic_avg is not None]
        high_count = len([m for m in metrics if m.risk_level == "HIGH"])
        rollups.append({
            "class_id": c.id,
            "class_name": c.name,
            "grade": c.grade,
            "section": c.section,
            "student_count": len(students),
            "avg_attendance": round(sum(att_vals) / len(att_vals), 1) if att_vals else None,
            "avg_homework": round(sum(hw_vals) / len(hw_vals), 1) if hw_vals else None,
            "avg_academic": round(sum(ac_vals) / len(ac_vals), 1) if ac_vals else None,
            "high_risk_count": high_count,
        })
    return rollups


# ---------------------------------------------------------------------------
# Generic cross-category aggregate handling
# ---------------------------------------------------------------------------

def _handle_aggregate_query(scope: ChatScope, parsed: ParsedQuery, context: Optional[ChatContext]) -> ChatMessageResponse:
    candidates = _candidate_students(scope, parsed, context)

    if parsed.wants_breakdown_by_class:
        return _handle_breakdown_by_class(scope, parsed)

    if not candidates:
        return _finish(responder.NO_DATA_MESSAGE, [], _context_from_parsed(parsed, []), scope, parsed)

    metrics = tools.gather_metrics(scope, candidates)

    if parsed.wants_count_only and "attendance" in parsed.categories:
        absent = [m for m in metrics if m.latest_attendance_status == "ABSENT"]
        reply = f"{len(absent)} student(s) were absent on their most recently recorded day{_scope_suffix(parsed, scope)}."
        return _finish(reply, [m.to_dict() for m in absent], _context_from_parsed(parsed, [m.student.id for m in absent]), scope, parsed)

    filtered = _apply_filters(scope, metrics, parsed)

    if parsed.academic_lowest and "academic" in parsed.categories:
        filtered = [m for m in filtered if m.academic_avg is not None]
        filtered.sort(key=lambda m: m.academic_avg)
        filtered = filtered[:10]
    elif "risk" in parsed.categories:
        filtered.sort(key=lambda m: m.risk_score, reverse=True)
    elif "attendance" in parsed.categories:
        filtered.sort(key=lambda m: (m.attendance_pct if m.attendance_pct is not None else 999))
    elif "academic" in parsed.categories:
        filtered.sort(key=lambda m: (m.academic_avg if m.academic_avg is not None else 999))

    data = [m.to_dict() for m in filtered]
    new_context = _context_from_parsed(parsed, [m.student.id for m in filtered])
    reply = _describe_aggregate_result(parsed, filtered, scope)
    return _finish(reply, data, new_context, scope, parsed)


def _handle_breakdown_by_class(scope: ChatScope, parsed: ParsedQuery) -> ChatMessageResponse:
    rollups = _class_rollups(scope)
    lines = []
    for r in rollups:
        bits = []
        if "attendance" in parsed.categories:
            bits.append(f"attendance {_fmt_pct(r['avg_attendance'])}")
        if "homework" in parsed.categories:
            bits.append(f"homework completion {_fmt_pct(r['avg_homework'])}")
        if "academic" in parsed.categories or not bits:
            bits.append(f"academic average {_fmt_pct(r['avg_academic'])}")
        if "risk" in parsed.categories:
            bits.append(f"{r['high_risk_count']} high-risk")
        lines.append(f"{r['class_name']}: " + ", ".join(bits))
    reply = "Here's the breakdown by class — " + "; ".join(lines) + "."
    return _finish(reply, rollups, ChatContext(categories=list(parsed.categories)), scope, parsed)


def _apply_filters(scope: ChatScope, metrics: List[tools.StudentMetrics], parsed: ParsedQuery) -> List[tools.StudentMetrics]:
    result = metrics

    if parsed.attendance_threshold is not None:
        cmp = parsed.attendance_cmp or "lt"
        if cmp == "lt":
            result = [m for m in result if m.attendance_pct is not None and m.attendance_pct < parsed.attendance_threshold]
        else:
            result = [m for m in result if m.attendance_pct is not None and m.attendance_pct > parsed.attendance_threshold]

    if parsed.attendance_trend:
        result = [m for m in result if m.attendance_trend == parsed.attendance_trend]

    if parsed.homework_filter == "NOT_COMPLETED":
        result = [m for m in result if m.homework_not_completed_count > 0]
    elif parsed.homework_filter == "LATE":
        result = [m for m in result if m.homework_late_count > 0]
    elif parsed.homework_filter == "POOR":
        result = [m for m in result if m.homework_completion_pct is not None and m.homework_completion_pct < 60.0]

    if parsed.homework_trend:
        result = [m for m in result if m.homework_trend == parsed.homework_trend]

    if parsed.academic_trend:
        result = [m for m in result if m.academic_trend == parsed.academic_trend]

    if parsed.risk_level:
        result = [m for m in result if m.risk_level == parsed.risk_level]
    if parsed.risk_level_exclude:
        result = [m for m in result if m.risk_level != parsed.risk_level_exclude]

    if parsed.risk_trend:
        result = [m for m in result if _risk_trend(scope, m.student.id) == parsed.risk_trend]

    if parsed.intervention_filter == "NONE":
        result = [m for m in result if not m.has_intervention]
    elif parsed.intervention_filter == "ONGOING":
        result = [m for m in result if m.has_ongoing_intervention]
    elif parsed.intervention_filter == "OVERDUE":
        result = [m for m in result if m.has_overdue_intervention]
    elif parsed.intervention_filter == "COMPLETED":
        result = [m for m in result if m.has_completed_intervention]

    return result


def _risk_trend(scope: ChatScope, student_id: str) -> Optional[str]:
    student = StudentService.get_student(student_id)
    if not student:
        return None
    history = tools.get_risk_history(scope, student)
    if len(history) < 2:
        return None
    ordered = sorted(history, key=lambda h: h["created_at"])
    prev, latest = ordered[-2], ordered[-1]
    if latest["risk_score"] > prev["risk_score"] + 2:
        return "WORSENING"
    if latest["risk_score"] < prev["risk_score"] - 2:
        return "IMPROVING"
    return None


# ---------------------------------------------------------------------------
# Reply formatting helpers
# ---------------------------------------------------------------------------

def _describe_aggregate_result(parsed: ParsedQuery, filtered: List[tools.StudentMetrics], scope: ChatScope) -> str:
    count = len(filtered)
    suffix = _scope_suffix(parsed, scope)

    descriptors = []
    if parsed.risk_level:
        descriptors.append(f"{parsed.risk_level.lower()}-risk")
    if parsed.risk_level_exclude:
        descriptors.append(f"not currently {parsed.risk_level_exclude.lower()}-risk")
    if parsed.attendance_threshold is not None:
        cmp_word = "below" if (parsed.attendance_cmp or "lt") == "lt" else "above"
        descriptors.append(f"with attendance {cmp_word} {parsed.attendance_threshold:g}%")
    if parsed.attendance_trend:
        descriptors.append(f"with {_trend_word(parsed.attendance_trend)} attendance")
    if parsed.homework_filter:
        hw_words = {"NOT_COMPLETED": "incomplete homework", "LATE": "frequent late homework", "POOR": "poor homework completion"}
        descriptors.append(f"with {hw_words.get(parsed.homework_filter)}")
    if parsed.homework_trend:
        descriptors.append(f"with {_trend_word(parsed.homework_trend)} homework completion")
    if parsed.academic_trend:
        descriptors.append(f"with {_trend_word(parsed.academic_trend)} test scores")
    if parsed.academic_lowest:
        descriptors.append("the lowest-performing")
    if parsed.intervention_filter:
        iv_words = {"NONE": "no intervention", "ONGOING": "an ongoing intervention", "OVERDUE": "an overdue intervention", "COMPLETED": "a completed intervention"}
        descriptors.append(f"with {iv_words.get(parsed.intervention_filter)}")

    descriptor_text = " and ".join(descriptors) if descriptors else "matching your criteria"

    if count == 0:
        return f"No students {descriptor_text}{suffix} right now."

    names = responder.name_list([m.to_dict() for m in filtered])
    return f"There are {count} student(s) {descriptor_text}{suffix}: {names}."


def _scope_suffix(parsed: ParsedQuery, scope: ChatScope) -> str:
    if parsed.grade and parsed.section:
        return f" in Grade {parsed.grade} Section {parsed.section}"
    if parsed.grade:
        return f" in Grade {parsed.grade}"
    if scope.is_principal:
        return " across the school"
    return " in your classes"


def _trend_phrase(trend: str) -> str:
    if trend == "INSUFFICIENT_DATA":
        return ""
    return f" The trend is {_trend_word(trend).lower()}."


def _trend_word(trend: Optional[str]) -> str:
    return {
        "DECLINING": "declining",
        "IMPROVING": "improving",
        "STABLE": "stable",
        "INSUFFICIENT_DATA": "not enough data yet",
    }.get(trend or "", "unknown")


def _fmt_pct(value: Optional[float]) -> str:
    return f"{value}%" if value is not None else "no data"


def _context_from_parsed(parsed: ParsedQuery, student_ids: List[str]) -> ChatContext:
    return ChatContext(
        categories=list(parsed.categories),
        attendance_threshold=parsed.attendance_threshold,
        attendance_cmp=parsed.attendance_cmp,
        attendance_trend=parsed.attendance_trend,
        homework_filter=parsed.homework_filter,
        homework_trend=parsed.homework_trend,
        academic_trend=parsed.academic_trend,
        academic_lowest=parsed.academic_lowest,
        risk_level=parsed.risk_level,
        risk_level_exclude=parsed.risk_level_exclude,
        risk_trend=parsed.risk_trend,
        intervention_filter=parsed.intervention_filter,
        grade=parsed.grade,
        section=parsed.section,
        last_student_ids=student_ids,
        wants_school_wide=parsed.wants_school_wide,
    )


def _finish(reply: str, data: Any, new_context: ChatContext, scope: ChatScope, parsed: ParsedQuery) -> ChatMessageResponse:
    polished = responder.polish(reply, data)
    return ChatMessageResponse(reply=polished, data=data, context=new_context, suggestions=_default_suggestions(scope))
