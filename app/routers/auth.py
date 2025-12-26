"""
Authentication endpoints
"""

from fastapi import APIRouter, HTTPException, status, Response, Request, Depends
from app.models import UserLogin, UserResponse
from app.database import get_db
from app.services.user import authenticate_user
from app.auth import create_session, delete_session, get_session_from_request, get_current_user
from app.config import settings


router = APIRouter()


@router.post("/login", response_model=UserResponse)
def login(credentials: UserLogin, response: Response):
    """
    Authenticate user and create session

    Args:
        credentials: Username and password
        response: FastAPI response object (to set cookie)

    Returns:
        User data

    Raises:
        401: If credentials are invalid
    """
    # Authenticate user
    with get_db() as db:
        user = authenticate_user(db, credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Create session
    session_id = create_session(user['id'])

    # Set session cookie
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax"
    )

    return UserResponse(**user)


@router.post("/logout")
def logout(request: Request, response: Response):
    """
    Logout user and clear session

    Args:
        request: FastAPI request object
        response: FastAPI response object (to clear cookie)

    Returns:
        Success message
    """
    # Get session from cookie
    session_id = get_session_from_request(request)

    # Delete session if exists
    if session_id:
        delete_session(session_id)

    # Clear cookie
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(user: dict = Depends(get_current_user)):
    """
    Get current authenticated user (for testing/debugging)

    Args:
        user: Current user from get_current_user dependency

    Returns:
        Current user data
    """
    return UserResponse(**user)
