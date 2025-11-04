"""Unit tests for security utilities"""

import pytest
from src.core.security import hash_password, verify_password, create_access_token, verify_access_token


def test_password_hashing():
    """Test password hashing and verification"""
    password = "securePassword123!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongPassword", hashed) is False


def test_jwt_token_creation_and_verification():
    """Test JWT token creation and verification"""
    # Note: JWT spec requires 'sub' to be a string, not an integer
    payload = {"sub": "12345", "username": "testuser"}
    token = create_access_token(data=payload)

    assert token is not None
    assert isinstance(token, str)

    decoded = verify_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "12345"
    assert decoded["username"] == "testuser"
    assert "exp" in decoded
    assert "iat" in decoded


def test_invalid_jwt_token():
    """Test invalid JWT token verification"""
    invalid_token = "invalid.token.here"
    decoded = verify_access_token(invalid_token)

    assert decoded is None
