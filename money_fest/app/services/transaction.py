"""
Transaction service layer - Business logic for transaction management
"""

import sqlite3
from typing import List, Optional
from app.services.batch import verify_batch_ownership
from app.services.category import increment_category_usage as increment_cat_usage


def list_transactions(
    db: sqlite3.Connection,
    batch_id: int,
    user_id: int
) -> List[dict]:
    """
    List all transactions for a batch

    Args:
        db: Database connection
        batch_id: Batch ID
        user_id: User ID (for ownership verification)

    Returns:
        List of transaction dicts

    Raises:
        ValueError: If batch not found or not owned by user
    """
    # Verify ownership
    if not verify_batch_ownership(db, batch_id, user_id):
        raise ValueError("Batch not found or you don't have permission to view it")

    # Get transactions
    cursor = db.execute("""
        SELECT id, batch_id, date, payee, amount, category, note, status,
               created_at, updated_at
        FROM transactions
        WHERE batch_id = ?
        ORDER BY date ASC, id ASC
    """, (batch_id,))

    rows = cursor.fetchall()

    # Convert to dicts
    transactions = []
    for row in rows:
        transactions.append({
            'id': row[0],
            'batch_id': row[1],
            'date': row[2],
            'payee': row[3],
            'amount': row[4],
            'category': row[5],
            'note': row[6],
            'status': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        })

    return transactions


def get_transaction_by_id(
    db: sqlite3.Connection,
    transaction_id: int
) -> Optional[dict]:
    """
    Get a single transaction by ID

    Args:
        db: Database connection
        transaction_id: Transaction ID

    Returns:
        Transaction dict or None if not found
    """
    cursor = db.execute("""
        SELECT id, batch_id, date, payee, amount, category, note, status,
               created_at, updated_at
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    row = cursor.fetchone()
    if not row:
        return None

    return {
        'id': row[0],
        'batch_id': row[1],
        'date': row[2],
        'payee': row[3],
        'amount': row[4],
        'category': row[5],
        'note': row[6],
        'status': row[7],
        'created_at': row[8],
        'updated_at': row[9]
    }


def update_transaction(
    db: sqlite3.Connection,
    transaction_id: int,
    category: Optional[str] = None,
    note: Optional[str] = None
) -> dict:
    """
    Update a transaction's category and/or note

    Args:
        db: Database connection
        transaction_id: Transaction ID
        category: Category to set (None to clear)
        note: Note to set (None to clear)

    Returns:
        Updated transaction dict

    Raises:
        ValueError: If transaction not found or category doesn't exist
    """
    # Get current transaction
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        raise ValueError(f"Transaction {transaction_id} not found")

    # Validate category exists (if provided and not empty)
    if category:
        if not category_exists(db, category):
            raise ValueError(f"Category '{category}' does not exist")

    # Determine new status
    if category:
        new_status = 'categorized'
    else:
        new_status = 'uncategorized'

    # Update transaction
    db.execute("""
        UPDATE transactions
        SET category = ?, note = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (category, note, new_status, transaction_id))

    # Increment category usage count (if category was set)
    if category:
        increment_cat_usage(db, category)

    db.commit()

    # Check if batch is now complete
    from app.services.batch import update_batch_status_if_complete
    update_batch_status_if_complete(db, transaction['batch_id'])

    # Return updated transaction
    return get_transaction_by_id(db, transaction_id)


def bulk_update_transactions(
    db: sqlite3.Connection,
    transaction_ids: List[int],
    category: Optional[str] = None,
    note: Optional[str] = None
) -> int:
    """
    Bulk update multiple transactions

    Args:
        db: Database connection
        transaction_ids: List of transaction IDs to update
        category: Category to set (None to leave unchanged)
        note: Note to set (None to leave unchanged)

    Returns:
        Number of transactions updated

    Raises:
        ValueError: If validation fails
    """
    if not transaction_ids:
        raise ValueError("No transaction IDs provided")

    # Validate category exists (if provided and not empty)
    if category:
        if not category_exists(db, category):
            raise ValueError(f"Category '{category}' does not exist")

    # Update each transaction (update_transaction handles batch status check)
    updated_count = 0
    for txn_id in transaction_ids:
        try:
            update_transaction(db, txn_id, category, note)
            updated_count += 1
        except ValueError:
            # Skip transactions that don't exist
            continue

    return updated_count


def category_exists(db: sqlite3.Connection, category: str) -> bool:
    """
    Check if a category exists in the database

    Args:
        db: Database connection
        category: Category full_path to check

    Returns:
        True if category exists, False otherwise
    """
    cursor = db.execute(
        "SELECT COUNT(*) FROM categories WHERE full_path = ?",
        (category,)
    )
    row = cursor.fetchone()
    return row[0] > 0


def clear_transaction_category(
    db: sqlite3.Connection,
    transaction_id: int
) -> dict:
    """
    Clear the category from a transaction

    Args:
        db: Database connection
        transaction_id: Transaction ID

    Returns:
        Updated transaction dict

    Raises:
        ValueError: If transaction not found
    """
    return update_transaction(db, transaction_id, category=None, note=None)


def get_uncategorized_transactions(
    db: sqlite3.Connection,
    batch_id: int,
    user_id: int
) -> List[dict]:
    """
    Get all uncategorized transactions for a batch

    Args:
        db: Database connection
        batch_id: Batch ID
        user_id: User ID (for ownership verification)

    Returns:
        List of uncategorized transaction dicts

    Raises:
        ValueError: If batch not found or not owned by user
    """
    # Verify ownership
    if not verify_batch_ownership(db, batch_id, user_id):
        raise ValueError("Batch not found or you don't have permission to view it")

    # Get uncategorized transactions
    cursor = db.execute("""
        SELECT id, batch_id, date, payee, amount, category, note, status,
               created_at, updated_at
        FROM transactions
        WHERE batch_id = ? AND status = 'uncategorized'
        ORDER BY date ASC, id ASC
    """, (batch_id,))

    rows = cursor.fetchall()

    # Convert to dicts
    transactions = []
    for row in rows:
        transactions.append({
            'id': row[0],
            'batch_id': row[1],
            'date': row[2],
            'payee': row[3],
            'amount': row[4],
            'category': row[5],
            'note': row[6],
            'status': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        })

    return transactions


def get_categorized_transactions(
    db: sqlite3.Connection,
    batch_id: int,
    user_id: int
) -> List[dict]:
    """
    Get all categorized transactions for a batch

    Args:
        db: Database connection
        batch_id: Batch ID
        user_id: User ID (for ownership verification)

    Returns:
        List of categorized transaction dicts

    Raises:
        ValueError: If batch not found or not owned by user
    """
    # Verify ownership
    if not verify_batch_ownership(db, batch_id, user_id):
        raise ValueError("Batch not found or you don't have permission to view it")

    # Get categorized transactions
    cursor = db.execute("""
        SELECT id, batch_id, date, payee, amount, category, note, status,
               created_at, updated_at
        FROM transactions
        WHERE batch_id = ? AND status = 'categorized'
        ORDER BY date ASC, id ASC
    """, (batch_id,))

    rows = cursor.fetchall()

    # Convert to dicts
    transactions = []
    for row in rows:
        transactions.append({
            'id': row[0],
            'batch_id': row[1],
            'date': row[2],
            'payee': row[3],
            'amount': row[4],
            'category': row[5],
            'note': row[6],
            'status': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        })

    return transactions
