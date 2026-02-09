"""
Cleanup utilities for Resume Critiquer application.
Manages export file retention and old file cleanup.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from src import config


def get_export_files() -> List[Tuple[Path, float]]:
    """
    Get all export files with their modification times.

    Returns:
        List of tuples (file_path, modification_time)
        Sorted by modification time (newest first)
    """
    export_files = []

    if not config.EXPORTS_DIR.exists():
        return export_files

    # Get all CSV, XLSX, and JSON files
    for pattern in ['*.csv', '*.xlsx', '*.json']:
        for file in config.EXPORTS_DIR.glob(pattern):
            if file.is_file():
                mtime = file.stat().st_mtime
                export_files.append((file, mtime))

    # Sort by modification time (newest first)
    export_files.sort(key=lambda x: x[1], reverse=True)

    return export_files


def cleanup_old_exports(max_keep: int = None, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Clean up old export files, keeping only the most recent ones.

    Args:
        max_keep: Maximum number of export files to keep (default from config)
        dry_run: If True, only report what would be deleted without deleting

    Returns:
        Tuple of (number_deleted, list_of_deleted_filenames)
    """
    if max_keep is None:
        max_keep = config.MAX_EXPORTS_TO_KEEP

    export_files = get_export_files()

    if len(export_files) <= max_keep:
        # Nothing to delete
        return 0, []

    # Files to delete are those beyond the max_keep limit
    files_to_delete = export_files[max_keep:]

    deleted_files = []
    for file_path, _ in files_to_delete:
        try:
            if not dry_run:
                file_path.unlink()
            deleted_files.append(file_path.name)
        except Exception as e:
            print(f"Warning: Could not delete {file_path.name}: {e}")

    return len(deleted_files), deleted_files


def get_export_summary() -> dict:
    """
    Get summary information about export files.

    Returns:
        Dictionary with export statistics
    """
    export_files = get_export_files()

    total_size = sum(f[0].stat().st_size for f in export_files)

    # Count by type
    csv_count = sum(1 for f in export_files if f[0].suffix == '.csv')
    xlsx_count = sum(1 for f in export_files if f[0].suffix == '.xlsx')
    json_count = sum(1 for f in export_files if f[0].suffix == '.json')

    # Get oldest and newest
    oldest = None
    newest = None
    if export_files:
        newest = datetime.fromtimestamp(export_files[0][1])
        oldest = datetime.fromtimestamp(export_files[-1][1])

    return {
        'total_files': len(export_files),
        'total_size_mb': total_size / (1024 * 1024),
        'csv_count': csv_count,
        'xlsx_count': xlsx_count,
        'json_count': json_count,
        'oldest_file': oldest,
        'newest_file': newest
    }


def cleanup_database_on_startup():
    """
    Perform database maintenance tasks on application startup.
    Currently just ensures the database directory exists.
    """
    # Ensure data directory exists
    config.DATA_DIR.mkdir(exist_ok=True)

    # Could add database vacuum, integrity checks, etc. here in the future
    pass


def get_database_size() -> float:
    """
    Get the size of the database file in MB.

    Returns:
        Size in MB, or 0 if database doesn't exist
    """
    db_path = Path(config.DB_PATH)
    if db_path.exists():
        return db_path.stat().st_size / (1024 * 1024)
    return 0.0


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "2.5 MB", "150 KB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
