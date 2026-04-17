"""
Tests for authentication service layer.

Tests user authentication, token generation, and user management.
"""

import pytest
from app.services import auth as auth_service
from app.db.models import User
from app.core.security import get_password_hash, verify_password


class TestAuthenticateService:
    """Test authentication logic."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_authenticate_valid_credentials(self, user_repo, test_user):
        """Valid credentials should authenticate successfully."""
        result = auth_service.authenticate(
            username="testdispatcher",
            password="testpassword123",
            users=user_repo,
        )
        
        assert result is not None
        assert "access_token" in result
        assert result["token_type"] == "bearer"

    @pytest.mark.unit
    @pytest.mark.service
    def test_authenticate_invalid_password(self, user_repo, test_user):
        """Invalid password should raise error."""
        with pytest.raises(Exception):  # HTTPException or similar
            auth_service.authenticate(
                username="testdispatcher",
                password="wrongpassword",
                users=user_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_authenticate_nonexistent_user(self, user_repo):
        """Nonexistent user should raise error."""
        with pytest.raises(Exception):
            auth_service.authenticate(
                username="nonexistent",
                password="anypassword",
                users=user_repo,
            )

    @pytest.mark.unit
    @pytest.mark.service
    def test_authenticate_inactive_user(self, user_repo, test_user_inactive):
        """Inactive user should not authenticate."""
        with pytest.raises(Exception):
            auth_service.authenticate(
                username="inactivedispatcher",
                password="testpassword123",
                users=user_repo,
            )


class TestEnsureDefaultDispatcher:
    """Test default dispatcher creation."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_ensure_default_dispatcher_creates_user(self, db_session, user_repo):
        """Calling ensure should create dispatcher if not exists."""
        result = auth_service.ensure_default_dispatcher(
            users=user_repo,
            username="testdispatcher",
            default_password="testpass123",
        )
        
        assert result is not None
        # User should now exist in database
        user = user_repo.get_by_username("testdispatcher")
        assert user is not None
        assert user.username == "testdispatcher"

    @pytest.mark.unit
    @pytest.mark.service
    def test_ensure_default_dispatcher_idempotent(self, user_repo):
        """Ensure should be idempotent."""
        # Call twice
        result1 = auth_service.ensure_default_dispatcher(
            users=user_repo,
            username="dispatcher",
            default_password="pass123",
        )
        
        result2 = auth_service.ensure_default_dispatcher(
            users=user_repo,
            username="dispatcher",
            default_password="pass123",
        )
        
        # Both should succeed
        assert result1 is not None
        assert result2 is not None

    @pytest.mark.unit
    @pytest.mark.service
    def test_ensure_default_dispatcher_sets_password(self, user_repo):
        """Default dispatcher should have correct password."""
        auth_service.ensure_default_dispatcher(
            users=user_repo,
            username="dispatcher",
            default_password="rescue1122",
        )
        
        user = user_repo.get_by_username("dispatcher")
        assert user is not None
        assert verify_password("rescue1122", user.password_hash)


class TestGetCurrentUser:
    """Test getting current authenticated user."""

    @pytest.mark.unit
    @pytest.mark.service
    def test_get_current_user_from_token(self, user_repo, access_token, test_user):
        """Current user should be extractable from token."""
        # This would typically be tested at the dependency level
        # But we can test the underlying logic
        from jose import jwt
        from app.core.config import settings
        
        decoded = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"])
        username = decoded.get("sub")
        
        user = user_repo.get_by_username(username)
        assert user is not None
        assert user.username == "testdispatcher"
