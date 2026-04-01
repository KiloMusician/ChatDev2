"""Legacy redirect for doctrine checker.

Canonical implementation:
    src/doctrine/doctrine_checker.py
"""

import logging
from pathlib import Path

from src.doctrine.doctrine_checker import (ComplianceReport, DoctrineChecker,
                                           DoctrineViolation)

logger = logging.getLogger(__name__)

__all__ = ["ComplianceReport", "DoctrineChecker", "DoctrineViolation"]


def main() -> None:
    """Entry point wrapper for legacy CLI usage."""
    checker = DoctrineChecker(Path.cwd())
    report = checker.check_compliance()
    logger.info(report.to_markdown())


if __name__ == "__main__":
    main()
