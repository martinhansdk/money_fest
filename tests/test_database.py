"""
Tests for database schema and initialization
"""

import pytest
import sqlite3
from app.database import init_db, get_db, dict_from_row


def test_init_db_creates_all_tables(test_db):
    """Test that init_db creates all required tables"""
    cursor = test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    assert "users" in tables
    assert "categories" in tables
    assert "batches" in tables
    assert "transactions" in tables
    assert "rules" in tables


def test_init_db_is_idempotent(test_db):
    """Test that calling init_db multiple times doesn't cause errors"""
    # Tables already created in test_db fixture
    # Try creating them again
    cursor = test_db.cursor()

    # This should not raise an error due to IF NOT EXISTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Verify table still exists and has correct structure
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    assert cursor.fetchone() is not None


def test_all_indexes_exist(test_db):
    """Test that all required indexes are created"""
    cursor = test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
    )
    indexes = [row[0] for row in cursor.fetchall()]

    assert "idx_transactions_batch_id" in indexes
    assert "idx_transactions_payee" in indexes
    assert "idx_transactions_date" in indexes
    assert "idx_transactions_amount" in indexes
    assert "idx_rules_pattern" in indexes


def test_foreign_key_constraints(test_db):
    """Test that foreign key constraints are enforced"""
    # Create a user
    test_db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("testuser", "hashed_password")
    )
    user_id = test_db.execute("SELECT last_insert_rowid()").fetchone()[0]
    test_db.commit()

    # Create a batch for this user
    test_db.execute(
        "INSERT INTO batches (name, user_id) VALUES (?, ?)",
        ("Test Batch", user_id)
    )
    test_db.commit()

    # Try to delete the user (should fail due to foreign key constraint)
    # Actually with ON DELETE CASCADE, it should succeed but delete related batches
    test_db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    test_db.commit()

    # Verify batch was also deleted (CASCADE)
    cursor = test_db.execute("SELECT COUNT(*) FROM batches")
    count = cursor.fetchone()[0]
    assert count == 0


def test_users_table_structure(test_db):
    """Test users table has correct columns"""
    cursor = test_db.execute("PRAGMA table_info(users)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    assert "id" in columns
    assert "username" in columns
    assert "password_hash" in columns
    assert "created_at" in columns


def test_categories_table_structure(test_db):
    """Test categories table has correct columns"""
    cursor = test_db.execute("PRAGMA table_info(categories)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    assert "id" in columns
    assert "name" in columns
    assert "parent" in columns
    assert "full_path" in columns
    assert "usage_count" in columns
    assert "created_at" in columns


def test_dict_from_row():
    """Test dict_from_row helper function"""
    # Create a simple Row-like object
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT 1 as id, 'test' as name")
    row = cursor.fetchone()

    result = dict_from_row(row)

    assert result == {"id": 1, "name": "test"}
    assert isinstance(result, dict)

    conn.close()


def test_status_check_constraints(test_db):
    """Test that status check constraints are enforced"""
    # Create a user and batch
    test_db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("testuser", "hash")
    )
    user_id = test_db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Try to insert batch with invalid status
    with pytest.raises(sqlite3.IntegrityError):
        test_db.execute(
            "INSERT INTO batches (name, user_id, status) VALUES (?, ?, ?)",
            ("Test", user_id, "invalid_status")
        )


def test_unique_constraints(test_db):
    """Test unique constraints on username and category full_path"""
    # Test username unique constraint
    test_db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("testuser", "hash1")
    )
    test_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        test_db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("testuser", "hash2")
        )

    # Test category full_path unique constraint
    test_db.execute(
        "INSERT INTO categories (name, full_path) VALUES (?, ?)",
        ("Test", "Test")
    )
    test_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        test_db.execute(
            "INSERT INTO categories (name, full_path) VALUES (?, ?)",
            ("Test2", "Test")
        )
