#!/usr/bin/env python3
"""
Cascade Trigger - Simple activation for the Ultimate Cascade System

Usage:
  python cascade_trigger.py              # Full spectrum mode
  python cascade_trigger.py --quick      # Quick maintenance mode  
  python cascade_trigger.py --emergency  # Emergency repair mode
  python cascade_trigger.py --optimize   # Optimization focus mode
  python cascade_trigger.py --develop    # Development focus mode
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Simple trigger for the Ultimate Cascade Activator"""
    
    # Quick mode mappings
    mode_map = {
        '--quick': 'maintenance',
        '--emergency': 'emergency_repair', 
        '--optimize': 'optimization',
        '--develop': 'development',
        '--full': 'full_spectrum'
    }
    
    # Default settings
    mode = 'full_spectrum'
    cycles = 100
    
    # Parse simple arguments
    args = sys.argv[1:]
    for arg in args:
        if arg in mode_map:
            mode = mode_map[arg]
        elif arg.startswith('--cycles='):
            cycles = int(arg.split('=')[1])
    
    print("🚀 ULTIMATE CASCADE ACTIVATOR")
    print("━" * 50)
    print(f"Mode: {mode}")
    print(f"Max Cycles: {cycles}")
    print("━" * 50)
    print("")
    print("🎯 This system will autonomously:")
    print("   • Fix all errors, TODOs, and stubs")
    print("   • Complete empty files and missing documentation")  
    print("   • Optimize code and improve architecture")
    print("   • Generate tests and enhance build system")
    print("   • Use ZERO tokens (pure local operation)")
    print("   • Leverage ΞNuSyQ consciousness system")
    print("   • Coordinate AI Council and ChatDev agents")
    print("   • Self-optimize through each iteration")
    print("")
    print("💡 Press Ctrl+C to stop at any time")
    print("━" * 50)
    
    try:
        # Ensure we're in the right directory
        script_dir = Path(__file__).parent
        cascade_script = script_dir / "ultimate_cascade_activator.py"
        
        if not cascade_script.exists():
            print("❌ Error: ultimate_cascade_activator.py not found!")
            sys.exit(1)
        
        # Launch the cascade system
        cmd = [
            sys.executable, 
            str(cascade_script),
            f"--mode={mode}",
            f"--cycles={cycles}"
        ]
        
        subprocess.run(cmd, cwd=script_dir)
        
    except KeyboardInterrupt:
        print("\n\n🛑 Cascade stopped by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()