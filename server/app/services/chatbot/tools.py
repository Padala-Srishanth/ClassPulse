"""
app.services.chatbot.tools — Controlled ClassPulse Tools

Every function in this module is a narrow, read-only "tool" the chatbot
orchestrator is allowed to call. Each one:
  1. Takes an already-resolved `ChatScope` (see scope.py) — never a raw role
     string or a client-supplied school/class id.
  2. Reuses the EXISTING ClassPulse services (StudentService,
     AttendanceService, HomeworkService, TestScoreService, RiskService,
     InterventionService, ClassService) rather than querying Firestore
     directly or duplicating business logic.
  3. Only reads data — nothing here writes, deletes, or mutates a record,
     recomputes a risk score, or triggers the ML pipeline. Risk data is read
     from the existing persisted RiskAlert (via RiskService.get_*), never
     recomputed on the fly, so a chat question never has a side effect.
  4. Raises ChatbotAuthorizationError / ChatbotDataError instead of ever
     returning data the caller isn't scoped to see.

This maps directly onto the tool set called out in the chatbot spec:
    get_student_summary, get_student_attendance, get_class_attendance,
    get_students_below_attendance_threshold, get_homework_status,
    get_student_test_scores, get_class_academic_performance,
    get_student_risk, get_high_risk_students, get_risk_history,
    get_interventions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.models.intervention import Intervention, InterventionStatus
from app.models.risk_alert import RiskAlert
from app.models.student import Student
from app.services.attendance_service import AttendanceService
from app.services.chatbot.scope import ChatScope, ChatbotDataError
from app.services.homework_service import HomeworkService
from app.services.intervention_service import InterventionService
from app.services.risk_service import RiskService
from app.services.test_score_service import TestScoreService

# Cap the number of students a single chat query will crunch through. This is
# a demo/single-school application; a real multi-thousand-student deployment
# would replace this per-student fan-out with pre-aggregated Firestore
# rollups, but the tool contract (read-only, scope-checked) stays the same.
MAX_STUDENTS_PER_QUERY = 300
ATTENDANCE_LOOKBACK = 120
HOMEWORK_LOOKBACK = 120
TEST_LOOKBACK = 60


def _trend_direction(values: List[float], min_points: int = 4) -> str:
    """Compare the second half of a chronologically-ordered series against the
    first half. Returns DECLINING / IMPROVING / STABLE / INSUFFICIENT_DATA.

    This is a lightweight, chat-scoped trend signal — a simple, transparent,
    backend-computed comparison (never left to the LLM), distinct from (and
    much cheaper than) the full weekly-signature ML trend engine used by the
    risk pipeline (app/ml/trends.py), which remains the authoritative source
    for actual risk scoring.
    """
    if len(values) < min_points:
        return "INSUFFICIENT_DATA"
    mid = len(values) // 2
    earlier = values[:mid]
    recent = values[mid:]
    earlier_avg = sum(earlier) / len(earlier)
    recent_avg = sum(recent) / len(recent)
    delta = recent_avg - earlier_avg
    if delta <= -3.0:
        return "DECLINING"
    if delta >= 3.0:
        return "IMPROVING"
    return "STABLE"


@dataclass
class StudentMetrics:
    student: Student
    attendance_pct: Optional[float] = None
    attendance_trend: str = "INSUFFICIENT_DATA"
    homework_completion_pct: Optional[float] = None
    homework_not_completed_count: int = 0
    homework_late_count: int = 0
    homework_trend: str = "INSUFFICIENT_DATA"
    academic_avg: Optional[float] = None
    academic_trend: str = "INSUFFICIENT_DATA"
    risk_level: str = "INSUFFICIENT_DATA"
    risk_score: float = 0.0
    risk_alert: Optional[RiskAlert] = None
    interventions: List[Intervention] = field(default_factory=list)
    latest_attendance_status: Optional[str] = None

    @property
    def has_intervention(self) -> bool:
        return len(self.interventions) > 0

    @property
    def has_ongoing_intervention(self) -> bool:
        return any(i.status in (InterventionStatus.PLANNED, InterventionStatus.IN_PROGRESS) for i in self.interventions)

    @property
    def has_completed_intervention(self) -> bool:
        return any(i.status == InterventionStatus.COMPLETED for i in self.interventions)

    @property
    def has_overdue_intervention(self) -> bool:
        today = date.today().isoformat()
        for i in self.interventions:
            if i.status in (InterventionStatus.PLANNED, InterventionStatus.IN_PROGRESS) and i.follow_up_date and i.follow_up_date < today:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student.id,
            "student_name": self.student.name,
            "student_code": self.student.student_code,
            "class_id": self.student.class_id,
            "grade": self.student.grade,
            "section": self.student.section,
            "attendance_pct": self.attendance_pct,
            "attendance_trend": self.attendance_trend,
            "homework_completion_pct": self.homework_completion_pct,
            "homework_trend": self.homework_trend,
            "academic_avg": self.academic_avg,
            "academic_trend": self.academic_trend,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "has_intervention": self.has_intervention,
        }


def _compute_metrics(student: Student) -> StudentMetrics:
    metrics = StudentMetrics(student=student)

    attendance_records = AttendanceService.list_student_attendance(student.id, limit=ATTENDANCE_LOOKBACK)
    if attendance_records:
        present = len([r for r in attendance_records if r.status.value in ("PRESENT", "LATE")])
        metrics.attendance_pct = round((present / len(attendance_records)) * 100, 1)
        presence_series = [1.0 if r.status.value in ("PRESENT", "LATE") else 0.0 for r in attendance_records]
        metrics.attendance_trend = _trend_direction([v * 100 for v in presence_series])
        # list_student_attendance orders ascending by date, so the last record is the latest.
        metrics.latest_attendance_status = attendance_records[-1].status.value

    homework_records = HomeworkService.list_student_homework(student.id, limit=HOMEWORK_LOOKBACK)
    if homework_records:
        completed = len([r for r in homework_records if r.status.value == "COMPLETED"])
        metrics.homework_completion_pct = round((completed / len(homework_records)) * 100, 1)
        metrics.homework_not_completed_count = len([r for r in homework_records if r.status.value == "NOT_COMPLETED"])
        metrics.homework_late_count = len([r for r in homework_records if r.status.value == "LATE"])
        completion_series = [100.0 if r.status.value == "COMPLETED" else 0.0 for r in homework_records]
        metrics.homework_trend = _trend_direction(completion_series)

    test_records = TestScoreService.list_student_test_scores(student.id, limit=TEST_LOOKBACK)
    if test_records:
        percentages = [r.percentage for r in test_records]
        metrics.academic_avg = round(sum(percentages) / len(percentages), 1)
        metrics.academic_trend = _trend_direction(percentages)

    alert = RiskService.get_student_latest_alert(student.id)
    if alert:
        metrics.risk_alert = alert
        metrics.risk_level = alert.risk_level.value
        metrics.risk_score = alert.risk_score

    metrics.interventions = InterventionService.list_student_interventions(student.id, limit=100)

    return metrics


def gather_metrics(scope: ChatScope, students: Optional[List[Student]] = None) -> List[StudentMetrics]:
    """Compute per-student metrics for every student in scope (or a given
    pre-filtered subset). This is the shared building block behind every
    cross-category chatbot question."""
    target = students if students is not None else scope.students()
    target = target[:MAX_STUDENTS_PER_QUERY]
    return [_compute_metrics(s) for s in target]


def find_students_by_query(scope: ChatScope, query: str) -> List[Student]:
    """Case-insensitive match against name or student_code, within scope only."""
    q = query.strip().lower()
    if not q:
        return []
    matches = []
    for s in scope.students():
        if q == s.student_code.lower() or q in s.name.lower():
            matches.append(s)
    return matches


# ---------------------------------------------------------------------------
# Tool: get_student_summary
# ---------------------------------------------------------------------------

def get_student_summary(scope: ChatScope, student: Student) -> Dict[str, Any]:
    scope.require_student(student)
    m = _compute_metrics(student)

    reasons = [r.get("explanation") for r in (m.risk_alert.reasons if m.risk_alert else [])]
    interventions = [
        {
            "id": i.id,
            "type": i.type.value,
            "status": i.status.value,
            "notes": i.notes,
            "follow_up_date": i.follow_up_date,
        }
        for i in m.interventions
    ]

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "student_code": student.student_code,
            "grade": student.grade,
            "section": student.section,
            "class_id": student.class_id,
        },
        "attendance_pct": m.attendance_pct,
        "attendance_trend": m.attendance_trend,
        "homework_completion_pct": m.homework_completion_pct,
        "academic_avg": m.academic_avg,
        "academic_trend": m.academic_trend,
        "risk_level": m.risk_level,
        "risk_score": m.risk_score,
        "risk_reasons": reasons,
        "interventions": interventions,
    }


# ---------------------------------------------------------------------------
# Tool: get_student_attendance
# ---------------------------------------------------------------------------

def get_student_attendance(scope: ChatScope, student: Student) -> Dict[str, Any]:
    scope.require_student(student)
    records = AttendanceService.list_student_attendance(student.id, limit=ATTENDANCE_LOOKBACK)
    present = len([r for r in records if r.status.value == "PRESENT"])
    absent = len([r for r in records if r.status.value == "ABSENT"])
    late = len([r for r in records if r.status.value == "LATE"])
    total = len(records)
    pct = round(((present + late) / total) * 100, 1) if total else None
    trend = _trend_direction([100.0 if r.status.value in ("PRESENT", "LATE") else 0.0 for r in records])
    return {
        "student_id": student.id,
        "student_name": student.name,
        "total_days": total,
        "present": present,
        "absent": absent,
        "late": late,
        "attendance_pct": pct,
        "trend": trend,
        "recent_records": [{"date": r.date, "status": r.status.value} for r in records[-15:]],
    }


# ---------------------------------------------------------------------------
# Tool: get_class_attendance
# ---------------------------------------------------------------------------

def get_class_attendance(scope: ChatScope, class_id: str) -> Dict[str, Any]:
    cls = scope.require_class(class_id)
    from app.services.student_service import StudentService
    students = StudentService.list_class_students(class_id, limit=MAX_STUDENTS_PER_QUERY)
    per_student = []
    total_pct = []
    for s in students:
        att = get_student_attendance(scope, s)
        per_student.append({"student_id": s.id, "student_name": s.name, "attendance_pct": att["attendance_pct"], "trend": att["trend"]})
        if att["attendance_pct"] is not None:
            total_pct.append(att["attendance_pct"])
    class_avg = round(sum(total_pct) / len(total_pct), 1) if total_pct else None
    return {
        "class_id": class_id,
        "class_name": cls.name,
        "grade": cls.grade,
        "section": cls.section,
        "student_count": len(students),
        "class_average_attendance_pct": class_avg,
        "students": per_student,
    }


# ---------------------------------------------------------------------------
# Tool: get_students_below_attendance_threshold
# ---------------------------------------------------------------------------

def get_students_below_attendance_threshold(
    scope: ChatScope, threshold: float, students: Optional[List[Student]] = None, cmp: str = "lt"
) -> List[Dict[str, Any]]:
    metrics = gather_metrics(scope, students)
    result = []
    for m in metrics:
        if m.attendance_pct is None:
            continue
        matches = (m.attendance_pct < threshold) if cmp == "lt" else (m.attendance_pct > threshold)
        if matches:
            result.append(m.to_dict())
    result.sort(key=lambda d: d["attendance_pct"])
    return result


# ---------------------------------------------------------------------------
# Tool: get_homework_status
# ---------------------------------------------------------------------------

def get_homework_status(
    scope: ChatScope, filter_status: str, students: Optional[List[Student]] = None
) -> List[Dict[str, Any]]:
    metrics = gather_metrics(scope, students)
    result = []
    for m in metrics:
        if filter_status == "NOT_COMPLETED" and m.homework_not_completed_count > 0:
            result.append(m.to_dict())
        elif filter_status == "LATE" and m.homework_late_count > 0:
            result.append(m.to_dict())
        elif filter_status == "POOR" and m.homework_completion_pct is not None and m.homework_completion_pct < 60.0:
            result.append(m.to_dict())
    result.sort(key=lambda d: (d["homework_completion_pct"] if d["homework_completion_pct"] is not None else 0))
    return result


# ---------------------------------------------------------------------------
# Tool: get_student_test_scores
# ---------------------------------------------------------------------------

def get_student_test_scores(scope: ChatScope, student: Student) -> Dict[str, Any]:
    scope.require_student(student)
    records = TestScoreService.list_student_test_scores(student.id, limit=TEST_LOOKBACK)
    percentages = [r.percentage for r in records]
    avg = round(sum(percentages) / len(percentages), 1) if percentages else None
    trend = _trend_direction(percentages)
    return {
        "student_id": student.id,
        "student_name": student.name,
        "test_count": len(records),
        "average_pct": avg,
        "trend": trend,
        "recent_scores": [
            {"subject": r.subject, "assessment_name": r.assessment_name, "date": r.assessment_date, "percentage": r.percentage}
            for r in records[-10:]
        ],
    }


# ---------------------------------------------------------------------------
# Tool: get_class_academic_performance
# ---------------------------------------------------------------------------

def get_class_academic_performance(scope: ChatScope, class_id: str) -> Dict[str, Any]:
    cls = scope.require_class(class_id)
    from app.services.student_service import StudentService
    students = StudentService.list_class_students(class_id, limit=MAX_STUDENTS_PER_QUERY)
    per_student = []
    all_avgs = []
    for s in students:
        info = get_student_test_scores(scope, s)
        per_student.append({"student_id": s.id, "student_name": s.name, "average_pct": info["average_pct"], "trend": info["trend"]})
        if info["average_pct"] is not None:
            all_avgs.append(info["average_pct"])
    class_avg = round(sum(all_avgs) / len(all_avgs), 1) if all_avgs else None
    lowest = sorted([p for p in per_student if p["average_pct"] is not None], key=lambda p: p["average_pct"])[:5]
    return {
        "class_id": class_id,
        "class_name": cls.name,
        "class_average_pct": class_avg,
        "student_count": len(students),
        "lowest_performers": lowest,
        "students": per_student,
    }


# ---------------------------------------------------------------------------
# Tool: get_student_risk
# ---------------------------------------------------------------------------

def get_student_risk(scope: ChatScope, student: Student) -> Dict[str, Any]:
    scope.require_student(student)
    alert = RiskService.get_student_latest_alert(student.id)
    if not alert:
        return {
            "student_id": student.id,
            "student_name": student.name,
            "risk_level": "INSUFFICIENT_DATA",
            "risk_score": None,
            "reasons": [],
        }
    return {
        "student_id": student.id,
        "student_name": student.name,
        "risk_level": alert.risk_level.value,
        "risk_score": alert.risk_score,
        "analysis_period": alert.analysis_period,
        "reasons": [r.get("explanation") for r in alert.reasons],
    }


# ---------------------------------------------------------------------------
# Tool: get_high_risk_students (also used for MEDIUM/LOW via risk_level param)
# ---------------------------------------------------------------------------

def get_high_risk_students(
    scope: ChatScope,
    risk_level: str = "HIGH",
    students: Optional[List[Student]] = None,
    exclude_level: Optional[str] = None,
) -> List[Dict[str, Any]]:
    metrics = gather_metrics(scope, students)
    result = []
    for m in metrics:
        if exclude_level and m.risk_level == exclude_level:
            continue
        if not exclude_level and m.risk_level != risk_level:
            continue
        result.append(m.to_dict())
    result.sort(key=lambda d: d["risk_score"], reverse=True)
    return result


# ---------------------------------------------------------------------------
# Tool: get_risk_history
# ---------------------------------------------------------------------------

def get_risk_history(scope: ChatScope, student: Student) -> List[Dict[str, Any]]:
    scope.require_student(student)
    alerts = RiskService.get_student_alert_history(student.id, limit=50)
    return [
        {
            "analysis_period": a.analysis_period,
            "risk_level": a.risk_level.value,
            "risk_score": a.risk_score,
            "created_at": a.created_at.isoformat(),
        }
        for a in alerts
    ]


# ---------------------------------------------------------------------------
# Tool: get_interventions
# ---------------------------------------------------------------------------

def get_interventions(
    scope: ChatScope,
    student: Optional[Student] = None,
    class_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if student is not None:
        scope.require_student(student)
        interventions = InterventionService.list_student_interventions(student.id, limit=200)
    elif class_id is not None:
        scope.require_class(class_id)
        interventions = InterventionService.list_class_interventions(class_id, limit=500)
    else:
        interventions = []
        for c in scope.classes:
            interventions.extend(InterventionService.list_class_interventions(c.id, limit=500))

    today = date.today().isoformat()
    result = []
    for i in interventions:
        is_overdue = (
            i.status in (InterventionStatus.PLANNED, InterventionStatus.IN_PROGRESS)
            and i.follow_up_date is not None
            and i.follow_up_date < today
        )
        if status_filter == "ONGOING" and i.status not in (InterventionStatus.PLANNED, InterventionStatus.IN_PROGRESS):
            continue
        if status_filter == "OVERDUE" and not is_overdue:
            continue
        if status_filter == "COMPLETED" and i.status != InterventionStatus.COMPLETED:
            continue
        result.append({
            "id": i.id,
            "student_id": i.student_id,
            "class_id": i.class_id,
            "type": i.type.value,
            "status": i.status.value,
            "notes": i.notes,
            "follow_up_date": i.follow_up_date,
            "is_overdue": is_overdue,
            "created_at": i.created_at.isoformat(),
        })
    return result


def students_without_intervention(scope: ChatScope, students: Optional[List[Student]] = None) -> List[Dict[str, Any]]:
    """Helper for 'high-risk students with no intervention' style questions."""
    metrics = gather_metrics(scope, students)
    return [m.to_dict() for m in metrics if not m.has_intervention]
