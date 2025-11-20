"""File collision detection and handling."""

import hashlib
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Tuple

try:
    import xxhash

    XXHASH_AVAILABLE = True
except ImportError:
    XXHASH_AVAILABLE = False

logger = logging.getLogger(__name__)


class CollisionMethod(Enum):
    """Methods for detecting file collisions."""

    SIZE = "size"  # Compare only file size
    HASH_SHA256 = "hash-sha256"  # Compare size and SHA256 hash
    HASH_FAST = "hash-fast"  # Compare size and fast hash (xxhash or blake2b)


class CollisionTracker:
    """Track extracted files and detect collisions."""

    def __init__(self, method: CollisionMethod = CollisionMethod.HASH_FAST):
        """
        Initialize collision tracker.

        Args:
            method: Method to use for collision detection
        """
        self.method = method
        # Map: relative_path -> (size, hash)
        self.files: Dict[str, Tuple[int, str | None]] = {}

    def _compute_hash(self, file_path: Path) -> str:
        """
        Compute file hash based on selected method.

        Args:
            file_path: Path to file

        Returns:
            Hash string or empty string if not needed
        """
        if self.method == CollisionMethod.SIZE:
            return ""

        # Choose hash algorithm
        if self.method == CollisionMethod.HASH_FAST:
            if XXHASH_AVAILABLE:
                hasher = xxhash.xxh64()
            else:
                hasher = hashlib.blake2b()
        else:  # HASH_SHA256
            hasher = hashlib.sha256()

        # Compute hash in chunks
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        return hasher.hexdigest()

    def check_collision(self, relative_path: str, file_path: Path) -> Tuple[bool, bool]:
        """
        Check if file collides with existing file.

        Args:
            relative_path: Relative path in archive
            file_path: Actual file path to check

        Returns:
            Tuple of (is_collision, files_are_identical)
            - (False, False): No collision, new file
            - (True, True): Collision, but files are identical (can skip)
            - (True, False): Collision, files are different (need rename)
        """
        if relative_path not in self.files:
            # No collision, new file
            size = file_path.stat().st_size
            file_hash = self._compute_hash(file_path) if self.method != CollisionMethod.SIZE else None
            self.files[relative_path] = (size, file_hash)
            return False, False

        # Collision detected
        existing_size, existing_hash = self.files[relative_path]
        current_size = file_path.stat().st_size

        # Different sizes = different files
        if current_size != existing_size:
            return True, False

        # Same size, check hash if needed
        if self.method == CollisionMethod.SIZE:
            # Only comparing sizes, assume identical
            return True, True

        current_hash = self._compute_hash(file_path)
        files_identical = current_hash == existing_hash

        return True, files_identical

    def register_file(self, relative_path: str, file_path: Path) -> None:
        """
        Register a file in tracker.

        Args:
            relative_path: Relative path in archive
            file_path: Actual file path
        """
        size = file_path.stat().st_size
        file_hash = self._compute_hash(file_path) if self.method != CollisionMethod.SIZE else None
        self.files[relative_path] = (size, file_hash)


def generate_unique_name(base_path: Path, original_name: str) -> Path:
    """
    Generate unique filename by adding suffix.

    Args:
        base_path: Base directory
        original_name: Original filename with relative path

    Returns:
        Unique path (e.g., file.jpg -> file-1.jpg -> file-2.jpg)
    """
    original_path = Path(original_name)
    stem = original_path.stem
    suffix = original_path.suffix
    parent = base_path / original_path.parent

    counter = 1
    while True:
        new_name = f"{stem}-{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            # Return relative path
            return Path(original_path.parent) / new_name
        counter += 1
