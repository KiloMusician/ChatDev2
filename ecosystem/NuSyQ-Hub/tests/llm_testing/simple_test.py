#!/usr/bin/env python3
"""Simple test to check what's actually working.

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["LLM", "Python", "AI", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import os
import subprocess
import sys
from pathlib import Path


def run_simple_llm_system_check() -> dict[str, object]:
    """Run lightweight environment checks without side effects at import time."""
    report: dict[str, object] = {
        "python_available": False,
        "ollama_available": False,
        "chatdev_path_exists": False,
        "files": {},
    }

    print("🔬 SIMPLE LLM SYSTEM TEST")
    print("=" * 40)

    # Test 1: Python
    try:
        print(f"✅ Python {sys.version}")
        report["python_available"] = True
    except Exception as e:
        print(f"❌ Python error: {e}")

    # Test 2: Ollama
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Ollama: {result.stdout.strip()}")
            report["ollama_available"] = True
        else:
            print("❌ Ollama not working")
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        print(f"❌ Ollama not found: {e}")

    # Test 3: ChatDev path discovery across likely local locations.
    chatdev_candidates = [
        os.getenv("CHATDEV_PATH"),
        "/mnt/c/Users/keath/NuSyQ/ChatDev",
        "C:/Users/keath/NuSyQ/ChatDev",
        "C:/Users/malik/Desktop/ChatDev_CORE/ChatDev-main",
    ]
    discovered_chatdev = next(
        (candidate for candidate in chatdev_candidates if candidate and Path(candidate).exists()),
        None,
    )
    if discovered_chatdev:
        print(f"✅ ChatDev directory exists: {discovered_chatdev}")
        report["chatdev_path_exists"] = True
    else:
        print("❌ ChatDev directory missing")

    # Test 4: Local source files.
    repo_root = Path(__file__).resolve().parents[2]
    our_files = [
        repo_root / "src" / "integration" / "chatdev_llm_adapter.py",
        repo_root / "src" / "ai" / "ollama_chatdev_integrator.py",
    ]

    file_report: dict[str, bool] = {}
    for file in our_files:
        exists = file.exists()
        file_report[str(file)] = exists
        if exists:
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    report["files"] = file_report

    print("\n🧐 VERDICT: Check results above")
    return report


def test_simple_llm_system_smoke() -> None:
    """Ensure diagnostic script runs safely under pytest collection/execution."""
    report = run_simple_llm_system_check()
    assert report["python_available"] is True
    assert isinstance(report["files"], dict)


if __name__ == "__main__":
    run_simple_llm_system_check()
