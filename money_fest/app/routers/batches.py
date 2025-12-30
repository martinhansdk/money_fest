"""
Batch management endpoints (Phase 2)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from typing import List
from app.database import get_db
from app.models import BatchResponse
from app.auth import get_current_user
from app.services.batch import (
    create_batch,
    get_batch_by_id,
    list_batches,
    delete_batch,
    archive_batch,
    unarchive_batch
)
from app.services.transaction import list_transactions
from app.services.csv_parser import get_parser, CSVGenerator
import sqlite3

router = APIRouter()


@router.post("", response_model=BatchResponse, status_code=201)
async def upload_batch(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Upload a CSV file and create a new batch

    Args:
        name: Batch name
        file: CSV file to upload

    Returns:
        Created batch with ID

    Raises:
        400: If CSV is invalid, empty, or cannot be parsed
    """
    # Read file content
    file_content = await file.read()

    # Validate file is not empty
    if not file_content or len(file_content.strip()) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Auto-detect format and get parser
    try:
        parser = get_parser(file_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Parse transactions
    try:
        parsed_transactions = parser.parse(file_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"CSV parsing failed: {e}")

    # Convert to dict format for create_batch
    transactions = [
        {
            'date': txn.date,
            'payee': txn.payee,
            'amount': txn.amount,
            'original_category': txn.original_category,
            'original_comment': txn.original_comment
        }
        for txn in parsed_transactions
    ]

    # Create batch
    try:
        batch_id = create_batch(db, name, user['id'], transactions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return created batch
    batch = get_batch_by_id(db, batch_id)
    return batch


@router.get("", response_model=List[BatchResponse])
def get_batches(
    include_archived: bool = False,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get all batches for the current user

    Args:
        include_archived: Include archived batches in results (default: False)

    Returns:
        List of batches sorted by creation date (newest first)
    """
    batches = list_batches(db, user['id'], include_archived)
    return batches


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get batch details by ID

    Args:
        batch_id: Batch ID

    Returns:
        Batch with progress information

    Raises:
        404: If batch not found
    """
    batch = get_batch_by_id(db, batch_id)

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Verify ownership
    if batch['user_id'] != user['id']:
        raise HTTPException(status_code=404, detail="Batch not found")

    return batch


@router.delete("/{batch_id}")
def delete_batch_endpoint(
    batch_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Delete a batch and all its transactions

    Args:
        batch_id: Batch ID to delete

    Returns:
        Success message

    Raises:
        404: If batch not found or not owned by user
    """
    try:
        delete_batch(db, batch_id, user['id'])
        return {"message": "Batch deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{batch_id}/archive")
def archive_batch_endpoint(
    batch_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Archive a batch (mark as archived)

    Args:
        batch_id: Batch ID to archive

    Returns:
        Success message

    Raises:
        404: If batch not found or not owned by user
    """
    # Verify ownership first
    batch = get_batch_by_id(db, batch_id)
    if not batch or batch['user_id'] != user['id']:
        raise HTTPException(status_code=404, detail="Batch not found")

    archive_batch(db, batch_id)
    return {"message": "Batch archived successfully"}


@router.post("/{batch_id}/unarchive")
def unarchive_batch_endpoint(
    batch_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Unarchive a batch (mark as in_progress)

    Args:
        batch_id: Batch ID to unarchive

    Returns:
        Success message

    Raises:
        404: If batch not found or not owned by user
    """
    # Verify ownership first
    batch = get_batch_by_id(db, batch_id)
    if not batch or batch['user_id'] != user['id']:
        raise HTTPException(status_code=404, detail="Batch not found")

    unarchive_batch(db, batch_id)
    return {"message": "Batch unarchived successfully"}


@router.get("/{batch_id}/download")
def download_batch(
    batch_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Download batch transactions as CSV (AceMoney format)

    Automatically archives the batch after download

    Args:
        batch_id: Batch ID to download

    Returns:
        CSV file with transactions in AceMoney format

    Raises:
        404: If batch not found or not owned by user
    """
    # Verify ownership
    batch = get_batch_by_id(db, batch_id)
    if not batch or batch['user_id'] != user['id']:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get all transactions
    try:
        transactions = list_transactions(db, batch_id, user['id'])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Generate CSV
    generator = CSVGenerator()
    csv_bytes = generator.generate(transactions)

    # Archive batch after download
    archive_batch(db, batch_id)

    # Return CSV as downloadable file
    filename = f"{batch['name'].replace(' ', '_')}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
