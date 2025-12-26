"""
Tests for CLI commands
"""

import pytest
import tempfile
import os
from app.services.user import create_user, get_user_by_username
from app.services.category import (
    parse_category_line,
    import_categories_from_file,
    get_all_categories
)
from app.services.backup import backup_database
from app.database import get_db


def test_parse_category_line_with_parent():
    """Test parsing category line with parent:child format"""
    result = parse_category_line("Automobile:Gasoline")

    assert result == ("Automobile", "Gasoline", "Automobile:Gasoline")


def test_parse_category_line_without_parent():
    """Test parsing category line with parent-only format"""
    result = parse_category_line("Clothing")

    assert result == (None, "Clothing", "Clothing")


def test_parse_category_line_empty():
    """Test parsing empty line"""
    result = parse_category_line("")

    assert result is None


def test_parse_category_line_whitespace():
    """Test parsing line with whitespace"""
    result = parse_category_line("  Education:Books  ")

    assert result == ("Education", "Books", "Education:Books")


def test_import_categories_from_file():
    """Test importing categories from a file"""
    # Create a temporary file with test categories
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Clothing\n")
        f.write("Clothing:Shoes\n")
        f.write("Education\n")
        f.write("Education:Books\n")
        f.write("\n")  # Empty line should be skipped
        f.write("Donations:Church\n")
        temp_path = f.name

    try:
        with get_db() as db:
            count = import_categories_from_file(db, temp_path)

            assert count == 5

            # Verify categories were imported
            categories = get_all_categories(db)
            assert len(categories) == 5

            full_paths = [cat['full_path'] for cat in categories]
            assert "Clothing" in full_paths
            assert "Clothing:Shoes" in full_paths
            assert "Education:Books" in full_paths
    finally:
        os.unlink(temp_path)


def test_import_categories_file_not_found():
    """Test importing from non-existent file"""
    with get_db() as db:
        with pytest.raises(FileNotFoundError):
            import_categories_from_file(db, "/nonexistent/file.txt")


def test_import_categories_with_duplicates():
    """Test importing categories with duplicate full_paths"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Clothing\n")
        f.write("Clothing\n")  # Duplicate
        f.write("Education\n")
        temp_path = f.name

    try:
        with get_db() as db:
            count = import_categories_from_file(db, temp_path)

            # Should only import 2 (duplicate is ignored)
            assert count == 2

            categories = get_all_categories(db)
            assert len(categories) == 2
    finally:
        os.unlink(temp_path)


def test_backup_database():
    """Test creating a database backup"""
    # Create a temporary database file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        source_db = f.name

    # Create a temporary directory for backup
    backup_dir = tempfile.mkdtemp()

    try:
        # Create a simple database
        import sqlite3
        conn = sqlite3.connect(source_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test (id) VALUES (1)")
        conn.commit()
        conn.close()

        # Create backup
        backup_path = backup_database(source_db, backup_dir)

        # Verify backup exists
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.db')
        assert 'backup' in backup_path

        # Verify backup contains data
        backup_conn = sqlite3.connect(backup_path)
        cursor = backup_conn.execute("SELECT COUNT(*) FROM test")
        count = cursor.fetchone()[0]
        assert count == 1
        backup_conn.close()

    finally:
        # Cleanup
        if os.path.exists(source_db):
            os.unlink(source_db)
        if os.path.exists(backup_path):
            os.unlink(backup_path)
        if os.path.exists(backup_dir):
            os.rmdir(backup_dir)


def test_backup_database_source_not_found():
    """Test backup fails when source database doesn't exist"""
    backup_dir = tempfile.mkdtemp()

    try:
        with pytest.raises(FileNotFoundError):
            backup_database("/nonexistent/database.db", backup_dir)
    finally:
        if os.path.exists(backup_dir):
            os.rmdir(backup_dir)


def test_create_user_via_service():
    """Test creating a user via the user service"""
    with get_db() as db:
        user_id = create_user(db, "cliuser", "password123")

        assert user_id > 0

        # Verify user was created
        user = get_user_by_username(db, "cliuser")
        assert user is not None
        assert user['username'] == "cliuser"


def test_get_all_categories():
    """Test retrieving all categories"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Category1\n")
        f.write("Category2:Subcategory\n")
        temp_path = f.name

    try:
        with get_db() as db:
            import_categories_from_file(db, temp_path)
            categories = get_all_categories(db)

            assert len(categories) == 2
            assert all('full_path' in cat for cat in categories)
            assert all('usage_count' in cat for cat in categories)

            # Verify sorted by full_path
            full_paths = [cat['full_path'] for cat in categories]
            assert full_paths == sorted(full_paths)
    finally:
        os.unlink(temp_path)


def test_category_with_latin1_encoding():
    """Test importing categories with special characters (Danish: ø, å, æ)"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='latin-1') as f:
        f.write("Møbler\n")  # Danish for Furniture
        f.write("Køkken:Bestik\n")  # Danish for Kitchen:Cutlery
        temp_path = f.name

    try:
        with get_db() as db:
            count = import_categories_from_file(db, temp_path)

            assert count == 2

            categories = get_all_categories(db)
            full_paths = [cat['full_path'] for cat in categories]

            assert "Møbler" in full_paths
            assert "Køkken:Bestik" in full_paths
    finally:
        os.unlink(temp_path)
