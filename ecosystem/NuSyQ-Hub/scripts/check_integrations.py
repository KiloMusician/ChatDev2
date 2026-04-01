"""Quick integration check script for Ollama, ChatDev, and Copilot

Run this script to get a quick health/status summary for common integrations.
"""

from pathlib import Path

from src.copilot.copilot_workspace_enhancer import CopilotWorkspaceEnhancer
from src.integration.Ollama_Integration_Hub import is_ollama_online


def check_ollama():
    online = is_ollama_online()
    print(f"Ollama Online: {online}")
    return online


def check_copilot(workspace: str = "."):
    enhancer = CopilotWorkspaceEnhancer(Path(workspace))
    try:
        results = enhancer.enhance_workspace()
        print(f"Copilot enhancement success: {results.get('success', False)}")
        return results
    except Exception as e:
        print(f"Copilot enhancement failed: {e}")
        return None


def main():
    print("Checking Ollama...")
    check_ollama()

    print("Checking Copilot enhancement (dry run)...")
    check_copilot(".")


if __name__ == "__main__":
    main()
