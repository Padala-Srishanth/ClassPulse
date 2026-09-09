"""
app.analytics.aggregation — Class and School Cohort Aggregation Engine
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.models.monthly_report import (
    DataStatus,
    MonthlyClassReport,
    MonthlySchoolReport,
    MonthlyStudentReport,
    TrendDirection,
)
from app.analytics.monthly_trends import MonthlyTrendAnalyzer


class MonthlyCohortAggregator:
    """Aggregates individual student monthly reports into class-level and school-level reports."""

    @classmethod
    def aggregate_class_report(
        cls,
        school_id: str,
        class_id: str,
        class_name: str,
        grade: str,
        section: str,
        report_period: str,
        student_reports: List[MonthlyStudentReport],
        prev_class_report: Optional[MonthlyClassReport] = None,
    ) -> MonthlyClassReport:
        year, month = map(int, report_period.split("-"))
        total_students = len(student_reports)

        reports_with_data = [
            r for r in student_reports
            if r.data_status in (DataStatus.SUFFICIENT_DATA, DataStatus.PARTIAL_DATA)
        ]
        total_with_data = len(reports_with_data)

        # 1. Averages
        att_vals = [
            r.attendance.get("attendance_percentage")
            for r in reports_with_data
            if r.attendance.get("attendance_percentage") is not None
        ]
        avg_att = round(statistics.mean(att_vals), 2) if att_vals else None

        hw_vals = [
            r.homework.get("completion_rate")
            for r in reports_with_data
            if r.homework.get("completion_rate") is not None
        ]
        avg_hw = round(statistics.mean(hw_vals), 2) if hw_vals else None

        acad_vals = [
            r.academic.get("average_percentage")
            for r in reports_with_data
            if r.academic.get("average_percentage") is not None
        ]
        avg_acad = round(statistics.mean(acad_vals), 2) if acad_vals else None

        # 2. Subject-wise averages
        subj_accum: Dict[str, List[float]] = {}
        for r in reports_with_data:
            sb = r.academic.get("subject_breakdown", {})
            for subj, data in sb.items():
                avg_p = data.get("average_percentage")
                if avg_p is not None:
                    subj_accum.setdefault(subj, []).append(avg_p)

        subject_wise_avg = {
            s: round(statistics.mean(scores), 2)
            for s, scores in subj_accum.items() if scores
        }

        # 3. Risk distributions
        high_risk = 0
        med_risk = 0
        low_risk = 0
        needs_data = 0

        for r in student_reports:
            lvl = r.risk.get("risk_level")
            if lvl == "HIGH":
                high_risk += 1
            elif lvl == "MEDIUM":
                med_risk += 1
            elif lvl == "LOW":
                low_risk += 1
            else:
                needs_data += 1

        # 4. Data status for the class
        if total_students == 0 or total_with_data == 0:
            data_status = DataStatus.NO_DATA
        elif total_with_data < max(1, total_students // 2):
            data_status = DataStatus.PARTIAL_DATA
        else:
            data_status = DataStatus.SUFFICIENT_DATA

        # 5. Month-over-month class trends
        prev_att = prev_class_report.average_attendance if prev_class_report else None
        prev_acad = prev_class_report.average_academic_percentage if prev_class_report else None
        prev_hw = prev_class_report.average_homework_completion if prev_class_report else None

        att_delta, att_dir = MonthlyTrendAnalyzer.evaluate_metric_trend(avg_att, prev_att)
        acad_delta, acad_dir = MonthlyTrendAnalyzer.evaluate_metric_trend(avg_acad, prev_acad)
        hw_delta, hw_dir = MonthlyTrendAnalyzer.evaluate_metric_trend(avg_hw, prev_hw)

        trends = {
            "previous_period": prev_class_report.report_period if prev_class_report else None,
            "attendance_delta": att_delta,
            "attendance_direction": att_dir.value,
            "academic_delta": acad_delta,
            "academic_direction": acad_dir.value,
            "homework_delta": hw_delta,
            "homework_direction": hw_dir.value,
        }

        doc_id = f"{class_id}_{report_period}"
        return MonthlyClassReport(
            id=doc_id,
            school_id=school_id,
            class_id=class_id,
            class_name=class_name,
            grade=grade,
            section=section,
            report_period=report_period,
            year=year,
            month=month,
            generated_at=datetime.now(tz=timezone.utc),
            data_status=data_status,
            total_students=total_students,
            total_students_with_data=total_with_data,
            average_attendance=avg_att,
            average_academic_percentage=avg_acad,
            subject_wise_average=subject_wise_avg,
            average_homework_completion=avg_hw,
            high_risk_count=high_risk,
            medium_risk_count=med_risk,
            low_risk_count=low_risk,
            needs_data_count=needs_data,
            trends=trends,
        )

    @classmethod
    def aggregate_school_report(
        cls,
        school_id: str,
        school_name: str,
        report_period: str,
        class_reports: List[MonthlyClassReport],
        student_reports: List[MonthlyStudentReport],
        interventions: Optional[List[Dict[str, Any]]] = None,
        prev_school_report: Optional[MonthlySchoolReport] = None,
    ) -> MonthlySchoolReport:
        year, month = map(int, report_period.split("-"))
        total_students = sum(c.total_students for c in class_reports)
        total_classes = len(class_reports)

        # School-wide attendance and academic averages
        att_vals = [c.average_attendance for c in class_reports if c.average_attendance is not None]
        avg_att = round(statistics.mean(att_vals), 2) if att_vals else None

        acad_vals = [c.average_academic_percentage for c in class_reports if c.average_academic_percentage is not None]
        avg_acad = round(statistics.mean(acad_vals), 2) if acad_vals else None

        # Risk totals
        high_risk = sum(c.high_risk_count for c in class_reports)
        med_risk = sum(c.medium_risk_count for c in class_reports)
        low_risk = sum(c.low_risk_count for c in class_reports)
        needs_data = sum(c.needs_data_count for c in class_reports)

        # Class comparisons
        class_comparisons = []
        for c in class_reports:
            class_comparisons.append({
                "class_id": c.class_id,
                "class_name": c.class_name,
                "grade": c.grade,
                "section": c.section,
                "total_students": c.total_students,
                "average_attendance": c.average_attendance,
                "average_academic_percentage": c.average_academic_percentage,
                "average_homework_completion": c.average_homework_completion,
                "high_risk_count": c.high_risk_count,
                "medium_risk_count": c.medium_risk_count,
                "low_risk_count": c.low_risk_count,
            })

        # Student risk leaderboard (Top 10 highest risk students)
        valid_students = [
            s for s in student_reports
            if s.risk.get("risk_score") is not None and s.risk.get("risk_score", 0) > 0
        ]
        valid_students.sort(key=lambda s: s.risk.get("risk_score", 0), reverse=True)

        leaderboard = []
        for s in valid_students[:10]:
            top_factors = s.risk.get("risk_factors", [])
            leaderboard.append({
                "student_id": s.student_id,
                "student_name": s.student_name,
                "student_code": s.student_code,
                "class_id": s.class_id,
                "risk_score": s.risk.get("risk_score"),
                "risk_level": s.risk.get("risk_level"),
                "primary_risk_factor": top_factors[0] if top_factors else "Performance drop",
                "attendance_percentage": s.attendance.get("attendance_percentage"),
                "academic_percentage": s.academic.get("average_percentage"),
            })

        # Monthly interventions summary
        interventions = interventions or []
        active_interventions = sum(1 for i in interventions if i.get("status") in ("ACTIVE", "IN_PROGRESS"))
        completed_interventions = sum(1 for i in interventions if i.get("status") == "COMPLETED")
        interventions_summary = {
            "total_logged": len(interventions),
            "active_count": active_interventions,
            "completed_count": completed_interventions,
        }

        # School trends
        prev_att = prev_school_report.average_attendance if prev_school_report else None
        prev_acad = prev_school_report.average_academic_percentage if prev_school_report else None

        att_delta, att_dir = MonthlyTrendAnalyzer.evaluate_metric_trend(avg_att, prev_att)
        acad_delta, acad_dir = MonthlyTrendAnalyzer.evaluate_metric_trend(avg_acad, prev_acad)

        trends = {
            "previous_period": prev_school_report.report_period if prev_school_report else None,
            "attendance_delta": att_delta,
            "attendance_direction": att_dir.value,
            "academic_delta": acad_delta,
            "academic_direction": acad_dir.value,
        }

        doc_id = f"{school_id}_{report_period}"
        return MonthlySchoolReport(
            id=doc_id,
            school_id=school_id,
            school_name=school_name,
            report_period=report_period,
            year=year,
            month=month,
            generated_at=datetime.now(tz=timezone.utc),
            data_status=DataStatus.SUFFICIENT_DATA if total_students > 0 else DataStatus.NO_DATA,
            total_students=total_students,
            total_classes=total_classes,
            average_attendance=avg_att,
            average_academic_percentage=avg_acad,
            high_risk_count=high_risk,
            medium_risk_count=med_risk,
            low_risk_count=low_risk,
            needs_data_count=needs_data,
            class_comparisons=class_comparisons,
            student_risk_leaderboard=leaderboard,
            monthly_interventions=interventions_summary,
            trends=trends,
        )
