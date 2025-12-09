"""Unit tests for app/security.py"""
import pytest
from datetime import timedelta
import jwt
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    revoke_access_token,
    JWT_SECRET,
    JWT_ALGORITHM
)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        hashed = hash_password("mypassword123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that hashing the same password produces different hashes."""
        password = "mypassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts

    def test_verify_password_correct(self):
        """Test verifying a correct password."""
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying an incorrect password."""
        password = "mypassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty(self):
        """Test verifying with empty password."""
        hashed = hash_password("mypassword123")
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        token = create_access_token(user_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test creating a token with custom expiration."""
        token = create_access_token(user_id=1, expires_delta=timedelta(minutes=5))
        assert isinstance(token, str)
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "1"

    def test_verify_access_token_valid(self):
        """Test verifying a valid token."""
        token = create_access_token(user_id=42)
        user_id = verify_access_token(token)
        assert user_id == 42

    def test_verify_access_token_invalid_signature(self):
        """Test verifying a token with invalid signature."""
        token = create_access_token(user_id=1)
        # Tamper with the token by replacing a character
        tampered_token = token[:-5] + "XXXXX"
        user_id = verify_access_token(tampered_token)
        assert user_id is None

    def test_verify_access_token_malformed(self):
        """Test verifying a malformed token."""
        user_id = verify_access_token("not.a.token")
        assert user_id is None

    def test_verify_access_token_empty(self):
        """Test verifying an empty token."""
        user_id = verify_access_token("")
        assert user_id is None

    def test_verify_access_token_expired(self):
        """Test verifying an expired token."""
        # Create token that expires immediately
        token = create_access_token(user_id=1, expires_delta=timedelta(seconds=-1))
        user_id = verify_access_token(token)
        assert user_id is None

    def test_revoke_access_token(self):
        """Test revoking a token (no-op for stateless JWTs)."""
        token = create_access_token(user_id=1)
        result = revoke_access_token(token)
        assert result is None
        # Token should still be valid since revocation is a no-op
        user_id = verify_access_token(token)
        assert user_id == 1
