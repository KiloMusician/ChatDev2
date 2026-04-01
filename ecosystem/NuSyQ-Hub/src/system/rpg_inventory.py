"""KILO-FOOLISH RPG Inventory System.

Real-time system state tracking and management.
"""

import asyncio
import json
import logging
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import psutil

try:
    from src.utils import config_helper
except ImportError:
    config_helper = None


class ComponentStatus(Enum):
    """Component status levels."""

    OFFLINE = "offline"
    STARTING = "starting"
    ONLINE = "online"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class SkillLevel(Enum):
    """System skill levels."""

    NOVICE = 1
    APPRENTICE = 2
    JOURNEYMAN = 3
    EXPERT = 4
    MASTER = 5
    GRANDMASTER = 6


@dataclass
class SystemComponent:
    """Individual system component tracking."""

    name: str
    status: ComponentStatus = ComponentStatus.OFFLINE
    version: str = "unknown"
    last_check: datetime = field(default_factory=datetime.now)
    health_score: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    uptime: float = 0.0
    auto_heal: bool = True


@dataclass
class SystemSkill:
    """System capability/skill tracking."""

    name: str
    level: SkillLevel = SkillLevel.NOVICE
    experience: int = 0
    max_experience: int = 100
    proficiency: float = 0.0
    last_used: datetime | None = None
    usage_count: int = 0
    success_rate: float = 0.0


@dataclass
class ResourceMetrics:
    """System resource tracking."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_usage: float = 0.0
    network_io: dict[str, int] = field(default_factory=dict)
    process_count: int = 0
    temperature: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SystemQuest:
    """Active system tasks/objectives."""

    id: str
    title: str
    description: str
    priority: int = 1  # 1-5
    progress: float = 0.0
    dependencies: list[str] = field(default_factory=list)
    rewards: list[str] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    deadline: datetime | None = None
    auto_complete: bool = False


class RPGInventorySystem:
    """Main RPG Inventory system for tracking KILO-FOOLISH state."""

    def __init__(self, update_interval: int = 5) -> None:
        """Initialize RPGInventorySystem with update_interval."""
        self.update_interval = update_interval
        self.components: dict[str, SystemComponent] = {}
        self.skills: dict[str, SystemSkill] = {}
        self.quests: dict[str, SystemQuest] = {}
        self.resources: ResourceMetrics = ResourceMetrics()
        self.system_stats = {
            "total_uptime": 0.0,
            "total_operations": 0,
            "success_rate": 0.0,
            "error_count": 0,
            "last_backup": None,
            "system_level": 1,
            "experience_points": 0,
        }

        self._running = False
        self._update_thread = None
        self._callbacks: list[Callable] = []
        self._data_file = Path("data/rpg_inventory.json")

        # Initialize core components
        self._initialize_components()
        self._initialize_skills()
        self._load_state()

    def _initialize_components(self) -> None:
        """Initialize system components."""
        core_components = {
            "python": SystemComponent(
                name="Python Environment",
                dependencies=[],
                capabilities=["code_execution", "package_management"],
                auto_heal=True,
            ),
            "pip": SystemComponent(
                name="Pip Package Manager",
                dependencies=["python"],
                capabilities=["package_install", "dependency_management"],
                auto_heal=True,
            ),
            "vscode": SystemComponent(
                name="Visual Studio Code",
                dependencies=[],
                capabilities=["code_editing", "debugging", "git_integration"],
                auto_heal=False,
            ),
            "ollama": SystemComponent(
                name="Ollama Local AI",
                dependencies=["python"],
                capabilities=["local_ai", "code_generation", "reasoning"],
                auto_heal=True,
            ),
            "openai": SystemComponent(
                name="OpenAI Integration",
                dependencies=["python"],
                capabilities=["cloud_ai", "advanced_reasoning", "large_context"],
                auto_heal=True,
            ),
            "git": SystemComponent(
                name="Git Version Control",
                dependencies=[],
                capabilities=["version_control", "collaboration", "backup"],
                auto_heal=False,
            ),
            "diagnostics": SystemComponent(
                name="Error Detection System",
                dependencies=["python"],
                capabilities=["error_detection", "auto_healing", "monitoring"],
                auto_heal=True,
            ),
            "coordinator": SystemComponent(
                name="AI Coordination Layer",
                dependencies=["python", "ollama", "openai"],
                capabilities=["ai_routing", "load_balancing", "fallback_handling"],
                auto_heal=True,
            ),
            "secrets": SystemComponent(
                name="Secrets Management",
                dependencies=["python"],
                capabilities=[
                    "api_key_management",
                    "secure_storage",
                    "environment_config",
                ],
                auto_heal=False,
            ),
        }

        self.components.update(core_components)

    def _initialize_skills(self) -> None:
        """Initialize system skills."""
        core_skills = {
            "code_generation": SystemSkill(
                name="Code Generation",
                max_experience=1000,
            ),
            "error_handling": SystemSkill(
                name="Error Handling & Recovery",
                max_experience=500,
            ),
            "ai_coordination": SystemSkill(
                name="AI System Coordination",
                max_experience=750,
            ),
            "performance_optimization": SystemSkill(
                name="Performance Optimization",
                max_experience=800,
            ),
            "security_management": SystemSkill(
                name="Security & Secrets Management",
                max_experience=600,
            ),
            "dependency_management": SystemSkill(
                name="Dependency & Package Management",
                max_experience=400,
            ),
            "monitoring": SystemSkill(
                name="System Monitoring & Diagnostics",
                max_experience=300,
            ),
            "automation": SystemSkill(
                name="Process Automation",
                max_experience=900,
            ),
        }

        self.skills.update(core_skills)

    async def start_monitoring(self) -> None:
        """Start real-time monitoring."""
        if self._running:
            return

        self._running = True
        logging.info("🎮 RPG Inventory system starting...")

        # Start background update thread
        self._update_thread = threading.Thread(target=self._background_update_loop, daemon=True)
        self._update_thread.start()

        # Perform initial system scan
        await self.full_system_scan()

        logging.info("✅ RPG Inventory system online!")

    def stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=5)
        self._save_state()
        logging.info("🛑 RPG Inventory system stopped")

    def _background_update_loop(self) -> None:
        """Background thread for continuous updates."""
        while self._running:
            try:
                # Check if event loop is running (avoid Thread-8 error)
                try:
                    asyncio.get_running_loop()
                    # If we have a loop, schedule the coroutine
                    _t = asyncio.create_task(self._update_system_state())
                    _t.add_done_callback(lambda t: None)  # keep ref; suppress dangling-task warning
                except RuntimeError:
                    # No running loop, use asyncio.run (safe in thread)
                    asyncio.run(self._update_system_state())
                time.sleep(self.update_interval)
            except Exception as e:
                logging.exception(f"RPG Inventory update error: {e}")
                time.sleep(self.update_interval)

    async def _update_system_state(self) -> None:
        """Update system state."""
        # Update resource metrics
        self._update_resource_metrics()

        # Update component health
        for component_name in self.components:
            await self._check_component_health(component_name)

        # Update skills based on usage
        self._update_skill_proficiency()

        # Check quest progress
        self._update_quest_progress()

        # Trigger callbacks
        for callback in self._callbacks:
            try:
                callback(self.get_system_snapshot())
            except Exception as e:
                logging.exception(f"Callback error: {e}")

    def _update_resource_metrics(self) -> None:
        """Update system resource metrics."""
        try:
            self.resources = ResourceMetrics(
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage=psutil.disk_usage(".").percent,
                network_io=dict(psutil.net_io_counters()._asdict()),
                process_count=len(psutil.pids()),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logging.exception(f"Resource metrics update failed: {e}")

    def update_resource_metrics(self) -> None:
        """Public wrapper to update system resource metrics.

        Exposes a safe, public method for external callers to refresh
        resource metrics without relying on the protected implementation.
        """
        self._update_resource_metrics()

    async def _check_component_health(self, component_name: str) -> None:
        """Check individual component health."""
        component = self.components.get(component_name)
        if not component:
            return

        try:
            health_score = 0.0
            status = ComponentStatus.OFFLINE
            errors: list[Any] = []
            if component_name == "python":
                result = subprocess.run(
                    ["python", "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    status = ComponentStatus.ONLINE
                    health_score = 100.0
                    component.version = result.stdout.strip()
                else:
                    errors.append("Python not accessible")

            elif component_name == "pip":
                result = subprocess.run(
                    ["pip", "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    status = ComponentStatus.ONLINE
                    health_score = 100.0
                    component.version = result.stdout.split()[1]
                else:
                    errors.append("Pip not accessible")

            elif component_name == "vscode":
                result = subprocess.run(
                    ["code", "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    status = ComponentStatus.ONLINE
                    health_score = 100.0
                    component.version = result.stdout.split("\n")[0]
                else:
                    status = ComponentStatus.WARNING
                    health_score = 50.0
                    errors.append("VS Code not in PATH")

            elif component_name == "ollama":
                try:
                    import requests

                    try:
                        from src.config.service_config import ServiceConfig

                        ollama_url = ServiceConfig.get_ollama_url()
                    except ImportError:
                        if config_helper:
                            ollama_url = config_helper.get_ollama_host()
                        else:
                            import os
                            from urllib.parse import urlparse

                            base = os.environ.get("OLLAMA_BASE_URL") or os.environ.get(
                                "OLLAMA_HOST", "http://127.0.0.1"
                            )
                            port = os.environ.get("OLLAMA_PORT", "11435")
                            parsed = urlparse(base if "://" in base else f"http://{base}")
                            netloc = (
                                f"{parsed.hostname}:{parsed.port}"
                                if parsed.port
                                else f"{parsed.hostname}:{port}"
                            )
                            ollama_url = f"{parsed.scheme}://{netloc}"

                    # Local-only Ollama status probe; HTTP is expected on loopback. # nosemgrep
                    response = requests.get(f"{ollama_url}/api/tags", timeout=3)  # nosemgrep
                    if response.status_code == 200:
                        status = ComponentStatus.ONLINE
                        health_score = 100.0
                        models = response.json().get("models", [])
                        component.metrics["available_models"] = len(models)
                    else:
                        status = ComponentStatus.WARNING
                        health_score = 30.0
                        errors.append("Ollama service not responding")
                except (OSError, ConnectionError, TimeoutError):
                    status = ComponentStatus.OFFLINE
                    errors.append("Ollama not accessible")

            elif component_name == "git":
                result = subprocess.run(
                    ["git", "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    status = ComponentStatus.ONLINE
                    health_score = 100.0
                    component.version = result.stdout.strip().split()[-1]
                else:
                    errors.append("Git not accessible")

            # Update component
            component.status = status
            component.health_score = health_score
            component.last_check = datetime.now()
            component.errors = errors

            # Auto-heal if enabled and component is down
            if component.auto_heal and status in [
                ComponentStatus.OFFLINE,
                ComponentStatus.ERROR,
            ]:
                await self._attempt_auto_heal(component_name)

        except Exception as e:
            component.status = ComponentStatus.ERROR
            component.errors = [str(e)]
            logging.exception(f"Health check failed for {component_name}: {e}")

    async def _attempt_auto_heal(self, component_name: str) -> None:
        """Attempt to auto-heal a component."""
        self.components[component_name]

        logging.info(f"🔧 Attempting auto-heal for {component_name}")

        # Component-specific healing strategies
        heal_strategies = {
            "pip": ["python", "-m", "ensurepip", "--upgrade"],
            "ollama": ["ollama", "serve"],  # Start Ollama service
        }

        if component_name in heal_strategies:
            try:
                subprocess.run(
                    heal_strategies[component_name],
                    check=False,
                    timeout=30,
                    capture_output=True,
                )
                logging.info(f"✅ Auto-heal attempted for {component_name}")
                self._gain_experience("error_handling", 10)
            except Exception as e:
                logging.exception(f"❌ Auto-heal failed for {component_name}: {e}")

    def _update_skill_proficiency(self) -> None:
        """Update skill proficiency based on usage."""
        for skill in self.skills.values():
            if skill.usage_count > 0:
                # Calculate proficiency based on experience and success rate
                level_progress = skill.experience / skill.max_experience
                skill.proficiency = min(100.0, level_progress * 100 * skill.success_rate)

                # Level up if enough experience
                if skill.experience >= skill.max_experience and skill.level.value < 6:
                    skill.level = SkillLevel(skill.level.value + 1)
                    skill.max_experience = int(skill.max_experience * 1.5)
                    self._gain_experience("automation", 20)  # Bonus for system growth
                    logging.info(f"🎉 Skill level up: {skill.name} -> {skill.level.name}")

    def _update_quest_progress(self) -> None:
        """Update quest progress."""
        for quest in self.quests.values():
            if quest.auto_complete:
                # Auto-update progress based on system state
                if quest.id == "setup_completion":
                    online_components = sum(
                        1 for c in self.components.values() if c.status == ComponentStatus.ONLINE
                    )
                    quest.progress = (online_components / len(self.components)) * 100

                elif quest.id == "ai_integration":
                    ai_components = ["ollama", "openai", "coordinator"]
                    online_ai = sum(
                        1
                        for name in ai_components
                        if self.components[name].status == ComponentStatus.ONLINE
                    )
                    quest.progress = (online_ai / len(ai_components)) * 100

    def _gain_experience(self, skill_name: str, points: int) -> None:
        """Gain experience in a skill."""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.experience += points
            skill.usage_count += 1
            skill.last_used = datetime.now()
            self.system_stats["experience_points"] += points

    def add_quest(self, quest: SystemQuest) -> None:
        """Add a new quest."""
        self.quests[quest.id] = quest
        logging.info(f"📋 New quest added: {quest.title}")

    def complete_quest(self, quest_id: str) -> None:
        """Complete a quest."""
        if quest_id in self.quests:
            quest = self.quests[quest_id]
            quest.progress = 100.0

            # Award rewards
            for reward in quest.rewards:
                if reward.startswith("experience:"):
                    skill, points = reward.split(":")[1:3]
                    self._gain_experience(skill, int(points))

            logging.info(f"✅ Quest completed: {quest.title}")
            del self.quests[quest_id]

    def add_callback(self, callback: Callable) -> None:
        """Add callback for state changes."""
        self._callbacks.append(callback)

    def get_system_snapshot(self) -> dict[str, Any]:
        """Get complete system snapshot."""
        return {
            "timestamp": datetime.now().isoformat(),
            "components": {name: asdict(comp) for name, comp in self.components.items()},
            "skills": {name: asdict(skill) for name, skill in self.skills.items()},
            "quests": {quest_id: asdict(quest) for quest_id, quest in self.quests.items()},
            "resources": asdict(self.resources),
            "system_stats": self.system_stats,
            "overall_health": self._calculate_overall_health(),
        }

    def _calculate_overall_health(self) -> float:
        """Calculate overall system health score."""
        if not self.components:
            return 0.0

        total_health = sum(comp.health_score for comp in self.components.values())
        return total_health / len(self.components)

    async def full_system_scan(self) -> None:
        """Perform comprehensive system scan."""
        logging.info("🔍 Performing full system scan...")

        # Check all components
        for component_name in self.components:
            await self._check_component_health(component_name)

        # Initialize default quests
        default_quests = [
            SystemQuest(
                id="setup_completion",
                title="Complete System Setup",
                description="Get all core components online",
                priority=5,
                auto_complete=True,
                rewards=["experience:automation:50"],
            ),
            SystemQuest(
                id="ai_integration",
                title="AI Integration Complete",
                description="Get all AI components working together",
                priority=4,
                auto_complete=True,
                rewards=["experience:ai_coordination:75"],
            ),
        ]

        for quest in default_quests:
            if quest.id not in self.quests:
                self.add_quest(quest)

        self._gain_experience("monitoring", 25)
        logging.info("✅ Full system scan completed")

    def _save_state(self) -> None:
        """Save current state to file."""
        try:
            self._data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._data_file, "w") as f:
                json.dump(self.get_system_snapshot(), f, indent=2, default=str)
        except Exception as e:
            logging.exception(f"Failed to save RPG Inventory state: {e}")

    def _load_state(self) -> None:
        """Load state from file."""
        try:
            if self._data_file.exists():
                with open(self._data_file) as f:
                    data = json.load(f)

                # Restore system stats
                if "system_stats" in data:
                    self.system_stats.update(data["system_stats"])

                logging.info("📦 RPG Inventory state loaded")
        except Exception as e:
            logging.exception(f"Failed to load RPG Inventory state: {e}")


# Global instance
_rpg_inventory = None


def get_rpg_inventory() -> RPGInventorySystem:
    """Get or create global RPG inventory instance."""
    global _rpg_inventory
    if _rpg_inventory is None:
        _rpg_inventory = RPGInventorySystem()
    return _rpg_inventory


# Convenience functions
async def start_rpg_monitoring() -> None:
    """Start RPG monitoring system."""
    inventory = get_rpg_inventory()
    await inventory.start_monitoring()


def get_system_status() -> dict[str, Any]:
    """Get current system status."""
    inventory = get_rpg_inventory()
    return inventory.get_system_snapshot()


def gain_experience(skill: str, points: int) -> None:
    """Gain experience in a skill."""
    inventory = get_rpg_inventory()
    inventory._gain_experience(skill, points)


def award_xp(
    skill: str,
    points: int,
    *,
    award_game_fn: Callable[..., Any] | None = None,
    achievement: str | None = None,
    feature: str | None = None,
) -> dict[str, Any]:
    """Unified XP award flow across RPG inventory and optional game awards."""
    if points <= 0:
        return {"success": False, "error": "XP points must be positive"}

    inventory = get_rpg_inventory()
    if skill not in inventory.skills:
        return {
            "success": False,
            "error": f"Unknown skill '{skill}'. Valid skills: {sorted(inventory.skills.keys())}",
        }

    inventory._gain_experience(skill, points)
    new_skill = inventory.skills[skill]
    rpg_result = {
        "skill": skill,
        "points_awarded": points,
        "new_experience": new_skill.experience,
        "level": new_skill.level.name if hasattr(new_skill.level, "name") else str(new_skill.level),
        "proficiency": new_skill.proficiency,
    }

    award_summary = None
    if award_game_fn is not None:
        award_summary = award_game_fn(
            xp=points,
            achievement=achievement,
            feature=feature,
        )

    return {"success": True, "rpg": rpg_result, "game_award": award_summary}


if __name__ == "__main__":
    # Test the RPG inventory system
    async def test_inventory() -> None:
        inventory = RPGInventorySystem()
        await inventory.start_monitoring()

        # Wait a bit for initial scan
        await asyncio.sleep(10)

        # Display status
        snapshot = inventory.get_system_snapshot()

        for comp in snapshot["components"].values():
            "✅" if comp["status"] == "online" else "❌"

        for skill in snapshot["skills"].values():
            skill["level"]
            skill["proficiency"]

        inventory.stop_monitoring()

    asyncio.run(test_inventory())
