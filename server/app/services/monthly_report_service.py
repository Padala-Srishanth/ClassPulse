"""
app.services.monthly_report_service — Monthly Report Generation & Aggregation Service
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger
from app.analytics.aggregation import MonthlyCohortAggregator
from app.analytics.monthly_features import MonthlyFeatureExtractor
from app.analytics.monthly_risk import MonthlyRiskCalculator
from app.analytics.monthly_trends import MonthlyTrendAnalyzer
from app.models.monthly_report import (
    DataStatus,
    MonthlyClassReport,
    MonthlySchoolReport,
    MonthlyStudentReport,
)
from app.services.attendance_service import AttendanceService
from app.services.class_service import ClassService
from app.services.homework_service import HomeworkService
from app.services.intervention_service import InterventionService
from app.services.school_service import SchoolService
from app.services.student_service import StudentService
from app.services.test_score_service import TestScoreService

logger = get_logger(__name__)


class MonthlyReportService:
    @staticmethod
    def _student_reports_collection():
        return get_firestore_client().collection("monthly_student_reports")

    @staticmethod
    def _class_reports_collection():
        return get_firestore_client().collection("monthly_class_reports")

    @staticmethod
    def _school_reports_collection():
        return get_firestore_client().collection("monthly_school_reports")

    # =========================================================================
    # Student Monthly Reports
    # =========================================================================

    @classmethod
    def get_student_report(
        cls, student_id: str, report_period: str, auto_generate: bool = True
    ) -> Optional[MonthlyStudentReport]:
        doc_id = f"{student_id}_{report_period}"
        doc = cls._student_reports_collection().document(doc_id).get()
        if doc.exists:
            return MonthlyStudentReport.from_firestore(doc.id, doc.to_dict())

        if auto_generate:
            return cls.generate_student_report(student_id, report_period)
        return None

    @classmethod
    def list_student_report_history(cls, student_id: str) -> List[MonthlyStudentReport]:
        docs = (
            cls._student_reports_collection()
            .where("student_id", "==", student_id)
            .stream()
        )
        reports = [MonthlyStudentReport.from_firestore(d.id, d.to_dict()) for d in docs]
        reports.sort(key=lambda r: r.report_period)
        return reports

    @classmethod
    def generate_student_report(
        cls, student_id: str, report_period: str, force: bool = False
    ) -> MonthlyStudentReport:
        doc_id = f"{student_id}_{report_period}"
        if not force:
            existing = cls._student_reports_collection().document(doc_id).get()
            if existing.exists:
                return MonthlyStudentReport.from_firestore(existing.id, existing.to_dict())

        student = StudentService.get_student(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found.")

        # 1. Fetch academic data from subcollections
        att_records = AttendanceService.list_student_attendance(student_id, limit=1000)
        hw_records = HomeworkService.list_student_homework(student_id, limit=1000)
        test_records = TestScoreService.list_student_test_scores(student_id, limit=1000)

        # 2. Extract monthly features for target period
        features = MonthlyFeatureExtractor.extract_monthly_features(
            report_period=report_period,
            attendance_records=att_records,
            homework_records=hw_records,
            test_records=test_records,
        )

        # 3. Retrieve prior reports for baseline & trend analysis
        prior_docs = (
            cls._student_reports_collection()
            .where("student_id", "==", student_id)
            .stream()
        )
        all_prior = [
            MonthlyStudentReport.from_firestore(d.id, d.to_dict())
            for d in prior_docs
            if d.id != doc_id
        ]
        all_prior.sort(key=lambda r: r.report_period)
        strictly_prior = [r for r in all_prior if r.report_period < report_period]

        # Filter prior raw records as fallback
        prior_att = [r for r in att_records if r.date < f"{report_period}-01"]
        prior_hw = [r for r in hw_records if r.assignment_date < f"{report_period}-01"]
        prior_test = [r for r in test_records if r.assessment_date < f"{report_period}-01"]

        baseline = MonthlyRiskCalculator.compute_historical_baseline(
            prior_reports=[r.model_dump() for r in strictly_prior],
            prior_attendance=prior_att,
            prior_homework=prior_hw,
            prior_tests=prior_test,
        )

        # Previous month report if available
        prev_report_model = strictly_prior[-1] if strictly_prior else None
        prev_report_dict = prev_report_model.model_dump() if prev_report_model else None

        # 4. Compute preliminary trends (without risk score)
        prelim_trends = MonthlyTrendAnalyzer.compute_trends(
            current_attendance_pct=features.attendance.get("attendance_percentage"),
            current_homework_pct=features.homework.get("completion_rate"),
            current_academic_pct=features.academic.get("average_percentage"),
            prev_report=prev_report_dict,
            historical_reports=[r.model_dump() for r in strictly_prior],
        )

        # 5. Evaluate risk using baseline and consecutive declining count
        consecutive_declining = prelim_trends.get("consecutive_declining_months", 0)
        risk_output = MonthlyRiskCalculator.evaluate_monthly_risk(
            data_status=features.data_status,
            attendance_percentage=features.attendance.get("attendance_percentage"),
            homework_completion_rate=features.homework.get("completion_rate"),
            academic_percentage=features.academic.get("average_percentage"),
            baseline=baseline,
            consecutive_declining_months=consecutive_declining,
        )

        # 6. Recompute full trends with risk score
        final_trends = MonthlyTrendAnalyzer.compute_trends(
            current_attendance_pct=features.attendance.get("attendance_percentage"),
            current_homework_pct=features.homework.get("completion_rate"),
            current_academic_pct=features.academic.get("average_percentage"),
            prev_report=prev_report_dict,
            historical_reports=[r.model_dump() for r in strictly_prior],
            current_risk_score=risk_output.risk_score,
        )

        # 7. Construct & persist report
        year, month = map(int, report_period.split("-"))
        now = datetime.now(tz=timezone.utc)
        report = MonthlyStudentReport(
            id=doc_id,
            school_id=student.school_id,
            class_id=student.class_id,
            student_id=student.id,
            student_name=student.name,
            student_code=student.student_code,
            report_period=report_period,
            year=year,
            month=month,
            generated_at=now,
            data_status=features.data_status,
            attendance=features.attendance,
            homework=features.homework,
            academic=features.academic,
            risk=risk_output.model_dump(),
            trends=final_trends,
        )

        cls._student_reports_collection().document(doc_id).set(report.to_firestore())
        logger.info("Generated monthly student report: %s for %s", doc_id, report_period)
        return report

    # =========================================================================
    # Class Monthly Reports
    # =========================================================================

    @classmethod
    def get_class_report(
        cls, class_id: str, report_period: str, auto_generate: bool = True
    ) -> Optional[MonthlyClassReport]:
        doc_id = f"{class_id}_{report_period}"
        doc = cls._class_reports_collection().document(doc_id).get()
        if doc.exists:
            return MonthlyClassReport.from_firestore(doc.id, doc.to_dict())

        if auto_generate:
            return cls.generate_class_report(class_id, report_period)
        return None

    @classmethod
    def generate_class_report(
        cls, class_id: str, report_period: str, force: bool = False
    ) -> MonthlyClassReport:
        doc_id = f"{class_id}_{report_period}"
        if not force:
            existing = cls._class_reports_collection().document(doc_id).get()
            if existing.exists:
                return MonthlyClassReport.from_firestore(existing.id, existing.to_dict())

        class_obj = ClassService.get_class(class_id)
        if not class_obj:
            raise ValueError(f"Class {class_id} not found.")

        students = StudentService.list_class_students(class_id, limit=500)
        student_reports: List[MonthlyStudentReport] = []

        for student in students:
            # Ensure each student has a report generated
            s_rep = cls.get_student_report(student.id, report_period, auto_generate=True)
            if s_rep:
                student_reports.append(s_rep)

        # Retrieve prior class report if exists
        prior_docs = (
            cls._class_reports_collection()
            .where("class_id", "==", class_id)
            .stream()
        )
        all_prior = [
            MonthlyClassReport.from_firestore(d.id, d.to_dict())
            for d in prior_docs
            if d.id != doc_id
        ]
        strictly_prior = [c for c in all_prior if c.report_period < report_period]
        strictly_prior.sort(key=lambda c: c.report_period)
        prev_class_report = strictly_prior[-1] if strictly_prior else None

        class_report = MonthlyCohortAggregator.aggregate_class_report(
            school_id=class_obj.school_id,
            class_id=class_id,
            class_name=class_obj.name,
            grade=class_obj.grade,
            section=class_obj.section,
            report_period=report_period,
            student_reports=student_reports,
            prev_class_report=prev_class_report,
        )

        cls._class_reports_collection().document(doc_id).set(class_report.to_firestore())
        logger.info("Generated monthly class report: %s for %s", doc_id, report_period)
        return class_report

    # =========================================================================
    # School Monthly Reports
    # =========================================================================

    @classmethod
    def get_school_report(
        cls, school_id: str, report_period: str, auto_generate: bool = True
    ) -> Optional[MonthlySchoolReport]:
        doc_id = f"{school_id}_{report_period}"
        doc = cls._school_reports_collection().document(doc_id).get()
        if doc.exists:
            return MonthlySchoolReport.from_firestore(doc.id, doc.to_dict())

        if auto_generate:
            return cls.generate_school_report(school_id, report_period)
        return None

    @classmethod
    def generate_school_report(
        cls, school_id: str, report_period: str, force: bool = False
    ) -> MonthlySchoolReport:
        doc_id = f"{school_id}_{report_period}"
        if not force:
            existing = cls._school_reports_collection().document(doc_id).get()
            if existing.exists:
                return MonthlySchoolReport.from_firestore(existing.id, existing.to_dict())

        school = SchoolService.get_school(school_id)
        if not school:
            raise ValueError(f"School {school_id} not found.")

        classes = ClassService.list_school_classes(school_id, limit=100)
        class_reports: List[MonthlyClassReport] = []
        all_student_reports: List[MonthlyStudentReport] = []

        for c in classes:
            c_rep = cls.get_class_report(c.id, report_period, auto_generate=True)
            if c_rep:
                class_reports.append(c_rep)
            # Gather students
            students = StudentService.list_class_students(c.id, limit=500)
            for s in students:
                s_rep = cls.get_student_report(s.id, report_period, auto_generate=True)
                if s_rep:
                    all_student_reports.append(s_rep)

        # Interventions
        interventions = InterventionService.list_school_interventions(school_id, limit=200)
        interventions_data = [i.model_dump() for i in interventions]

        # Prior school report
        prior_docs = (
            cls._school_reports_collection()
            .where("school_id", "==", school_id)
            .stream()
        )
        all_prior = [
            MonthlySchoolReport.from_firestore(d.id, d.to_dict())
            for d in prior_docs
            if d.id != doc_id
        ]
        strictly_prior = [s for s in all_prior if s.report_period < report_period]
        strictly_prior.sort(key=lambda s: s.report_period)
        prev_school_report = strictly_prior[-1] if strictly_prior else None

        school_report = MonthlyCohortAggregator.aggregate_school_report(
            school_id=school_id,
            school_name=school.name,
            report_period=report_period,
            class_reports=class_reports,
            student_reports=all_student_reports,
            interventions=interventions_data,
            prev_school_report=prev_school_report,
        )

        cls._school_reports_collection().document(doc_id).set(school_report.to_firestore())
        logger.info("Generated monthly school report: %s for %s", doc_id, report_period)
        return school_report
