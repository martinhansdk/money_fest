"""
Similar transactions endpoints (Phase 6)
"""

from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.auth import get_current_user
from app.services.similar import get_similar_transactions
import sqlite3

router = APIRouter()


@router.get("/transactions/{transaction_id}/similar")
def get_similar(
    transaction_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get similar transactions for a given transaction

    Returns transactions similar by:
    - Payee (fuzzy match, ≥60% similarity)
    - Amount (±10%)
    - Date (surrounding transactions in same batch)

    Args:
        transaction_id: ID of the transaction to find similar for

    Returns:
        Dict with:
        - transaction: The reference transaction
        - by_payee: List of similar transactions by payee
        - by_amount: List of similar transactions by amount
        - surrounding: List of surrounding transactions by date

    Raises:
        404: If transaction not found or not owned by user
    """
    try:
        result = get_similar_transactions(db, user['id'], transaction_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
