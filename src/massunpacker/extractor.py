"""Main extraction logic for massunpacker."""

import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .collision import CollisionMethod, CollisionTracker, generate_unique_name
from .encoding import decode_filename, fix_zip_filename
from .i18n import _
from .utils import check_disk_space, is_safe_path

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of extracting a single archive."""

    archive_path: Path
    success: bool
    files_extracted: int = 0
    files_skipped: int = 0  # Identical files
    files_renamed: int = 0  # Collisions
    size_compressed: int = 0
    size_uncompressed: int = 0
    errors: List[str] = field(default_factory=list)
    collisions: List[tuple[str, str]] = field(default_factory=list)  # (original, new_name)


class Extractor:
    """Main extractor class handling zip archive extraction."""

    def __init__(
        self,
        output_dir: Path,
        collision_method: CollisionMethod = CollisionMethod.HASH_FAST,
        safety_margin: int = 100 * 1024 * 1024,
    ):
        """
        Initialize extractor.

        Args:
            output_dir: Directory where files will be extracted
            collision_method: Method for detecting collisions
            safety_margin: Safety margin for disk space (bytes)
        """
        self.output_dir = output_dir.resolve()
        self.collision_tracker = CollisionTracker(method=collision_method)
        self.safety_margin = safety_margin

    def extract_archive(self, archive_path: Path) -> ExtractionResult:
        """
        Extract single zip archive.

        Args:
            archive_path: Path to zip archive

        Returns:
            ExtractionResult with statistics and errors
        """
        result = ExtractionResult(archive_path=archive_path, success=True)
        result.size_compressed = archive_path.stat().st_size

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                # Calculate total uncompressed size
                total_size = sum(info.file_size for info in zf.infolist())
                result.size_uncompressed = total_size

                # Check disk space
                has_space, available = check_disk_space(self.output_dir, total_size, self.safety_margin)
                if not has_space:
                    error_msg = _(
                        "Insufficient disk space: need {need} MB, available {avail} MB"
                    ).format(
                        need=round((total_size + self.safety_margin) / 1024 / 1024, 2),
                        avail=round(available / 1024 / 1024, 2),
                    )
                    logger.error(error_msg)
                    result.success = False
                    result.errors.append(error_msg)
                    return result

                # Extract each file
                for info in zf.infolist():
                    if info.is_dir():
                        continue

                    try:
                        self._extract_file(zf, info, result)
                    except Exception as e:
                        error_msg = _("Error extracting {file}: {error}").format(
                            file=info.filename, error=str(e)
                        )
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        result.success = False

        except zipfile.BadZipFile as e:
            error_msg = _("Corrupted archive: {error}").format(error=str(e))
            logger.error(error_msg)
            result.success = False
            result.errors.append(error_msg)
        except Exception as e:
            error_msg = _("Unexpected error: {error}").format(error=str(e))
            logger.error(error_msg)
            result.success = False
            result.errors.append(error_msg)

        return result

    def _extract_file(self, zf: zipfile.ZipFile, info: zipfile.ZipInfo, result: ExtractionResult) -> None:
        """
        Extract single file from archive.

        Args:
            zf: Open ZipFile object
            info: ZipInfo for file to extract
            result: ExtractionResult to update
        """
        # Try to decode filename
        try:
            # ZipFile already decodes filename, but might be wrong
            filename = info.filename
            # Try to fix common encoding issues
            filename = fix_zip_filename(filename)
        except Exception:
            # Fallback to raw bytes
            raw_name = info.filename.encode("cp437")
            filename, encoding = decode_filename(raw_name)
            if encoding:
                logger.debug(f"Decoded filename using {encoding}: {filename}")

        # Security check: prevent path traversal
        target_path = self.output_dir / filename
        if not is_safe_path(self.output_dir, target_path):
            error_msg = _("Unsafe path detected: {path}").format(path=filename)
            logger.warning(error_msg)
            result.errors.append(error_msg)
            return

        # Create parent directory
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract to temporary location first
        temp_path = target_path.parent / f".tmp_{target_path.name}"

        try:
            # Extract file
            with zf.open(info) as source, open(temp_path, "wb") as target:
                target.write(source.read())

            # Check for collision
            is_collision, files_identical = self.collision_tracker.check_collision(filename, temp_path)

            if is_collision:
                if files_identical:
                    # Same file, skip
                    logger.debug(f"Skipping identical file: {filename}")
                    temp_path.unlink()
                    result.files_skipped += 1
                else:
                    # Different file, rename
                    new_relative_path = generate_unique_name(self.output_dir, filename)
                    new_target_path = self.output_dir / new_relative_path
                    new_target_path.parent.mkdir(parents=True, exist_ok=True)

                    temp_path.rename(new_target_path)
                    self.collision_tracker.register_file(str(new_relative_path), new_target_path)

                    result.files_renamed += 1
                    result.collisions.append((filename, str(new_relative_path)))

                    logger.warning(
                        _("Collision detected: {old} -> {new}").format(
                            old=filename, new=str(new_relative_path)
                        )
                    )
            else:
                # New file, move to final location
                temp_path.rename(target_path)
                result.files_extracted += 1

        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise
