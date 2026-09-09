"""
tests/v1/test_uploads.py — Image & Attachment Upload Tests
"""

import io
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


def test_upload_image_success(app, mock_student_token):
    """Test authenticated user can upload a valid image."""
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            files = {
                "file": ("question_diagram.png", io.BytesIO(fake_png), "image/png")
            }
            res = client.post("/api/v1/uploads/image", files=files)
            assert res.status_code == 201, res.text
            data = res.json()["data"]
            assert "url" in data
            assert data["filename"] == "question_diagram.png"
            assert data["content_type"] == "image/png"
            assert data["size"] == len(fake_png)

            # Now test retrieving the file
            download_url = data["url"]
            # download_url is like "/api/v1/uploads/files/{filename}"
            get_res = client.get(download_url)
            assert get_res.status_code == 200, get_res.text
            assert get_res.headers["content-type"] == "image/png"
            assert get_res.content == fake_png


def test_upload_image_invalid_type(app, mock_student_token):
    """Test uploading an unsupported MIME type is rejected."""
    fake_text = b"This is a text file, not an image."

    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            files = {
                "file": ("notes.txt", io.BytesIO(fake_text), "text/plain")
            }
            res = client.post("/api/v1/uploads/image", files=files)
            assert res.status_code == 400, res.text
            assert "INVALID_IMAGE_TYPE" in res.text


def test_upload_image_empty_file(app, mock_student_token):
    """Test uploading an empty file is rejected."""
    with patch("app.core.security.verify_firebase_token", new=AsyncMock(return_value=mock_student_token)):
        with TestClient(app, headers={"Authorization": "Bearer mock"}, raise_server_exceptions=False) as client:
            files = {
                "file": ("empty.png", io.BytesIO(b""), "image/png")
            }
            res = client.post("/api/v1/uploads/image", files=files)
            assert res.status_code == 400, res.text
            assert "EMPTY_FILE" in res.text


def test_get_nonexistent_file(app):
    """Test requesting a file that does not exist returns 404."""
    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/api/v1/uploads/files/nonexistent_file_12345.png")
        assert res.status_code == 404
        assert "FILE_NOT_FOUND" in res.text


def test_get_file_path_traversal_protection(app):
    """Test directory traversal attack is blocked."""
    with TestClient(app, raise_server_exceptions=False) as client:
        res = client.get("/api/v1/uploads/files/../../secret.txt")
        assert res.status_code in (404, 400)
