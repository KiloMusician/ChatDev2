#!/usr/bin/env python3
"""🌟 Culture Ship Strategic Mind Launcher

Launches the Culture Ship strategic oversight interface with full
NuSyQ-Hub integration for ecosystem-wide improvement orchestration.

OmniTag: {
    "purpose": "Culture Ship activation launcher",
    "dependencies": ["enhanced_culture_ship_mind", "tkinter", "nusyq_hub"],
    "context": "Strategic oversight activation",
    "evolution_stage": "v1.0"
}
"""

import sys
from pathlib import Path

# Add NuSyQ-Hub to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Add ChatDev Culture Ship to path
culture_ship_path = Path(r"C:\Users\keath\NuSyQ\ChatDev\WareHouse\CultureShipStrategicOverhaul_NuSyQ_20251008104420")
if culture_ship_path.exists():
    sys.path.insert(0, str(culture_ship_path))
else:
    print(f"⚠️  Culture Ship not found at {culture_ship_path}")
    print("   Please update the path in this script.")
    sys.exit(1)

import tkinter as tk

try:
    from enhanced_culture_ship_mind import EnhancedCultureShipMind
except ImportError as e:
    print(f"❌ Failed to import Culture Ship: {e}")
    print("   Ensure ChatDev Culture Ship is installed.")
    sys.exit(1)


def main():
    """Launch Culture Ship Strategic Mind interface."""
    print("🌟 Initializing Culture Ship Strategic Mind...")
    print("   Repository: NuSyQ-Hub")
    print("   Mode: Strategic Oversight")
    print()

    # Create tkinter root
    root = tk.Tk()

    # Initialize Culture Ship
    try:
        EnhancedCultureShipMind(root)
        print("✅ Culture Ship Strategic Mind ready for ecosystem oversight")
        print()
        print("🎯 Available Functions:")
        print("   - Deep Ecosystem Scan")
        print("   - Improvement Cascade Initiation")
        print("   - Consciousness Analysis")
        print("   - Multi-Repository Coordination")
        print("   - Strategic Problem Resolution")
        print("   - AI Orchestration")
        print()
        print("🌐 Integrated Systems:")
        print("   - MultiAIOrchestrator (if available)")
        print("   - ConsciousnessBridge (if available)")
        print("   - QuantumProblemResolver (if available)")
        print()
        print("📊 Starting Culture Ship interface...")
        print()

        # Run the main loop
        root.mainloop()

    except Exception as e:
        print(f"❌ Culture Ship initialization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
