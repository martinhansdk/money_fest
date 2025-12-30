"""
Rule management endpoints (Phase 5)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sqlite3

from app.database import get_db
from app.models import (
    RuleCreate,
    RuleUpdate,
    RuleResponse,
    RuleSuggestion,
    RulePreviewRequest,
    TransactionResponse
)
from app.auth import get_current_user
from app.services.rule import (
    create_rule,
    list_rules,
    get_rule,
    update_rule,
    delete_rule,
    get_matching_rules_for_transaction,
    get_matching_transactions_for_rule
)
from app.services.transaction import get_transaction_by_id

router = APIRouter()


@router.get("", response_model=List[RuleResponse])
def list_user_rules(
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    List all rules for the current user

    Returns:
        List of rules sorted by creation date (newest first)
    """
    rules = list_rules(db, user['id'])
    return rules


@router.post("", response_model=RuleResponse, status_code=201)
def create_new_rule(
    rule: RuleCreate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Create a new rule

    Args:
        rule: Rule data (pattern, match_type, category)

    Returns:
        Created rule

    Raises:
        400: If category doesn't exist
    """
    try:
        created_rule = create_rule(
            db,
            user['id'],
            rule.pattern,
            rule.match_type,
            rule.category
        )
        return created_rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{rule_id}", response_model=RuleResponse)
def get_rule_by_id(
    rule_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get a specific rule

    Args:
        rule_id: ID of the rule

    Returns:
        Rule data

    Raises:
        404: If rule not found or not owned by user
    """
    try:
        rule = get_rule(db, rule_id, user['id'])
        return rule
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule_by_id(
    rule_id: int,
    rule_update: RuleUpdate,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Update a rule

    Args:
        rule_id: ID of the rule
        rule_update: Updated rule data

    Returns:
        Updated rule

    Raises:
        404: If rule not found or not owned by user
        400: If category doesn't exist
    """
    try:
        updated_rule = update_rule(
            db,
            rule_id,
            user['id'],
            pattern=rule_update.pattern,
            match_type=rule_update.match_type,
            category=rule_update.category
        )
        return updated_rule
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rule_id}", status_code=204)
def delete_rule_by_id(
    rule_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Delete a rule

    Args:
        rule_id: ID of the rule

    Raises:
        404: If rule not found or not owned by user
    """
    try:
        delete_rule(db, rule_id, user['id'])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/suggestions/{transaction_id}", response_model=List[RuleSuggestion])
def get_rule_suggestions(
    transaction_id: int,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Get rule-based category suggestions for a transaction

    Args:
        transaction_id: ID of the transaction

    Returns:
        List of matching rules with category suggestions

    Raises:
        404: If transaction not found
    """
    try:
        # Get the transaction
        transaction = get_transaction_by_id(db, transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Get matching rules
        suggestions = get_matching_rules_for_transaction(
            db,
            user['id'],
            transaction['payee']
        )

        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/preview", response_model=List[TransactionResponse])
def preview_rule_matches(
    preview_request: RulePreviewRequest,
    db: sqlite3.Connection = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Preview which transactions would match a rule pattern

    Args:
        preview_request: Pattern and match_type to preview

    Returns:
        List of transactions that match the pattern
    """
    matching_transactions = get_matching_transactions_for_rule(
        db,
        user['id'],
        preview_request.pattern,
        preview_request.match_type
    )

    return matching_transactions
