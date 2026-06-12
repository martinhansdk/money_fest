"""
Global application settings endpoints (key-value store)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict
import sqlite3

from app.database import get_db
from app.auth import get_current_user

router = APIRouter()


class SettingsUpdate(BaseModel):
    """Request model for updating settings (partial upsert)"""
    settings: Dict[str, str]


@router.get("", response_model=Dict[str, str])
def get_settings(
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get all global settings as a key-value dict
    """
    cursor = db.execute("SELECT key, value FROM app_settings")
    return {row[0]: row[1] for row in cursor.fetchall()}


@router.put("", response_model=Dict[str, str])
def update_settings(
    update: SettingsUpdate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Upsert the given settings keys, leaving other keys untouched

    Returns:
        All settings after the update
    """
    for key, value in update.settings.items():
        db.execute(
            """
            INSERT INTO app_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value)
        )
    db.commit()
    cursor = db.execute("SELECT key, value FROM app_settings")
    return {row[0]: row[1] for row in cursor.fetchall()}
