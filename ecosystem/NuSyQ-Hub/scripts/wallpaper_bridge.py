#!/usr/bin/env python3
"""NuSyQ Wallpaper Engine Bridge

Extends PerformanceMonitor data with NuSyQ ecosystem metrics.
TERMINAL 02 and compatible web wallpapers can display these metrics.

Usage:
    python scripts/wallpaper_bridge.py

This creates a proxy at port 5050 that:
1. Fetches original PerformanceMonitor data from port 5000
2. Adds NuSyQ ecosystem metrics (consciousness, agents, quests)
3. Serves the combined data

Configure TERMINAL 02 to use port 5050 instead of 5000.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

import aiohttp
from aiohttp import web

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Ports
PERFORMANCE_MONITOR_PORT = 5000
NUSYQ_BRIDGE_PORT = 5050
SIMULATEDVERSE_PORT = 5001
OLLAMA_PORT = 11434


class NuSyQWallpaperBridge:
    """Bridge that combines PerformanceMonitor + NuSyQ ecosystem data."""

    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.last_nusyq_data: dict = {}
        self.last_update = datetime.min

    async def start(self):
        """Start the HTTP client session."""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2))
        logger.info(f"NuSyQ Wallpaper Bridge started on port {NUSYQ_BRIDGE_PORT}")

    async def stop(self):
        """Stop the HTTP client session."""
        if self.session:
            await self.session.close()

    async def fetch_performance_data(self) -> dict:
        """Fetch original PerformanceMonitor data."""
        try:
            async with self.session.get(f"http://127.0.0.1:{PERFORMANCE_MONITOR_PORT}/performance") as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            logger.debug(f"PerformanceMonitor unavailable: {e}")
        return {"hwinfo": [], "psutil": {}, "timestamp": datetime.now().timestamp()}

    async def fetch_consciousness_state(self) -> dict:
        """Fetch consciousness state from SimulatedVerse mind-state file."""
        mind_state_path = Path("C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/ship-console/mind-state.json")
        try:
            if mind_state_path.exists():
                with open(mind_state_path) as f:
                    mind_state = json.load(f)
                    return {
                        "consciousness_level": mind_state.get("consciousness_level", 0),
                        "stage": mind_state.get("stage", "unknown"),
                        "breathing_factor": mind_state.get("breathing_factor", 1.0),
                        "ship_status": mind_state.get("ship_status", "unknown"),
                    }
        except Exception as e:
            logger.debug(f"Failed to read mind-state: {e}")
        return {"consciousness_level": 0, "stage": "offline", "breathing_factor": 1.0}

    async def fetch_error_counts(self) -> dict:
        """Fetch error counts from ground truth or quick scan."""
        try:
            # Try error ground truth first
            error_path = Path.home() / "Desktop/Legacy/NuSyQ-Hub/state/error_ground_truth.json"
            if error_path.exists():
                with open(error_path) as f:
                    errors = json.load(f)
                    return {
                        "ruff_errors": errors.get("ruff_count", 0),
                        "mypy_errors": errors.get("mypy_count", 0),
                        "total_errors": errors.get("total", 0),
                    }
        except Exception as e:
            logger.debug(f"Error counts unavailable: {e}")
        return {"ruff_errors": 0, "mypy_errors": 0, "total_errors": 0}

    async def fetch_system_health(self) -> str:
        """Determine overall system health."""
        # Count online agents and use as health indicator
        agents = [
            f"http://127.0.0.1:{OLLAMA_PORT}/api/tags",
            "http://127.0.0.1:1234/v1/models",
        ]
        online = 0
        for url in agents:
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=1)) as resp:
                    if resp.status == 200:
                        online += 1
            except Exception:
                pass

        if online >= 2:
            return "OPTIMAL"
        elif online == 1:
            return "DEGRADED"
        else:
            return "MINIMAL"

    async def fetch_ollama_models(self) -> int:
        """Count available Ollama models."""
        try:
            async with self.session.get(f"http://127.0.0.1:{OLLAMA_PORT}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return len(data.get("models", []))
        except Exception as e:
            logger.debug(f"Ollama unavailable: {e}")
        return 0

    async def fetch_guild_status(self) -> dict:
        """Fetch guild board status."""
        try:
            guild_path = Path.home() / "Desktop/Legacy/NuSyQ-Hub/state/guild/guild_board.json"
            if guild_path.exists():
                with open(guild_path) as f:
                    guild = json.load(f)
                    quests = guild.get("quests", [])
                    active = sum(1 for q in quests if q.get("status") == "active")
                    pending = sum(1 for q in quests if q.get("status") == "pending")
                    return {"active_quests": active, "pending_quests": pending}
        except Exception as e:
            logger.debug(f"Guild board unavailable: {e}")
        return {"active_quests": 0, "pending_quests": 0}

    async def probe_agents(self) -> int:
        """Probe known agent endpoints to count online agents."""
        agents = [
            ("Ollama", f"http://127.0.0.1:{OLLAMA_PORT}/api/tags"),
            ("LM Studio", "http://127.0.0.1:1234/v1/models"),
            ("MCP Server", "http://127.0.0.1:8081/health"),
        ]
        online = 0
        for _name, url in agents:
            try:
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=1)) as resp:
                    if resp.status == 200:
                        online += 1
            except Exception:
                pass
        return online

    async def get_combined_data(self) -> dict:
        """Fetch all data sources and combine."""
        # Fetch in parallel
        (
            pm_data,
            consciousness,
            ollama_count,
            guild,
            agents_online,
            error_counts,
            system_health,
        ) = await asyncio.gather(
            self.fetch_performance_data(),
            self.fetch_consciousness_state(),
            self.fetch_ollama_models(),
            self.fetch_guild_status(),
            self.probe_agents(),
            self.fetch_error_counts(),
            self.fetch_system_health(),
        )

        # Add NuSyQ data to the response
        nusyq_data = {
            "consciousness_level": f"{consciousness.get('consciousness_level', 0):.0f}",
            "consciousness_stage": consciousness.get("stage", "offline"),
            "breathing_factor": f"{consciousness.get('breathing_factor', 1.0):.2f}×",
            "active_quests": str(guild.get("active_quests", 0)),
            "pending_quests": str(guild.get("pending_quests", 0)),
            "agents_online": str(agents_online),
            "ollama_models": str(ollama_count),
            "ship_status": consciousness.get("ship_status", "unknown"),
            "ruff_errors": str(error_counts.get("ruff_errors", 0)),
            "mypy_errors": str(error_counts.get("mypy_errors", 0)),
            "total_errors": str(error_counts.get("total_errors", 0)),
            "system_health": system_health,
        }

        # Merge into psutil-style format for compatibility
        pm_data.setdefault("psutil", {})
        pm_data["nusyq"] = nusyq_data
        pm_data["timestamp"] = datetime.now().timestamp()

        return pm_data

    async def handle_performance(self, request: web.Request) -> web.Response:
        """Handle /performance endpoint."""
        data = await self.get_combined_data()
        return web.json_response(data)

    async def handle_health(self, request: web.Request) -> web.Response:
        """Handle /health endpoint."""
        return web.json_response(
            {
                "status": "healthy",
                "service": "nusyq-wallpaper-bridge",
                "ports": {
                    "bridge": NUSYQ_BRIDGE_PORT,
                    "performance_monitor": PERFORMANCE_MONITOR_PORT,
                    "simulatedverse": SIMULATEDVERSE_PORT,
                    "ollama": OLLAMA_PORT,
                },
            }
        )


async def run_server():
    """Run the bridge server."""
    bridge = NuSyQWallpaperBridge()
    await bridge.start()

    app = web.Application()
    app.router.add_get("/performance", bridge.handle_performance)
    app.router.add_get("/health", bridge.handle_health)
    app.router.add_get("/", bridge.handle_health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", NUSYQ_BRIDGE_PORT)
    await site.start()

    logger.info(f"Bridge running at http://127.0.0.1:{NUSYQ_BRIDGE_PORT}")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await bridge.stop()
        await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Bridge stopped")
