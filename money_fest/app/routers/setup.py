"""
Setup router for first-time user creation
Allows web-based user setup before any users exist in the database
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from app.database import get_db_context
from app.services.user import create_user


router = APIRouter()


class SetupRequest(BaseModel):
    """Request model for setup endpoint"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


def users_exist() -> bool:
    """Check if any users exist in the database"""
    try:
        with get_db_context() as db:
            cursor = db.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            return count > 0
    except Exception:
        # If table doesn't exist yet, no users exist
        return False


@router.get("/setup", response_class=HTMLResponse)
async def setup_page():
    """
    Serve the setup page for first-time user creation.
    Redirects to login if users already exist.
    """
    if users_exist():
        return RedirectResponse(url="/static/index.html", status_code=303)

    # Serve setup page (will be at /static/setup.html)
    with open("app/static/setup.html", "r") as f:
        html_content = f.read()

    return HTMLResponse(content=html_content)


@router.post("/setup")
async def create_first_user(setup_data: SetupRequest):
    """
    Create the first user account.
    Only accessible when no users exist.
    """
    # Security check: only allow setup if no users exist
    if users_exist():
        raise HTTPException(
            status_code=403,
            detail="Setup is no longer available. Users already exist."
        )

    try:
        with get_db_context() as db:
            user_id = create_user(db, setup_data.username, setup_data.password)

        return {
            "success": True,
            "message": f"User '{setup_data.username}' created successfully",
            "user_id": user_id
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )
