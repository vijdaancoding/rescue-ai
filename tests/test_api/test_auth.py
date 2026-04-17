"""
Tests for authentication API endpoints.

Tests login, token generation, and dispatcher setup.
"""

import pytest
from uuid import uuid4

from app.db.models import User
from app.core.security import get_password_hash


class TestAuthLogin:
    """Test /auth/login endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_success(self, client, test_user):
        """Successful login should return access token."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testdispatcher",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 20

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_wrong_password(self, client, test_user):
        """Login with wrong password should fail."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testdispatcher",
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert "detail" in response.json()

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_nonexistent_user(self, client):
        """Login with nonexistent user should fail."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistentuser",
                "password": "anypassword",
            },
        )
        
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_inactive_user(self, client, test_user_inactive):
        """Login with inactive user should fail."""
        response = client.post(
            "/auth/login",
            data={
                "username": "inactivedispatcher",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_empty_username(self, client):
        """Login with empty username should fail."""
        response = client.post(
            "/auth/login",
            data={
                "username": "",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code in [400, 422]

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_empty_password(self, client, test_user):
        """Login with empty password should fail."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testdispatcher",
                "password": "",
            },
        )
        
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_login_token_is_valid_jwt(self, client, test_user):
        """Returned token should be a valid JWT."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testdispatcher",
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # JWT format should be: header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3
        # Each part should be non-empty
        for part in parts:
            assert len(part) > 0


class TestSetupDispatcher:
    """Test /auth/setup-dispatcher endpoint."""

    @pytest.mark.unit
    @pytest.mark.api
    def test_setup_dispatcher_creates_user(self, client, db_session):
        """Setup should create a default dispatcher user."""
        # Delete any existing dispatcher
        from app.repositories.users import UserRepository
        repo = UserRepository(db_session)
        existing = repo.get_by_username("dispatcher")
        if existing:
            db_session.delete(existing)
            db_session.commit()
        
        response = client.post("/auth/setup-dispatcher")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "username" in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_setup_dispatcher_idempotent(self, client, db_session):
        """Setup should be idempotent (safe to call multiple times)."""
        # First call
        response1 = client.post("/auth/setup-dispatcher")
        assert response1.status_code == 200
        
        # Second call should also succeed
        response2 = client.post("/auth/setup-dispatcher")
        assert response2.status_code == 200

    @pytest.mark.unit
    @pytest.mark.api
    def test_setup_dispatcher_can_login_after(self, client, db_session):
        """Created dispatcher should be able to login."""
        # Setup
        client.post("/auth/setup-dispatcher")
        
        # Try to login
        response = client.post(
            "/auth/login",
            data={
                "username": "dispatcher",
                "password": "rescue1122",
            },
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
