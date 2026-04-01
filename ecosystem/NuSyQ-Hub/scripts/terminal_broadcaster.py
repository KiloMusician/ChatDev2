#!/usr/bin/env python3
"""Terminal Broadcaster - Send real-time updates to all terminals

Monitors system activity and broadcasts updates to appropriate terminals.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.terminal_output import to_main, to_metrics, to_tasks, to_zeta


class TerminalBroadcaster:
    """Broadcasts system events to appropriate terminals."""

    def __init__(self, root: Path):
        self.root = root
        self.service_state_file = root / "state" / "services" / "services.json"
        self.last_broadcast = {}

    def broadcast_startup(self) -> None:
        """Broadcast system startup message."""
        to_zeta("🚀 NuSyQ-Hub services starting...")
        to_main("System initialization complete")

    def broadcast_service_status(self) -> None:
        """Broadcast service status to terminals."""
        if not self.service_state_file.exists():
            return

        try:
            state = json.loads(self.service_state_file.read_text())
            services = state.get("services", {})

            active_count = sum(1 for s in services.values() if s.get("status") == "running")
            message = f"📊 Services: {active_count}/{len(services)} running"

            # Only broadcast if changed
            if self.last_broadcast.get("services") != message:
                to_metrics(message)
                self.last_broadcast["services"] = message

        except Exception:
            pass  # Silent fail

    def broadcast_quest_updates(self) -> None:
        """Broadcast quest status updates."""
        quest_file = self.root / "data" / "ecosystem" / "quest_assignments.json"
        if not quest_file.exists():
            return

        try:
            with open(quest_file) as f:
                quests = json.load(f)
                total = len(quests.get("assignments", {}))
                message = f"📋 Active quests: {total}"

                if self.last_broadcast.get("quests") != message:
                    to_tasks(message)
                    self.last_broadcast["quests"] = message

        except Exception:
            pass

    def run_forever(self, interval: int = 30) -> None:
        """Run broadcaster loop."""
        print("=" * 70)
        print("📡 TERMINAL BROADCASTER ACTIVE")
        print("=" * 70)
        print(f"\nBroadcast interval: {interval}s")
        print("Press Ctrl+C to stop\n")

        self.broadcast_startup()

        try:
            while True:
                self.broadcast_service_status()
                self.broadcast_quest_updates()
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✅ Broadcaster stopped")


def main():
    """Main entry point."""
    broadcaster = TerminalBroadcaster(ROOT)
    broadcaster.run_forever(interval=60)


if __name__ == "__main__":
    main()
