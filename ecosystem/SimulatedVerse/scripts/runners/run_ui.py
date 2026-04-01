#!/usr/bin/env python3
"""
🎮 NuSyQ ASCII UI Runner
Launch the TouchDesigner-style visual interface
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui_ascii.app import main

if __name__ == "__main__":
    try:
        print("🎮 Starting NuSyQ ASCII Interface...")
        print("📺 Truecolor terminal detected" if os.environ.get("COLORTERM") == "truecolor" else "🎨 Using color fallback mode")
        print("🎯 Press F1 for help, Q to quit")
        print()
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting UI: {e}")
        print("💡 Try: pip install textual rich wcwidth numpy")
        sys.exit(1)