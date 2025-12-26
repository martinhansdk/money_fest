"""
Pytest configuration and fixtures for testing
"""

import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db
from app.services.user import create_user
from app.auth import create_session
from app.config import settings


@pytest.fixture
def test_db():
    """
    Create an in-memory SQLite database for testing

    Yields:
        Database connection with schema initialized
    """
    # Create in-memory database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Initialize schema
    cursor = conn.cursor()

    # Table 1: users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: categories
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent TEXT,
            full_path TEXT NOT NULL UNIQUE,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 3: batches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'complete', 'archived')),
            date_range_start TEXT,
            date_range_end TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Table 4: transactions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            payee TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            note TEXT,
            status TEXT DEFAULT 'uncategorized' CHECK(status IN ('uncategorized', 'categorized')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (batch_id) REFERENCES batches (id) ON DELETE CASCADE,
            FOREIGN KEY (category) REFERENCES categories (full_path) ON DELETE SET NULL
        )
    """)

    # Table 5: rules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pattern TEXT NOT NULL,
            match_type TEXT NOT NULL CHECK(match_type IN ('contains', 'exact')),
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (category) REFERENCES categories (full_path) ON DELETE CASCADE
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_batch_id ON transactions (batch_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_payee ON transactions (payee)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions (amount)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rules_pattern ON rules (pattern)")

    conn.commit()

    yield conn

    conn.close()


@pytest.fixture
def client():
    """
    Create a TestClient for the FastAPI application

    Yields:
        FastAPI TestClient
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def authenticated_client(client):
    """
    Create an authenticated TestClient with a logged-in user

    Args:
        client: FastAPI TestClient fixture

    Yields:
        TestClient with session cookie for authenticated requests
    """
    # Create a test user
    from app.database import get_db
    from app.services.user import create_user

    with get_db() as db:
        user_id = create_user(db, "testuser", "testpass123")

    # Login to get session cookie
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200

    yield client


@pytest.fixture
def sample_categories():
    """
    Provide a list of sample categories for testing

    Returns:
        List of category tuples (parent, name, full_path)
    """
    return [
        (None, "Clothing", "Clothing"),
        ("Clothing", "Shoes", "Clothing:Shoes"),
        (None, "Donations", "Donations"),
        ("Donations", "Church", "Donations:Church"),
        (None, "Education", "Education"),
        ("Education", "Books", "Education:Books"),
        ("Education", "Tuition", "Education:Tuition"),
    ]
