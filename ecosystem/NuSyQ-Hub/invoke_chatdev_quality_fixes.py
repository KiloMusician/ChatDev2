#!/usr/bin/env python3
"""ChatDev Code Quality Fixer for NuSyQ-Hub
Invokes ChatDev multi-agent team to systematically fix code quality issues
"""

import os
import subprocess
import sys


def resolve_chatdev_path() -> str:
    env_chatdev = os.environ.get("CHATDEV_PATH")
    if env_chatdev:
        return os.path.abspath(env_chatdev)

    nusyq_root = os.environ.get("NUSYQ_ROOT_PATH")
    if nusyq_root:
        return os.path.abspath(os.path.join(nusyq_root, "ChatDev"))

    return os.path.abspath(os.path.join(os.path.expanduser("~"), "NuSyQ", "ChatDev"))


CHATDEV_PATH = resolve_chatdev_path()

if not os.path.exists(CHATDEV_PATH):
    print(f"ERROR: ChatDev not found at {CHATDEV_PATH}")
    sys.exit(1)

# Task specification for ChatDev
TASK = """Fix code quality issues in NuSyQ-Hub:
1. Replace 50+ broad 'except Exception' handlers with specific exception types
   (FileNotFoundError, ImportError, ConnectionError, JSONDecodeError, etc)
2. Add encoding='utf-8' to all open() calls (30+ instances)
3. Remove 20+ unused imports
4. Remove 10+ unused variables
5. Fix whitespace issues around operators and slice notation

Reference the error patterns from get_errors tool and the detailed specification
in docs/CHATDEV_CODE_QUALITY_TASK.md"""

PROJECT_NAME = "NuSyQ_CodeQuality_Fixes_Phase1"
MODEL = "qwen2.5-coder:14b"

# Run ChatDev
cmd = [
    sys.executable,
    os.path.join(CHATDEV_PATH, "run_ollama.py"),
    "--task",
    TASK,
    "--name",
    PROJECT_NAME,
    "--model",
    MODEL,
]

print(f"🚀 Invoking ChatDev from: {CHATDEV_PATH}")
print("📋 Task: Code Quality Fixes for NuSyQ-Hub")
print(f"🤖 Model: {MODEL}")
print(f"📁 Project: {PROJECT_NAME}")
print("")

os.chdir(CHATDEV_PATH)
result = subprocess.run(cmd)
sys.exit(result.returncode)
