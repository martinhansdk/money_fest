"""
Database schema and connection management for Money Fest
Uses SQLite with raw SQL (no ORM)
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import settings


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    Database dependency for FastAPI

    Usage in FastAPI:
        def endpoint(db: sqlite3.Connection = Depends(get_db)):
            cursor = db.execute("SELECT * FROM users")
            result = cursor.fetchall()

    Usage in CLI/scripts:
        with get_db_context() as db:
            cursor = db.execute("SELECT * FROM users")
            result = cursor.fetchall()
    """
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_db_context() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections (for CLI and scripts)

    Usage:
        with get_db_context() as db:
            cursor = db.execute("SELECT * FROM users")
            result = cursor.fetchall()
    """
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the database schema
    Creates all tables and indexes (idempotent)
    """
    with get_db_context() as db:
        # Table 1: users
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table 2: categories
        db.execute("""
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
        db.execute("""
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
        db.execute("""
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
        db.execute("""
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

        # Indexes for transactions table
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_batch_id
            ON transactions (batch_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_payee
            ON transactions (payee)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions (date)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_amount
            ON transactions (amount)
        """)

        # Index for rules table
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rules_pattern
            ON rules (pattern)
        """)

        db.commit()


def dict_from_row(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row object to a dictionary"""
    return {key: row[key] for key in row.keys()}
