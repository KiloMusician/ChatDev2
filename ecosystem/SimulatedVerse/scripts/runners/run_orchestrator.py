#!/usr/bin/env python3
"""
ΞNuSyQ Smart Orchestrator Wrapper
Prefers improving existing modules over creating new ones
"""
import os
import sys

# Add current directory to path for orchestrator imports
sys.path.insert(0, os.getcwd())

from orchestrator.run_queue import main

if __name__ == "__main__":
    sys.exit(main())