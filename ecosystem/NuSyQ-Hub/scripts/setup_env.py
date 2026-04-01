# Unified Environment Setup for NuSyQ-Hub
# Usage: python scripts/setup_env.py

import os
import subprocess
import sys
from pathlib import Path

VENV_PATH = Path(".venv")
REQ_PATH = Path("requirements.txt")

if not VENV_PATH.exists():
    print("Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_PATH)])
else:
    print("Virtual environment already exists.")

pip_path = VENV_PATH / ("Scripts/pip.exe" if os.name == "nt" else "bin/pip")

if REQ_PATH.exists():
    print("Installing dependencies from requirements.txt...")
    subprocess.check_call([str(pip_path), "install", "-r", str(REQ_PATH)])
else:
    print("requirements.txt not found!")

print("Environment setup complete.")
