#!/usr/bin/env python3
"""
One-time migration to fix batch statuses for existing batches.

This script checks all 'in_progress' batches and updates them to 'complete'
if all their transactions are categorized.

Run this once after deploying the batch status auto-update feature.
"""

import sqlite3
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import get_database_path


def fix_batch_statuses():
    """Fix batch statuses for all existing batches"""
    db_path = get_database_path()

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Find all in_progress batches
    cursor.execute("""
        SELECT id, name FROM batches WHERE status = 'in_progress'
    """)
    in_progress_batches = cursor.fetchall()

    print(f"Found {len(in_progress_batches)} in_progress batches")

    updated_count = 0

    for batch_id, batch_name in in_progress_batches:
        # Check if all transactions are categorized
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'categorized' THEN 1 ELSE 0 END) as categorized
            FROM transactions
            WHERE batch_id = ?
        """, (batch_id,))

        row = cursor.fetchone()
        total = row[0]
        categorized = row[1] or 0

        if total > 0 and categorized == total:
            # All transactions categorized, mark as complete
            cursor.execute("""
                UPDATE batches
                SET status = 'complete', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (batch_id,))

            print(f"  ✓ Updated batch '{batch_name}' (ID: {batch_id}) to 'complete'")
            updated_count += 1
        else:
            print(f"  - Batch '{batch_name}' (ID: {batch_id}) still has {total - categorized}/{total} uncategorized transactions")

    conn.commit()
    conn.close()

    print(f"\nMigration complete: {updated_count} batches updated to 'complete'")


if __name__ == '__main__':
    fix_batch_statuses()
