"""
Category service for importing and managing categories
"""

import sqlite3
from typing import Optional
from app.database import dict_from_row


def parse_category_line(line: str) -> Optional[tuple[Optional[str], str, str]]:
    """
    Parse a category line from categories.txt

    Args:
        line: Line from categories file (e.g., "Parent:Child" or "Parent")

    Returns:
        Tuple of (parent, name, full_path) or None if line is invalid/empty

    Examples:
        "Automobile:Gasoline" -> ("Automobile", "Gasoline", "Automobile:Gasoline")
        "Clothing" -> (None, "Clothing", "Clothing")
        "" -> None
    """
    # Strip whitespace
    line = line.strip()

    # Skip empty lines
    if not line:
        return None

    # Check if it contains a colon (parent:child format)
    if ':' in line:
        parts = line.split(':', 1)  # Split on first colon only
        if len(parts) == 2:
            parent = parts[0].strip()
            name = parts[1].strip()
            full_path = f"{parent}:{name}"
            return (parent, name, full_path)

    # Parent-only category (no colon)
    return (None, line, line)


def import_categories_from_file(db: sqlite3.Connection, filepath: str) -> int:
    """
    Import categories from a file into the database

    Args:
        db: Database connection
        filepath: Path to categories file

    Returns:
        Number of categories imported

    The function:
    - Handles both UTF-8 and latin-1 encoding
    - Skips empty lines
    - Uses INSERT OR IGNORE to skip duplicates
    - Imports all categories in a single transaction
    """
    # Try to read file with UTF-8 first, fallback to latin-1
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='latin-1') as f:
            lines = f.readlines()

    # Parse all lines
    categories = []
    for line in lines:
        parsed = parse_category_line(line)
        if parsed:
            categories.append(parsed)

    # Import categories into database
    count = 0
    for parent, name, full_path in categories:
        try:
            cursor = db.execute(
                """
                INSERT OR IGNORE INTO categories (name, parent, full_path, usage_count)
                VALUES (?, ?, ?, 0)
                """,
                (name, parent, full_path)
            )
            if cursor.rowcount > 0:
                count += 1
        except sqlite3.Error:
            # Skip errors (e.g., constraint violations)
            continue

    db.commit()
    return count


def get_all_categories(db: sqlite3.Connection) -> list[dict]:
    """
    Get all categories from database

    Args:
        db: Database connection

    Returns:
        List of category dicts sorted by full_path
    """
    cursor = db.execute(
        """
        SELECT id, name, parent, full_path, usage_count, created_at
        FROM categories
        ORDER BY full_path
        """
    )
    rows = cursor.fetchall()
    return [dict_from_row(row) for row in rows]


def get_category_by_full_path(db: sqlite3.Connection, full_path: str) -> Optional[dict]:
    """
    Get a category by its full_path

    Args:
        db: Database connection
        full_path: Full path of the category (e.g., "Automobile:Gasoline")

    Returns:
        Category dict if found, None otherwise
    """
    cursor = db.execute(
        """
        SELECT id, name, parent, full_path, usage_count, created_at
        FROM categories
        WHERE full_path = ?
        """,
        (full_path,)
    )
    row = cursor.fetchone()
    return dict_from_row(row) if row else None


def increment_category_usage(db: sqlite3.Connection, full_path: str) -> None:
    """
    Increment the usage count for a category

    Args:
        db: Database connection
        full_path: Full path of the category
    """
    db.execute(
        "UPDATE categories SET usage_count = usage_count + 1 WHERE full_path = ?",
        (full_path,)
    )
    db.commit()


def get_frequent_categories(db: sqlite3.Connection, limit: int = 15) -> list[dict]:
    """
    Get frequently used categories

    Args:
        db: Database connection
        limit: Maximum number of categories to return (default 15)

    Returns:
        List of category dicts sorted by usage_count (descending) then full_path (ascending)
    """
    cursor = db.execute(
        """
        SELECT id, name, parent, full_path, usage_count, created_at
        FROM categories
        WHERE usage_count > 0
        ORDER BY usage_count DESC, full_path ASC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cursor.fetchall()
    return [dict_from_row(row) for row in rows]
