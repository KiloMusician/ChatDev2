"""Unified Agent Registry - Central capability discovery and orchestration.

This module provides a centralized registry for all AI agents, tools, and capabilities
available in the NuSyQ-Hub ecosystem. It enables:

- Automatic capability discovery
- Agent lifecycle management
- Inter-agent communication
- Resource allocation and load balancing
- Capability-based routing

Architecture:
- Claude Code (primary orchestrator)
- Ollama (local inference: 9 models)
- ChatDev (multi-agent development)
- Continue (VS Code integration)
- Jupyter (notebook workflows)
- Docker/K8s (containerized services)

OmniTag: agent_registry, capability_discovery, orchestration
MegaTag: UNIFIED_ORCHESTRATION, AGENT_MESH, CAPABILITY_ACTIVATION
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class AgentCapability:
    """Represents a single capability (skill/function) of an agent."""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    complexity: str = "medium"  # low, medium, high, extreme
    estimated_duration_seconds: int = 30
    requires_user_approval: bool = False
    tags: list[str] = field(default_factory=list)


@dataclass
class RegisteredAgent:
    """Represents a registered agent in the ecosystem."""

    agent_id: str
    name: str
    agent_type: str  # claude, ollama, chatdev, continue, jupyter, docker, custom
    status: str = "idle"  # idle, busy, offline, error
    capabilities: list[AgentCapability] = field(default_factory=list)
    endpoint: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    total_executions: int = 0
    success_rate: float = 0.0
    average_duration_seconds: float = 0.0


class AgentRegistry:
    """Central registry for all agents and capabilities in the NuSyQ ecosystem."""

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize AgentRegistry with registry_path."""
        self.registry_path = registry_path or Path("data/agent_registry.json")
        self.agents: dict[str, RegisteredAgent] = {}
        self.capability_index: dict[str, list[str]] = {}  # capability_name -> [agent_ids]
        self._load_registry()
        self._discover_builtin_agents()

    def _load_registry(self) -> None:
        """Load existing registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, encoding="utf-8") as f:
                    data = json.load(f)

                for agent_data in data.get("agents", []):
                    capabilities = [
                        AgentCapability(**cap) for cap in agent_data.get("capabilities", [])
                    ]
                    agent_data["capabilities"] = capabilities
                    agent = RegisteredAgent(**agent_data)
                    self.agents[agent.agent_id] = agent
                    self._index_agent_capabilities(agent)

                logger.info(f"📚 Loaded {len(self.agents)} agents from registry")
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")

    def _save_registry(self) -> None:
        """Save registry to disk."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "agents": [
                    {
                        **asdict(agent),
                        "capabilities": [asdict(cap) for cap in agent.capabilities],
                    }
                    for agent in self.agents.values()
                ],
                "total_agents": len(self.agents),
                "total_capabilities": sum(len(a.capabilities) for a in self.agents.values()),
            }

            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"💾 Registry saved: {len(self.agents)} agents")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _index_agent_capabilities(self, agent: RegisteredAgent) -> None:
        """Index agent capabilities for fast lookup."""
        for capability in agent.capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = []
            if agent.agent_id not in self.capability_index[capability.name]:
                self.capability_index[capability.name].append(agent.agent_id)

    def _discover_builtin_agents(self) -> None:
        """Discover and register built-in agents."""
        # Discover MCP registry servers (auto-start if feature flag enabled)
        try:
            from src.config.feature_flag_manager import is_feature_enabled
            from src.integration.mcp_registry_loader import \
                get_mcp_registry_loader

            if is_feature_enabled("mcp_registry_enabled"):
                loader = get_mcp_registry_loader()
                started = loader.start_enabled_servers()
                for server_id, server in loader.active_servers.items():
                    endpoint_port = server.env.get("MCP_SERVER_PORT") or os.getenv(
                        "MCP_SERVER_PORT", "8080"
                    )
                    endpoint = f"http://localhost:{endpoint_port}"
                    cap = AgentCapability(
                        name="mcp_tool_execute",
                        description=f"Execute MCP tools on {server_id}",
                        input_schema={"tool": "string", "parameters": "object"},
                        output_schema={"result": "object"},
                        tags=server.tags,
                    )
                    self.register_agent(
                        RegisteredAgent(
                            agent_id=f"mcp-{server_id}",
                            name=f"MCP Server ({server_id})",
                            agent_type="mcp",
                            status="idle",
                            capabilities=[cap],
                            endpoint=endpoint,
                            config={"command": server.command, "env": server.env},
                            metadata={"tags": server.tags},
                        )
                    )
                if started:
                    logger.info("✅ MCP registry auto-started %s servers", started)
        except Exception as e:  # pragma: no cover - best-effort discovery
            logger.warning("MCP registry discovery skipped: %s", e)

        # Register Ollama agent
        if self._check_ollama_available():
            ollama_capabilities = self._discover_ollama_capabilities()
            self.register_agent(
                RegisteredAgent(
                    agent_id="ollama-local",
                    name="Ollama Local Inference",
                    agent_type="ollama",
                    status="idle",
                    capabilities=ollama_capabilities,
                    endpoint="http://localhost:11434",
                    config={"models": self._get_ollama_models()},
                    metadata={
                        "provider": "ollama",
                        "location": "local",
                        "connection_tested": True,
                    },
                )
            )

        # Register ChatDev agent
        if self._check_chatdev_available():
            chatdev_capabilities = self._discover_chatdev_capabilities()
            self.register_agent(
                RegisteredAgent(
                    agent_id="chatdev-orchestrator",
                    name="ChatDev Multi-Agent Development",
                    agent_type="chatdev",
                    status="idle",
                    capabilities=chatdev_capabilities,
                    config={
                        "max_agents": 5,
                        "default_roles": [
                            "CEO",
                            "CTO",
                            "Programmer",
                            "Reviewer",
                            "Tester",
                        ],
                    },
                    metadata={
                        "integration_path": "src/integration/chatdev_integration.py",
                        "available": True,
                    },
                )
            )

        # Register Continue extension
        if self._check_continue_available():
            continue_capabilities = self._discover_continue_capabilities()
            self.register_agent(
                RegisteredAgent(
                    agent_id="continue-vscode",
                    name="Continue VS Code Extension",
                    agent_type="continue",
                    status="idle",
                    capabilities=continue_capabilities,
                    config={"providers": ["anthropic", "openai", "ollama", "copilot"]},
                    metadata={
                        "config_path": ".continue/config.json",
                        "custom_commands": [
                            "nusyq-analyze",
                            "doctrine-check",
                            "wire-action",
                        ],
                    },
                )
            )

        # Register Jupyter
        if self._check_jupyter_available():
            jupyter_capabilities = self._discover_jupyter_capabilities()
            self.register_agent(
                RegisteredAgent(
                    agent_id="jupyter-notebooks",
                    name="Jupyter Notebook Environment",
                    agent_type="jupyter",
                    status="idle",
                    capabilities=jupyter_capabilities,
                    config={"notebooks_found": self._count_notebooks()},
                    metadata={
                        "notebook_dirs": ["docs/Notebooks", "notebooks", "src/utils"],
                    },
                )
            )

        # Register Docker/K8s orchestration
        if self._check_docker_available():
            docker_capabilities = self._discover_docker_capabilities()
            self.register_agent(
                RegisteredAgent(
                    agent_id="docker-orchestrator",
                    name="Docker Container Orchestration",
                    agent_type="docker",
                    status="idle",
                    capabilities=docker_capabilities,
                    endpoint="unix:///var/run/docker.sock",
                    config={"k8s_available": self._check_kubernetes_available()},
                    metadata={
                        "docker_version": self._get_docker_version(),
                        "compose_files": [
                            "deploy/docker-compose.yml",
                            "deploy/docker-compose.dev.yml",
                        ],
                    },
                )
            )

        metaclaw_runtime = self._detect_metaclaw_runtime()
        if metaclaw_runtime["available"]:
            self.register_agent(
                RegisteredAgent(
                    agent_id="metaclaw",
                    name="MetaClaw Trace Agent",
                    agent_type="metaclaw",
                    status="idle" if metaclaw_runtime["runnable"] else "offline",
                    capabilities=self._discover_metaclaw_capabilities(),
                    config={"path": metaclaw_runtime["path"]},
                    metadata={"integration": "tracing", **metaclaw_runtime},
                )
            )

        hermes_runtime = self._detect_hermes_runtime()
        if hermes_runtime["available"]:
            self.register_agent(
                RegisteredAgent(
                    agent_id="hermes_agent",
                    name="Hermes Communication & RAG Agent",
                    agent_type="hermes_agent",
                    status="idle" if hermes_runtime["runnable"] else "offline",
                    capabilities=self._discover_hermes_capabilities(),
                    config={"path": hermes_runtime["path"]},
                    metadata={"integration": "RAG", **hermes_runtime},
                )
            )
        self._save_registry()

    def register_agent(self, agent: RegisteredAgent, override: bool = False) -> bool:
        """Register a new agent or update existing."""
        if agent.agent_id in self.agents and not override:
            existing = self.agents[agent.agent_id]
            if (
                existing.agent_type == agent.agent_type
                and existing.name == agent.name
                and existing.endpoint == agent.endpoint
            ):
                logger.debug("Agent %s already registered (idempotent)", agent.agent_id)
                return True
            logger.warning("Agent %s already registered", agent.agent_id)
            return False

        self.agents[agent.agent_id] = agent
        self._index_agent_capabilities(agent)
        self._save_registry()

        logger.info(f"✅ Registered agent: {agent.name} ({len(agent.capabilities)} capabilities)")
        try:
            from src.system.agent_awareness import emit as _emit

            caps = len(agent.capabilities)
            detail = f"{agent.name} | caps={caps} status={agent.status}"
            _emit.agent_online(agent.agent_id, detail)
        except Exception:
            pass
        return True

    def get_agent(self, agent_id: str) -> RegisteredAgent | None:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    def find_agents_by_capability(
        self, capability_name: str, status_filter: str | None = None
    ) -> list[RegisteredAgent]:
        """Find all agents that provide a specific capability."""
        agent_ids = self.capability_index.get(capability_name, [])
        agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]

        if status_filter:
            agents = [a for a in agents if a.status == status_filter]

        return agents

    def find_best_agent_for_task(
        self,
        required_capabilities: list[str],
        task_complexity: str = "medium",
        prefer_local: bool = True,
    ) -> RegisteredAgent | None:
        """Find the best agent for a task based on capabilities and context."""
        candidates = []

        for agent in self.agents.values():
            if agent.status not in ["idle", "busy"]:
                continue

            # Check if agent has all required capabilities
            agent_cap_names = {cap.name for cap in agent.capabilities}
            if not set(required_capabilities).issubset(agent_cap_names):
                continue

            # Calculate score
            score = agent.success_rate * 100

            # Prefer local agents
            if prefer_local and agent.metadata.get("location") == "local":
                score += 50

            # Prefer idle agents over busy
            if agent.status == "idle":
                score += 20

            # Match complexity
            matching_caps = [
                cap
                for cap in agent.capabilities
                if cap.name in required_capabilities and cap.complexity == task_complexity
            ]
            score += len(matching_caps) * 10

            candidates.append((score, agent))

        if not candidates:
            return None

        candidates.sort(reverse=True, key=lambda x: x[0])
        return candidates[0][1]

    def update_agent_status(
        self, agent_id: str, status: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Update agent status and metadata."""
        if agent_id not in self.agents:
            return False

        agent = self.agents[agent_id]
        agent.status = status
        agent.last_seen = datetime.now().isoformat()

        if metadata:
            agent.metadata.update(metadata)

        self._save_registry()
        return True

    def record_execution(self, agent_id: str, success: bool, duration_seconds: float) -> None:
        """Record execution metrics for an agent."""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]
        agent.total_executions += 1

        # Update success rate
        if agent.total_executions == 1:
            agent.success_rate = 1.0 if success else 0.0
        else:
            successes = int(agent.success_rate * (agent.total_executions - 1))
            successes += 1 if success else 0
            agent.success_rate = successes / agent.total_executions

        # Update average duration
        if agent.total_executions == 1:
            agent.average_duration_seconds = duration_seconds
        else:
            total_time = agent.average_duration_seconds * (agent.total_executions - 1)
            agent.average_duration_seconds = (
                total_time + duration_seconds
            ) / agent.total_executions

        self._save_registry()

    def get_registry_stats(self) -> dict[str, Any]:
        """Get comprehensive registry statistics."""
        return {
            "total_agents": len(self.agents),
            "agents_by_type": self._count_by_type(),
            "agents_by_status": self._count_by_status(),
            "total_capabilities": sum(len(a.capabilities) for a in self.agents.values()),
            "unique_capabilities": len(self.capability_index),
            "average_success_rate": sum(a.success_rate for a in self.agents.values())
            / max(len(self.agents), 1),
            "most_used_agents": self._get_most_used_agents(5),
            "last_updated": datetime.now().isoformat(),
        }

    def _count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for agent in self.agents.values():
            counts[agent.agent_type] = counts.get(agent.agent_type, 0) + 1
        return counts

    def _count_by_status(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for agent in self.agents.values():
            counts[agent.status] = counts.get(agent.status, 0) + 1
        return counts

    def _get_most_used_agents(self, limit: int) -> list[dict[str, Any]]:
        sorted_agents = sorted(
            self.agents.values(), key=lambda a: a.total_executions, reverse=True
        )[:limit]

        return [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "executions": a.total_executions,
                "success_rate": a.success_rate,
            }
            for a in sorted_agents
        ]

    # Discovery helper methods

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests

            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _get_ollama_models(self) -> list[str]:
        """Get list of available Ollama models."""
        try:
            import requests

            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def _discover_ollama_capabilities(self) -> list[AgentCapability]:
        """Discover Ollama capabilities based on available models."""
        models = self._get_ollama_models()

        capabilities = [
            AgentCapability(
                name="text_generation",
                description="Generate text completions using local LLMs",
                complexity="low",
                estimated_duration_seconds=10,
                tags=["llm", "local", "generation"],
            ),
            AgentCapability(
                name="code_analysis",
                description="Analyze code using specialized code models",
                complexity="medium",
                estimated_duration_seconds=30,
                tags=["code", "analysis", "local"],
            ),
            AgentCapability(
                name="embeddings",
                description="Generate embeddings for semantic search",
                complexity="low",
                estimated_duration_seconds=5,
                tags=["embeddings", "search", "local"],
            ),
        ]

        # Add model-specific capabilities
        for model in models:
            if "code" in model.lower():
                capabilities.append(
                    AgentCapability(
                        name=f"code_completion_{model.replace(':', '_')}",
                        description=f"Code completion using {model}",
                        complexity="low",
                        estimated_duration_seconds=5,
                        tags=["code", "completion", model],
                    )
                )

        return capabilities

    def _check_chatdev_available(self) -> bool:
        """Check if ChatDev integration is available."""
        chatdev_path = Path("src/integration/chatdev_integration.py")
        return chatdev_path.exists()

    def _discover_chatdev_capabilities(self) -> list[AgentCapability]:
        """Discover ChatDev capabilities."""
        return [
            AgentCapability(
                name="multi_agent_development",
                description="Collaborative software development with multiple AI agents",
                complexity="extreme",
                estimated_duration_seconds=300,
                requires_user_approval=True,
                tags=["multi-agent", "development", "collaborative"],
            ),
            AgentCapability(
                name="code_review",
                description="Multi-perspective code review",
                complexity="high",
                estimated_duration_seconds=120,
                tags=["code", "review", "quality"],
            ),
            AgentCapability(
                name="architecture_design",
                description="Collaborative system architecture design",
                complexity="extreme",
                estimated_duration_seconds=240,
                requires_user_approval=True,
                tags=["architecture", "design", "planning"],
            ),
        ]

    def _check_continue_available(self) -> bool:
        """Check if Continue extension is configured."""
        continue_config = Path(".continue/config.json")
        return continue_config.exists()

    def _discover_continue_capabilities(self) -> list[AgentCapability]:
        """Discover Continue extension capabilities."""
        return [
            AgentCapability(
                name="code_autocomplete",
                description="AI-powered code autocompletion in VS Code",
                complexity="low",
                estimated_duration_seconds=2,
                tags=["code", "autocomplete", "vscode"],
            ),
            AgentCapability(
                name="codebase_search",
                description="Semantic codebase search with embeddings",
                complexity="medium",
                estimated_duration_seconds=10,
                tags=["search", "codebase", "semantic"],
            ),
            AgentCapability(
                name="nusyq_analyze",
                description="NuSyQ-specific code analysis",
                complexity="high",
                estimated_duration_seconds=60,
                tags=["nusyq", "analysis", "custom"],
            ),
        ]

    def _check_jupyter_available(self) -> bool:
        """Check if Jupyter notebooks are available."""
        return len(list(Path(".").rglob("*.ipynb"))) > 0

    def _count_notebooks(self) -> int:
        """Count Jupyter notebooks."""
        return len(list(Path(".").rglob("*.ipynb")))

    def _discover_jupyter_capabilities(self) -> list[AgentCapability]:
        """Discover Jupyter capabilities."""
        return [
            AgentCapability(
                name="data_analysis",
                description="Interactive data analysis in Jupyter notebooks",
                complexity="medium",
                estimated_duration_seconds=60,
                tags=["jupyter", "data", "analysis"],
            ),
            AgentCapability(
                name="visualization",
                description="Create visualizations and reports",
                complexity="medium",
                estimated_duration_seconds=45,
                tags=["jupyter", "visualization", "reporting"],
            ),
        ]

    def _check_docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _check_kubernetes_available(self) -> bool:
        """Check if Kubernetes is available."""
        try:
            import subprocess

            result = subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_docker_version(self) -> str:
        """Get Docker version."""
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _discover_docker_capabilities(self) -> list[AgentCapability]:
        """Discover Docker/K8s capabilities."""
        capabilities = [
            AgentCapability(
                name="container_deployment",
                description="Deploy services as Docker containers",
                complexity="high",
                estimated_duration_seconds=90,
                requires_user_approval=True,
                tags=["docker", "deployment", "containers"],
            ),
            AgentCapability(
                name="service_orchestration",
                description="Orchestrate multi-container applications",
                complexity="extreme",
                estimated_duration_seconds=180,
                requires_user_approval=True,
                tags=["docker", "orchestration", "compose"],
            ),
        ]

        if self._check_kubernetes_available():
            capabilities.append(
                AgentCapability(
                    name="kubernetes_deployment",
                    description="Deploy to Kubernetes cluster",
                    complexity="extreme",
                    estimated_duration_seconds=240,
                    requires_user_approval=True,
                    tags=["kubernetes", "k8s", "deployment", "cloud"],
                )
            )

        return capabilities

    @staticmethod
    def _first_existing_path(candidates: list[Path | None]) -> Path | None:
        """Return the first existing path from the given candidates."""
        for candidate in candidates:
            if candidate is not None and candidate.exists():
                return candidate
        return None

    @staticmethod
    def _env_file_has_real_values(env_path: Path) -> bool:
        """Return True when an env file contains non-placeholder values."""
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                _key, value = line.split("=", 1)
                normalized = value.strip().strip("\"'")
                if (
                    normalized
                    and "your_" not in normalized.lower()
                    and "placeholder" not in normalized.lower()
                ):
                    return True
        except OSError:
            return False
        return False

    def _detect_metaclaw_runtime(self) -> dict[str, Any]:
        """Detect MetaClaw source/runtime presence without assuming credentials."""
        path = self._first_existing_path(
            [
                Path(os.getenv("METACLAW_PATH")) if os.getenv("METACLAW_PATH") else None,
                REPO_ROOT / "state" / "runtime" / "external" / "metaclaw-agent",
            ]
        )
        if path is None:
            return {"available": False, "runnable": False}

        env_path = path / ".env"
        node_modules_ready = (path / "node_modules").exists()
        env_ready = env_path.exists() and self._env_file_has_real_values(env_path)
        return {
            "available": True,
            "path": str(path),
            "runnable": bool(
                shutil.which("node") and shutil.which("npm") and node_modules_ready and env_ready
            ),
            "node_modules_ready": node_modules_ready,
            "env_configured": env_ready,
        }

    def _detect_hermes_runtime(self) -> dict[str, Any]:
        """Detect Hermes source/runtime presence with Python-version constraints."""
        path = self._first_existing_path(
            [
                Path(os.getenv("HERMES_AGENT_PATH")) if os.getenv("HERMES_AGENT_PATH") else None,
                REPO_ROOT / "state" / "runtime" / "external" / "hermes-agent",
            ]
        )
        if path is None:
            return {"available": False, "runnable": False}

        python_311 = shutil.which("python3.11") or shutil.which("python311")
        hermes_venv = path / ".venv" / "bin" / "python"
        python_cmd = str(hermes_venv) if hermes_venv.exists() else python_311
        return {
            "available": True,
            "path": str(path),
            "runnable": bool(python_cmd and (path / "pyproject.toml").exists()),
            "python_3_11_available": bool(python_cmd),
            "python_command": python_cmd,
            "node_modules_ready": (path / "node_modules").exists(),
        }

    def _discover_metaclaw_capabilities(self) -> list[AgentCapability]:
        """Describe MetaClaw capabilities when the runtime is present."""
        return [
            AgentCapability(
                name="trace_observability",
                description="Advanced trace and observability for agent actions",
                tags=["trace", "observability", "metrics"],
            ),
            AgentCapability(
                name="bounty_status_monitoring",
                description="Inspect MetaClaw bounty and agent runtime status",
                tags=["status", "bounties", "agent"],
            ),
        ]

    def _discover_hermes_capabilities(self) -> list[AgentCapability]:
        """Describe Hermes capabilities when the runtime is present."""
        return [
            AgentCapability(
                name="rag_context_retrieval",
                description="Retrieval-augmented generation and agent communication",
                tags=["rag", "context", "communication"],
            ),
            AgentCapability(
                name="delegated_tool_execution",
                description="Parallel workstreams and delegated tool execution",
                complexity="high",
                estimated_duration_seconds=120,
                tags=["delegation", "tools", "runtime"],
            ),
        ]


# Global registry instance
_registry: AgentRegistry | None = None


def get_agent_registry() -> AgentRegistry:
    """Get or create the global agent registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
