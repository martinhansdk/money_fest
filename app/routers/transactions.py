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
from app.websocket.connection_manager import manager
from app.services.batch import get_batch_progress
import sqlite3
import asyncio

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
async def bulk_update_endpoint(
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
        # Get batch_id from first transaction before update
        if bulk_update.transaction_ids:
            first_transaction = get_transaction_by_id(db, bulk_update.transaction_ids[0])
            batch_id = first_transaction['batch_id'] if first_transaction else None
        else:
            batch_id = None

        count = bulk_update_transactions(
            db,
            bulk_update.transaction_ids,
            category=bulk_update.category,
            note=bulk_update.note
        )

        # Broadcast updates via WebSocket
        if batch_id:
            # Broadcast progress update
            progress = get_batch_progress(db, batch_id)
            await manager.broadcast_batch_progress(batch_id, progress)

            # Get updated transactions and broadcast them
            for transaction_id in bulk_update.transaction_ids:
                transaction = get_transaction_by_id(db, transaction_id)
                if transaction:
                    await manager.broadcast_transaction_updated(batch_id, transaction, user_id=user['id'])

            # Check if batch is complete
            if progress['categorized_count'] == progress['total_count'] and progress['total_count'] > 0:
                await manager.broadcast_batch_complete(batch_id)

        return {"updated": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_transaction_endpoint(
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

        # Broadcast update via WebSocket
        await manager.broadcast_transaction_updated(
            transaction['batch_id'],
            transaction,
            user_id=user['id']
        )

        # Broadcast progress update
        progress = get_batch_progress(db, transaction['batch_id'])
        await manager.broadcast_batch_progress(
            transaction['batch_id'],
            progress
        )

        # Check if batch is complete
        if progress['categorized_count'] == progress['total_count'] and progress['total_count'] > 0:
            await manager.broadcast_batch_complete(transaction['batch_id'])

        return transaction
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
