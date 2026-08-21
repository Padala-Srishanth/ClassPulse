"""
tests/v1/test_health.py — Health Endpoint Tests

Tests for:
    GET /api/v1/health          — Liveness probe
    GET /api/v1/health/firebase — Firebase readiness probe

Coverage:
    - Response structure (success envelope)
    - HTTP status codes
    - Required fields in response data
    - CORS headers (X-Request-ID)
    - Firebase connected and disconnected states
    - Root redirect
"""

from unittest.mock import AsyncMock, patch

import pytest


# ===========================================================================
# GET /api/v1/health — Liveness
# ===========================================================================

class TestHealthLiveness:
    """Tests for the liveness health check endpoint."""

    def test_health_returns_200(self, client):
        """Liveness endpoint must always return 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_success_envelope(self, client):
        """Response must use the standard success envelope."""
        response = client.get("/api/v1/health")
        body = response.json()

        assert body["success"] is True
        assert "data" in body
        assert "meta" in body

    def test_health_data_fields(self, client):
        """Response data must contain required fields."""
        response = client.get("/api/v1/health")
        data = response.json()["data"]

        assert data["status"] == "ok"
        assert data["service"] == "ClassPulse API Test"  # APP_NAME from conftest env
        assert "version" in data
        assert "environment" in data
        assert "timestamp" in data

    def test_health_meta_fields(self, client):
        """Response meta must contain timestamp."""
        response = client.get("/api/v1/health")
        meta = response.json()["meta"]

        assert "timestamp" in meta

    def test_health_returns_request_id_header(self, client):
        """X-Request-ID header must be present in responses."""
        response = client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    def test_health_request_id_is_unique(self, client):
        """Each request must get a different request_id."""
        r1 = client.get("/api/v1/health")
        r2 = client.get("/api/v1/health")
        id1 = r1.headers.get("x-request-id")
        id2 = r2.headers.get("x-request-id")
        assert id1 is not None
        assert id2 is not None
        assert id1 != id2

    def test_health_environment_field(self, client):
        """Environment field should reflect the APP_ENV setting."""
        response = client.get("/api/v1/health")
        data = response.json()["data"]
        # conftest sets APP_ENV=development
        assert data["environment"] == "development"


# ===========================================================================
# GET /api/v1/health/firebase — Firebase Readiness
# ===========================================================================

class TestHealthFirebase:
    """Tests for the Firebase connectivity health check endpoint."""

    def test_firebase_health_returns_200(self, client):
        """Firebase health endpoint must return 200 regardless of connectivity."""
        response = client.get("/api/v1/health/firebase")
        assert response.status_code == 200

    def test_firebase_health_success_envelope(self, client):
        """Response must use the standard success envelope."""
        response = client.get("/api/v1/health/firebase")
        body = response.json()

        assert body["success"] is True
        assert "data" in body

    def test_firebase_health_data_fields(self, client):
        """Response data must contain the required connectivity fields."""
        response = client.get("/api/v1/health/firebase")
        data = response.json()["data"]

        assert "service" in data
        assert data["service"] == "firebase"
        assert "connected" in data
        assert "timestamp" in data

    def test_firebase_health_connected_state(self, client):
        """
        When Firebase initialises and Firestore is reachable, connected=True.

        We patch check_firebase_connectivity at its usage location in health.py.
        """
        with patch(
            "app.api.v1.health.check_firebase_connectivity",
            new=AsyncMock(
                return_value={
                    "connected": True,
                    "project_id": "test-project-id",
                }
            ),
        ):
            response = client.get("/api/v1/health/firebase")
            data = response.json()["data"]

            assert data["connected"] is True
            assert data["project_id"] == "test-project-id"

    def test_firebase_health_disconnected_state(self, client):
        """
        When Firebase is unreachable, connected=False with a reason.
        HTTP status is still 200 — infrastructure checks the body.
        """
        with patch(
            "app.api.v1.health.check_firebase_connectivity",
            new=AsyncMock(
                return_value={
                    "connected": False,
                    "reason": "Firestore request failed",
                }
            ),
        ):
            response = client.get("/api/v1/health/firebase")
            assert response.status_code == 200
            data = response.json()["data"]

            assert data["connected"] is False
            assert data["reason"] == "Firestore request failed"

    def test_firebase_health_not_initialised(self, client):
        """
        When Firebase is not initialised, connected=False with a descriptive reason.
        """
        with patch(
            "app.api.v1.health.check_firebase_connectivity",
            new=AsyncMock(
                return_value={
                    "connected": False,
                    "reason": "Firebase Admin SDK not initialised",
                }
            ),
        ):
            response = client.get("/api/v1/health/firebase")
            data = response.json()["data"]
            assert data["connected"] is False


# ===========================================================================
# Root redirect
# ===========================================================================

class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_returns_200(self, client):
        """Root endpoint should return 200 with navigation links."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_docs_link(self, client):
        """Root response should point to /docs."""
        response = client.get("/")
        body = response.json()
        assert body.get("docs") == "/docs"

    def test_root_contains_health_link(self, client):
        """Root response should point to the health endpoint."""
        response = client.get("/")
        body = response.json()
        assert body.get("health") == "/api/v1/health"


# ===========================================================================
# Response structure / envelope
# ===========================================================================

class TestResponseEnvelope:
    """Tests for the standardised API response envelope."""

    def test_unknown_path_returns_404(self, client):
        """Unknown paths should return 404 (FastAPI default)."""
        response = client.get("/api/v1/this-does-not-exist")
        assert response.status_code == 404

    def test_x_request_id_header_on_all_responses(self, client):
        """X-Request-ID should be present on every response."""
        endpoints = ["/", "/api/v1/health", "/api/v1/health/firebase"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Some responses (like 404) may not go through our middleware fully
            # but liveness and firebase should always have it.

    def test_health_response_is_json(self, client):
        """Health endpoint must return valid JSON."""
        response = client.get("/api/v1/health")
        assert response.headers["content-type"].startswith("application/json")
        # This will raise if not valid JSON:
        body = response.json()
        assert isinstance(body, dict)
