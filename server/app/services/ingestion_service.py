"""
app.services.ingestion_service — CSV Data Ingestion Service
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import re
from typing import Dict, List, Optional, Set, Tuple
import uuid

from fastapi import HTTPException, UploadFile, status

from app.core.firebase import get_firestore_client
from app.core.logging import get_logger
from app.models.academic import (
    AttendanceRecord,
    AttendanceStatus,
    HomeworkRecord,
    HomeworkStatus,
    TestScoreRecord,
)
from app.models.student import Student
from app.schemas.ingestion import ImportSummary, RowError
from app.services.student_service import StudentService

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class IngestionService:
    @classmethod
    async def validate_file(cls, file: UploadFile) -> str:
        """Validate filename, size, and decode CSV content."""
        if not file.filename or not file.filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_FILE_TYPE", "message": "Only CSV files are allowed."},
            )

        content = await file.read()
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "EMPTY_FILE", "message": "Uploaded CSV file is empty."},
            )

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "FILE_TOO_LARGE", "message": "File size exceeds 5 MB limit."},
            )

        # Attempt UTF-8 then fallback to Latin-1
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content.decode("latin-1")
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"code": "INVALID_ENCODING", "message": "Unable to decode CSV file. Please use UTF-8."},
                )

    @classmethod
    def _parse_csv(cls, text: str) -> List[Dict[str, str]]:
        """Parse CSV text into list of dicts with stripped keys & values."""
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            return []
        
        # Clean header keys (strip whitespace, lower/normalize)
        rows = []
        for row in reader:
            cleaned_row = {
                (k.strip() if k else ""): (v.strip() if v else "")
                for k, v in row.items() if k
            }
            if any(cleaned_row.values()):  # Ignore empty lines
                rows.append(cleaned_row)
        return rows

    @classmethod
    def _write_batches(cls, write_ops: List[Tuple[str, str, dict]]):
        """
        Execute Firestore writes in batches (max 450 items per batch).
        write_ops is a list of (parent_doc_path, subcollection_name, record_dict).
        """
        db = get_firestore_client()
        batch_size = 450
        
        for i in range(0, len(write_ops), batch_size):
            chunk = write_ops[i:i + batch_size]
            batch = db.batch()
            for student_id, subcollection, record_data in chunk:
                doc_id = record_data["id"]
                data = {k: v for k, v in record_data.items() if k != "id"}
                doc_ref = (
                    db.collection("students")
                    .document(student_id)
                    .collection(subcollection)
                    .document(doc_id)
                )
                batch.set(doc_ref, data)
            batch.commit()

    @classmethod
    def _log_import(
        cls, batch_id: str, school_id: str, import_type: str, summary: ImportSummary
    ):
        """Write audit log entry into import_logs collection."""
        db = get_firestore_client()
        now = datetime.now(tz=timezone.utc)
        
        log_data = {
            "batch_id": batch_id,
            "school_id": school_id,
            "import_type": import_type,
            "total_rows": summary.total_rows,
            "successful_rows": summary.successful_rows,
            "failed_rows": summary.failed_rows,
            "duplicate_rows": summary.duplicate_rows,
            "created_at": now,
        }
        db.collection("import_logs").document(batch_id).set(log_data)

    # -------------------------------------------------------------------------
    # Attendance Ingestion
    # Expected columns: student_code, date, status
    # -------------------------------------------------------------------------
    @classmethod
    async def ingest_attendance(
        cls, school_id: str, file: UploadFile
    ) -> ImportSummary:
        text = await cls.validate_file(file)
        rows = cls._parse_csv(text)
        
        required_cols = {"student_code", "date", "status"}
        if not rows:
            return ImportSummary(
                batch_id=str(uuid.uuid4()),
                total_rows=0,
                successful_rows=0,
                failed_rows=0,
                duplicate_rows=0,
                errors=[RowError(row_number=1, error="CSV has no data rows.")],
            )
            
        header_cols = set(rows[0].keys())
        if not required_cols.issubset(header_cols):
            missing = required_cols - header_cols
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MISSING_COLUMNS",
                    "message": f"CSV is missing required columns: {', '.join(missing)}",
                },
            )

        batch_id = str(uuid.uuid4())
        errors: List[RowError] = []
        seen_ids: Set[str] = set()
        write_ops: List[Tuple[str, str, dict]] = []
        duplicate_count = 0
        now = datetime.now(tz=timezone.utc)

        # Cache student lookup to avoid duplicate queries
        student_cache: Dict[str, Optional[Student]] = {}

        for idx, row in enumerate(rows, start=2):
            code = row.get("student_code", "").strip()
            date_str = row.get("date", "").strip()
            status_str = row.get("status", "").strip().upper()

            if not code or not date_str or not status_str:
                errors.append(RowError(row_number=idx, error="Missing required values in row."))
                continue

            if not DATE_REGEX.match(date_str):
                errors.append(RowError(row_number=idx, error=f"Invalid date format '{date_str}', expected YYYY-MM-DD."))
                continue

            try:
                att_status = AttendanceStatus(status_str)
            except ValueError:
                errors.append(RowError(row_number=idx, error=f"Invalid status '{status_str}'. Allowed: PRESENT, ABSENT, LATE, EXCUSED."))
                continue

            if code not in student_cache:
                student_cache[code] = StudentService.get_student_by_code(school_id, code)

            student = student_cache[code]
            if not student:
                errors.append(RowError(row_number=idx, error=f"Student code '{code}' not found in this school."))
                continue

            record_id = AttendanceRecord.make_id(student.id, date_str)
            if record_id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(record_id)

            rec = AttendanceRecord(
                id=record_id,
                student_id=student.id,
                school_id=school_id,
                class_id=student.class_id,
                date=date_str,
                status=att_status,
                source="csv",
                import_batch_id=batch_id,
                created_at=now,
            )
            write_ops.append((student.id, "attendance", rec.to_firestore() | {"id": record_id}))

        if write_ops:
            cls._write_batches(write_ops)

        summary = ImportSummary(
            batch_id=batch_id,
            total_rows=len(rows),
            successful_rows=len(write_ops),
            failed_rows=len(errors),
            duplicate_rows=duplicate_count,
            errors=errors[:100],  # Cap error list in response
        )
        cls._log_import(batch_id, school_id, "attendance", summary)
        return summary

    # -------------------------------------------------------------------------
    # Homework Ingestion
    # Expected columns: student_code, assignment_id, assignment_date, status
    # -------------------------------------------------------------------------
    @classmethod
    async def ingest_homework(
        cls, school_id: str, file: UploadFile
    ) -> ImportSummary:
        text = await cls.validate_file(file)
        rows = cls._parse_csv(text)
        
        required_cols = {"student_code", "assignment_id", "assignment_date", "status"}
        if not rows:
            return ImportSummary(
                batch_id=str(uuid.uuid4()),
                total_rows=0,
                successful_rows=0,
                failed_rows=0,
                duplicate_rows=0,
                errors=[RowError(row_number=1, error="CSV has no data rows.")],
            )
            
        header_cols = set(rows[0].keys())
        if not required_cols.issubset(header_cols):
            missing = required_cols - header_cols
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MISSING_COLUMNS",
                    "message": f"CSV is missing required columns: {', '.join(missing)}",
                },
            )

        batch_id = str(uuid.uuid4())
        errors: List[RowError] = []
        seen_ids: Set[str] = set()
        write_ops: List[Tuple[str, str, dict]] = []
        duplicate_count = 0
        now = datetime.now(tz=timezone.utc)
        student_cache: Dict[str, Optional[Student]] = {}

        for idx, row in enumerate(rows, start=2):
            code = row.get("student_code", "").strip()
            assignment_id = row.get("assignment_id", "").strip()
            date_str = row.get("assignment_date", "").strip()
            status_str = row.get("status", "").strip().upper()

            if not code or not assignment_id or not date_str or not status_str:
                errors.append(RowError(row_number=idx, error="Missing required values in row."))
                continue

            if not DATE_REGEX.match(date_str):
                errors.append(RowError(row_number=idx, error=f"Invalid date format '{date_str}', expected YYYY-MM-DD."))
                continue

            try:
                hw_status = HomeworkStatus(status_str)
            except ValueError:
                errors.append(RowError(row_number=idx, error=f"Invalid status '{status_str}'. Allowed: COMPLETED, NOT_COMPLETED, LATE."))
                continue

            if code not in student_cache:
                student_cache[code] = StudentService.get_student_by_code(school_id, code)

            student = student_cache[code]
            if not student:
                errors.append(RowError(row_number=idx, error=f"Student code '{code}' not found in this school."))
                continue

            record_id = HomeworkRecord.make_id(student.id, assignment_id, date_str)
            if record_id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(record_id)

            rec = HomeworkRecord(
                id=record_id,
                student_id=student.id,
                school_id=school_id,
                class_id=student.class_id,
                assignment_id=assignment_id,
                assignment_date=date_str,
                status=hw_status,
                source="csv",
                import_batch_id=batch_id,
                created_at=now,
            )
            write_ops.append((student.id, "homework", rec.to_firestore() | {"id": record_id}))

        if write_ops:
            cls._write_batches(write_ops)

        summary = ImportSummary(
            batch_id=batch_id,
            total_rows=len(rows),
            successful_rows=len(write_ops),
            failed_rows=len(errors),
            duplicate_rows=duplicate_count,
            errors=errors[:100],
        )
        cls._log_import(batch_id, school_id, "homework", summary)
        return summary

    # -------------------------------------------------------------------------
    # Test Score Ingestion
    # Expected columns: student_code, subject, assessment_name, assessment_date, score, max_score
    # -------------------------------------------------------------------------
    @classmethod
    async def ingest_test_scores(
        cls, school_id: str, file: UploadFile
    ) -> ImportSummary:
        text = await cls.validate_file(file)
        rows = cls._parse_csv(text)
        
        required_cols = {"student_code", "subject", "assessment_name", "assessment_date", "score", "max_score"}
        if not rows:
            return ImportSummary(
                batch_id=str(uuid.uuid4()),
                total_rows=0,
                successful_rows=0,
                failed_rows=0,
                duplicate_rows=0,
                errors=[RowError(row_number=1, error="CSV has no data rows.")],
            )
            
        header_cols = set(rows[0].keys())
        if not required_cols.issubset(header_cols):
            missing = required_cols - header_cols
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MISSING_COLUMNS",
                    "message": f"CSV is missing required columns: {', '.join(missing)}",
                },
            )

        batch_id = str(uuid.uuid4())
        errors: List[RowError] = []
        seen_ids: Set[str] = set()
        write_ops: List[Tuple[str, str, dict]] = []
        duplicate_count = 0
        now = datetime.now(tz=timezone.utc)
        student_cache: Dict[str, Optional[Student]] = {}

        for idx, row in enumerate(rows, start=2):
            code = row.get("student_code", "").strip()
            subject = row.get("subject", "").strip()
            assessment_name = row.get("assessment_name", "").strip()
            date_str = row.get("assessment_date", "").strip()
            score_str = row.get("score", "").strip()
            max_score_str = row.get("max_score", "").strip()

            if not code or not subject or not assessment_name or not date_str or not score_str or not max_score_str:
                errors.append(RowError(row_number=idx, error="Missing required values in row."))
                continue

            if not DATE_REGEX.match(date_str):
                errors.append(RowError(row_number=idx, error=f"Invalid date format '{date_str}', expected YYYY-MM-DD."))
                continue

            try:
                score = float(score_str)
                max_score = float(max_score_str)
            except ValueError:
                errors.append(RowError(row_number=idx, error=f"Score and max_score must be numeric (got score='{score_str}', max_score='{max_score_str}')."))
                continue

            if score < 0:
                errors.append(RowError(row_number=idx, error=f"Score cannot be negative (got '{score}')."))
                continue

            if max_score <= 0:
                errors.append(RowError(row_number=idx, error=f"Max score must be greater than 0 (got '{max_score}')."))
                continue

            if score > max_score:
                errors.append(RowError(row_number=idx, error=f"Score ({score}) exceeds max score ({max_score})."))
                continue

            if code not in student_cache:
                student_cache[code] = StudentService.get_student_by_code(school_id, code)

            student = student_cache[code]
            if not student:
                errors.append(RowError(row_number=idx, error=f"Student code '{code}' not found in this school."))
                continue

            record_id = TestScoreRecord.make_id(student.id, subject, assessment_name, date_str)
            if record_id in seen_ids:
                duplicate_count += 1
                continue
            seen_ids.add(record_id)

            rec = TestScoreRecord(
                id=record_id,
                student_id=student.id,
                school_id=school_id,
                class_id=student.class_id,
                subject=subject,
                assessment_name=assessment_name,
                assessment_date=date_str,
                score=score,
                max_score=max_score,
                source="csv",
                import_batch_id=batch_id,
                created_at=now,
            )
            write_ops.append((student.id, "test_scores", rec.to_firestore() | {"id": record_id}))

        if write_ops:
            cls._write_batches(write_ops)

        summary = ImportSummary(
            batch_id=batch_id,
            total_rows=len(rows),
            successful_rows=len(write_ops),
            failed_rows=len(errors),
            duplicate_rows=duplicate_count,
            errors=errors[:100],
        )
        cls._log_import(batch_id, school_id, "test_scores", summary)
        return summary
