"""Encoding detection and handling for zip archive filenames."""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Encodings to try, in order of preference
ENCODINGS = ["utf-8", "cp866", "cp1251", "latin1"]


def decode_filename(raw_bytes: bytes, tried_encodings: list[str] | None = None) -> Tuple[str, str | None]:
    """
    Try to decode filename from bytes using various encodings.

    Args:
        raw_bytes: Raw bytes of filename
        tried_encodings: List of encodings to try (None for defaults)

    Returns:
        Tuple of (decoded_name, encoding_used or None if failed)
    """
    if tried_encodings is None:
        tried_encodings = ENCODINGS

    for encoding in tried_encodings:
        try:
            decoded = raw_bytes.decode(encoding)
            # Check if decoded string looks reasonable
            if "\x00" not in decoded and decoded.isprintable() or any(ord(c) > 127 for c in decoded):
                logger.debug(f"Successfully decoded filename using {encoding}")
                return decoded, encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    # Fallback: create safe filename from bytes
    logger.warning(f"Could not decode filename, using fallback: {raw_bytes[:50]}")
    safe_name = "unknown_" + raw_bytes.hex()[:32]
    return safe_name, None


def fix_zip_filename(filename: str) -> str:
    """
    Fix potentially incorrectly decoded zip filename.

    Some zip utilities encode filenames incorrectly. Try to detect and fix.

    Args:
        filename: Filename to check and fix

    Returns:
        Fixed filename
    """
    # Try to detect mojibake (incorrectly decoded UTF-8 as CP1252/Latin1)
    try:
        # If string was incorrectly decoded from UTF-8 to Latin1,
        # encode back to Latin1 and decode as UTF-8
        reencoded = filename.encode("latin1")
        fixed = reencoded.decode("utf-8")
        logger.debug(f"Fixed mojibake: {filename} -> {fixed}")
        return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    return filename
