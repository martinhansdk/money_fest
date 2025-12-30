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
    min_similarity: float = 0.6,
    tolerance: float = 0.10,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get similar transactions for a given transaction

    Returns transactions similar by:
    - Payee (fuzzy match, configurable similarity threshold)
    - Amount (configurable tolerance percentage)
    - Date (surrounding transactions in same batch)

    Args:
        transaction_id: ID of the transaction to find similar for
        min_similarity: Minimum similarity for payee matching (0.0-1.0, default 0.6)
        tolerance: Tolerance for amount matching (0.0-1.0, default 0.10 = ±10%)

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
        result = get_similar_transactions(
            db, user['id'], transaction_id,
            min_similarity=min_similarity,
            tolerance=tolerance
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
