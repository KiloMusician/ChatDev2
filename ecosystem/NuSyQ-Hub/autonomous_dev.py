#!/usr/bin/env python3
"""Quick launcher for Autonomous Development Agent.

Usage:
    python autonomous_dev.py                    # Interactive mode
    python autonomous_dev.py game "snake game"  # Generate game
    python autonomous_dev.py webapp "dashboard" # Generate web app
    python autonomous_dev.py package "my_lib"   # Create package
    python autonomous_dev.py debug              # Debug system
    python autonomous_dev.py status             # Show status
"""

import asyncio
import sys

from src.agents.autonomous_development_agent import AutonomousDevelopmentAgent


async def main() -> None:
    """Main entry point for autonomous development."""
    agent = AutonomousDevelopmentAgent()

    # Initialize systems
    print("🤖 Initializing Autonomous Development Agent...")
    initialized = await agent.initialize_systems()

    if not initialized:
        print("❌ Failed to initialize systems")
        return

    print("\n✅ All systems ready!")

    # Parse command
    if len(sys.argv) < 2:
        # Interactive mode
        print("\n" + "=" * 60)
        print("AUTONOMOUS DEVELOPMENT AGENT")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  game <description>    - Generate a game")
        print("  webapp <description>  - Generate a web app")
        print("  package <name>        - Create a Python package")
        print("  debug                 - Debug the system")
        print("  status                - Show system status")
        print("\nExample:")
        print('  python autonomous_dev.py game "snake game with power-ups"')
        print("\nStatus:")
        status = agent.get_status()
        print(f"  AI Models: {status['models_available']}")
        print(f"  Active Projects: {status['active_projects']}")
        print(f"  Multi-Agent: {'✅' if status['capabilities']['multi_agent'] else '❌'}")
        print(f"  Docker: {'✅' if status['capabilities']['docker'] else '❌'}")
        return

    command = sys.argv[1].lower()

    if command == "game":
        if len(sys.argv) < 3:
            print('❌ Usage: python autonomous_dev.py game "<description>"')
            return

        description = " ".join(sys.argv[2:])
        print(f"\n🎮 Generating game: {description}")
        result = await agent.generate_game(description)
        print(f"\n✅ Project initialized: {result['project_id']}")
        print(f"📁 Output directory: {result['project_dir']}")
        print(f"👥 Agents deployed: {len(result['agents'])}")

    elif command == "webapp":
        if len(sys.argv) < 3:
            print('❌ Usage: python autonomous_dev.py webapp "<description>"')
            return

        description = " ".join(sys.argv[2:])
        print(f"\n🌐 Generating web app: {description}")
        result = await agent.generate_web_app(description)
        print(f"\n✅ Project initialized: {result['project_id']}")
        print(f"📁 Output directory: {result['project_dir']}")
        print(f"👥 Agents deployed: {len(result['agents'])}")

    elif command == "package":
        if len(sys.argv) < 3:
            print("❌ Usage: python autonomous_dev.py package <name> [description]")
            return

        name = sys.argv[2]
        functionality = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "General purpose library"
        print(f"\n📦 Creating package: {name}")
        result = await agent.create_package(name, functionality)
        print(f"\n✅ Project initialized: {result['project_id']}")
        print(f"📁 Output directory: {result['project_dir']}")
        print(f"👥 Agents deployed: {len(result['agents'])}")

    elif command == "debug":
        print("\n🐛 Running system diagnostics...")
        result = await agent.debug_system()
        print("\n✅ Debug complete")
        print(f"Target: {result['target']}")

    elif command == "status":
        status = agent.get_status()
        print("\n" + "=" * 60)
        print("SYSTEM STATUS")
        print("=" * 60)
        print(f"\nTimestamp: {status['timestamp']}")
        print("\nSystems:")
        for system, online in status["systems"].items():
            print(f"  {system}: {'✅' if online else '❌'}")
        print(f"\nProjects: {status['active_projects']} active")
        print(f"Agent Team: {status['agent_team_size']} agents")
        print(f"AI Models: {status['models_available']} available")
        print("\nCapabilities:")
        for cap, enabled in status["capabilities"].items():
            print(f"  {cap}: {'✅' if enabled else '❌'}")

    else:
        print(f"❌ Unknown command: {command}")
        print("Available: game, webapp, package, debug, status")


if __name__ == "__main__":
    asyncio.run(main())
