"""
User management endpoints (requires authentication)
Allows authenticated users to create additional users
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.database import get_db
from app.services.user import create_user, get_all_users
from app.auth import get_current_user
import sqlite3


router = APIRouter()


class CreateUserRequest(BaseModel):
    """Request model for creating a user"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


@router.post("/create")
async def create_new_user(
    user_data: CreateUserRequest,
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new user (requires authentication)

    Args:
        user_data: Username and password for new user
        db: Database connection
        current_user: Currently authenticated user

    Returns:
        Success message with user ID

    Raises:
        400: If username already exists or invalid data
        401: If not authenticated
    """
    try:
        user_id = create_user(db, user_data.username, user_data.password)

        return {
            "success": True,
            "message": f"User '{user_data.username}' created successfully",
            "user_id": user_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@router.get("/list")
async def list_users(
    db: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all users (requires authentication)

    Args:
        db: Database connection
        current_user: Currently authenticated user

    Returns:
        List of users (id, username, created_at)

    Raises:
        401: If not authenticated
    """
    users = get_all_users(db)

    # Return users without password hashes
    return [
        {
            'id': user['id'],
            'username': user['username'],
            'created_at': user['created_at']
        }
        for user in users
    ]
