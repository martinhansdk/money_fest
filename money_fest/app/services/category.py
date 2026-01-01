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


def create_category(db: sqlite3.Connection, full_path: str) -> dict:
    """
    Create a new category with automatic parent detection from full_path

    Args:
        db: Database connection
        full_path: Full path of the category (e.g., "Food:Groceries")

    Returns:
        Created category dict

    Raises:
        ValueError: If full_path format is invalid, parent doesn't exist, or category already exists
    """
    # Validate full_path format
    if ':' not in full_path:
        raise ValueError("Category must include parent (e.g., 'Food:Groceries')")

    parts = full_path.split(':')
    parent = ':'.join(parts[:-1]) if len(parts) > 1 else None
    name = parts[-1]

    # Validate parent exists if specified
    if parent:
        parent_category = get_category_by_full_path(db, parent)
        if not parent_category:
            raise ValueError(f"Parent category '{parent}' does not exist")

    # Check for duplicate full_path
    existing = get_category_by_full_path(db, full_path)
    if existing:
        raise ValueError(f"Category '{full_path}' already exists")

    # Insert category
    cursor = db.execute(
        """INSERT INTO categories (name, parent, full_path, usage_count)
           VALUES (?, ?, ?, 0)""",
        (name, parent, full_path)
    )
    db.commit()

    return get_category_by_full_path(db, full_path)


def update_category(db: sqlite3.Connection, category_id: int, updates: dict) -> dict:
    """
    Update category name or parent. Cascades to children and transactions.

    Args:
        db: Database connection
        category_id: ID of the category to update
        updates: Dictionary with 'new_name' and/or 'new_parent' keys

    Returns:
        Updated category dict

    Raises:
        ValueError: If category not found, parent doesn't exist, or would create duplicate
    """
    cursor = db.execute(
        "SELECT * FROM categories WHERE id = ?", (category_id,)
    )
    category = cursor.fetchone()

    if not category:
        raise ValueError("Category not found")

    category = dict_from_row(category)
    old_full_path = category['full_path']

    # Build new full_path
    name = updates.get('new_name', category['name'])
    new_parent = updates.get('new_parent')

    if new_parent is not None:
        # Validate new parent exists if specified
        if new_parent:
            parent_cat = get_category_by_full_path(db, new_parent)
            if not parent_cat:
                raise ValueError(f"Parent '{new_parent}' does not exist")
        new_full_path = f"{new_parent}:{name}" if new_parent else name
    else:
        # Keep existing parent
        parent = category['parent']
        new_full_path = f"{parent}:{name}" if parent else name

    # Check for duplicate
    if new_full_path != old_full_path:
        existing = get_category_by_full_path(db, new_full_path)
        if existing:
            raise ValueError(f"Category '{new_full_path}' already exists")

    # Determine final parent value
    if new_parent is not None:
        final_parent = new_parent if new_parent else None
    else:
        final_parent = category['parent']

    # Update category
    db.execute(
        """UPDATE categories
           SET name = ?, parent = ?, full_path = ?
           WHERE id = ?""",
        (name, final_parent, new_full_path, category_id)
    )

    # Update all child categories (full_path starts with old_full_path)
    db.execute(
        """UPDATE categories
           SET full_path = REPLACE(full_path, ?, ?),
               parent = REPLACE(parent, ?, ?)
           WHERE full_path LIKE ?""",
        (old_full_path, new_full_path, old_full_path, new_full_path, f"{old_full_path}:%")
    )

    # Update all transactions using this category
    db.execute(
        """UPDATE transactions
           SET category = ?
           WHERE category = ?""",
        (new_full_path, old_full_path)
    )

    # Update transactions using child categories
    db.execute(
        """UPDATE transactions
           SET category = REPLACE(category, ?, ?)
           WHERE category LIKE ?""",
        (old_full_path, new_full_path, f"{old_full_path}:%")
    )

    db.commit()

    return get_category_by_full_path(db, new_full_path)


def delete_category_with_replacement(
    db: sqlite3.Connection,
    category_id: int,
    replacement_id: int
) -> None:
    """
    Delete category and replace in all transactions

    Args:
        db: Database connection
        category_id: ID of the category to delete
        replacement_id: ID of the category to use as replacement

    Raises:
        ValueError: If categories not found or invalid replacement
    """
    # Get categories
    cursor = db.execute(
        "SELECT * FROM categories WHERE id = ?", (category_id,)
    )
    category = cursor.fetchone()

    if not category:
        raise ValueError("Category not found")

    category = dict_from_row(category)

    cursor = db.execute(
        "SELECT * FROM categories WHERE id = ?", (replacement_id,)
    )
    replacement = cursor.fetchone()

    if not replacement:
        raise ValueError("Replacement category not found")

    replacement = dict_from_row(replacement)

    if category_id == replacement_id:
        raise ValueError("Cannot replace category with itself")

    old_full_path = category['full_path']
    new_full_path = replacement['full_path']

    # Update all transactions using this category
    db.execute(
        """UPDATE transactions
           SET category = ?
           WHERE category = ?""",
        (new_full_path, old_full_path)
    )

    # Update transactions using child categories
    db.execute(
        """UPDATE transactions
           SET category = ?
           WHERE category LIKE ?""",
        (new_full_path, f"{old_full_path}:%")
    )

    # Update replacement category usage_count
    cursor = db.execute(
        """SELECT COUNT(*) as count FROM transactions
           WHERE category = ?""",
        (new_full_path,)
    )
    affected_count = cursor.fetchone()[0]

    db.execute(
        "UPDATE categories SET usage_count = ? WHERE id = ?",
        (affected_count, replacement_id)
    )

    # Delete category and all children
    db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    db.execute(
        "DELETE FROM categories WHERE full_path LIKE ?",
        (f"{old_full_path}:%",)
    )

    db.commit()
