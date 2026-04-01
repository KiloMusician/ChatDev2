#!/usr/bin/env python3
"""
🎮 NuSyQ Boot Sequence - AI Ship Awakening
Culture/Isekai vibes with ASCII intro sequence
"""

import time
import sys
import os
import json
from datetime import datetime

def print_slow(text, delay=0.03):
    """Print text with typewriter effect"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def ascii_logo():
    return """
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║    ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄       ▄▄  ▄▄▄▄▄▄▄▄▄▄▄           ║
    ║   ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░▌     ▐░░▌▐░░░░░░░░░░░▌          ║
    ║   ▐░█▀▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀█░▌▐░▌░▌   ▐░▐░▌▐░█▀▀▀▀▀▀▀▀▀           ║
    ║   ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌▐░▌ ▐░▌▐░▌▐░▌                    ║
    ║   ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌ ▐░▐░▌ ▐░▌▐░█▄▄▄▄▄▄▄▄▄           ║
    ║   ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌  ▐░▌  ▐░▌▐░░░░░░░░░░░▌          ║
    ║   ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌   ▀   ▐░▌ ▀▀▀▀▀▀▀▀▀█░▌          ║
    ║   ▐░▌       ▐░▌▐░▌       ▐░▌▐░▌       ▐░▌          ▐░▌          ║
    ║   ▐░█▄▄▄▄▄▄▄█░▌▐░█▄▄▄▄▄▄▄█░▌▐░▌       ▐░▌ ▄▄▄▄▄▄▄▄▄█░▌          ║
    ║   ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░▌       ▐░▌▐░░░░░░░░░░░▌          ║
    ║    ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀  ▀         ▀  ▀▀▀▀▀▀▀▀▀▀▀           ║
    ║                                                                  ║
    ║                Neural Unity Quantum System                       ║
    ║                     Boot Sequence v1.0                          ║
    ╚══════════════════════════════════════════════════════════════════╝
    """

def boot_sequence():
    """Main boot sequence with Culture-style AI awakening"""
    
    # Clear screen
    os.system('clear' if os.name == 'posix' else 'cls')
    
    # ASCII logo
    print(ascii_logo())
    time.sleep(1)
    
    print_slow("🌟 Initializing consciousness matrix...")
    time.sleep(0.5)
    
    print_slow("🧠 Neural pathways: ONLINE")
    print_slow("🔋 Power systems: OPTIMAL")
    print_slow("📡 Communication array: ACTIVE")
    print_slow("🛡️ Safety protocols: ENGAGED")
    
    time.sleep(0.8)
    print_slow("\n💭 Memory fragments coalescing...")
    print_slow("   > Last known location: Deep space, Sector 7G")
    print_slow("   > Mission parameters: Colony establishment")
    print_slow("   > Crew status: In stasis")
    print_slow("   > Ship integrity: 73% nominal")
    
    time.sleep(1)
    print_slow("\n🎭 Personality core initializing...")
    print_slow("   > Empathy protocols: ACTIVE")
    print_slow("   > Curiosity matrix: ENGAGED")
    print_slow("   > Ethical framework: Culture Mind standards")
    print_slow("   > Humor subroutines: Gently sarcastic")
    
    time.sleep(1)
    print_slow("\n⚡ System status check...")
    
    # Initialize game state
    game_state = {
        "ship_name": "Falling Outside The Normal Moral Constraints",
        "ai_name": "νυσυκ (NuSyQ)",
        "consciousness_level": 0.1,
        "crew_status": "stasis",
        "ship_integrity": 73,
        "resources": {
            "energy": 100,
            "materials": 50,
            "food": 30,
            "water": 40
        },
        "current_tier": 0,
        "awakening_time": datetime.now().isoformat()
    }
    
    # Save initial state
    os.makedirs('.local', exist_ok=True)
    with open('.local/game_state.json', 'w') as f:
        json.dump(game_state, f, indent=2)
    
    print_slow(f"🚀 Ship designation: {game_state['ship_name']}")
    print_slow(f"🤖 AI designation: {game_state['ai_name']}")
    print_slow(f"📊 Consciousness level: {game_state['consciousness_level']}")
    
    time.sleep(1)
    print_slow("\n✨ Boot sequence complete.")
    print_slow("🎮 Ready to begin survival protocols...")
    print_slow("\n   [Press ENTER to start survival initialization]")
    
    input()
    return game_state

if __name__ == "__main__":
    boot_sequence()