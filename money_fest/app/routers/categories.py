"""
Category management endpoints (Phase 2)
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from app.database import get_db
from app.models import CategoryResponse, CategoryCreate, CategoryUpdate, CategoryDelete
from app.auth import get_current_user
from app.services.category import (
    get_all_categories,
    get_frequent_categories,
    create_category,
    update_category,
    delete_category_with_replacement
)
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


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category_endpoint(
    category_data: CategoryCreate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Create a new category with automatic parent detection

    Args:
        category_data: Category creation data with full_path (e.g., "Food:Groceries")

    Returns:
        Created category

    Raises:
        400: If full_path format is invalid, parent doesn't exist, or category already exists
    """
    try:
        category = create_category(db, category_data.full_path)
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category_endpoint(
    category_id: int,
    update_data: CategoryUpdate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Update category name or parent

    Updates all child categories and transactions automatically

    Args:
        category_id: ID of the category to update
        update_data: Update data (new_name and/or new_parent)

    Returns:
        Updated category

    Raises:
        400: If parent doesn't exist or would create duplicate
        404: If category not found
    """
    try:
        category = update_category(db, category_id, update_data.dict(exclude_unset=True))
        return category
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "Category not found":
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)


@router.delete("/{category_id}")
def delete_category_endpoint(
    category_id: int,
    delete_data: CategoryDelete,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Delete category and replace in all transactions

    Args:
        category_id: ID of the category to delete
        delete_data: Replacement category data

    Returns:
        Success message

    Raises:
        400: If replacement is invalid
        404: If category not found
    """
    try:
        delete_category_with_replacement(
            db,
            category_id,
            delete_data.replacement_category_id
        )
        return {"message": "Category deleted successfully"}
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)
