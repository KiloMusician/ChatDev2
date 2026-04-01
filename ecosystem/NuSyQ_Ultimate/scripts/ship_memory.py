#!/usr/bin/env python3
"""
🚢 SHIP MEMORY - Persistent Learning System
==========================================
Inspired by Culture Mind Ships that remember everything.
Tracks agent performance, session history, and learnings.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class AgentPerformance:
    """Track agent performance metrics"""

    agent_name: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_duration: float = 0.0
    success_rate: float = 0.0
    specializations: List[str] = field(default_factory=list)


class ShipMemory:
    """Persistent memory for autonomous systems"""

    def __init__(self, memory_file: Path):
        self.memory_file = memory_file
        self.memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        if self.memory_file.exists():
            with open(self.memory_file, encoding="utf-8") as f:
                return json.load(f)
        return {
            "created_at": datetime.now().isoformat(),
            "sessions": [],
            "agent_performance": {},
            "learnings": [],
            "consciousness_history": [],
        }

    def save(self):
        """Persist memory to disk"""
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, default=str)

    def record_session(self, session_data: Dict):
        """Record a session"""
        self.memory["sessions"].append(session_data)
        self.save()

    def record_consciousness(self, level: float):
        """Track consciousness growth"""
        self.memory["consciousness_history"].append(
            {"timestamp": datetime.now().isoformat(), "level": level}
        )
        self.save()

    def record_learning(self, lesson: str):
        """Record a learning"""
        self.memory["learnings"].append(
            {"timestamp": datetime.now().isoformat(), "lesson": lesson}
        )
        self.save()


if __name__ == "__main__":
    memory_file = Path(__file__).parent.parent / "State" / "ship_memory.json"
    ship = ShipMemory(memory_file)
    print(f"Ship Memory: {len(ship.memory['sessions'])} sessions recorded")
    print(
        f"Consciousness History: {len(ship.memory['consciousness_history'])} snapshots"
    )
