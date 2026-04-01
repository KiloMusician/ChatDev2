"""ChatDev Generator - Wrapper around ChatDev for factory integration.

Standardizes ChatDev output to factory format, tracks metrics, preserves
WareHouse metadata. ChatDev is the primary generator for complex projects.
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ChatDevGenerationResult:
    """Result of ChatDev generation."""

    project_name: str
    warehouse_path: Path  # Raw ChatDev WareHouse output
    model_used: str  # e.g., "qwen2.5-coder:7b"
    token_cost: float  # Estimated token cost
    created_at: str
    task_description: str
    success: bool = True
    error_message: str | None = None


class ChatDevGenerator:
    """Wrapper for ChatDev multi-agent code generation."""

    def __init__(self, chatdev_path: Path):
        """Initialize ChatDev generator.

        Args:
            chatdev_path: Path to ChatDev installation
        """
        self.source_chatdev_path = Path(chatdev_path)
        self.chatdev_path = self._prepare_runtime_chatdev_path(self.source_chatdev_path)
        self.runner = self._select_runner()
        self.warehouse_dir = self._resolve_warehouse_dir()
        self.warehouse_search_roots = self._warehouse_search_candidates()

    @staticmethod
    def _dir_is_writable(path: Path) -> bool:
        """Return True when directory exists and allows create/delete operations."""
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return True
        except OSError:
            return False

    def _prepare_runtime_chatdev_path(self, source_path: Path) -> Path:
        """Ensure ChatDev runs from a writable location.

        Some host setups expose ChatDev as read-only (for this process), which breaks
        ChatDev's hardcoded `WareHouse/*.log` writes. When that happens we mirror the
        runtime into a temp path and execute there.
        """
        warehouse_path = source_path / "WareHouse"
        if self._dir_is_writable(warehouse_path):
            return source_path

        runtime_root = Path(tempfile.gettempdir()) / "chatdev_runtime" / source_path.name
        runtime_root.parent.mkdir(parents=True, exist_ok=True)

        if not (runtime_root / "run.py").exists():

            def _ignore(path: str, names: list[str]) -> list[str]:
                # Copy ChatDev code/configs, skip historical WareHouse payloads.
                if Path(path).name == "WareHouse":
                    return names
                return []

            shutil.copytree(
                source_path,
                runtime_root,
                dirs_exist_ok=True,
                ignore=_ignore,
            )
            (runtime_root / "WareHouse").mkdir(parents=True, exist_ok=True)

        return runtime_root

    def _select_runner(self) -> Path:
        """Select the best available ChatDev runner."""
        run_ollama = self.chatdev_path / "run_ollama.py"
        run_py = self.chatdev_path / "run.py"
        if run_ollama.exists():
            return run_ollama
        if run_py.exists():
            return run_py
        raise FileNotFoundError(
            f"ChatDev not found at {self.chatdev_path}. Missing run_ollama.py or run.py"
        )

    def _resolve_warehouse_dir(self) -> Path:
        """Resolve a writable warehouse directory for ChatDev outputs."""
        candidates: list[Path] = []

        warehouse_env = os.environ.get("CHATDEV_WAREHOUSE_PATH")
        if warehouse_env:
            candidates.append(Path(warehouse_env))

        candidates.extend(
            [
                self.chatdev_path / "WareHouse",
                self.source_chatdev_path / "WareHouse",
                Path.cwd() / "chatdev_warehouse",
                Path("/tmp/chatdev_warehouse"),
            ]
        )

        for candidate in candidates:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
            except OSError:
                continue
            if os.access(candidate, os.W_OK):
                return candidate

        raise PermissionError("Unable to resolve writable ChatDev warehouse directory")

    def _warehouse_search_candidates(self) -> list[Path]:
        """Collect candidate roots where ChatDev may write generated projects."""
        roots: list[Path] = [
            self.warehouse_dir,
            self.chatdev_path / "WareHouse",
            self.source_chatdev_path / "WareHouse",
            Path.cwd() / "WareHouse",
            Path.cwd() / "chatdev_warehouse",
        ]
        seen: set[Path] = set()
        unique: list[Path] = []
        for root in roots:
            if root in seen:
                continue
            seen.add(root)
            unique.append(root)
        return unique

    @staticmethod
    def _to_ollama_root_url(openai_base_url: str) -> str:
        """Convert OpenAI-compatible base URL to Ollama root URL for run_ollama.py."""
        normalized = openai_base_url.rstrip("/")
        if normalized.endswith("/v1"):
            return normalized[:-3]
        return normalized

    def _normalize_chatdev_model(self, model: str) -> str:
        """Convert factory model labels to ChatDev's expected CLI model enum names."""
        if self.runner.name != "run.py":
            return model

        accepted = {"GPT_3_5_TURBO", "GPT_4", "GPT_4_TURBO", "GPT_4O", "GPT_4O_MINI"}
        if model in accepted:
            return model

        lower = model.lower()
        if "4o-mini" in lower:
            return "GPT_4O_MINI"
        if "4o" in lower:
            return "GPT_4O"
        if "gpt-4-turbo" in lower or "4-turbo" in lower:
            return "GPT_4_TURBO"
        if "gpt-4" in lower:
            return "GPT_4"
        return "GPT_3_5_TURBO"

    @staticmethod
    def _ollama_has_model(installed: list[str], name: str) -> bool:
        """Return True if model exists by full name or base name."""
        base = name.split(":", 1)[0]
        for model in installed:
            model_base = model.split(":", 1)[0]
            if model == name or model_base == base:
                return True
        return False

    def _ollama_installed_models(self) -> list[str]:
        """Best-effort list of local Ollama models."""
        try:
            proc = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []

        models: list[str] = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("name"):
                continue
            model_name = line.split()[0]
            if model_name:
                models.append(model_name)
        return models

    def _ensure_ollama_alias_for_chatdev(self, chatdev_model: str, source_hint: str) -> None:
        """Ensure ChatDev's OpenAI model name resolves against local Ollama."""
        target_alias_map = {
            "GPT_3_5_TURBO": "gpt-3.5-turbo-16k",
            "GPT_4": "gpt-4",
            "GPT_4_TURBO": "gpt-4-turbo",
            "GPT_4O": "gpt-4o",
            "GPT_4O_MINI": "gpt-4o-mini",
        }
        target = target_alias_map.get(chatdev_model)
        if not target:
            return

        installed = self._ollama_installed_models()
        if self._ollama_has_model(installed, target):
            return

        source_candidates = [
            source_hint,
            os.environ.get("CHATDEV_OLLAMA_SOURCE_MODEL", ""),
            "qwen2.5-coder:14b",
            "qwen2.5-coder:7b",
            "llama3.1:8b",
        ]
        source = next(
            (
                candidate
                for candidate in source_candidates
                if candidate and self._ollama_has_model(installed, candidate)
            ),
            "",
        )
        if not source:
            return

        subprocess.run(
            ["ollama", "cp", source, target],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def generate(
        self,
        task: str,
        project_name: str,
        model: str = "qwen2.5-coder:7b",
        org_name: str = "NuSyQ",
    ) -> ChatDevGenerationResult:
        """Generate code using ChatDev.

        Args:
            task: Natural language task description
            project_name: Name of project to generate
            model: LLM model to use
            org_name: Organization name (for WareHouse folder)

        Returns:
            ChatDevGenerationResult with generation metadata and output path
        """
        start_time = datetime.now()

        runner = self.runner
        chatdev_model = self._normalize_chatdev_model(model)

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.chatdev_path)
        env["CHATDEV_MODEL"] = chatdev_model
        openai_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        ollama_root_url = self._to_ollama_root_url(openai_base_url)
        env["OLLAMA_BASE_URL"] = openai_base_url
        env["BASE_URL"] = openai_base_url
        env["OPENAI_BASE_URL"] = openai_base_url
        env["OPENAI_API_KEY"] = env.get("OPENAI_API_KEY", "ollama-local")
        env["CHATDEV_WAREHOUSE_PATH"] = str(self.warehouse_dir)

        # Vanilla ChatDev `run.py` maps `GPT_*` enums to fixed OpenAI model IDs.
        # When pointed at Ollama's OpenAI endpoint we ensure those IDs exist.
        if runner.name == "run.py":
            self._ensure_ollama_alias_for_chatdev(chatdev_model, model)

        cmd = [
            "python",
            str(runner),
            "--task",
            task,
            "--name",
            project_name,
            "--org",
            org_name,
            "--model",
            chatdev_model,
        ]
        if runner.name == "run_ollama.py":
            cmd.extend(["--ollama-url", ollama_root_url])

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.chatdev_path),
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                env=env,
            )

            if result.returncode != 0:
                output = "\n".join(
                    [chunk for chunk in [result.stdout, result.stderr] if chunk]
                ).strip()
                return ChatDevGenerationResult(
                    project_name=project_name,
                    warehouse_path=self.warehouse_dir,
                    model_used=chatdev_model,
                    token_cost=0.0,
                    created_at=start_time.isoformat(),
                    task_description=task,
                    success=False,
                    error_message=output or "chatdev subprocess failed",
                )

            # Find generated project in WareHouse
            warehouse_path = self._find_warehouse_output(project_name, org_name, start_time)

            # Estimate token cost (based on ChatDev's typical usage)
            token_cost = self._estimate_token_cost(warehouse_path, model)

            return ChatDevGenerationResult(
                project_name=project_name,
                warehouse_path=warehouse_path,
                model_used=chatdev_model,
                token_cost=token_cost,
                created_at=start_time.isoformat(),
                task_description=task,
                success=True,
            )

        except subprocess.TimeoutExpired:
            return ChatDevGenerationResult(
                project_name=project_name,
                warehouse_path=self.warehouse_dir,
                model_used=model,
                token_cost=0.0,
                created_at=start_time.isoformat(),
                task_description=task,
                success=False,
                error_message="ChatDev generation timeout (> 1 hour)",
            )

        except Exception as e:
            return ChatDevGenerationResult(
                project_name=project_name,
                warehouse_path=self.warehouse_dir,
                model_used=model,
                token_cost=0.0,
                created_at=start_time.isoformat(),
                task_description=task,
                success=False,
                error_message=str(e),
            )

    def _find_warehouse_output(
        self, project_name: str, org_name: str, after_time: datetime
    ) -> Path:
        """Find the generated project in WareHouse directory.

        ChatDev creates: WareHouse/{ProjectName}_{OrgName}_{Timestamp}/
        """
        candidates: list[tuple[float, Path]] = []
        pattern = f"{project_name}_{org_name}_*"

        # First pass: files created after generation start.
        for root in self.warehouse_search_roots:
            if not root.exists():
                continue
            for dir_path in root.glob(pattern):
                if not dir_path.is_dir():
                    continue
                try:
                    mtime = dir_path.stat().st_mtime
                except OSError:
                    continue
                if mtime >= after_time.timestamp():
                    candidates.append((mtime, dir_path))

        if candidates:
            return max(candidates, key=lambda item: item[0])[1]

        # Fallback pass: any matching output, newest wins.
        for root in self.warehouse_search_roots:
            if not root.exists():
                continue
            for dir_path in root.glob(pattern):
                if not dir_path.is_dir():
                    continue
                try:
                    mtime = dir_path.stat().st_mtime
                except OSError:
                    continue
                candidates.append((mtime, dir_path))

        if candidates:
            return max(candidates, key=lambda item: item[0])[1]

        # Final fallback: writable warehouse root.
        return self.warehouse_dir

    def _estimate_token_cost(self, warehouse_path: Path, model: str) -> float:
        """Estimate token cost from generated files."""
        # This is a rough estimate based on generated code size
        # Real token counting would require proper tokenizer

        total_chars = 0
        if warehouse_path.is_file() and warehouse_path.suffix == ".py":
            try:
                total_chars += len(warehouse_path.read_text(encoding="utf-8"))
            except OSError:
                total_chars += 0
        elif warehouse_path.is_dir():
            for py_file in warehouse_path.glob("**/*.py"):
                try:
                    total_chars += len(py_file.read_text(encoding="utf-8"))
                except OSError:
                    continue

        # Rough estimate: 1 token ≈ 4 characters
        tokens = total_chars / 4

        # Model-specific pricing (approximate)
        price_per_1k = {
            "qwen2.5-coder:7b": 0.0,  # Local = free
            "qwen2.5-coder:14b": 0.0,
            "gpt-4": 0.03,  # OpenAI pricing
            "claude-3-opus": 0.015,  # Anthropic pricing
        }

        price = (tokens / 1000) * price_per_1k.get(model, 0.0)
        return price

    # -------------------------------------------------------------------------
    # AbstractGenerator interface methods (for registry compatibility)
    # -------------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "chatdev"

    def is_available(self) -> bool:
        """Check if ChatDev is available and configured."""
        return self.chatdev_path.exists() and self.runner.exists()

    def supports_language(self, language: str) -> bool:
        """ChatDev primarily supports Python."""
        return language.lower() == "python"

    def get_capabilities(self) -> dict:
        """Get provider capabilities."""
        return {
            "supported_languages": ["python"],
            "max_tokens": 100000,  # Multi-agent, no real limit
            "supports_parallel": False,  # Sequential agent conversation
            "cost_per_1k_tokens": 0.0,  # Uses local Ollama
            "requires_api_key": False,
            "local": True,
            "multi_agent": True,
            "default_model": "qwen2.5-coder:14b",
        }
