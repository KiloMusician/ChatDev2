"""Legacy redirect for ChatDev testing chamber.

Canonical implementation:
    src/orchestration/chatdev_testing_chamber.py

This shim keeps older imports working while consolidating behavior in the
orchestration module.
"""

from src.orchestration.chatdev_testing_chamber import ChatDevTestingChamber
from src.orchestration.chatdev_testing_chamber import \
    main as chatdev_testing_main

__all__ = ["ChatDevTestingChamber", "chatdev_testing_main"]


def main() -> None:
    """Entry point wrapper for legacy CLI usage."""
    chatdev_testing_main()


if __name__ == "__main__":
    main()
