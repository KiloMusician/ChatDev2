#!/usr/bin/env python3
"""Ecosystem Package Installer
Installs all development and runtime dependencies for NuSyQ-Hub.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Metasynthesis Output System integration
try:
    from src.output.metasynthesis_output_system import (
        ExecutionContext,
        MetasynthesisOutputSystem,
        OperationReceipt,
        OutputTier,
        Signal,
        SignalSeverity,
    )
except ImportError:
    MetasynthesisOutputSystem = None  # type: ignore
    OutputTier = None  # type: ignore
    ExecutionContext = None  # type: ignore
    Signal = None  # type: ignore
    SignalSeverity = None  # type: ignore
    OperationReceipt = None  # type: ignore

# Terminal routing
try:
    from src.output.terminal_router import Channel, emit_route
except ImportError:

    def emit_route(*_args, **_kwargs):  # type: ignore
        return None

    class Channel:  # type: ignore
        TASKS = "TASKS"


REQUIRED_PACKAGES = {
    # Core runtime
    "aiofiles": "Async file I/O",
    "httpx": "Modern HTTP client",
    "pydantic": "Data validation",
    "python-dotenv": "Environment management",
    # Development tools
    "black": "Code formatting",
    "ruff": "Fast linting",
    "mypy": "Static type checking",
    "pytest": "Testing framework",
    "pytest-asyncio": "Async test support",
    "pytest-cov": "Coverage reporting",
    "pytest-watch": "Auto-test on changes",
    # Automation & monitoring
    "watchdog": "File system monitoring",
    "rich": "Terminal formatting",
    "typer": "CLI building",
    # Interactive development
    "ipython": "Enhanced REPL",
    "jupyter": "Notebooks",
    # AI/ML ecosystem
    "openai": "OpenAI API client",
    "anthropic": "Anthropic API client",
}

OPTIONAL_PACKAGES = {
    # Enhanced development
    "ptpython": "Better Python REPL",
    "devtools": "Debug printing",
    "icecream": "Better debugging",
    "beartype": "Runtime type checking",
    # Observability
    "opentelemetry-api": "OpenTelemetry API",
    "opentelemetry-sdk": "OpenTelemetry SDK",
    "opentelemetry-exporter-otlp": "OTLP exporter",
}


def install_packages(packages: dict[str, str], optional: bool = False):
    """Install packages with progress reporting."""
    label = "📦 Optional" if optional else "🔧 Required"
    total = len(packages)

    print(f"\n{label} Packages ({total} total):\n")

    for i, (pkg, desc) in enumerate(packages.items(), 1):
        print(f"  [{i}/{total}] Installing {pkg} ({desc})...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", pkg],
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"    ✅ {pkg} installed")
        except subprocess.CalledProcessError as e:
            if optional:
                print(f"    ⚠️  {pkg} failed (optional, continuing)")
            else:
                print(f"    ❌ {pkg} failed!")
                print(e.stderr)
                return False

    return True


def main():
    """Install ecosystem packages."""
    emit_route(Channel.TASKS, "NuSyQ Ecosystem Package Installer")
    print(
        """
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║          🔧 NuSyQ Ecosystem Package Installer                                 ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
    )

    # Upgrade pip first
    print("📦 Upgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    print("✅ pip upgraded\n")

    # Install required packages
    required_ok = install_packages(REQUIRED_PACKAGES, optional=False)
    if not required_ok:
        print("\n❌ Required package installation failed!")
        return 1

    # Install optional packages
    print("\n" + ("=" * 80))
    optional_ok = install_packages(OPTIONAL_PACKAGES, optional=True)

    print(
        """
╔════════════════════════════════════════════════════════════════════════════════╗
║                                                                                ║
║          ✅ Package Installation Complete!                                    ║
║                                                                                ║
║  Next steps:                                                                  ║
║    • Run tests: pytest tests/ -v                                             ║
║    • Start watcher: python scripts/dev_watcher.py                            ║
║    • Format code: black src/                                                 ║
║    • Lint code: ruff check src/                                              ║
║                                                                                ║
╚════════════════════════════════════════════════════════════════════════════════╝
"""
    )

    # Emit metasynthesis receipt
    try:
        root = Path(__file__).parent.parent
        if MetasynthesisOutputSystem is not None and ExecutionContext is not None and OperationReceipt is not None:
            run_id = f"install_packages_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            system = MetasynthesisOutputSystem(tier=OutputTier.BASIC)
            context = ExecutionContext(
                run_id=run_id,
                agent_id="install_dev_packages",
                branch="unknown",
                python_version=sys.version.split(" ")[0],
                venv_active=(sys.prefix != sys.base_prefix),
                timestamp=datetime.now().isoformat(),
                cwd=str(root),
            )

            signals = [
                Signal(
                    severity=SignalSeverity.SUCCESS if required_ok else SignalSeverity.FAIL,
                    category="[INSTALL]",
                    message="Required packages installation",
                    confidence=0.95,
                ),
                Signal(
                    severity=SignalSeverity.INFO if optional_ok else SignalSeverity.WARN,
                    category="[INSTALL]",
                    message="Optional packages installation",
                    confidence=0.8,
                ),
            ]

            outcome = "✅ Success" if required_ok else "⚠️ Degraded (some installs failed)"
            receipt = OperationReceipt(
                context=context,
                title="Ecosystem Package Installer",
                signals=signals,
                artifacts=[],
                outcome=outcome,
                next_actions=[
                    "Run tests: pytest tests/ -v",
                    "Start watcher: python scripts/dev_watcher.py",
                ],
                guild_implications={"setup": "ready" if required_ok else "partial"},
            )

            state_dir = root / "state" / "receipts"
            state_dir.mkdir(parents=True, exist_ok=True)
            out_path = state_dir / f"{run_id}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(system.render_machine_footer(receipt), f, indent=2)
    except (RuntimeError, OSError):
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
