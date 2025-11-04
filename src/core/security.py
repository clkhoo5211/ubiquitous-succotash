"""Security utilities for authentication and authorization

Implements password hashing, JWT token generation/validation, and session management.
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from jwt import PyJWTError as JWTError

from src.core.config import config


def hash_password(password: str) -> str:
    """Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Bcrypt has a 72-byte limit, truncate if necessary
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')[:72]
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token

    Args:
        data: Payload data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.security.jwt_expiration_minutes)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(
        to_encode, config.security.jwt_secret_key, algorithm=config.security.jwt_algorithm
    )
    return encoded_jwt


def verify_access_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT access token

    Args:
        token: JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            config.security.jwt_secret_key,
            algorithms=[config.security.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def generate_session_token() -> str:
    """Generate a random session token

    Returns:
        Random session token string (32 chars)
    """
    import secrets

    return secrets.token_urlsafe(32)
