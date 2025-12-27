"""
Transaction management endpoints (Phase 2)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.database import get_db
from app.models import TransactionResponse, TransactionUpdate, BulkTransactionUpdate
from app.auth import get_current_user
from app.services.transaction import (
    list_transactions,
    get_transaction_by_id,
    update_transaction,
    bulk_update_transactions
)
import sqlite3

router = APIRouter()


@router.get("/batches/{batch_id}/transactions", response_model=List[TransactionResponse])
def get_batch_transactions(
    batch_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get all transactions for a batch

    Args:
        batch_id: ID of the batch

    Returns:
        List of transactions sorted by date

    Raises:
        404: If batch not found or not owned by user
    """
    try:
        transactions = list_transactions(db, batch_id, user['id'])
        return transactions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/transactions/bulk")
def bulk_update_endpoint(
    bulk_update: BulkTransactionUpdate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Bulk update multiple transactions

    Args:
        bulk_update: Bulk update data (transaction IDs, category, note)

    Returns:
        Number of transactions updated

    Raises:
        400: If validation fails (no IDs, invalid category)
    """
    try:
        count = bulk_update_transactions(
            db,
            bulk_update.transaction_ids,
            category=bulk_update.category,
            note=bulk_update.note
        )
        return {"updated": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction_endpoint(
    transaction_id: int,
    update: TransactionUpdate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Update a transaction's category and/or note

    Args:
        transaction_id: ID of the transaction
        update: Update data (category and/or note)

    Returns:
        Updated transaction

    Raises:
        404: If transaction not found
        400: If category doesn't exist
    """
    try:
        transaction = update_transaction(
            db,
            transaction_id,
            category=update.category,
            note=update.note
        )
        return transaction
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
