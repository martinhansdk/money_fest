"""
Similar transactions finder
Finds transactions similar to a given one across all user's batches
"""

import sqlite3
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from datetime import datetime, timedelta


def similarity_ratio(a: str, b: str) -> float:
    """
    Calculate similarity ratio between two strings

    Args:
        a: First string
        b: Second string

    Returns:
        Float between 0 and 1 (1 = identical)
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_similar_by_payee(
    db: sqlite3.Connection,
    user_id: int,
    payee: str,
    exclude_transaction_id: Optional[int] = None,
    min_similarity: float = 0.6,
    limit: int = 50
) -> List[Dict]:
    """
    Find transactions with similar payees using fuzzy matching

    Args:
        db: Database connection
        user_id: User ID to scope search
        payee: Payee string to match against
        exclude_transaction_id: Transaction ID to exclude from results
        min_similarity: Minimum similarity threshold (0-1)
        limit: Maximum number of results

    Returns:
        List of transaction dicts with similarity scores
    """
    cursor = db.execute("""
        SELECT
            t.id,
            t.batch_id,
            t.date,
            t.payee,
            t.amount,
            t.category,
            t.note,
            b.name as batch_name
        FROM transactions t
        JOIN batches b ON t.batch_id = b.id
        WHERE b.user_id = ?
        ORDER BY t.date DESC
        LIMIT 1000
    """, (user_id,))

    all_transactions = cursor.fetchall()

    # Calculate similarity for each transaction
    similar = []
    for row in all_transactions:
        # Skip if this is the transaction we're comparing against
        if exclude_transaction_id and row[0] == exclude_transaction_id:
            continue

        ratio = similarity_ratio(payee, row[3])  # row[3] is payee

        if ratio >= min_similarity:
            similar.append({
                'id': row[0],
                'batch_id': row[1],
                'batch_name': row[7],
                'date': row[2],
                'payee': row[3],
                'amount': row[4],
                'category': row[5],
                'note': row[6],
                'similarity': round(ratio, 3)
            })

    # Sort by similarity (descending) then by date (descending)
    similar.sort(key=lambda x: (-x['similarity'], x['date']), reverse=True)

    return similar[:limit]


def find_similar_by_amount(
    db: sqlite3.Connection,
    user_id: int,
    amount: float,
    exclude_transaction_id: Optional[int] = None,
    tolerance: float = 0.10,
    limit: int = 50
) -> List[Dict]:
    """
    Find transactions with similar amounts (±tolerance)

    Args:
        db: Database connection
        user_id: User ID to scope search
        amount: Amount to match against
        exclude_transaction_id: Transaction ID to exclude from results
        tolerance: Percentage tolerance (0.10 = ±10%)
        limit: Maximum number of results

    Returns:
        List of transaction dicts
    """
    min_amount = amount * (1 - tolerance)
    max_amount = amount * (1 + tolerance)

    cursor = db.execute("""
        SELECT
            t.id,
            t.batch_id,
            t.date,
            t.payee,
            t.amount,
            t.category,
            t.note,
            b.name as batch_name
        FROM transactions t
        JOIN batches b ON t.batch_id = b.id
        WHERE b.user_id = ?
            AND t.amount BETWEEN ? AND ?
            AND (? IS NULL OR t.id != ?)
        ORDER BY ABS(t.amount - ?) ASC, t.date DESC
        LIMIT ?
    """, (user_id, min_amount, max_amount, exclude_transaction_id, exclude_transaction_id, amount, limit))

    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            'id': row[0],
            'batch_id': row[1],
            'batch_name': row[7],
            'date': row[2],
            'payee': row[3],
            'amount': row[4],
            'category': row[5],
            'note': row[6]
        })

    return transactions


def find_surrounding_transactions(
    db: sqlite3.Connection,
    user_id: int,
    transaction_id: int,
    batch_id: int,
    date: str,
    days_before: int = 3,
    days_after: int = 3,
    limit: int = 20
) -> List[Dict]:
    """
    Find transactions around a given date (context)

    Args:
        db: Database connection
        user_id: User ID to scope search
        transaction_id: Transaction ID to exclude from results
        batch_id: Batch ID of the reference transaction
        date: Reference date (YYYY-MM-DD format)
        days_before: Number of days before to include
        days_after: Number of days after to include
        limit: Maximum number of results

    Returns:
        List of transaction dicts ordered by date
    """
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    start_date = (date_obj - timedelta(days=days_before)).strftime('%Y-%m-%d')
    end_date = (date_obj + timedelta(days=days_after)).strftime('%Y-%m-%d')

    cursor = db.execute("""
        SELECT
            t.id,
            t.batch_id,
            t.date,
            t.payee,
            t.amount,
            t.category,
            t.note,
            b.name as batch_name
        FROM transactions t
        JOIN batches b ON t.batch_id = b.id
        WHERE b.user_id = ?
            AND t.batch_id = ?
            AND t.date BETWEEN ? AND ?
            AND t.id != ?
        ORDER BY t.date ASC, t.id ASC
        LIMIT ?
    """, (user_id, batch_id, start_date, end_date, transaction_id, limit))

    transactions = []
    for row in cursor.fetchall():
        transactions.append({
            'id': row[0],
            'batch_id': row[1],
            'batch_name': row[7],
            'date': row[2],
            'payee': row[3],
            'amount': row[4],
            'category': row[5],
            'note': row[6]
        })

    return transactions


def get_similar_transactions(
    db: sqlite3.Connection,
    user_id: int,
    transaction_id: int
) -> Dict:
    """
    Get all similar transactions for a given transaction
    Combines payee, amount, and surrounding matches

    Args:
        db: Database connection
        user_id: User ID to scope search
        transaction_id: Transaction ID to find similar for

    Returns:
        Dict with by_payee, by_amount, and surrounding lists

    Raises:
        ValueError: If transaction not found or not owned by user
    """
    # Get the reference transaction
    cursor = db.execute("""
        SELECT
            t.id,
            t.batch_id,
            t.date,
            t.payee,
            t.amount,
            t.category,
            t.note,
            b.name as batch_name
        FROM transactions t
        JOIN batches b ON t.batch_id = b.id
        WHERE t.id = ? AND b.user_id = ?
    """, (transaction_id, user_id))

    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Transaction {transaction_id} not found or not owned by user")

    transaction = {
        'id': row[0],
        'batch_id': row[1],
        'batch_name': row[7],
        'date': row[2],
        'payee': row[3],
        'amount': row[4],
        'category': row[5],
        'note': row[6]
    }

    # Find similar transactions
    by_payee = find_similar_by_payee(
        db, user_id, transaction['payee'],
        exclude_transaction_id=transaction_id,
        min_similarity=0.6,
        limit=30
    )

    by_amount = find_similar_by_amount(
        db, user_id, float(transaction['amount']),
        exclude_transaction_id=transaction_id,
        tolerance=0.10,
        limit=30
    )

    surrounding = find_surrounding_transactions(
        db, user_id, transaction_id,
        transaction['batch_id'],
        transaction['date'],
        days_before=3,
        days_after=3,
        limit=20
    )

    return {
        'transaction': transaction,
        'by_payee': by_payee,
        'by_amount': by_amount,
        'surrounding': surrounding
    }
