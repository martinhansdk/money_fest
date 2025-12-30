"""
Category management endpoints (Phase 2)
"""

from fastapi import APIRouter, Depends, Query
from typing import List
from app.database import get_db
from app.models import CategoryResponse
from app.auth import get_current_user
from app.services.category import get_all_categories, get_frequent_categories
import sqlite3

router = APIRouter()


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get all categories

    Returns list of all categories sorted by full_path
    """
    categories = get_all_categories(db)
    return categories


@router.get("/frequent", response_model=List[CategoryResponse])
def list_frequent_categories(
    limit: int = Query(default=15, ge=1, le=50),
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get frequently used categories

    Returns top N categories by usage_count

    Args:
        limit: Maximum number of categories to return (1-50, default 15)
    """
    categories = get_frequent_categories(db, limit)
    return categories
