"""
Batch service layer - Business logic for batch management
"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple


def create_batch(
    db: sqlite3.Connection,
    name: str,
    user_id: int,
    transactions: List[dict]
) -> int:
    """
    Create a new batch with transactions

    Args:
        db: Database connection
        name: Batch name
        user_id: User ID (owner)
        transactions: List of transaction dicts with keys:
            - date (str): YYYY-MM-DD format
            - payee (str)
            - amount (float): Negative for expenses, positive for income
            - original_category (str, optional)
            - original_comment (str, optional)

    Returns:
        Batch ID

    Raises:
        ValueError: If validation fails
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Batch name is required")

    if not transactions:
        raise ValueError("At least one transaction is required")

    # Calculate date range from transactions
    dates = [txn['date'] for txn in transactions]
    date_range_start = min(dates)
    date_range_end = max(dates)

    # Insert batch
    cursor = db.execute("""
        INSERT INTO batches (name, user_id, status, date_range_start, date_range_end)
        VALUES (?, ?, 'in_progress', ?, ?)
    """, (name.strip(), user_id, date_range_start, date_range_end))

    batch_id = cursor.lastrowid

    # Bulk insert transactions
    for txn in transactions:
        # Determine status based on whether original_category exists
        original_category = txn.get('original_category', '')
        status = 'categorized' if original_category else 'uncategorized'

        db.execute("""
            INSERT INTO transactions (
                batch_id, date, payee, amount, category, note, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id,
            txn['date'],
            txn['payee'],
            txn['amount'],
            original_category or None,
            txn.get('original_comment', '') or None,
            status
        ))

    db.commit()

    return batch_id


def get_batch_by_id(db: sqlite3.Connection, batch_id: int) -> Optional[dict]:
    """
    Get batch details by ID with calculated progress

    Args:
        db: Database connection
        batch_id: Batch ID

    Returns:
        Batch dict with progress fields, or None if not found
    """
    cursor = db.execute("""
        SELECT id, name, user_id, status, date_range_start, date_range_end,
               created_at, updated_at
        FROM batches
        WHERE id = ?
    """, (batch_id,))

    row = cursor.fetchone()
    if not row:
        return None

    # Convert row to dict
    batch = {
        'id': row[0],
        'name': row[1],
        'user_id': row[2],
        'status': row[3],
        'date_range_start': row[4],
        'date_range_end': row[5],
        'created_at': row[6],
        'updated_at': row[7]
    }

    # Add progress information
    progress = get_batch_progress(db, batch_id)
    batch.update(progress)

    return batch


def list_batches(
    db: sqlite3.Connection,
    user_id: int,
    include_archived: bool = False
) -> List[dict]:
    """
    List all batches for a user

    Args:
        db: Database connection
        user_id: User ID
        include_archived: If True, include archived batches

    Returns:
        List of batch dicts with progress fields
    """
    # Build query
    query = """
        SELECT id, name, user_id, status, date_range_start, date_range_end,
               created_at, updated_at
        FROM batches
        WHERE user_id = ?
    """
    params = [user_id]

    if not include_archived:
        query += " AND status != 'archived'"

    query += " ORDER BY created_at DESC"

    cursor = db.execute(query, params)
    rows = cursor.fetchall()

    # Convert to dicts with progress
    batches = []
    for row in rows:
        batch = {
            'id': row[0],
            'name': row[1],
            'user_id': row[2],
            'status': row[3],
            'date_range_start': row[4],
            'date_range_end': row[5],
            'created_at': row[6],
            'updated_at': row[7]
        }

        # Add progress information
        progress = get_batch_progress(db, batch['id'])
        batch.update(progress)

        batches.append(batch)

    return batches


def delete_batch(db: sqlite3.Connection, batch_id: int, user_id: int) -> None:
    """
    Delete a batch (and its transactions via CASCADE)

    Args:
        db: Database connection
        batch_id: Batch ID to delete
        user_id: User ID (for ownership verification)

    Raises:
        ValueError: If batch not found or not owned by user
    """
    # Verify ownership
    if not verify_batch_ownership(db, batch_id, user_id):
        raise ValueError("Batch not found or you don't have permission to delete it")

    # Delete batch (CASCADE removes transactions)
    db.execute("DELETE FROM batches WHERE id = ?", (batch_id,))
    db.commit()


def archive_batch(db: sqlite3.Connection, batch_id: int) -> None:
    """
    Archive a batch (set status to 'archived')

    Args:
        db: Database connection
        batch_id: Batch ID to archive
    """
    db.execute("""
        UPDATE batches
        SET status = 'archived', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (batch_id,))
    db.commit()


def unarchive_batch(db: sqlite3.Connection, batch_id: int) -> None:
    """
    Unarchive a batch (set status to 'in_progress')

    Args:
        db: Database connection
        batch_id: Batch ID to unarchive
    """
    db.execute("""
        UPDATE batches
        SET status = 'in_progress', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (batch_id,))
    db.commit()


def update_batch_status_if_complete(db: sqlite3.Connection, batch_id: int) -> None:
    """
    Check if all transactions in a batch are categorized and update status to 'complete'

    Only updates batches that are currently 'in_progress'. Does not affect 'archived' batches.

    Args:
        db: Database connection
        batch_id: Batch ID to check
    """
    # Get current batch status
    cursor = db.execute("""
        SELECT status FROM batches WHERE id = ?
    """, (batch_id,))
    row = cursor.fetchone()

    if not row:
        return

    current_status = row[0]

    # Only update if currently in_progress
    if current_status != 'in_progress':
        return

    # Check if all transactions are categorized
    cursor = db.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status = 'categorized' THEN 1 ELSE 0 END) as categorized
        FROM transactions
        WHERE batch_id = ?
    """, (batch_id,))

    row = cursor.fetchone()
    total = row[0]
    categorized = row[1]

    # If all transactions are categorized, mark batch as complete
    if total > 0 and categorized == total:
        db.execute("""
            UPDATE batches
            SET status = 'complete', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (batch_id,))
        db.commit()


def calculate_batch_date_range(
    db: sqlite3.Connection,
    batch_id: int
) -> Tuple[Optional[str], Optional[str]]:
    """
    Calculate date range for a batch from its transactions

    Args:
        db: Database connection
        batch_id: Batch ID

    Returns:
        Tuple of (start_date, end_date) or (None, None) if no transactions
    """
    cursor = db.execute("""
        SELECT MIN(date) as start_date, MAX(date) as end_date
        FROM transactions
        WHERE batch_id = ?
    """, (batch_id,))

    row = cursor.fetchone()
    return (row[0], row[1]) if row else (None, None)


def get_batch_progress(db: sqlite3.Connection, batch_id: int) -> dict:
    """
    Get batch progress statistics

    Args:
        db: Database connection
        batch_id: Batch ID

    Returns:
        Dict with keys:
            - total_count: Total number of transactions
            - categorized_count: Number of categorized transactions
            - progress_percent: Percentage complete (0-100)
    """
    cursor = db.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN category IS NOT NULL THEN 1 ELSE 0 END) as categorized
        FROM transactions
        WHERE batch_id = ?
    """, (batch_id,))

    row = cursor.fetchone()
    total = row[0] or 0
    categorized = row[1] or 0

    # Calculate percentage
    progress_percent = (categorized / total * 100) if total > 0 else 0.0

    return {
        'total_count': total,
        'categorized_count': categorized,
        'progress_percent': round(progress_percent, 1)
    }


def verify_batch_ownership(
    db: sqlite3.Connection,
    batch_id: int,
    user_id: int
) -> bool:
    """
    Verify that a user owns a batch

    Args:
        db: Database connection
        batch_id: Batch ID
        user_id: User ID

    Returns:
        True if user owns the batch, False otherwise
    """
    cursor = db.execute(
        "SELECT user_id FROM batches WHERE id = ?",
        (batch_id,)
    )
    row = cursor.fetchone()

    if not row:
        return False

    return row[0] == user_id


def update_batch_date_range(db: sqlite3.Connection, batch_id: int) -> None:
    """
    Update batch date range based on its transactions

    Args:
        db: Database connection
        batch_id: Batch ID
    """
    start_date, end_date = calculate_batch_date_range(db, batch_id)

    if start_date and end_date:
        db.execute("""
            UPDATE batches
            SET date_range_start = ?, date_range_end = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (start_date, end_date, batch_id))
        db.commit()
