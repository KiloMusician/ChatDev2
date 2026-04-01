#!/usr/bin/env python3
"""
ΞNuSyQ Duplicate & Naming Consolidation - Entry Point
Safe surgical mode for repository cleanup
"""
import os
import sys

# Add .ops to path for consolidator imports
sys.path.insert(0, os.path.join(os.getcwd(), ".ops"))

from consolidator.main import main

if __name__ == "__main__":
    sys.exit(main())