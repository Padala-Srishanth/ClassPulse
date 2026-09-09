"""
app.services.upload_service — Upload Service for Images and Attachments

Handles file validation, size limits, and dual storage (Firebase Storage with
automatic fallback to local persistent disk storage).
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Dict, Optional, Set

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.firebase import get_storage_bucket
from app.core.logging import get_logger

logger = get_logger(__name__)

# Allowed MIME types for photo / image sharing
ALLOWED_IMAGE_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

# 10 MB maximum upload size
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Base directory for local disk fallback
_CURRENT_DIR = Path(__file__).resolve().parent
_SERVER_ROOT = _CURRENT_DIR.parent.parent
UPLOAD_DIR = _SERVER_ROOT / "uploads" / "images"


class UploadService:
    """Service to handle photo uploads with Firebase Storage & local fallback."""

    @classmethod
    def _ensure_upload_dir(cls) -> Path:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        return UPLOAD_DIR

    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        name = os.path.basename(filename)
        # Remove any non-alphanumeric, dots, dashes, underscores
        clean = re.sub(r"[^\w\.-]", "_", name)
        return clean or "image.png"

    @classmethod
    async def save_image(
        cls,
        file: UploadFile,
        folder: str = "doubts",
    ) -> Dict[str, object]:
        """
        Validate and save an uploaded image file.

        Returns:
            Dict with {url, filename, content_type, size}
        """
        content_type = file.content_type or ""
        if content_type.lower() not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_IMAGE_TYPE",
                    "message": f"Unsupported file type '{content_type}'. Allowed types: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}",
                },
            )

        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "EMPTY_FILE", "message": "Uploaded file is empty."},
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
                },
            )

        original_filename = file.filename or "image.png"
        safe_name = cls._sanitize_filename(original_filename)
        unique_filename = f"{uuid.uuid4().hex}_{safe_name}"

        # 1. Attempt upload to Firebase Storage if available
        settings = get_settings()
        if settings.is_production and settings.FIREBASE_PROJECT_ID != "classpulse-demo":
            try:
                bucket = get_storage_bucket()
                blob = bucket.blob(f"uploads/{folder}/{unique_filename}")
                blob.upload_from_string(content, content_type=content_type)
                blob.make_public()
                public_url = blob.public_url
                logger.info("Image uploaded to Firebase Storage: %s", public_url)
                return {
                    "url": public_url,
                    "filename": original_filename,
                    "content_type": content_type,
                    "size": file_size,
                }
            except Exception as exc:
                logger.warning("Firebase Storage upload skipped/failed (%s). Falling back to local storage.", exc)

        # 2. Local disk fallback
        upload_dir = cls._ensure_upload_dir()
        file_path = upload_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(content)

        relative_url = f"/api/v1/uploads/files/{unique_filename}"
        logger.info("Image saved to local storage: %s -> %s", file_path, relative_url)

        return {
            "url": relative_url,
            "filename": original_filename,
            "content_type": content_type,
            "size": file_size,
        }

    @classmethod
    def get_file_path(cls, filename: str) -> Optional[Path]:
        """
        Safely resolve a file from the uploads directory.
        Guards against directory traversal attacks.
        """
        clean_name = os.path.basename(filename)
        resolved = (UPLOAD_DIR / clean_name).resolve()
        try:
            resolved.relative_to(UPLOAD_DIR.resolve())
        except ValueError:
            return None

        if resolved.is_file() and resolved.exists():
            return resolved
        return None
