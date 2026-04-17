"""
Tests for health check and observability endpoints.

Tests system health status, readiness checks, and monitoring endpoints.
"""

import pytest


class TestHealthCheckEndpoint:
    """Test GET /health endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_health_check_returns_ok(self, client):
        """Health check should return 200 OK."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_health_check_includes_version(self, client):
        """Health check should include version info."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have version or service info
        assert "version" in data or "service" in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_health_check_no_auth_required(self, client):
        """Health check should not require authentication."""
        response = client.get("/health")
        
        # Should not be 401
        assert response.status_code != 401


class TestReadinessProbe:
    """Test readiness and liveness probes."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_readiness_probe_success(self, client):
        """Readiness probe should indicate system is ready."""
        response = client.get("/health/ready")
        
        # Should return 200 if ready, 503 if not
        assert response.status_code in [200, 503]

    @pytest.mark.unit
    @pytest.mark.api
    def test_liveness_probe_success(self, client):
        """Liveness probe should indicate system is alive."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
