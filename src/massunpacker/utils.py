"""Utility functions for massunpacker."""

import shutil
from pathlib import Path
from typing import Iterator

from natsort import natsorted


def get_sorted_zip_files(patterns: list[str], limit: int | None = None) -> list[Path]:
    """
    Get list of zip files from patterns or file paths, naturally sorted.

    Args:
        patterns: List of glob patterns or file paths (e.g., ["path/*.zip"] or ["file1.zip", "file2.zip"])
        limit: Maximum number of files to return (None for all)

    Returns:
        List of Path objects for matching zip files, naturally sorted
    """
    all_files = set()

    for pattern in patterns:
        path = Path(pattern)

        # Check if it's an existing file
        if path.exists() and path.is_file():
            all_files.add(path.resolve())
        # Otherwise treat as glob pattern
        elif "*" in pattern or "?" in pattern:
            # Find the base directory from pattern
            parts = pattern.split("*")[0]
            if "/" in parts or "\\" in parts:
                base_dir = Path(parts).parent
                relative_pattern = pattern.replace(str(base_dir) + "/", "").replace(str(base_dir) + "\\", "")
            else:
                base_dir = Path.cwd()
                relative_pattern = pattern

            # Get all matching files
            matches = base_dir.glob(relative_pattern)
            all_files.update(p.resolve() for p in matches if p.is_file())
        else:
            # Try as file path even if doesn't exist yet (might be a typo, will error later)
            if path.suffix.lower() == ".zip":
                all_files.add(path.resolve())

    # Natural sort
    sorted_files = natsorted(list(all_files), key=lambda p: str(p))

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
