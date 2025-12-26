"""
User service for user management and authentication
"""

import bcrypt
import sqlite3
from typing import Optional
from app.database import dict_from_row


def validate_password(password: str) -> None:
    """
    Validate password meets minimum requirements

    Args:
        password: Plain text password

    Raises:
        ValueError: If password doesn't meet requirements
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_user(db: sqlite3.Connection, username: str, password: str) -> int:
    """
    Create a new user with hashed password

    Args:
        db: Database connection
        username: Username (must be unique)
        password: Plain text password (will be hashed)

    Returns:
        User ID of created user

    Raises:
        ValueError: If password is invalid or username already exists
    """
    validate_password(password)
    password_hash = hash_password(password)

    try:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise ValueError(f"Username '{username}' already exists")
        raise


def get_user_by_username(db: sqlite3.Connection, username: str) -> Optional[dict]:
    """
    Get user by username

    Args:
        db: Database connection
        username: Username to search for

    Returns:
        User dict if found, None otherwise
    """
    cursor = db.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    return dict_from_row(row) if row else None


def get_user_by_id(db: sqlite3.Connection, user_id: int) -> Optional[dict]:
    """
    Get user by ID

    Args:
        db: Database connection
        user_id: User ID to search for

    Returns:
        User dict if found, None otherwise
    """
    cursor = db.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    return dict_from_row(row) if row else None


def authenticate_user(db: sqlite3.Connection, username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password

    Args:
        db: Database connection
        username: Username
        password: Plain text password

    Returns:
        User dict (without password_hash) if authentication successful, None otherwise
    """
    user = get_user_by_username(db, username)
    if not user:
        return None

    if not verify_password(password, user['password_hash']):
        return None

    # Return user without password_hash
    return {
        'id': user['id'],
        'username': user['username'],
        'created_at': user['created_at']
    }
