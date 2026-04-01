# ΞNuSyQ Duplicate & Naming Consolidation System
from .detector import DuplicateDetector
from .planner import ConsolidationPlanner
from .main import main

__version__ = "1.0.0"
__all__ = ["DuplicateDetector", "ConsolidationPlanner", "main"]