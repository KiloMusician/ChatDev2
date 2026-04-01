"""ChatDev Integration Setup Script.

Sets up ChatDev to work with KILO-FOOLISH offline LLMs and secure API fallback.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

# Add our src to path
sys.path.append(str(Path(__file__).parent / "src"))


async def main() -> None:
    # Add output deduplication to prevent repeated messages
    last_output = None

    def dedupe_print(message) -> None:
        nonlocal last_output
        if message != last_output:
            last_output = message

    dedupe_print("🚀 CHATDEV + KILO-FOOLISH INTEGRATION SETUP")
    dedupe_print("=" * 60)

    # Step 1: Check if ChatDev is installed
    dedupe_print("📦 Checking ChatDev installation...")
    try:
        import importlib.util

        if importlib.util.find_spec("chatdev") is not None:
            dedupe_print("✅ ChatDev is installed")
        else:
            raise ImportError("ChatDev not found")
    except ImportError:
        dedupe_print("❌ ChatDev not found. Installing...")
        try:
            from src.utils.safe_subprocess import safe_subprocess

            safe_subprocess.run([sys.executable, "-m", "pip", "install", "chatdev"], check=True)
            dedupe_print("✅ ChatDev installed successfully")
        except subprocess.CalledProcessError:
            dedupe_print("❌ Failed to install ChatDev")
            return

    # Step 2: Setup our integration
    try:
        from integration.chatdev_environment_patcher import \
            patch_chatdev_for_kilo_foolish
        from integration.chatdev_llm_adapter import setup_chatdev_integration

        # Initialize adapter
        adapter = await setup_chatdev_integration()

        # Apply patches
        await patch_chatdev_for_kilo_foolish()

        # Test the integration
        await adapter.process_chatdev_request(
            "Programmer",
            "Write a simple Hello World function in Python",
            {"test_mode": True},
        )

        # Get status
        status = adapter.get_chatdev_integration_status()

        # Show available models for each role
        for role in adapter.role_model_mapping:
            status["model_availability"].get(role, False)

    except (ImportError, RuntimeError, AttributeError, ValueError):
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
