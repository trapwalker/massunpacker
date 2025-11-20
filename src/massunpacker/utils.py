"""Utility functions for massunpacker."""

import shutil
from pathlib import Path
from typing import Iterator

from natsort import natsorted


def get_sorted_zip_files(pattern: str, limit: int | None = None) -> list[Path]:
    """
    Get list of zip files matching the pattern, naturally sorted.

    Args:
        pattern: Glob pattern for zip files (e.g., "path/*/file_*.zip")
        limit: Maximum number of files to return (None for all)

    Returns:
        List of Path objects for matching zip files, naturally sorted
    """
    # Find the base directory from pattern
    parts = pattern.split("*")[0]
    if "/" in parts or "\\" in parts:
        base_dir = Path(parts).parent
    else:
        base_dir = Path.cwd()

    # Get all matching files
    files = list(base_dir.glob(pattern.replace(str(base_dir) + "/", "")))

    # Natural sort
    sorted_files = natsorted(files, key=lambda p: str(p))

    # Apply limit
    if limit is not None:
        sorted_files = sorted_files[:limit]

    return sorted_files


def check_disk_space(target_dir: Path, required_bytes: int, safety_margin: int = 100 * 1024 * 1024) -> tuple[bool, int]:
    """
    Check if there's enough disk space for extraction.

    Args:
        target_dir: Directory where files will be extracted
        required_bytes: Number of bytes needed
        safety_margin: Extra bytes to keep free (default 100MB)

    Returns:
        Tuple of (has_enough_space, available_bytes)
    """
    stat = shutil.disk_usage(target_dir)
    available = stat.free
    needed = required_bytes + safety_margin

    return available >= needed, available


def ensure_directory(path: Path, description: str = "directory") -> None:
    """
    Ensure directory exists, create if needed.

    Args:
        path: Directory path
        description: Human-readable description for error messages

    Raises:
        RuntimeError: If directory cannot be created
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Cannot create {description} at {path}: {e}") from e


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """
    Check if target path is safe (no path traversal).

    Args:
        base_dir: Base directory that should contain the target
        target_path: Target path to check

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve both paths and check if target is under base
        base_resolved = base_dir.resolve()
        target_resolved = target_path.resolve()
        return target_resolved.is_relative_to(base_resolved)
    except (ValueError, OSError):
        return False
