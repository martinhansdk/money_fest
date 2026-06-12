"""
Rule management service functions (Phase 5)
"""

import sqlite3
from typing import List, Optional
from app.database import dict_from_row


def create_rule(
    db: sqlite3.Connection,
    user_id: int,
    pattern: str,
    match_type: str,
    category: str
) -> dict:
    """
    Create a new rule

    Args:
        db: Database connection
        user_id: ID of the user creating the rule
        pattern: Pattern to match (e.g., "Starbucks")
        match_type: How to match - "contains" or "exact"
        category: Category to suggest when matched

    Returns:
        Created rule as dictionary

    Raises:
        ValueError: If category doesn't exist
    """
    # Validate category exists
    category_row = db.execute(
        "SELECT id FROM categories WHERE full_path = ?",
        (category,)
    ).fetchone()

    if not category_row:
        raise ValueError(f"Category '{category}' does not exist")

    # Create rule
    cursor = db.execute(
        """
        INSERT INTO rules (user_id, pattern, match_type, category)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, pattern, match_type, category)
    )

    rule_id = cursor.lastrowid

    # Fetch and return created rule
    row = db.execute(
        "SELECT * FROM rules WHERE id = ?",
        (rule_id,)
    ).fetchone()

    return dict_from_row(row)


def list_rules(db: sqlite3.Connection, user_id: int) -> List[dict]:
    """
    List all rules for a user

    Args:
        db: Database connection
        user_id: ID of the user

    Returns:
        List of rules sorted by creation date (newest first)
    """
    cursor = db.execute(
        """
        SELECT * FROM rules
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

    return [dict_from_row(row) for row in cursor.fetchall()]


def get_rule(db: sqlite3.Connection, rule_id: int, user_id: int) -> Optional[dict]:
    """
    Get a specific rule

    Args:
        db: Database connection
        rule_id: ID of the rule
        user_id: ID of the user (for ownership check)

    Returns:
        Rule as dictionary or None if not found

    Raises:
        ValueError: If rule not found or not owned by user
    """
    row = db.execute(
        "SELECT * FROM rules WHERE id = ? AND user_id = ?",
        (rule_id, user_id)
    ).fetchone()

    if not row:
        raise ValueError(f"Rule {rule_id} not found")

    return dict_from_row(row)


def update_rule(
    db: sqlite3.Connection,
    rule_id: int,
    user_id: int,
    pattern: Optional[str] = None,
    match_type: Optional[str] = None,
    category: Optional[str] = None
) -> dict:
    """
    Update a rule

    Args:
        db: Database connection
        rule_id: ID of the rule
        user_id: ID of the user (for ownership check)
        pattern: New pattern (optional)
        match_type: New match type (optional)
        category: New category (optional)

    Returns:
        Updated rule as dictionary

    Raises:
        ValueError: If rule not found, not owned by user, or category doesn't exist
    """
    # Verify rule exists and is owned by user
    get_rule(db, rule_id, user_id)

    # Build update query dynamically
    updates = []
    params = []

    if pattern is not None:
        updates.append("pattern = ?")
        params.append(pattern)

    if match_type is not None:
        updates.append("match_type = ?")
        params.append(match_type)

    if category is not None:
        # Validate category exists
        category_row = db.execute(
            "SELECT id FROM categories WHERE full_path = ?",
            (category,)
        ).fetchone()

        if not category_row:
            raise ValueError(f"Category '{category}' does not exist")

        updates.append("category = ?")
        params.append(category)

    if not updates:
        # No updates requested, just return current rule
        return get_rule(db, rule_id, user_id)

    # Execute update
    params.extend([rule_id, user_id])
    db.execute(
        f"UPDATE rules SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
        params
    )

    # Return updated rule
    return get_rule(db, rule_id, user_id)


def delete_rule(db: sqlite3.Connection, rule_id: int, user_id: int) -> None:
    """
    Delete a rule

    Args:
        db: Database connection
        rule_id: ID of the rule
        user_id: ID of the user (for ownership check)

    Raises:
        ValueError: If rule not found or not owned by user
    """
    # Verify rule exists and is owned by user
    get_rule(db, rule_id, user_id)

    # Delete rule
    db.execute(
        "DELETE FROM rules WHERE id = ? AND user_id = ?",
        (rule_id, user_id)
    )


def get_matching_rules_for_transaction(
    db: sqlite3.Connection,
    user_id: int,
    payee: str
) -> List[dict]:
    """
    Get all rules that match a transaction's payee

    Args:
        db: Database connection
        user_id: ID of the user
        payee: Payee to match against rules

    Returns:
        List of matching rules with suggestions
    """
    # Get all rules for user
    rules = list_rules(db, user_id)

    matching_rules = []
    for rule in rules:
        pattern = rule['pattern']
        match_type = rule['match_type']

        # Check if rule matches
        matches = False
        if match_type == 'contains':
            matches = pattern.lower() in payee.lower()
        elif match_type == 'exact':
            matches = pattern.lower() == payee.lower()

        if matches:
            matching_rules.append({
                'rule_id': rule['id'],
                'category': rule['category'],
                'pattern': rule['pattern'],
                'match_type': rule['match_type']
            })

    return matching_rules


def get_matching_transactions_for_rule(
    db: sqlite3.Connection,
    user_id: int,
    pattern: str,
    match_type: str,
    batch_id: Optional[int] = None,
    limit: int = 500
) -> List[dict]:
    """
    Preview which transactions would match a rule pattern

    Args:
        db: Database connection
        user_id: ID of the user
        pattern: Pattern to match
        match_type: How to match - "contains" or "exact"
        batch_id: Limit matches to one batch (None = all the user's batches)
        limit: Maximum number of matches to return

    Returns:
        List of matching transactions (each includes batch_name)
    """
    if match_type == 'exact':
        payee_condition = "LOWER(t.payee) = LOWER(?)"
        payee_param = pattern
    else:
        # LIKE special characters in the pattern must be escaped for a literal match
        escaped = pattern.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        payee_condition = "LOWER(t.payee) LIKE '%' || LOWER(?) || '%' ESCAPE '\\'"
        payee_param = escaped

    query = f"""
        SELECT t.*, b.name AS batch_name FROM transactions t
        JOIN batches b ON t.batch_id = b.id
        WHERE b.user_id = ? AND {payee_condition}
    """
    params: list = [user_id, payee_param]

    if batch_id is not None:
        query += " AND t.batch_id = ?"
        params.append(batch_id)

    query += " ORDER BY t.date DESC LIMIT ?"
    params.append(limit)

    cursor = db.execute(query, params)
    return [dict_from_row(row) for row in cursor.fetchall()]
