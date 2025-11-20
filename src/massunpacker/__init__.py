"""Mass unpack utility for extracting multiple zip archives."""

from .collision import CollisionMethod, CollisionTracker
from .extractor import Extractor, ExtractionResult

__version__ = "0.1.0"
__all__ = ["CollisionMethod", "CollisionTracker", "Extractor", "ExtractionResult"]
