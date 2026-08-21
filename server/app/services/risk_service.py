"""
app.services.risk_service — AI/ML Risk Analysis Orchestration & Alert Persistence
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger
from app.ml.anomaly import AnomalyDetector
from app.ml.baseline import BaselineCalculator
from app.ml.config import ml_settings
from app.ml.explainability import ExplainabilityEngine
from app.ml.features import FeatureExtractor
from app.ml.scoring import RiskLevel, RiskScorer
from app.ml.trends import TrendAnalyzer
from app.models.risk_alert import AlertStatus, RiskAlert
from app.models.student import Student
from app.schemas.risk import (
    ClassRiskSummaryResponse,
    RiskAlertResponse,
    StudentRiskAnalysisResponse,
)
from app.services.attendance_service import AttendanceService
from app.services.homework_service import HomeworkService
from app.services.student_service import StudentService
from app.services.test_score_service import TestScoreService

logger = get_logger(__name__)


class RiskService:
    @staticmethod
    def _alerts_collection():
        return get_firestore_client().collection("risk_alerts")

    @classmethod
    def analyze_student_risk(cls, student: Student) -> StudentRiskAnalysisResponse:
        """
        Run the complete ML pipeline on a single student and persist risk alert.
        """
        # 1. Fetch raw academic records from student subcollections
        attendance_records = AttendanceService.list_student_attendance(student.id, limit=500)
        homework_records = HomeworkService.list_student_homework(student.id, limit=500)
        test_records = TestScoreService.list_student_test_scores(student.id, limit=500)

        # 2. Feature Extraction: Weekly Engagement Signatures
        signatures = FeatureExtractor.build_weekly_signatures(
            attendance_records=attendance_records,
            homework_records=homework_records,
            test_records=test_records,
        )

        # Analysis period is the most recent observed week (or current week)
        analysis_period = signatures[-1].week_key if signatures else datetime.now(tz=timezone.utc).strftime("%Y-W%U")

        # 3. Historical Baseline
        baseline, baseline_sigs, recent_sigs = BaselineCalculator.calculate_baseline(signatures)

        # 4. Trend Analysis
        trends = TrendAnalyzer.analyze_trends(baseline, recent_sigs)

        # 5. Statistical Anomaly Detection
        anomaly = AnomalyDetector.detect_anomalies(baseline, trends)

        # 6. Multi-Signal Risk Scoring
        score_output = RiskScorer.compute_risk(baseline, trends, anomaly)

        # 7. Structured Explainability
        reasons = ExplainabilityEngine.generate_reasons(baseline, trends, anomaly, score_output)

        # 8. Persist Risk Alert in Firestore
        alert_id = f"alert_{student.id}_{analysis_period.replace('-', '_')}"
        now = datetime.now(tz=timezone.utc)

        signals_summary = {
            "recent_attendance_rate": trends.recent_attendance_rate,
            "baseline_attendance_rate": baseline.baseline_attendance_rate,
            "attendance_delta": trends.attendance_delta,
            "recent_homework_completion_rate": trends.recent_homework_completion_rate,
            "baseline_homework_completion_rate": baseline.baseline_homework_completion_rate,
            "homework_delta": trends.homework_delta,
            "recent_test_average": trends.recent_test_average,
            "baseline_test_average": baseline.baseline_test_average,
            "test_delta": trends.test_delta,
            "consecutive_dropping_weeks": trends.consecutive_dropping_weeks,
        }

        risk_alert = RiskAlert(
            id=alert_id,
            school_id=student.school_id,
            class_id=student.class_id,
            student_id=student.id,
            risk_score=score_output.risk_score,
            risk_level=score_output.risk_level,
            model_version=score_output.model_version,
            reasons=[r.model_dump() for r in reasons],
            signals=signals_summary,
            analysis_period=analysis_period,
            status=AlertStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        cls._alerts_collection().document(alert_id).set(risk_alert.to_firestore())

        return StudentRiskAnalysisResponse(
            student_id=student.id,
            school_id=student.school_id,
            class_id=student.class_id,
            risk_score=score_output.risk_score,
            risk_level=score_output.risk_level,
            model_version=score_output.model_version,
            analysis_period=analysis_period,
            reasons=reasons,
            weekly_signatures=signatures,
            baseline=baseline.model_dump(),
            trends=trends.model_dump(),
            alert=RiskAlertResponse.from_model(risk_alert),
        )

    @classmethod
    def analyze_class_risk(cls, class_id: str, school_id: str) -> ClassRiskSummaryResponse:
        """
        Run risk analysis across all students in a class and produce class cohort summary.
        """
        students = StudentService.list_class_students(class_id, limit=500)

        high_count = 0
        med_count = 0
        low_count = 0
        insufficient_count = 0
        alerts: List[RiskAlertResponse] = []

        for student in students:
            res = cls.analyze_student_risk(student)
            if res.alert:
                alerts.append(res.alert)

            if res.risk_level == RiskLevel.HIGH:
                high_count += 1
            elif res.risk_level == RiskLevel.MEDIUM:
                med_count += 1
            elif res.risk_level == RiskLevel.LOW:
                low_count += 1
            elif res.risk_level == RiskLevel.INSUFFICIENT_DATA:
                insufficient_count += 1

        return ClassRiskSummaryResponse(
            class_id=class_id,
            school_id=school_id,
            total_students=len(students),
            high_risk_count=high_count,
            medium_risk_count=med_count,
            low_risk_count=low_count,
            insufficient_data_count=insufficient_count,
            alerts=alerts,
        )

    @classmethod
    def get_student_latest_alert(cls, student_id: str) -> Optional[RiskAlert]:
        query = (
            cls._alerts_collection()
            .where("student_id", "==", student_id)
            .where("status", "==", AlertStatus.ACTIVE.value)
            .limit(1)
        )
        docs = list(query.stream())
        if not docs:
            return None
        return RiskAlert.from_firestore(docs[0].id, docs[0].to_dict())

    @classmethod
    def get_student_alert_history(
        cls, student_id: str, skip: int = 0, limit: int = 50
    ) -> List[RiskAlert]:
        docs = (
            cls._alerts_collection()
            .where("student_id", "==", student_id)
            .offset(skip)
            .limit(limit)
            .stream()
        )
        return [RiskAlert.from_firestore(doc.id, doc.to_dict()) for doc in docs]

    @classmethod
    def get_class_active_alerts(cls, class_id: str) -> List[RiskAlert]:
        docs = (
            cls._alerts_collection()
            .where("class_id", "==", class_id)
            .where("status", "==", AlertStatus.ACTIVE.value)
            .stream()
        )
        return [RiskAlert.from_firestore(doc.id, doc.to_dict()) for doc in docs]
