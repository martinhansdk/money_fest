"""
Authentication and session management
Uses in-memory session storage for simplicity (2 users)
Sessions are cryptographically signed using itsdangerous
"""

import secrets
import sqlite3
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from app.config import settings
from app.database import get_db
from app.services.user import get_user_by_id


# In-memory session storage: {session_id: user_id}
# Sessions are lost on restart (acceptable for 2-user home use)
_sessions: dict[str, int] = {}

# Serializer for signing session tokens
_serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def create_session(user_id: int) -> str:
    """
    Create a new session for a user and return a signed token

    Args:
        user_id: ID of the user to create session for

    Returns:
        Signed session token (cryptographically signed with SECRET_KEY)
    """
    # Generate random session ID
    session_id = secrets.token_urlsafe(32)

    # Store session in memory
    _sessions[session_id] = user_id

    # Sign the session ID with the secret key
    signed_token = _serializer.dumps(session_id, salt='session')

    return signed_token


def verify_session(signed_token: str) -> Optional[int]:
    """
    Verify a signed session token and return the user ID

    Args:
        signed_token: Signed session token to verify

    Returns:
        User ID if session is valid, None otherwise
    """
    try:
        # Verify signature and extract session ID
        # max_age is in seconds (matches SESSION_MAX_AGE)
        session_id = _serializer.loads(
            signed_token,
            salt='session',
            max_age=settings.SESSION_MAX_AGE
        )

        # Look up user ID from in-memory storage
        return _sessions.get(session_id)

    except (BadSignature, SignatureExpired):
        # Token was tampered with or expired
        return None


def delete_session(signed_token: str) -> None:
    """
    Delete a session (logout)

    Args:
        signed_token: Signed session token to delete
    """
    try:
        # Extract session ID from signed token
        session_id = _serializer.loads(signed_token, salt='session')
        _sessions.pop(session_id, None)
    except (BadSignature, SignatureExpired):
        # Token invalid, nothing to delete
        pass


def get_session_from_request(request: Request) -> Optional[str]:
    """
    Extract signed session token from request cookie

    Args:
        request: FastAPI request object

    Returns:
        Signed session token if found in cookie, None otherwise
    """
    return request.cookies.get(settings.SESSION_COOKIE_NAME)


def get_current_user(request: Request, db: sqlite3.Connection = Depends(get_db)) -> dict:
    """
    FastAPI dependency to get current authenticated user

    Args:
        request: FastAPI request object
        db: Database connection

    Returns:
        User dict (id, username, created_at)

    Raises:
        HTTPException: 401 if not authenticated
    """
    # Get session from cookie
    session_id = get_session_from_request(request)
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Verify session
    user_id = verify_session(session_id)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    # Get user from database
    user = get_user_by_id(db, user_id)

    if not user:
        # Session exists but user was deleted
        delete_session(session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Return user without password_hash
    return {
        'id': user['id'],
        'username': user['username'],
        'created_at': user['created_at']
    }


def get_active_sessions_count() -> int:
    """
    Get the number of active sessions (for debugging/monitoring)

    Returns:
        Number of active sessions
    """
    return len(_sessions)
