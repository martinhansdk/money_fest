"""
Authentication and session management
Uses in-memory session storage for simplicity (2 users)
"""

import secrets
import sqlite3
from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from app.config import settings
from app.database import get_db
from app.services.user import get_user_by_id


# In-memory session storage: {session_id: user_id}
# Sessions are lost on restart (acceptable for 2-user home use)
_sessions: dict[str, int] = {}


def create_session(user_id: int) -> str:
    """
    Create a new session for a user

    Args:
        user_id: ID of the user to create session for

    Returns:
        Session ID (secure random token)
    """
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = user_id
    return session_id


def verify_session(session_id: str) -> Optional[int]:
    """
    Verify a session and return the user ID

    Args:
        session_id: Session ID to verify

    Returns:
        User ID if session is valid, None otherwise
    """
    return _sessions.get(session_id)


def delete_session(session_id: str) -> None:
    """
    Delete a session (logout)

    Args:
        session_id: Session ID to delete
    """
    _sessions.pop(session_id, None)


def get_session_from_request(request: Request) -> Optional[str]:
    """
    Extract session ID from request cookie

    Args:
        request: FastAPI request object

    Returns:
        Session ID if found in cookie, None otherwise
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
