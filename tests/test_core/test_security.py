"""
Tests for core security utilities (password hashing, JWT tokens).

Ensures cryptographic operations are working correctly and securely.
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification."""

    @pytest.mark.unit
    def test_hash_password_creates_different_hashes(self):
        """Different hashes should be generated for the same password."""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # Hashes should be different but both should verify
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    @pytest.mark.unit
    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "CorrectPassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    @pytest.mark.unit
    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        password = "CorrectPassword123"
        hashed = get_password_hash(password)
        assert verify_password("WrongPassword123", hashed) is False

    @pytest.mark.unit
    def test_verify_password_empty_string(self):
        """Empty password should fail verification."""
        password = "CorrectPassword123"
        hashed = get_password_hash(password)
        assert verify_password("", hashed) is False

    @pytest.mark.unit
    def test_verify_password_special_characters(self):
        """Password with special characters should hash and verify correctly."""
        password = "P@ssw0rd!#$%&*()"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("P@ssw0rd!#$%&*", hashed) is False

    @pytest.mark.unit
    def test_verify_password_unicode(self):
        """Password with unicode characters should work."""
        password = "پاس‌ورڈ123اردو"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


class TestAccessToken:
    """Test JWT access token creation and validation."""

    @pytest.mark.unit
    def test_create_access_token_success(self):
        """Token should be created with valid expire time."""
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        
        assert isinstance(token, str)
        assert len(token.split('.')) == 3  # JWT format: header.payload.signature

    @pytest.mark.unit
    def test_create_access_token_contains_exp(self):
        """Token should contain expiration claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert "exp" in decoded
        assert "sub" in decoded
        assert decoded["sub"] == "testuser"

    @pytest.mark.unit
    def test_create_access_token_expiration_time(self):
        """Token expiration should be set to ACCESS_TOKEN_EXPIRE_MINUTES."""
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Token should expire in approximately ACCESS_TOKEN_EXPIRE_MINUTES
        expires_in = exp_time - now
        expected_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        # Allow 5 second variance
        assert abs(expires_in.total_seconds() - expected_seconds) < 5

    @pytest.mark.unit
    def test_create_access_token_multiple_claims(self):
        """Token should preserve multiple data claims."""
        data = {
            "sub": "testuser",
            "user_id": "123",
            "role": "dispatcher",
        }
        token = create_access_token(data=data)
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        assert decoded["sub"] == "testuser"
        assert decoded["user_id"] == "123"
        assert decoded["role"] == "dispatcher"

    @pytest.mark.unit
    def test_create_access_token_invalid_secret_raises_error(self):
        """Decoding with wrong secret should raise JWTError."""
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong_secret", algorithms=["HS256"])

    @pytest.mark.unit
    def test_create_access_token_integrity(self):
        """Tampering with token should raise JWTError."""
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        
        # Tamper with the token
        tampered = token[:-10] + "hacked1234"
        
        with pytest.raises(JWTError):
            jwt.decode(tampered, settings.SECRET_KEY, algorithms=["HS256"])
