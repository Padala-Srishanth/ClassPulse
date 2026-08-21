"""
tests/v1/test_ml_features.py — Weekly Feature Extraction & Aggregation Tests
"""

from app.ml.features import FeatureExtractor, get_iso_week
from app.models.academic import (
    AttendanceRecord,
    AttendanceStatus,
    HomeworkRecord,
    HomeworkStatus,
    TestScoreRecord,
)


def test_get_iso_week_conversion():
    assert get_iso_week("2024-09-02") == "2024-W36"
    assert get_iso_week("2024-09-08") == "2024-W36"
    assert get_iso_week("2024-09-09") == "2024-W37"


def test_feature_extractor_aggregates_rates():
    # 3 days in Week 36
    att_records = [
        AttendanceRecord(
            id="a1", student_id="s1", school_id="sch1", class_id="c1",
            date="2024-09-02", status=AttendanceStatus.PRESENT
        ),
        AttendanceRecord(
            id="a2", student_id="s1", school_id="sch1", class_id="c1",
            date="2024-09-03", status=AttendanceStatus.ABSENT
        ),
        AttendanceRecord(
            id="a3", student_id="s1", school_id="sch1", class_id="c1",
            date="2024-09-04", status=AttendanceStatus.LATE
        ),
    ]

    # 2 homeworks in Week 36
    hw_records = [
        HomeworkRecord(
            id="h1", student_id="s1", school_id="sch1", class_id="c1",
            assignment_id="hw1", assignment_date="2024-09-02", status=HomeworkStatus.COMPLETED
        ),
        HomeworkRecord(
            id="h2", student_id="s1", school_id="sch1", class_id="c1",
            assignment_id="hw2", assignment_date="2024-09-04", status=HomeworkStatus.NOT_COMPLETED
        ),
    ]

    # 1 test in Week 36
    test_records = [
        TestScoreRecord(
            id="t1", student_id="s1", school_id="sch1", class_id="c1",
            subject="Math", assessment_name="Quiz 1", assessment_date="2024-09-05",
            score=40.0, max_score=50.0  # 80%
        )
    ]

    signatures = FeatureExtractor.build_weekly_signatures(
        attendance_records=att_records,
        homework_records=hw_records,
        test_records=test_records,
    )

    assert len(signatures) == 1
    sig = signatures[0]
    assert sig.week_key == "2024-W36"
    # Present (1.0) + Late (0.5) = 1.5 out of 3 -> 50.0%
    assert sig.attendance_rate == 50.0
    # Completed (1.0) out of 2 -> 50.0%
    assert sig.homework_completion_rate == 50.0
    # Test average = 80.0%
    assert sig.average_test_percentage == 80.0
    assert sig.test_count == 1


def test_missing_data_distinguished_from_zero():
    # Only attendance recorded in Week 37
    att_records = [
        AttendanceRecord(
            id="a4", student_id="s1", school_id="sch1", class_id="c1",
            date="2024-09-09", status=AttendanceStatus.PRESENT
        ),
    ]

    signatures = FeatureExtractor.build_weekly_signatures(
        attendance_records=att_records,
        homework_records=[],
        test_records=[],
    )

    assert len(signatures) == 1
    sig = signatures[0]
    assert sig.attendance_rate == 100.0
    # Homework and tests should be None, NOT 0.0!
    assert sig.homework_completion_rate is None
    assert sig.average_test_percentage is None
    assert sig.test_count == 0
