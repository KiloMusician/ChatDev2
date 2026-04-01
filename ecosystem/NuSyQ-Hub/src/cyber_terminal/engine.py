"""CyberTerminal game loop and virtual filesystem."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Node:
    name: str
    is_dir: bool = True
    content: str | None = None
    children: dict[str, Node] = field(default_factory=dict)

    def add(self, child: Node) -> None:
        self.children[child.name] = child

    def get(self, name: str) -> Node | None:
        return self.children.get(name)

    def list_names(self) -> list[str]:
        return sorted(self.children.keys())


def build_world() -> Node:
    root = Node("/")
    home = Node("home")
    runner = Node("netrunner")
    tutorial = Node("tutorial")
    logs = Node("logs")

    intro_txt = Node(
        "intro.txt",
        is_dir=False,
        content=(
            "Welcome to CyberTerminal.\n"
            "Learn to navigate, probe, and defend advanced systems.\n"
            "Try commands: ls, cd tutorial, cat readme.txt, tasks, hack\n"
        ),
    )
    tutorial_readme = Node(
        "readme.txt",
        is_dir=False,
        content=(
            "Tutorial Steps:\n"
            "1. pwd - locate yourself\n"
            "2. ls - survey the directory\n"
            "3. cd ops - move into operations\n"
            "4. cat mission.txt - read mission brief\n"
        ),
    )
    ops = Node("ops")
    mission = Node(
        "mission.txt",
        is_dir=False,
        content=(
            "Your target is a simulated relay.\n"
            "Use scan, connect relay, and download logs.\n"
            "Remember: elegance > brute force.\n"
        ),
    )
    ops.add(mission)
    tutorial.add(tutorial_readme)
    tutorial.add(ops)

    logs.add(
        Node(
            "relay.log",
            is_dir=False,
            content="[0042] relay ping sweep detected anomalies...\n",
        )
    )

    runner.add(intro_txt)
    runner.add(tutorial)
    runner.add(logs)
    home.add(runner)
    root.add(home)
    return root


class CyberTerminal:
    """Simple cyberpunk terminal learning simulator."""

    PROMPT = "cyber@hub"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    def __init__(
        self,
        world: Node | None = None,
        state_path: Path | None = None,
        enable_colors: bool = True,
    ) -> None:
        """Initialize CyberTerminal with world, state_path, enable_colors."""
        self.root = world or build_world()
        self.cwd: list[str] = ["/", "home", "netrunner"]
        self.tasks = [
            ("Run pwd", False, "pwd"),
            ("List directory", False, "ls"),
            ("Read intro", False, "cat intro.txt"),
            ("Enter tutorial", False, "cd tutorial"),
            ("Read tutorial readme", False, "cat readme.txt"),
        ]
        self.missions = [
            ("Scan relay", False, "scan"),
            ("Connect relay", False, "connect relay"),
            ("Download relay logs", False, "download relay"),
        ]
        self.mission_catalog = self._load_mission_catalog()
        self.active_mission: str | None = None
        self.completed_missions: set[str] = set()
        self._recent_commands: list[str] = []
        self.score = 0
        self.state_path = state_path or Path.home() / ".cyberterminal" / "state.json"
        self.enable_colors = enable_colors
        self._load_state()

    # ---------- filesystem helpers ----------
    def _resolve(self, path: str) -> Node | None:
        parts = self._normalize(path)
        node = self.root
        for part in parts[1:]:
            node = node.get(part)
            if node is None or (not node.is_dir and part != parts[-1]):
                return None
        return node

    def _normalize(self, path: str) -> list[str]:
        if path.startswith("/"):
            parts = [p for p in path.split("/") if p]
            return ["/", *parts]
        parts = self.cwd.copy()
        for token in path.split("/"):
            if token in ("", "."):
                continue
            if token == "..":
                if len(parts) > 1:
                    parts.pop()
            else:
                parts.append(token)
        return parts

    def _pwd_str(self) -> str:
        return "/" if self.cwd == ["/"] else "/".join(self.cwd).replace("//", "/")

    # ---------- commands ----------
    def cmd_pwd(self) -> str:
        self._complete("pwd")
        return self._pwd_str()

    def cmd_ls(self) -> str:
        node = self._resolve(self._pwd_str())
        if not node:
            return "Path not found."
        self._complete("ls")
        return "  ".join(node.list_names())

    def cmd_cd(self, path: str) -> str:
        target = self._resolve(path)
        if not target or not target.is_dir:
            return f"cd: no such directory: {path}"
        self.cwd = self._normalize(path)
        self._complete("cd tutorial" if "tutorial" in path else None)
        return f"Moved to {self._pwd_str()}"

    def cmd_cat(self, path: str) -> str:
        target = self._resolve(path)
        if not target or target.is_dir:
            return f"cat: no such file: {path}"
        self._complete(f"cat {target.name}")
        return target.content or ""

    def cmd_tasks(self) -> str:
        lines = []
        for name, done, _cmd in self.tasks:
            status = "✔" if done else "…"
            lines.append(f"[{status}] {name}")
        for name, done, _cmd in self.missions:
            status = "✔" if done else "…"
            lines.append(f"[{status}] {name}")
        lines.append(f"Score: {self.score}")
        if self.active_mission:
            lines.append(f"Active mission: {self.active_mission}")
        if self.completed_missions:
            lines.append(f"Completed missions: {', '.join(sorted(self.completed_missions))}")
        return "\n".join(lines)

    def cmd_hack(self) -> str:
        self._complete("hack")
        return (
            "Spinning up neuro-link...\n"
            "Chromatic datastream floods the HUD.\n"
            "Hint: explore /home/netrunner/tutorial for ops brief."
        )

    def cmd_scan(self) -> str:
        self._complete("scan")
        return "[SCAN] Relay signature found.\nOpen port 2210 (simulated). Next: connect relay"

    def cmd_connect(self, target: str) -> str:
        if target != "relay":
            return f"connect: unknown target '{target}'"
        if not self._is_done("scan"):
            return "connect: relay requires prior scan."
        self._complete("connect relay")
        return "Connected to relay. Download logs to proceed."

    def cmd_download(self, target: str) -> str:
        if target != "relay":
            return f"download: unknown target '{target}'"
        if not self._is_done("connect relay"):
            return "download: connect to relay first."
        self._complete("download relay")
        return "Logs downloaded: stored in /home/netrunner/logs/relay.log"

    def cmd_missions(self) -> str:
        if not self.mission_catalog:
            return "No missions loaded."
        lines = []
        for mission in self.mission_catalog:
            if mission["id"] in self.completed_missions:
                tag = "✔"
            elif mission["id"] == self.active_mission:
                tag = "*"
            else:
                tag = " "
            lines.append(f"[{tag}] {mission['id']}: {mission['title']} — {mission['goal']}")
        return "\n".join(lines)

    def cmd_mission_detail(self, mission_id: str) -> str:
        mission = next((m for m in self.mission_catalog if m["id"] == mission_id), None)
        if not mission:
            return f"mission: unknown id '{mission_id}'"
        self.active_mission = mission_id
        prompt = mission.get("prompt")
        reward = mission.get("score_bonus", 20)
        grade = mission.get("grade", "PASS")
        parts = [
            f"Mission {mission['id']}: {mission['title']}",
            f"Goal: {mission['goal']}",
            f"Required: {', '.join(mission.get('required_commands', []))}",
            f"Success: {mission['success_criteria']}",
            f"Flavor: {mission['flavor']}",
        ]
        if prompt:
            parts.append(f"Prompt: {prompt}")
        parts.append(f"Reward: +{reward} score | Grade: {grade}")
        self._save_state()
        return "\n".join(parts)

    # ---------- game loop ----------
    def execute(self, line: str) -> str:
        line = line.strip()
        if not line:
            return ""
        parts = line.split()
        cmd, args = parts[0], parts[1:]
        if cmd == "pwd":
            return self.cmd_pwd()
        if cmd == "ls":
            return self.cmd_ls()
        if cmd == "cd":
            return self.cmd_cd(args[0] if args else "/")
        if cmd == "cat":
            return self.cmd_cat(args[0] if args else "")
        if cmd == "tasks":
            return self.cmd_tasks()
        if cmd == "hack":
            return self.cmd_hack()
        if cmd == "scan":
            return self.cmd_scan()
        if cmd == "connect":
            return self.cmd_connect(args[0] if args else "")
        if cmd == "download":
            return self.cmd_download(args[0] if args else "")
        if cmd == "missions":
            return self.cmd_missions()
        if cmd == "mission":
            return self.cmd_mission_detail(args[0] if args else "")
        if cmd in ("quit", "exit"):
            return "exit"
        return f"Unknown command: {cmd}"

    def prompt(self) -> str:
        prefix = f"{self.PROMPT}:{self._pwd_str()}$ "
        if not self.enable_colors:
            return prefix
        return f"{self.CYAN}{prefix}{self.RESET}"

    def _complete(self, match: str | None) -> None:
        if not match:
            return
        for bucket in (self.tasks, self.missions):
            for idx, (name, done, check) in enumerate(bucket):
                if done:
                    continue
                if check == match or (check.startswith("cat") and match.startswith("cat")):
                    bucket[idx] = (name, True, check)
                    self.score += 10
                    self._save_state()
                    return

    def _is_done(self, check: str) -> bool:
        for bucket in (self.tasks, self.missions):
            for _name, done, key in bucket:
                if key == check:
                    return done
        return False

    def _after_command(self, command: str) -> str | None:
        """Track recent commands and update mission completion."""
        self._recent_commands.append(command)
        if len(self._recent_commands) > 50:
            self._recent_commands.pop(0)
        return self._check_mission_completion(command)

    def _load_mission_catalog(self) -> list[dict]:
        """Load mission seeds; prefer latest ChatDev output if present."""
        # Prefer ChatDev WareHouse outputs (Windows + WSL + local fallbacks).
        warehouse_candidates = [
            Path(os.getenv("CHATDEV_WAREHOUSE", "")) if os.getenv("CHATDEV_WAREHOUSE") else None,
            Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main/WareHouse"),
            Path("/mnt/c/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main/WareHouse"),
            Path.home() / "NuSyQ" / "ChatDev" / "WareHouse",
            Path("WareHouse"),
        ]
        warehouse = next((p for p in warehouse_candidates if p and p.exists()), Path("WareHouse"))
        candidates = []
        if warehouse.exists():
            for path in warehouse.glob("**/*.json"):
                try:
                    data = json.loads(path.read_text())
                    if (
                        isinstance(data, list)
                        and all(isinstance(x, dict) for x in data)
                        and any("required_commands" in d for d in data)
                    ):
                        candidates.append((path.stat().st_mtime, path, data))
                except Exception:
                    continue
        candidates.sort(reverse=True)
        if candidates:
            _mtime, path, data = candidates[0]
            return data

        # Fallback to repo seed
        seeds_path = Path("docs/Projects/CyberTerminal_missions.json")
        if seeds_path.exists():
            try:
                data = json.loads(seeds_path.read_text())
                if isinstance(data, list):
                    return data
            except Exception:
                return []
        return []

    def _check_mission_completion(self, command: str) -> str | None:
        """Mark mission complete when required commands are executed."""
        if not self.active_mission:
            return None
        mission = next((m for m in self.mission_catalog if m["id"] == self.active_mission), None)
        if not mission:
            return None
        reqs = mission.get("required_commands", [])
        if not reqs:
            return None
        if not hasattr(self, "_req_progress"):
            self._req_progress: dict[str, set[str]] = {}
        prog = self._req_progress.setdefault(self.active_mission, set())
        prog.add(command.strip())
        if all(r in prog for r in reqs):
            self.completed_missions.add(self.active_mission)
            bonus = mission.get("score_bonus", 20)
            grade = mission.get("grade", "PASS")
            self.score += int(bonus)
            completed_id = self.active_mission
            self.active_mission = None
            self._save_state()
            return f"🏁 Mission {completed_id} completed! {grade} +{bonus} score."
        return None

    # ---------- persistence ----------
    def _load_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text())
            task_flags = data.get("tasks", [])
            mission_flags = data.get("missions", [])
            self.active_mission = data.get("active_mission")
            self.completed_missions = set(data.get("completed_missions", []))
            if "score" in data:
                self.score = int(data.get("score", 0))
            else:
                self.score = 10 * (
                    sum(bool(x) for x in task_flags) + sum(bool(x) for x in mission_flags)
                )
            if len(task_flags) == len(self.tasks):
                updated = []
                for (name, _d, check), done in zip(self.tasks, task_flags, strict=False):
                    updated.append((name, bool(done), check))
                self.tasks = updated
            if len(mission_flags) == len(self.missions):
                updated = []
                for (name, _d, check), done in zip(self.missions, mission_flags, strict=False):
                    updated.append((name, bool(done), check))
                self.missions = updated
        except Exception:
            # If corrupt, reset silently
            logger.debug("Suppressed Exception", exc_info=True)

    def _save_state(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "tasks": [done for (_n, done, _c) in self.tasks],
                "missions": [done for (_n, done, _c) in self.missions],
                "score": self.score,
                "active_mission": self.active_mission,
                "completed_missions": sorted(self.completed_missions),
            }
            self.state_path.write_text(json.dumps(data, indent=2))
        except Exception:
            # non-fatal
            logger.debug("Suppressed Exception", exc_info=True)


def run_cli() -> None:
    game = CyberTerminal()
    banner = (
        f"{game.CYAN if game.enable_colors else ''}"
        "╔════════════════════════════════════╗\n"
        "║   CYBERTerminal v0.1               ║\n"
        "║   chrome dusk / neon glyphs        ║\n"
        "╚════════════════════════════════════╝\n"
        f"{game.RESET if game.enable_colors else ''}"
        "Type 'help' for quick tips, 'exit' to quit.\n"
    )
    logger.info("\n" + banner)
    while True:
        try:
            line = input(game.prompt())
        except (EOFError, KeyboardInterrupt):
            logger.info("\n👋 Link terminated.")
            break
        if line.strip() == "help":
            logger.info(
                "Commands: pwd, ls, cd <path>, cat <file>, tasks, missions, mission <id>, "
                "hack, scan, connect <target>, download <target>, exit"
            )
            continue
        out = game.execute(line)
        notice = game._after_command(line.strip())
        if out == "exit":
            logger.info("👋 See you in the datastream.")
            break
        if out:
            logger.info(out)
        if notice:
            logger.info(notice)


if __name__ == "__main__":
    run_cli()
