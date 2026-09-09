"""
app.api.v1.uploads — Image & Attachment Upload Endpoints

Endpoints:
  POST /uploads/image          - Upload an image file (JPEG, PNG, WebP, GIF)
  GET  /uploads/files/{name}   - Retrieve an uploaded file (local disk fallback)
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, get_current_user
from app.services.upload_service import UploadService
from app.utils.responses import success_response

router = APIRouter(tags=["Uploads"])


@router.post("/image", summary="Upload a photo / image attachment", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload (JPEG, PNG, WebP, GIF)"),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload a photo for doubts or replies.
    Returns the file URL and metadata.
    """
    result = await UploadService.save_image(file=file, folder="doubts")
    return success_response(data=result, status_code=status.HTTP_201_CREATED)


@router.get("/files/{filename}", summary="Retrieve an uploaded file")
async def get_uploaded_file(filename: str):
    """
    Serve an uploaded file stored on local disk.
    Protected against directory traversal.
    """
    file_path = UploadService.get_file_path(filename)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "FILE_NOT_FOUND", "message": "The requested file does not exist."},
        )

    mime_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        path=str(file_path),
        media_type=mime_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=86400"},
    )
