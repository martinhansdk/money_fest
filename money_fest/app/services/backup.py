"""
Backup service for database backups
"""

import shutil
import os
from datetime import datetime
from pathlib import Path


def backup_database(source_path: str, dest_dir: str) -> str:
    """
    Create a backup copy of the database file

    Args:
        source_path: Path to the source database file
        dest_dir: Directory to save the backup to

    Returns:
        Full path to the created backup file

    Raises:
        FileNotFoundError: If source database doesn't exist
        IOError: If backup fails
    """
    # Check if source exists
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Database file not found: {source_path}")

    # Create destination directory if it doesn't exist
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    source_filename = os.path.basename(source_path)
    name_without_ext = os.path.splitext(source_filename)[0]
    backup_filename = f"{name_without_ext}_backup_{timestamp}.db"
    dest_path = os.path.join(dest_dir, backup_filename)

    # Copy the database file
    try:
        shutil.copy2(source_path, dest_path)
    except Exception as e:
        raise IOError(f"Failed to create backup: {str(e)}")

    # Verify the backup was created
    if not os.path.exists(dest_path):
        raise IOError("Backup file was not created")

    return dest_path
