"""AI Orchestrator - Intelligent provider selection for code generation.

Routes work to ChatDev, Ollama, Claude based on project complexity,
token budget, and availability. ChatDev is the primary generator for
complex multi-file projects.
"""

import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AIProviderType(Enum):
    """Available AI providers."""

    CHATDEV = "chatdev"
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"
    MANUAL = "manual"


class AIOrchestrator:
    """Intelligent AI provider selection for factory generation tasks.

    Selection Logic:
    - complexity > 5 files OR requires_multifile=True → ChatDev (PRIORITY)
    - offline_required=True → Ollama (qwen2.5-coder)
    - research_heavy=True → Claude
    - fallback → Ollama, then OpenAI
    """

    def __init__(self):
        """Initialize orchestrator with provider detection."""
        self.chatdev_path = self._detect_chatdev()
        self.ollama_available = self._detect_ollama()
        self.claude_available = self._detect_claude()
        self.openai_available = self._detect_openai()

    def _chatdev_runner_score(self, path: Path) -> int:
        """Score a ChatDev path by available runner capabilities."""
        score = 0
        if (path / "run_ollama.py").exists():
            score += 2
        if (path / "run.py").exists():
            score += 1
        return score

    def _chatdev_has_runner(self, path: Path) -> bool:
        """Return True if path has any supported ChatDev runner."""
        return self._chatdev_runner_score(path) > 0

    def _provider_available(self, provider: AIProviderType) -> bool:
        """Check if a provider is currently available for selection."""
        if provider == AIProviderType.CHATDEV:
            return self.chatdev_path is not None
        if provider == AIProviderType.OLLAMA:
            return self.ollama_available
        if provider == AIProviderType.CLAUDE:
            return self.claude_available
        if provider == AIProviderType.OPENAI:
            return self.openai_available
        return provider == AIProviderType.MANUAL

    def _detect_chatdev(self) -> Path | None:
        """Detect ChatDev installation."""
        candidates: list[Path] = []

        # Check environment variable first
        chatdev_env = os.environ.get("CHATDEV_PATH")
        if chatdev_env:
            candidates.append(Path(chatdev_env))

        # Check common locations (including archived versions)
        candidates.extend(
            [
                Path("/mnt/c/Users/keath/NuSyQ/ChatDev"),
                Path("/mnt/c/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main"),
                Path(
                    "/mnt/c/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main-archived-20260208"
                ),
                Path("C:/Users/keath/NuSyQ/ChatDev"),
                Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main"),
                Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main-archived-20260208"),
                Path.home() / "NuSyQ" / "ChatDev",
                Path.home() / "Desktop" / "Legacy" / "ChatDev_CORE" / "ChatDev-main",
                Path.home()
                / "Desktop"
                / "Legacy"
                / "ChatDev_CORE"
                / "ChatDev-main-archived-20260208",
                Path.home() / ".chatdev",
            ]
        )

        best_path: Path | None = None
        best_score = -1
        seen: set[Path] = set()
        for path in candidates:
            if path in seen:
                continue
            seen.add(path)
            if not path.exists():
                continue
            score = self._chatdev_runner_score(path)
            if score > best_score:
                best_score = score
                best_path = path

        if best_path and self._chatdev_has_runner(best_path):
            return best_path

        # Legacy fallback list for compatibility with prior installs.
        common_paths = [
            Path("C:/Users/keath/NuSyQ/ChatDev"),
            Path("C:/Users/keath/Desktop/Legacy/ChatDev_CORE/ChatDev-main"),
            Path.home() / "NuSyQ" / "ChatDev",
            Path.home() / "Desktop" / "Legacy" / "ChatDev_CORE" / "ChatDev-main",
            Path.home() / ".chatdev",
        ]

        for path in common_paths:
            if self._chatdev_has_runner(path):
                return path

        return None

    def _detect_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            import socket

            with socket.create_connection(("127.0.0.1", 11434), timeout=1.5):
                return True
        except OSError:
            return False

    def _detect_claude(self) -> bool:
        """Check if Claude/Anthropic API is configured."""
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    def _detect_openai(self) -> bool:
        """Check if OpenAI API is configured."""
        return bool(os.environ.get("OPENAI_API_KEY"))

    def select_provider(
        self,
        complexity: int = 5,  # 1-10 scale
        requires_multifile: bool = False,
        offline_required: bool = False,
        research_heavy: bool = False,
        token_budget: float | None = None,
        user_preference: str | None = None,
    ) -> AIProviderType:
        """Select best AI provider for given constraints.

        Args:
            complexity: Project complexity (1-10)
            requires_multifile: Needs multi-file generation
            offline_required: Must work offline
            research_heavy: Requires research/planning
            token_budget: Max tokens allowed (None = unlimited)
            user_preference: User-specified provider name

        Returns:
            Selected AI provider type
        """
        # User preference overrides everything
        if user_preference:
            try:
                preferred = AIProviderType(user_preference.lower())
                if self._provider_available(preferred):
                    return preferred
            except ValueError:
                logger.debug("Suppressed ValueError", exc_info=True)

        # ChatDev priority: complex projects
        if (complexity >= 5 or requires_multifile) and self.chatdev_path:
            return AIProviderType.CHATDEV

        # Offline handling
        if offline_required:
            if self.ollama_available:
                return AIProviderType.OLLAMA
            elif self.chatdev_path:
                return AIProviderType.CHATDEV
            else:
                raise RuntimeError(
                    "Offline required but no offline providers available. Install Ollama or ChatDev."
                )

        # Research/planning
        if research_heavy and self.claude_available:
            return AIProviderType.CLAUDE

        # Token budget consider
        if token_budget and token_budget < 10000 and self.ollama_available:
            return AIProviderType.OLLAMA  # Local, free tokens

        # Default priority chain
        if self.chatdev_path:
            return AIProviderType.CHATDEV

        if self.ollama_available:
            return AIProviderType.OLLAMA

        if self.claude_available:
            return AIProviderType.CLAUDE

        if self.openai_available:
            return AIProviderType.OPENAI

        raise RuntimeError(
            "No AI providers available. Configure at least one: ChatDev, Ollama, Claude, or OpenAI"
        )

    def get_generator_config(self, provider: AIProviderType) -> dict[str, Any]:
        """Get configuration for selected provider."""
        if provider == AIProviderType.CHATDEV:
            runner = None
            if self.chatdev_path:
                run_ollama = self.chatdev_path / "run_ollama.py"
                run_py = self.chatdev_path / "run.py"
                runner = str(run_ollama if run_ollama.exists() else run_py)
            return {
                "type": "chatdev",
                "path": str(self.chatdev_path),
                "runner": runner,
                "methods": ["run.py", "run_ollama.py"],
                "max_files": 20,
                "supports_teams": True,
                "incremental_learning": True,
            }

        elif provider == AIProviderType.OLLAMA:
            return {
                "type": "ollama",
                "base_url": "http://localhost:11434/v1",
                "models": ["qwen2.5-coder:7b", "qwen2.5-coder:14b", "starcoder2:15b"],
                "default_model": "qwen2.5-coder:7b",
                "max_files": 5,
                "supports_teams": False,
                "local": True,
                "offline": True,
            }

        elif provider == AIProviderType.CLAUDE:
            return {
                "type": "claude",
                "base_url": "https://api.anthropic.com",
                "model": "claude-3-opus-20240229",
                "max_tokens": 4000,
                "supports_teams": False,
            }

        elif provider == AIProviderType.OPENAI:
            return {
                "type": "openai",
                "base_url": "https://api.openai.com",
                "model": "gpt-4",
                "max_tokens": 8000,
                "supports_teams": False,
            }

        else:
            return {}

    def explain_selection(self, provider: AIProviderType, reason: str = "") -> str:
        """Generate human-readable explanation for selection."""
        reasons = {
            AIProviderType.CHATDEV: "Multi-agent team for complex projects (CEO, CTO, Programmer, Tester, Reviewer)",
            AIProviderType.OLLAMA: "Local LLM for fast iterations and token savings",
            AIProviderType.CLAUDE: "Research and high-level planning",
            AIProviderType.OPENAI: "High-quality generation with GPT-4",
            AIProviderType.MANUAL: "User-provided code",
        }

        return f"Selected: {provider.value.upper()} - {reasons.get(provider, reason)}"
