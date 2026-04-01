"""Capability registry for NuSyQ spine.

Provides unified service discovery and capability registration:
- Loads capabilities from config/nusyq_capabilities.json
- Auto-discovers scripts, tools, connectors, workflows
- Registers new Agent Protocol components

OmniTag: [registry, discovery, capabilities, spine]
MegaTag: CAP⨳REG⦾SPINE→∞
"""

import contextlib
import json
import logging
from pathlib import Path
from typing import Any

from src.core.result import Ok, Result

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
CAP_PATH = ROOT / "config" / "nusyq_capabilities.json"


class CapabilityRegistry:
    def __init__(self) -> None:
        """Initialize CapabilityRegistry."""
        self._caps: dict[str, Any] = {}
        self.load()
        # on init, attempt lightweight discovery of scripts/tools
        with contextlib.suppress(OSError, RuntimeError):  # discovery is best-effort
            self.discover()

    def load(self) -> None:
        if CAP_PATH.exists():
            try:
                with open(CAP_PATH, encoding="utf-8") as f:
                    self._caps = json.load(f)
            except (OSError, json.JSONDecodeError):
                self._caps = {}

    def list_all(self) -> dict:
        """Return a copy of all registered capabilities."""
        return dict(self._caps)

    def find(self, query: str) -> list[dict]:
        res = []
        q = query.lower()
        for name, meta in self._caps.items():
            if q in name.lower() or q in json.dumps(meta).lower():
                res.append({"name": name, "meta": meta})
        return res

    def discover(self, search_dirs: list[str] | None = None) -> None:
        """Discover simple capabilities in common locations and register them.

        This is a lightweight scanner: looks under 'scripts', 'src/tools', and 'ops'
        for python files and registers them with a small metadata blob.
        """
        import glob

        if search_dirs is None:
            search_dirs = ["scripts", "src/tools", "ops"]
        found = {}
        root = CAP_PATH.parents[1]
        for sd in search_dirs:
            pattern = str(root / sd / "**" / "*.py")
            for p in glob.glob(pattern, recursive=True):
                name = Path(p).stem
                rel = str(Path(p).relative_to(root))
                meta = {"path": rel, "example": f"python {rel}", "tags": ["script"]}
                found[name] = meta
        # merge into existing registry without overwriting explicit entries
        for n, m in found.items():
            if n not in self._caps:
                self._caps[n] = m
        # persist
        CAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CAP_PATH, "w", encoding="utf-8") as f:
            json.dump(self._caps, f, ensure_ascii=False, indent=2)

    def register(self, name: str, meta: dict) -> None:
        self._caps[name] = meta
        CAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CAP_PATH, "w", encoding="utf-8") as f:
            json.dump(self._caps, f, ensure_ascii=False, indent=2)

    def unregister(self, name: str) -> bool:
        """Remove a capability from the registry."""
        if name in self._caps:
            del self._caps[name]
            CAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CAP_PATH, "w", encoding="utf-8") as f:
                json.dump(self._caps, f, ensure_ascii=False, indent=2)
            return True
        return False

    def get(self, name: str) -> dict | None:
        """Get capability metadata by name."""
        return self._caps.get(name)

    def get_by_tag(self, tag: str) -> list[dict]:
        """Find capabilities by tag."""
        results = []
        for name, meta in self._caps.items():
            tags = meta.get("tags", [])
            if tag in tags:
                results.append({"name": name, "meta": meta})
        return results

    def register_agent_protocol_components(self) -> Result[dict]:
        """Register all Agent Protocol components (connectors, workflows, test-loop).

        This wires the new infrastructure into the capability registry for
        unified service discovery.

        Returns:
            Result[dict]: Registration summary
        """
        registered = []
        errors = []

        # Register connector system
        try:
            from src.connectors.registry import get_connector_registry

            connector_reg = get_connector_registry()
            connector_status = connector_reg.get_status()

            self.register(
                "connector_registry",
                {
                    "type": "service",
                    "module": "src.connectors.registry",
                    "entry_point": "get_connector_registry",
                    "description": "Connector registry for external integrations",
                    "tags": ["connector", "integration", "agent-protocol"],
                    "status": connector_status,
                },
            )
            registered.append("connector_registry")

            # Register individual connectors
            for conn_info in connector_reg.list_connectors():
                conn_name = f"connector:{conn_info.get('name', 'unknown')}"
                self.register(
                    conn_name,
                    {
                        "type": "connector",
                        "connector_type": conn_info.get("type", "unknown"),
                        "enabled": conn_info.get("enabled", False),
                        "tags": ["connector", "agent-protocol"],
                    },
                )
                registered.append(conn_name)

        except ImportError as e:
            errors.append(f"connector_registry: {e}")
            logger.warning(f"Could not register connector registry: {e}")

        # Register workflow engine
        try:
            from src.workflow.engine import get_workflow_engine

            engine = get_workflow_engine()
            workflows = engine.list_workflows()

            self.register(
                "workflow_engine",
                {
                    "type": "service",
                    "module": "src.workflow.engine",
                    "entry_point": "get_workflow_engine",
                    "description": "n8n-style workflow execution engine",
                    "tags": ["workflow", "automation", "agent-protocol"],
                    "workflow_count": len(workflows),
                },
            )
            registered.append("workflow_engine")

            # Register individual workflows
            for wf in workflows:
                wf_name = f"workflow:{wf.get('id', 'unknown')}"
                self.register(
                    wf_name,
                    {
                        "type": "workflow",
                        "name": wf.get("name", ""),
                        "node_count": wf.get("node_count", 0),
                        "enabled": wf.get("enabled", True),
                        "tags": ["workflow", "agent-protocol"],
                    },
                )
                registered.append(wf_name)

        except ImportError as e:
            errors.append(f"workflow_engine: {e}")
            logger.warning(f"Could not register workflow engine: {e}")

        # Register test loop
        try:
            from src.automation.test_loop import TestLoop

            self.register(
                "test_loop",
                {
                    "type": "service",
                    "module": "src.automation.test_loop",
                    "entry_point": "TestLoop",
                    "description": "Self-testing AI loop with iterative fixes",
                    "tags": ["testing", "automation", "ai", "agent-protocol"],
                },
            )
            registered.append("test_loop")

        except ImportError as e:
            errors.append(f"test_loop: {e}")
            logger.warning(f"Could not register test loop: {e}")

        # Register web app templates
        try:
            from src.factories.templates import BaseWebApp

            self.register(
                "webapp_factory",
                {
                    "type": "factory",
                    "module": "src.factories.templates",
                    "entry_point": "BaseWebApp",
                    "description": "Web application template factory",
                    "tags": ["factory", "webapp", "agent-protocol"],
                },
            )
            registered.append("webapp_factory")

        except ImportError as e:
            errors.append(f"webapp_factory: {e}")
            logger.warning(f"Could not register webapp factory: {e}")

        logger.info(
            f"Agent Protocol registration: {len(registered)} components, {len(errors)} errors"
        )

        return Ok(
            {
                "registered": registered,
                "errors": errors,
                "total_registered": len(registered),
                "total_errors": len(errors),
            }
        )

    def health_check(self) -> Result[dict]:
        """Perform health check on registry and registered services.

        Returns:
            Result[dict]: Health status
        """
        healthy_services = []
        unhealthy_services = []

        for name, meta in self._caps.items():
            if meta.get("type") == "service":
                module_path = meta.get("module", "")
                try:
                    # Just check if we can import
                    __import__(module_path)
                    healthy_services.append(name)
                except ImportError:
                    unhealthy_services.append(name)

        return Ok(
            {
                "status": "healthy" if not unhealthy_services else "degraded",
                "total_capabilities": len(self._caps),
                "healthy_services": len(healthy_services),
                "unhealthy_services": len(unhealthy_services),
                "unhealthy": unhealthy_services,
            }
        )


REGISTRY = CapabilityRegistry()


def get_capability_registry() -> CapabilityRegistry:
    """Get the global capability registry instance.

    Returns:
        CapabilityRegistry: The singleton registry
    """
    return REGISTRY
