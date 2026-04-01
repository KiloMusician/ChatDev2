#!/usr/bin/env python3
"""Minimal SimulatedVerse Launcher.
[ROUTE AGENTS] 🤖

Starts SimulatedVerse agents without full persistence layer
Uses agent API endpoints directly
"""

import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

try:
    from src.config.service_config import ServiceConfig
except ImportError:
    ServiceConfig = None

try:
    from src.utils.timeout_config import get_http_timeout
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from src.utils.timeout_config import get_http_timeout


def _ensure_scheme(url: str) -> str:
    return url if "://" in url else f"http://{url}"


def _resolve_simulatedverse_url() -> str:
    """Resolve SimulatedVerse base URL using config/env with safe defaults."""
    if ServiceConfig:
        return ServiceConfig.get_simulatedverse_url().rstrip("/")

    base = os.getenv("SIMULATEDVERSE_BASE_URL")
    if base:
        return _ensure_scheme(base).rstrip("/")

    host = os.getenv("SIMULATEDVERSE_HOST", "http://127.0.0.1")
    port = os.getenv("SIMULATEDVERSE_PORT", "5001")
    parsed = urlparse(_ensure_scheme(host))
    if parsed.port:
        return parsed.geturl().rstrip("/")
    netloc = f"{parsed.hostname}:{port}" if parsed.hostname else f"127.0.0.1:{port}"
    return f"{parsed.scheme}://{netloc}"


def _to_existing_path(path_str: str) -> Path | None:
    """Normalize Windows/WSL path strings and return an existing path when possible."""
    raw = path_str.strip()
    if not raw:
        return None

    direct = Path(raw)
    if direct.exists():
        return direct

    windows_match = re.match(r"^([A-Za-z]):[\\/](.*)$", raw)
    if windows_match:
        drive = windows_match.group(1).lower()
        tail = windows_match.group(2).replace("\\", "/")
        wsl_path = Path(f"/mnt/{drive}/{tail}")
        if wsl_path.exists():
            return wsl_path

    return None


def _resolve_simulatedverse_path() -> Path:
    """Resolve SimulatedVerse repo path from env/config with safe fallbacks."""
    env_path = os.getenv("SIMULATEDVERSE_PATH") or os.getenv("SIMULATEDVERSE_ROOT")
    if env_path:
        resolved_env = _to_existing_path(env_path)
        if resolved_env:
            if (resolved_env / "package.json").exists():
                return resolved_env
            nested = resolved_env / "SimulatedVerse"
            if (nested / "package.json").exists():
                return nested

    repos_json = Path(__file__).resolve().parents[1] / "config" / "repos.json"
    if repos_json.exists():
        try:
            with open(repos_json, encoding="utf-8") as f:
                repos = json.load(f)
            repo_candidate = repos.get("SimulatedVerse")
            if isinstance(repo_candidate, str):
                resolved_repo = _to_existing_path(repo_candidate)
                if resolved_repo:
                    if (resolved_repo / "package.json").exists():
                        return resolved_repo
                    nested = resolved_repo / "SimulatedVerse"
                    if (nested / "package.json").exists():
                        return nested
        except (OSError, json.JSONDecodeError):
            pass

    # Relative workspace fallback.
    candidate = (Path(__file__).resolve().parents[1] / ".." / "SimulatedVerse" / "SimulatedVerse").resolve()
    if (candidate / "package.json").exists():
        return candidate

    # Last resort: current working directory sibling.
    cwd_fallback = Path(str(Path.cwd())) / ".." / "SimulatedVerse" / "SimulatedVerse"
    return cwd_fallback.resolve()


class SimulatedVerseMinimal:
    """Minimal SimulatedVerse launcher."""

    def __init__(self):
        self.simulatedverse_path = _resolve_simulatedverse_path()
        self.base_url = _resolve_simulatedverse_url()
        self.agents_available = [
            "librarian",
            "alchemist",
            "artificer",
            "intermediary",
            "council",
            "party",
            "culture-ship",
            "redstone",
            "zod",
        ]

    def check_if_running(self) -> bool:
        """Check if SimulatedVerse is already running."""
        try:
            timeout = get_http_timeout("SIMULATEDVERSE", default=2)
            response = requests.get(f"{self.base_url}/api/health", timeout=timeout)
            return bool(response.status_code == 200)
        except requests.RequestException:
            return False

    def start_agents_only(self, timeout: int = 30) -> subprocess.Popen | None:
        """Start SimulatedVerse with agents but bypass broken persistence.

        Uses simple Express server instead of full system
        """
        package_json = self.simulatedverse_path / "package.json"
        if not package_json.exists():
            print(f"❌ SimulatedVerse package.json not found at: {package_json}")
            return None

        if self.check_if_running():
            return None

        minimal_server = self.simulatedverse_path / "server" / "minimal_server.ts"
        minimal_server_content = """
import express from 'express';
import cors from 'cors';

const app = express();
app.use(cors());
app.use(express.json());

const HOST = process.env.SIMULATEDVERSE_HOST || '127.0.0.1';
const PORT = Number(process.env.SIMULATEDVERSE_PORT || 5001);
const BASE = HOST.startsWith('http') ? HOST : `http://${HOST}`;

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', mode: 'minimal', agents: 9 });
});

// Agent API routes (dynamic imports to avoid persistence layer)
const loadAgentRoutes = async () => {
    try {
        const { agentsRouter } = await import('./router/agents.js');
        app.use('/api/agents', agentsRouter);
        console.log('✅ Agent routes loaded');
    } catch (error) {
        console.log('⚠️  Agent routes not available:', error.message);
    }

    try {
        const { proposals } = await import('./router/proposals.js');
        app.use('/api/proposals', proposals);
        console.log('✅ Proposal routes loaded');
    } catch (error) {
        console.log('⚠️  Proposal routes not available:', error.message);
    }

    try {
        const { pu } = await import('./router/pu.js');
        app.use('/api/pu', pu);
        console.log('✅ PU Queue routes loaded');
    } catch (error) {
        console.log('⚠️  PU Queue routes not available:', error.message);
    }
};

loadAgentRoutes();

app.listen(PORT, HOST, () => {
    console.log(`
======================================================================
 SIMULATEDVERSE MINIMAL MODE
 Agent API: ${BASE}:${PORT}/api/agents
 Health Check: ${BASE}:${PORT}/api/health
======================================================================
    `);
});
"""

        # Prefer npm run script on Windows and when available for correct script resolution
        use_npm_run = self._detect_use_npm_run()

        # Only generate the fallback minimal server file when we are not reusing an
        # existing dev:minimal script from the SimulatedVerse repo.
        if not use_npm_run:
            self._write_minimal_server(minimal_server, minimal_server_content)

        # Ensure dependencies are installed (tsx required)
        node_modules = self.simulatedverse_path / "node_modules"
        if not node_modules.exists():
            self._ensure_node_modules_installed()

        if use_npm_run:
            cmd = ["npm", "run", "dev:minimal"]
        else:
            # Fallback to npx tsx directly
            cmd = ["npx", "tsx", "server/minimal_server.ts"]

        # If on Windows, prefer invoking via cmd to correctly resolve .cmd shim files
        is_windows = os.name == "nt"
        exec_cmd = self._build_exec_cmd(cmd, use_npm_run, is_windows)

        print(f"🔧 Starting minimal SimulatedVerse with command: {exec_cmd} (cwd={self.simulatedverse_path})")

        process = self._start_process(exec_cmd)

        # Wait for startup
        started_proc = self._wait_for_startup(process, timeout)
        return started_proc

    def test_agent_api(self):
        """Test agent API endpoints."""
        # Test health
        try:
            timeout = get_http_timeout("SIMULATEDVERSE", default=5)
            response = requests.get(f"{self.base_url}/api/health", timeout=timeout)
        except requests.RequestException:
            return False

        # Test agent list
        try:
            timeout = get_http_timeout("SIMULATEDVERSE", default=5)
            response = requests.get(f"{self.base_url}/api/agents", timeout=timeout)
            if response.status_code == 200:
                agents = response.json()
                # Handle either list or dict: if dict, try to read 'agents' key
                if isinstance(agents, dict):
                    agents_list = agents.get("agents") or agents.get("items") or list(agents.values())
                elif isinstance(agents, list):
                    agents_list = agents
                else:
                    agents_list = []

                for _agent in agents_list[:3]:  # Show first 3
                    print(f"✅ Agent available: {_agent}")
        except requests.RequestException:
            pass

        return True

    def _ensure_node_modules_installed(self) -> None:
        """Attempt to run `npm ci` to restore node_modules.

        This is best-effort; failure to run `npm` is logged but not fatal.
        """
        package_lock = self.simulatedverse_path / "package-lock.json"
        primary_cmd = ["npm", "ci"] if package_lock.exists() else ["npm", "install", "--no-audit"]
        fallback_cmd = ["npm", "install", "--no-audit"]

        try:
            print(f"📦 node_modules not found - attempting to run '{' '.join(primary_cmd)}'...")
            subprocess.run(primary_cmd, cwd=str(self.simulatedverse_path), check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            if primary_cmd == fallback_cmd:
                print("⚠️  npm install failed or npm not available:", exc)
                return
            print("⚠️  npm ci failed; attempting npm install fallback:", exc)
            try:
                subprocess.run(fallback_cmd, cwd=str(self.simulatedverse_path), check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as fallback_exc:
                print("⚠️  npm install fallback failed or npm not available:", fallback_exc)

    def _detect_use_npm_run(self) -> bool:
        """Return True if package.json contains a dev:minimal script.

        Safer to parse JSON and return False on error rather than raising.
        """
        pkg = self.simulatedverse_path / "package.json"
        if not pkg.exists():
            return False

        try:
            import json as _json

            data = _json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
            return "dev:minimal" in scripts
        except (FileNotFoundError, _json.JSONDecodeError, PermissionError) as exc:
            print("⚠️  Unable to parse package.json to find dev:minimal script:", exc)
            return False

    def _build_exec_cmd(self, base_cmd: list[str], use_npm_run: bool, is_windows: bool) -> list[str]:
        """Build a cross-platform exec command for running the minimal server.

        On Windows, prefer `cmd /c` invocations so that `npm.cmd` and `npx.cmd` are resolved.
        """
        if is_windows:
            if use_npm_run:
                return ["cmd", "/c", *base_cmd]
            # If npx isn't available as a binary, use cmd /c to run it through the shell
            try:
                subprocess.run(["npx", "--version"], cwd=str(self.simulatedverse_path), check=True)
                return base_cmd
            except (subprocess.CalledProcessError, FileNotFoundError):
                return ["cmd", "/c", "npx tsx server/minimal_server.ts"]

        return base_cmd

    def _write_minimal_server(self, path: Path, content: str) -> None:
        """Write the minimal server TypeScript file to disk."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
        except OSError as exc:
            print("⚠️  Failed writing minimal_server.ts:", exc)

    def _start_process(self, exec_cmd: list[str]) -> subprocess.Popen:
        """Start the process and return the Popen handle."""
        env = os.environ.copy()
        if os.name != "nt":
            # Ensure tsx/npm use Linux-native temp dirs under WSL/Linux and avoid drvfs socket failures.
            env["TMPDIR"] = "/tmp"
            env["TMP"] = "/tmp"
            env["TEMP"] = "/tmp"
        detach = str(env.get("NUSYQ_SIMULATEDVERSE_DETACH", "")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        if detach:
            hub_root = Path(env.get("NUSYQ_HUB_PATH", Path(__file__).resolve().parents[1]))
            log_dir = hub_root / "state" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "simulatedverse_minimal_runtime.log"
            print(f"📝 Detached mode enabled; logging to {log_path}")
            with open(log_path, "a", encoding="utf-8") as log_fh:
                process = subprocess.Popen(
                    exec_cmd,
                    cwd=str(self.simulatedverse_path),
                    stdout=log_fh,
                    stderr=subprocess.STDOUT,
                    text=True,
                    shell=False,
                    env=env,
                    start_new_session=True,
                )
            return process

        return subprocess.Popen(
            exec_cmd,
            cwd=str(self.simulatedverse_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=False,
            env=env,
        )

    def _wait_for_startup(self, process: subprocess.Popen, timeout: int = 30) -> subprocess.Popen | None:
        """Wait up to 'timeout' seconds for process to become healthy and return it.

        Will log output if process exists early for diagnostics.
        """
        for i in range(timeout):
            time.sleep(1)
            # If process exited early, dump its output for diagnostics
            if process.poll() is not None:
                try:
                    if process.stdout:
                        remaining = process.stdout.read()
                    else:
                        remaining = None
                except (ValueError, AttributeError, OSError) as exc:
                    remaining = f"<failed reading stdout: {exc}>"
                print("⚠️  SimulatedVerse minimal process exited early. Output:\n", remaining)
                return None
            if self.check_if_running():
                return process
            if i % 5 == 0:
                print(f"... waiting for SimulatedVerse minimal to boot ({i + 1}/{timeout})")

        return None


def _detach_requested() -> bool:
    """Return True when the launcher is explicitly running in detached mode."""
    return str(os.getenv("NUSYQ_SIMULATEDVERSE_DETACH", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def main():
    """Run minimal SimulatedVerse launcher."""
    import argparse

    parser = argparse.ArgumentParser(description="Start a minimal SimulatedVerse instance for local testing.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force start a new minimal SimulatedVerse instance even if one is detected running.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds to wait for the server to respond.",
    )

    args = parser.parse_args()
    launcher = SimulatedVerseMinimal()

    # Start SimulatedVerse
    process = None
    if args.force:
        process = launcher.start_agents_only(timeout=args.timeout)
    else:
        if not launcher.check_if_running():
            process = launcher.start_agents_only(timeout=args.timeout)

    if process or launcher.check_if_running():
        # Test API
        launcher.test_agent_api()

        if process and not _detach_requested():
            try:
                process.wait()
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
    else:
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
