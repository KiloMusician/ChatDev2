"""Hacking Game Mechanics — BitBurner/Hacknet integration with RPG Inventory.

Core APIs for scanning/connecting to components, exploiting vulnerabilities,
managing traces, and executing scripts with resource constraints.

OmniTag: {
    "purpose": "game_mechanics_engine",
    "tags": ["Hacking", "Games", "Async", "Networking"],
    "category": "gameplay",
    "evolution_stage": "prototype"
}
"""

import logging
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class ExploitType(Enum):
    """Types of exploits analogous to Hacknet tools."""

    SSH_CRACK = "ssh_crack"  # Crack SSH protocol
    SQL_INJECT = "sql_inject"  # SQL injection attack
    BUFFER_OVERFLOW = "buffer_overflow"  # Memory exploit
    CONFIG_LEAK = "config_leak"  # Extract configuration
    SERVICE_HIJACK = "service_hijack"  # Hijack running service
    PRIVILEGE_ESCALATE = "privilege_escalate"  # Gain sudo/admin


class TraceStatus(Enum):
    """Status of active trace/alarm when entering a component."""

    SAFE = "safe"  # No trace started
    TRACING = "tracing"  # Trace active, countdown running
    CRITICAL = "critical"  # Trace almost complete, will lockdown
    LOCKDOWN = "lockdown"  # Locked down, must evade or fail


@dataclass
class Port:
    """Port exposed by a component (like Hacknet servers)."""

    port_number: int
    service_name: str  # "SSH", "HTTP", "SQL", "RPC", etc.
    open: bool = False
    vulnerable: bool = False
    exploit_type: ExploitType | None = None
    access_level: int = 0  # 0=guest, 1=user, 2=admin, 3=root


@dataclass
class Trace:
    """Active trace/alarm on a component when user is intrusions."""

    id: str
    component_name: str
    start_time: datetime
    duration_seconds: int  # Timer before lockdown
    current_countdown: int  # Seconds remaining
    trace_status: TraceStatus = TraceStatus.SAFE
    triggered_at: datetime | None = None

    def is_active(self) -> bool:
        """Check if trace is still running."""
        if self.trace_status == TraceStatus.LOCKDOWN:
            return True
        if not self.triggered_at:
            return False
        elapsed = (datetime.now() - self.triggered_at).total_seconds()
        return elapsed < self.duration_seconds

    def update_countdown(self) -> int:
        """Update countdown and return remaining seconds."""
        if not self.triggered_at:
            self.current_countdown = self.duration_seconds
        else:
            elapsed = (datetime.now() - self.triggered_at).total_seconds()
            self.current_countdown = max(0, self.duration_seconds - int(elapsed))

            if self.current_countdown <= 0:
                self.trace_status = TraceStatus.LOCKDOWN
            elif self.current_countdown <= 10:
                self.trace_status = TraceStatus.CRITICAL
            elif self.current_countdown <= self.duration_seconds:
                self.trace_status = TraceStatus.TRACING

        return self.current_countdown


@dataclass
class ScanResult:
    """Result of scanning a component (like Hacknet scan)."""

    component_name: str
    ip_address: str
    ports: list[Port]
    services: list[str]
    vulnerabilities: list[str]
    open_exploits: list[ExploitType]
    admin_access: bool = False
    security_level: int = 0  # 0-5, higher = more secure
    trace_risk: float = 0.0  # 0-1, likelihood of triggering trace


@dataclass
class ExploitResult:
    """Result of running an exploit against a component."""

    success: bool
    exploit_type: ExploitType
    access_gained: int  # 0=guest, 1=user, 2=admin, 3=root
    data_exfiltrated: str | None = None
    trace_triggered: bool = False
    new_access_level: int = 0
    error_message: str | None = None


class HackingController:
    """Controller for hacking-game mechanics."""

    def __init__(self):
        """Initialize hacking controller."""
        self.active_traces: dict[str, Trace] = {}
        self.component_access_levels: dict[str, int] = {}  # Track player's access per component
        self.scanned_components: dict[str, ScanResult] = {}
        self.exploits_available: dict[str, list[ExploitType]] = {}
        self.player_memory_usage: int = 0  # Simulate Hacknet memory constraints
        self.max_memory: int = 32  # Max concurrent programs/scripts
        logger.info("HackingController initialized")

    def create_component_ports(self, component_name: str) -> list[Port]:
        """Generate ports for a given component based on its type."""
        ports = []
        service_map = {
            "python": [
                Port(22, "SSH", open=True, vulnerable=True, exploit_type=ExploitType.SSH_CRACK),
                Port(5000, "HTTP", open=True, vulnerable=False),
            ],
            "ollama": [
                Port(
                    11434,
                    "HTTP-API",
                    open=True,
                    vulnerable=True,
                    exploit_type=ExploitType.CONFIG_LEAK,
                ),
            ],
            "postgres": [
                Port(5432, "SQL", open=False, vulnerable=True, exploit_type=ExploitType.SQL_INJECT),
            ],
            "git": [
                Port(22, "SSH", open=True, vulnerable=False),
                Port(9418, "GIT", open=True, vulnerable=False),
            ],
            "openai": [
                Port(443, "HTTPS-API", open=True, vulnerable=False),
            ],
        }

        for port_def in service_map.get(component_name, []):
            ports.append(port_def)

        return ports

    async def scan(self, component_name: str) -> ScanResult:
        """Scan a component to discover ports, services, vulnerabilities.

        Equivalent to Hacknet's 'scan' command.
        """
        logger.info(f"Scanning component: {component_name}")

        ports = self.create_component_ports(component_name)
        if not ports:
            ports = [Port(80, "HTTP", open=random.choice([True, False]))]

        open_ports = [p for p in ports if p.open]
        services = [p.service_name for p in ports]
        vulnerabilities = [p.exploit_type.value for p in ports if p.vulnerable and p.exploit_type]

        result = ScanResult(
            component_name=component_name,
            ip_address=f"192.168.1.{hash(component_name) % 254 + 1}",
            ports=ports,
            services=services,
            vulnerabilities=vulnerabilities,
            open_exploits=[p.exploit_type for p in ports if p.exploit_type and p.open],
            security_level=random.randint(1, 5),
            trace_risk=random.uniform(0.1, 0.8),
        )

        self.scanned_components[component_name] = result
        logger.info(
            f"Scan complete: {len(open_ports)} open ports, {len(vulnerabilities)} vulnerabilities"
        )
        return result

    async def connect(self, component_name: str) -> bool:
        """Attempt to connect to a component.

        If security high, may trigger trace. Requires open SSH or HTTP port.
        """
        logger.info(f"Connecting to: {component_name}")

        if component_name not in self.scanned_components:
            scan_result = await self.scan(component_name)
        else:
            scan_result = self.scanned_components[component_name]

        ssh_ports = [p for p in scan_result.ports if p.service_name == "SSH" and p.open]
        if not ssh_ports:
            logger.warning(f"No open SSH ports on {component_name}")
            return False

        # Security check: higher security means higher chance of trace trigger
        if random.random() < scan_result.trace_risk * 0.3:
            await self._trigger_trace(component_name, duration=random.randint(30, 120))
            logger.warning(f"Trace triggered on {component_name}")

        self.component_access_levels[component_name] = 1  # User level
        logger.info(f"Connected to {component_name} with user access")
        return True

    async def _trigger_trace(self, component_name: str, duration: int = 60) -> Trace:
        """Start a trace/alarm on a component (Hacknet-style timer)."""
        trace = Trace(
            id=str(uuid4()),
            component_name=component_name,
            start_time=datetime.now(),
            duration_seconds=duration,
            current_countdown=duration,
            trace_status=TraceStatus.TRACING,
            triggered_at=datetime.now(),
        )
        self.active_traces[component_name] = trace
        logger.warning(f"Trace started on {component_name}, {duration}s to lockdown")
        return trace

    async def exploit(
        self,
        component_name: str,
        exploit_type: ExploitType,
        _xp_reward: int = 50,
    ) -> ExploitResult:
        """Execute an exploit against a component.

        Returns access level gained (0=fail, 1=user, 2=admin, 3=root).
        """
        logger.info(f"Executing {exploit_type.value} exploit on {component_name}")

        if component_name not in self.scanned_components:
            scan_result = await self.scan(component_name)
        else:
            scan_result = self.scanned_components[component_name]

        # Check if this component has this vulnerability
        if exploit_type not in scan_result.open_exploits:
            logger.warning(f"Exploit {exploit_type.value} not available on {component_name}")
            return ExploitResult(
                success=False,
                exploit_type=exploit_type,
                access_gained=0,
                error_message="Exploit not available on this component",
            )

        # Simulate exploit execution
        success_rate = 0.6 + (self.component_access_levels.get(component_name, 0) * 0.15)
        success = random.random() < success_rate

        if success:
            new_access = min(3, self.component_access_levels.get(component_name, 0) + 1)
            self.component_access_levels[component_name] = new_access
            logger.info(f"Exploit succeeded, access level now {new_access}")

            # High access might trigger trace
            trace_triggered = random.random() < 0.3 and new_access >= 3
            if trace_triggered:
                await self._trigger_trace(component_name, duration=random.randint(20, 60))

            return ExploitResult(
                success=True,
                exploit_type=exploit_type,
                access_gained=new_access,
                new_access_level=new_access,
                trace_triggered=trace_triggered,
            )
        else:
            logger.warning(f"Exploit failed on {component_name}")
            return ExploitResult(
                success=False,
                exploit_type=exploit_type,
                access_gained=0,
                error_message="Exploit execution failed",
            )

    async def patch(self, component_name: str) -> bool:
        """Patch/update a component to remove vulnerabilities.

        Requires admin access. Removes open exploits.
        """
        logger.info(f"Patching component: {component_name}")

        access_level = self.component_access_levels.get(component_name, 0)
        if access_level < 2:  # Requires admin/root
            logger.error(f"Insufficient access to patch {component_name}")
            return False

        if component_name in self.scanned_components:
            scan = self.scanned_components[component_name]
            # Clear vulnerabilities
            for port in scan.ports:
                port.vulnerable = False
                port.exploit_type = None
            scan.vulnerabilities.clear()
            scan.open_exploits.clear()
            logger.info(f"Successfully patched {component_name}")
            return True

        return False

    def check_traces(self) -> dict[str, TraceStatus]:
        """Poll all active traces and return their status.

        Returns dict of component_name -> TraceStatus.
        """
        statuses = {}
        for comp_name, trace in list(self.active_traces.items()):
            trace.update_countdown()
            statuses[comp_name] = trace.trace_status
            if not trace.is_active():
                del self.active_traces[comp_name]
                logger.info(f"Trace on {comp_name} cleared")
        return statuses

    def allocate_memory(self, program_name: str, memory_cost: int) -> bool:
        """Allocate memory for running a script/program (Hacknet-style).

        Returns True if allocated, False if insufficient memory.
        """
        if self.player_memory_usage + memory_cost > self.max_memory:
            logger.warning(
                f"Insufficient memory for {program_name} ({self.player_memory_usage + memory_cost}/{self.max_memory})"
            )
            return False

        self.player_memory_usage += memory_cost
        logger.info(
            f"Allocated {memory_cost} memory to {program_name} ({self.player_memory_usage}/{self.max_memory})"
        )
        return True

    def free_memory(self, memory_cost: int) -> None:
        """Free memory after a script completes."""
        self.player_memory_usage = max(0, self.player_memory_usage - memory_cost)
        logger.info(
            f"Freed {memory_cost} memory ({self.player_memory_usage}/{self.max_memory} used)"
        )

    def get_status(self) -> dict[str, Any]:
        """Get current hacking status."""
        return {
            "active_traces": {
                comp: trace.trace_status.value for comp, trace in self.active_traces.items()
            },
            "access_levels": self.component_access_levels,
            "memory_used": f"{self.player_memory_usage}/{self.max_memory}",
            "scanned_count": len(self.scanned_components),
        }


# Global instance
_hacking_controller: HackingController | None = None


def get_hacking_controller() -> HackingController:
    """Get or create global HackingController instance."""
    global _hacking_controller
    if _hacking_controller is None:
        _hacking_controller = HackingController()
    return _hacking_controller
