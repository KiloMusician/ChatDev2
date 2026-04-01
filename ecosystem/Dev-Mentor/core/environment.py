"""
core/environment.py — Meta-aware environment detector for the DevMentor ecosystem.

Philosophy: offline-first, zero AI, pure stdlib.
Detects: Docker · Replit · VS Code · WSL · Windows · macOS · Linux
Probes:  sibling repos · running services · available shells · network

Usage:
    env = get_environment()              # cached singleton
    print(env.format_report())           # human-readable
    plan = env.activation_plan()         # list of (status, msg, cmd) tuples
    env_dict = env.to_dict()             # JSON-serializable
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).parent.parent

# ─── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class RuntimeInfo:
    name: str                       # docker|replit|vscode|wsl|windows|linux|mac|codespaces
    is_container: bool = False
    is_replit: bool = False
    is_vscode: bool = False
    is_wsl: bool = False
    is_windows: bool = False
    is_codespaces: bool = False
    shell: str = "unknown"          # bash|zsh|fish|pwsh|cmd|unknown
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SiblingRepo:
    name: str
    path: Path
    exists: bool
    is_git: bool
    has_manifest: bool = False      # has agent_manifest.json or similar
    note: str = ""


@dataclass
class ServiceProbe:
    name: str
    local_port: int
    alive: bool
    tier: str = "optional"         # offline_core|ai_amplifier|optional
    start_cmd: Optional[str] = None
    note: str = ""


# ─── Main class ───────────────────────────────────────────────────────────────

class Environment:
    """
    Detects the current runtime environment and probes the ecosystem.
    All detection is deterministic and offline-capable.
    """

    PORT_MAP_PATH = ROOT / "config" / "port_map.json"

    KNOWN_SIBLINGS = {
        "NuSyQ-Hub":      "Agent manifest spine — connects all repos",
        "NuSyQ":          "Alternative NuSyQ-Hub location",
        "SimulatedVerse": "Simulation substrate / CyberTerminal game engine",
        "CyberTerminal":  "CLI terminal game (SimulatedVerse variant)",
        "Dev-Mentor":     "This repo (self-reference check)",
    }

    def __init__(self, root: Optional[Path] = None, probe_services: bool = True):
        self.root = root or ROOT
        self._probe_services = probe_services
        self.runtime: RuntimeInfo = RuntimeInfo(name="unknown")
        self.siblings: Dict[str, SiblingRepo] = {}
        self.services: List[ServiceProbe] = []
        self.port_map: Dict = {}
        self.network_ok: Optional[bool] = None
        self.detected_at: str = datetime.now(timezone.utc).isoformat()
        self._ready = False

    # ── Detection ──────────────────────────────────────────────────────────────

    def detect(self) -> "Environment":
        """Run all detection and probing. Returns self for chaining."""
        self._detect_runtime()
        self._detect_shell()
        self._detect_siblings()
        self._load_port_map()
        if self._probe_services:
            self._probe_all_services()
        self._detect_network()
        self._ready = True
        return self

    def _detect_runtime(self) -> None:
        r = RuntimeInfo(name="unknown")

        # Docker
        if Path("/.dockerenv").exists():
            r.is_container = True
            r.name = "docker"
        else:
            try:
                cg = Path("/proc/self/cgroup").read_text()
                if "docker" in cg or "containerd" in cg:
                    r.is_container = True
                    r.name = "docker"
            except (OSError, PermissionError):
                pass

        # GitHub Codespaces
        if os.getenv("CODESPACES") or os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"):
            r.is_codespaces = True
            r.name = "codespaces"
            r.details["codespaces_domain"] = os.getenv(
                "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "")

        # Replit
        repl_id = os.getenv("REPL_ID") or os.getenv("REPLIT_DB_URL") or os.getenv("REPLIT_CLUSTER")
        dev_domain = os.getenv("REPLIT_DEV_DOMAIN", "")
        if repl_id or dev_domain:
            r.is_replit = True
            r.name = "replit"
            r.details["repl_id"] = os.getenv("REPL_ID", "")
            r.details["dev_domain"] = dev_domain
            r.details["auto_sleep_min"] = os.getenv("AUTO_SLEEP_MINUTES", "")

        # VS Code (terminal inside editor)
        if os.getenv("VSCODE_PID") or os.getenv("TERM_PROGRAM") == "vscode" or os.getenv("VSCODE_IPC_HOOK_CLI"):
            r.is_vscode = True
            if r.name == "unknown":
                r.name = "vscode"

        # WSL
        try:
            proc_ver = Path("/proc/version").read_text().lower()
            if "microsoft" in proc_ver or "wsl" in proc_ver:
                r.is_wsl = True
                r.details["wsl"] = True
                if r.name == "unknown":
                    r.name = "wsl"
        except (OSError, PermissionError):
            pass

        # Windows
        if os.name == "nt" or sys.platform == "win32":
            r.is_windows = True
            if r.name == "unknown":
                r.name = "windows"

        # Fallback: OS
        if r.name == "unknown":
            plat = sys.platform
            if plat.startswith("linux"):
                r.name = "linux"
            elif plat.startswith("darwin"):
                r.name = "mac"

        r.details["python"] = sys.version.split()[0]
        r.details["platform"] = platform.platform()
        r.details["hostname"] = socket.gethostname()
        self.runtime = r

    def _detect_shell(self) -> None:
        """Detect the active shell."""
        shell_env = os.getenv("SHELL", "")
        term_prog = os.getenv("TERM_PROGRAM", "")
        if "pwsh" in shell_env or "powershell" in shell_env.lower():
            self.runtime.shell = "pwsh"
        elif "zsh" in shell_env:
            self.runtime.shell = "zsh"
        elif "fish" in shell_env:
            self.runtime.shell = "fish"
        elif "bash" in shell_env:
            self.runtime.shell = "bash"
        elif self.runtime.is_windows:
            self.runtime.shell = "cmd"
        elif term_prog == "vscode":
            self.runtime.shell = "bash"  # default in vscode terminal
        else:
            self.runtime.shell = "unknown"

    def _detect_siblings(self) -> None:
        """Locate sibling repositories in the parent directory."""
        parent = self.root.parent
        for name, note in self.KNOWN_SIBLINGS.items():
            path = parent / name
            exists = path.exists()
            is_git = (path / ".git").exists() if exists else False
            has_manifest = any([
                (path / "state" / "agent_manifest.json").exists(),
                (path / "agent_manifest.json").exists(),
            ]) if exists else False
            self.siblings[name] = SiblingRepo(
                name=name, path=path, exists=exists,
                is_git=is_git, has_manifest=has_manifest, note=note,
            )

    def _load_port_map(self) -> None:
        try:
            self.port_map = json.loads(self.PORT_MAP_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            self.port_map = {}

    def _tcp_probe(self, host: str, port: int, timeout: float = 1.0) -> bool:
        """Pure stdlib TCP connect probe."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ConnectionRefusedError, TimeoutError):
            return False

    def _probe_all_services(self) -> None:
        """Probe all declared ports from port_map.json."""
        offline_core = set(self.port_map.get("offline_core", []))
        ai_amps = set(self.port_map.get("ai_amplifiers", []))
        ports_cfg = self.port_map.get("ports", {})

        # In Docker, use container DNS names from docker_env_vars instead of localhost.
        # Build port→host map from URLs like "http://gordon:3000" → host="gordon", port=3000.
        docker_host_map: Dict[int, str] = {}
        if self.runtime.is_container:
            import re as _re
            for url in self.port_map.get("docker_env_vars", {}).values():
                m = _re.match(r"https?://([^:/]+):(\d+)", str(url))
                if m:
                    docker_host_map[int(m.group(2))] = m.group(1)

        probes: List[ServiceProbe] = []
        for ext_port_str, info in ports_cfg.items():
            local_port = info.get("local_port", int(ext_port_str))
            tier = (
                "offline_core" if ext_port_str in offline_core else
                "ai_amplifier" if ext_port_str in ai_amps else
                "optional"
            )
            probe_host = docker_host_map.get(local_port, "localhost")
            alive = self._tcp_probe(probe_host, local_port)
            probes.append(ServiceProbe(
                name=info.get("name", f"port:{local_port}"),
                local_port=local_port,
                alive=alive,
                tier=tier,
                start_cmd=info.get("script"),
                note=info.get("note", ""),
            ))
        self.services = probes

    def _detect_network(self) -> None:
        """Quick internet connectivity check."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            self.network_ok = True
        except OSError:
            self.network_ok = False

    # ── Reporting ─────────────────────────────────────────────────────────────

    def activation_plan(self) -> List[Tuple[str, str, Optional[str]]]:
        """
        Returns list of (status, message, fix_command) tuples.
        status: 'ok' | 'warn' | 'error'
        """
        plan: List[Tuple[str, str, Optional[str]]] = []

        # 1. Critical services
        for svc in self.services:
            if svc.tier == "offline_core":
                if svc.alive:
                    plan.append(("ok", f"{svc.name} — running", None))
                else:
                    plan.append(("error", f"{svc.name} — DARK (port {svc.local_port})",
                                 svc.start_cmd))

        # 2. AI amplifiers (warn if down, not error)
        for svc in self.services:
            if svc.tier == "ai_amplifier":
                if not svc.alive:
                    plan.append(("warn", f"{svc.name} — offline (AI optional, not required)",
                                 svc.start_cmd))

        # 3. Sibling repos
        for name, repo in self.siblings.items():
            if name == "Dev-Mentor":
                continue
            if repo.exists:
                link = " [connected]" if repo.has_manifest else ""
                plan.append(("ok", f"Sibling repo: {name}{link}", None))
            else:
                plan.append(("warn", f"Sibling repo: {name} — not found at {repo.path}", None))

        # 4. Network
        if self.network_ok is True:
            plan.append(("ok", "Network: internet reachable", None))
        elif self.network_ok is False:
            plan.append(("warn", "Network: offline — LLM cloud APIs unavailable", None))

        # 5. Environment-specific notes
        r = self.runtime
        if r.is_replit:
            plan.append(("ok", f"Replit: dev domain = {r.details.get('dev_domain', 'unknown')}", None))
        if r.is_container and not r.is_replit:
            plan.append(("ok", "Running inside Docker container", None))
        if r.is_vscode:
            plan.append(("ok", "VS Code terminal detected — tasks.json panel available", None))
        if r.is_wsl:
            plan.append(("ok", "WSL detected — Docker Desktop bridge available", None))

        return plan

    def format_report(self, compact: bool = False) -> str:
        """Return a human-readable environment report."""
        r = self.runtime
        lines: List[str] = []
        # Header
        lines += [
            "╔══════════════════════════════════════════════════════════╗",
            f"║  ECOSYSTEM ENVIRONMENT REPORT                            ║",
            f"║  Surface: {r.name.upper():<48}║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
        ]
        # Runtime flags
        flags = []
        if r.is_container:    flags.append("container")
        if r.is_replit:       flags.append("replit")
        if r.is_vscode:       flags.append("vscode")
        if r.is_wsl:          flags.append("wsl")
        if r.is_codespaces:   flags.append("codespaces")
        if r.is_windows:      flags.append("windows")
        if flags:
            lines.append(f"  Flags   : {' · '.join(flags)}")
        lines.append(f"  Shell   : {r.shell}")
        lines.append(f"  Python  : {r.details.get('python', '?')}")
        lines.append(f"  Host    : {r.details.get('hostname', '?')}")
        if r.is_replit and r.details.get("dev_domain"):
            lines.append(f"  Domain  : https://{r.details['dev_domain']}")
        lines.append("")

        if not compact:
            # Services
            alive = [s for s in self.services if s.alive]
            dark = [s for s in self.services if not s.alive]
            lines.append(f"  Services: {len(alive)} alive · {len(dark)} dark")
            for svc in sorted(self.services, key=lambda s: (s.tier != "offline_core", not s.alive)):
                icon = "✓" if svc.alive else "✗"
                tier_tag = {"offline_core": "CORE", "ai_amplifier": "AI  ", "optional": "OPT "}.get(svc.tier, "    ")
                lines.append(f"    {icon} [{tier_tag}] :{svc.local_port:<5}  {svc.name[:42]}")
            lines.append("")

            # Sibling repos
            lines.append("  Siblings:")
            for name, repo in self.siblings.items():
                if name == "Dev-Mentor":
                    continue
                icon = "✓" if repo.exists else "·"
                link = " ✦" if repo.has_manifest else ""
                lines.append(f"    {icon} {name}{link}")
            lines.append("")

            # Network
            net_tag = "✓ reachable" if self.network_ok else ("✗ offline" if self.network_ok is False else "? unknown")
            lines.append(f"  Network : {net_tag}")
            lines.append("")

        # Activation plan summary
        plan = self.activation_plan()
        errors = [p for p in plan if p[0] == "error"]
        warns = [p for p in plan if p[0] == "warn"]
        if errors:
            lines.append(f"  ⚠  {len(errors)} CRITICAL issue(s):")
            for _, msg, cmd in errors:
                lines.append(f"    ✗ {msg}")
                if cmd:
                    lines.append(f"      → {cmd}")
        if warns and not compact:
            lines.append(f"  ⚡  {len(warns)} warning(s):")
            for _, msg, _ in warns[:5]:
                lines.append(f"    · {msg}")

        if not errors and not warns:
            lines.append("  ✓  All systems nominal. The grid is awake.")

        lines.append("")
        lines.append(f"  Detected: {self.detected_at}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serializable snapshot of the environment."""
        r = self.runtime
        return {
            "detected_at": self.detected_at,
            "runtime": {
                "name": r.name, "shell": r.shell,
                "is_container": r.is_container, "is_replit": r.is_replit,
                "is_vscode": r.is_vscode, "is_wsl": r.is_wsl,
                "is_windows": r.is_windows, "is_codespaces": r.is_codespaces,
                "details": r.details,
            },
            "network_ok": self.network_ok,
            "siblings": {
                n: {"exists": r2.exists, "is_git": r2.is_git, "has_manifest": r2.has_manifest}
                for n, r2 in self.siblings.items()
            },
            "services": [
                {"name": s.name, "port": s.local_port, "alive": s.alive, "tier": s.tier}
                for s in self.services
            ],
            "activation_plan": [
                {"status": st, "message": msg, "fix": cmd}
                for st, msg, cmd in self.activation_plan()
            ],
        }


# ─── Extended detection methods (SC Playbook additions) ────────────────────────

def detect_local_llms() -> List[Dict[str, Any]]:
    """Probe common local LLM endpoint ports. Returns list of live endpoints."""
    _LLM_PORTS = {
        11434: "Ollama",
        1234:  "LM Studio",
        5001:  "LocalAI",
        8000:  "Generic LLM API",
        1106:  "Replit AI Proxy",
        8080:  "Open WebUI",
    }
    found = []
    for port, name in _LLM_PORTS.items():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.3)
            result = s.connect_ex(("localhost", port))
            s.close()
            if result == 0:
                found.append({"name": name, "port": port,
                               "url": f"http://localhost:{port}"})
        except Exception:
            pass
    return found


def detect_container_depth() -> int:
    """Count container nesting depth by reading /proc/self/cgroup."""
    try:
        with open("/proc/self/cgroup") as f:
            lines = f.readlines()
        depth = sum(1 for l in lines if "docker" in l or "lxc" in l or "kubepods" in l)
        return depth
    except Exception:
        return 0


def get_system_resources() -> Dict[str, Any]:
    """Return CPU cores, memory, disk info. Uses psutil if available, else /proc."""
    try:
        import psutil as _ps
        vm = _ps.virtual_memory()
        du = _ps.disk_usage("/")
        cpu_pct = _ps.cpu_percent(interval=0.1)
        return {
            "cpu_cores": _ps.cpu_count(logical=True),
            "cpu_percent": cpu_pct,
            "memory_total_mb": vm.total // 1024 // 1024,
            "memory_available_mb": vm.available // 1024 // 1024,
            "memory_percent": vm.percent,
            "disk_total_gb": round(du.total / 1e9, 1),
            "disk_free_gb": round(du.free / 1e9, 1),
            "disk_percent": du.percent,
            "source": "psutil",
        }
    except ImportError:
        pass
    # Fallback: read /proc
    try:
        mem: Dict[str, int] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])
        total = mem.get("MemTotal", 0)
        avail = mem.get("MemAvailable", mem.get("MemFree", 0))
        pct = round((1 - avail / max(total, 1)) * 100, 1) if total else 0.0
        return {
            "cpu_cores": os.cpu_count() or 1,
            "cpu_percent": None,
            "memory_total_mb": total // 1024,
            "memory_available_mb": avail // 1024,
            "memory_percent": pct,
            "disk_total_gb": None,
            "disk_free_gb": None,
            "disk_percent": None,
            "source": "proc",
        }
    except Exception:
        return {"cpu_cores": 1, "memory_total_mb": 0, "source": "unavailable"}


def detect_installed_tools() -> List[Dict[str, str]]:
    """Scan PATH for hacking / development tools relevant to the game world."""
    _TOOLS = [
        # Core dev
        ("git",        "Version control — run `git log` to explore history"),
        ("python3",    "Python runtime — core language of Terminal Depths"),
        ("sqlite3",    "SQLite CLI — inspect game state databases directly"),
        ("redis-cli",  "Redis client — interact with agent pub/sub channels"),
        ("curl",       "HTTP client — probe API endpoints"),
        ("jq",         "JSON processor — parse game API responses"),
        ("tmux",       "Terminal multiplexer — run multiple agents in one view"),
        # Network / security
        ("nmap",       "Network scanner — real reconnaissance tool"),
        ("nc",         "Netcat — the backbone of `nc chimera-control 8443`"),
        ("netstat",    "Network stats — see what's listening"),
        ("ss",         "Socket stats — modern netstat replacement"),
        ("strace",     "Syscall tracer — see what processes are actually doing"),
        ("gdb",        "GNU Debugger — find the bug, find the truth"),
        ("john",       "Password cracker — crack /etc/shadow hashes"),
        ("hashcat",    "GPU password cracker — faster than john for bulk"),
        ("hydra",      "Login brute-forcer — test credentials"),
        # Analysis
        ("strings",    "Extract printable strings from binaries"),
        ("xxd",        "Hex dump — see raw bytes"),
        ("file",       "Detect file type by magic bytes"),
        ("binwalk",    "Firmware/binary analysis — find hidden data"),
        ("exiftool",   "Metadata analysis — clues in file properties"),
        # Misc
        ("docker",     "Container runtime — build isolated environments"),
        ("gh",         "GitHub CLI — create issues from the game"),
        ("ollama",     "Local LLM runner — offline AI agents"),
    ]
    found = []
    for name, desc in _TOOLS:
        path = shutil.which(name)
        if path:
            found.append({"name": name, "path": path, "desc": desc})
    return found


def get_capabilities_report() -> Dict[str, Any]:
    """Full capabilities snapshot — used by `system capabilities` in-game."""
    return {
        "local_llms":       detect_local_llms(),
        "container_depth":  detect_container_depth(),
        "system_resources": get_system_resources(),
        "installed_tools":  detect_installed_tools(),
        "replit_ai_proxy":  detect_local_llms().__class__  # re-use probe, port 1106
    }


# ─── Singleton ─────────────────────────────────────────────────────────────────

_instance: Optional[Environment] = None


def get_environment(refresh: bool = False, probe: bool = True) -> Environment:
    """Return the cached environment singleton. Detect on first call."""
    global _instance
    if _instance is None or refresh:
        _instance = Environment(probe_services=probe).detect()
    return _instance


# ─── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="DevMentor environment detector")
    ap.add_argument("--json",    action="store_true", help="Output JSON")
    ap.add_argument("--compact", action="store_true", help="Compact report")
    ap.add_argument("--plan",    action="store_true", help="Activation plan only")
    args = ap.parse_args()

    env = get_environment(probe=not args.compact)

    if args.json:
        print(json.dumps(env.to_dict(), indent=2))
    elif args.plan:
        plan = env.activation_plan()
        for status, msg, cmd in plan:
            icon = "✓" if status == "ok" else ("✗" if status == "error" else "·")
            print(f"  {icon} {msg}")
            if cmd:
                print(f"    → {cmd}")
    else:
        print(env.format_report(compact=args.compact))
