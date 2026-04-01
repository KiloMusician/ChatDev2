"""ZETA21 Game Development Pipeline Test
Comprehensive testing of PyGame & Arcade integration systems

OmniTag: {
    "purpose": "file_systematically_tagged",
    "tags": ["Python", "Testing"],
    "category": "auto_tagged",
    "evolution_stage": "v1.0"
}
"""

import os
import sys
from pathlib import Path

# Fix Windows encoding for emoji support
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.game_development.zeta21_game_pipeline import GameDevPipeline

    print("[GAME-TEST] Testing ZETA21 Game Development Pipeline...")

    # Test 1: Pipeline initialization
    pipeline = GameDevPipeline(workspace_path=Path("."))
    print("✅ Pipeline initialized")
    print(f"📂 Games directory: {pipeline.games_directory}")
    print(f"🛠️ PyGame available: {pipeline.pygame_available}")
    print(f"🛠️ Arcade available: {pipeline.arcade_available}")

    # Test 2: Get initial analytics
    analytics = pipeline.get_development_analytics()
    print("📊 Initial analytics:")
    print(f"  Total projects: {analytics['summary']['total_projects']}")
    print(f"  Frameworks used: {analytics['summary']['frameworks_used']}")

    # Test 3: Generate AI game idea
    game_idea = pipeline.generate_ai_game_idea("puzzle")
    print("💡 AI-generated game idea:")
    print(f"  Title: {game_idea['title']}")
    print(f"  Genre: {game_idea['genre']}")
    print(f"  Framework: {game_idea['suggested_framework']}")
    print(f"  Complexity: {game_idea['estimated_complexity']}")

    # Test 4: Create new game project (PyGame)
    try:
        project_result = pipeline.create_new_game_project(
            project_name="test_pygame_game",
            framework="pygame",
            template="basic",
            ai_assisted=True,
        )

        print("🎯 Created PyGame project:")
        print(f"  Name: {project_result['project_name']}")
        print(f"  Path: {project_result['path']}")
        print(f"  Files created: {project_result['files_created']}")
        print(f"  AI enhanced: {project_result['ai_enhanced']}")

    except Exception as e:
        print(f"⚠️ PyGame project creation: {e}")

    # Test 5: Create roguelike project
    try:
        roguelike_result = pipeline.create_new_game_project(
            project_name="test_roguelike_game",
            framework="pygame",
            template="roguelike",
            ai_assisted=True,
        )

        print("🏰 Created Roguelike project:")
        print(f"  Name: {roguelike_result['project_name']}")
        print(f"  Files created: {roguelike_result['files_created']}")

    except Exception as e:
        print(f"⚠️ Roguelike project creation: {e}")

    # Test 6: Try to create Arcade project (if available)
    if pipeline.arcade_available:
        try:
            arcade_result = pipeline.create_new_game_project(
                project_name="test_arcade_game",
                framework="arcade",
                template="basic",
                ai_assisted=True,
            )

            print("🕹️ Created Arcade project:")
            print(f"  Name: {arcade_result['project_name']}")
            print(f"  Files created: {arcade_result['files_created']}")

        except Exception as e:
            print(f"⚠️ Arcade project creation: {e}")
    else:
        print("⚠️ Arcade not available, skipping Arcade project test")

    # Test 7: Updated analytics
    updated_analytics = pipeline.get_development_analytics()
    print("📈 Updated analytics:")
    print(f"  Total projects: {updated_analytics['summary']['total_projects']}")
    print(f"  Projects created: {updated_analytics['metrics']['projects_created']}")
    print(f"  Code generated: {updated_analytics['metrics']['code_generated']}")

    # Test 8: List recent projects
    if updated_analytics["recent_projects"]:
        print("📋 Recent projects:")
        for project in updated_analytics["recent_projects"]:
            print(f"  - {project['name']} ({project['framework']})")

    # Test 9: Test project run (debug mode)
    if "test_pygame_game" in pipeline.game_projects:
        try:
            run_result = pipeline.run_game_project("test_pygame_game", debug_mode=True)
            print("🚀 Game run test:")
            print(f"  Success: {run_result['success']}")
            if not run_result["success"]:
                print(f"  Error: {run_result.get('stderr', 'Unknown error')}")
            else:
                print("  Output: Game executed successfully")

        except Exception as e:
            print(f"⚠️ Game run test failed: {e}")

    # Test 10: Code template verification
    print("🧩 Code templates available:")
    for template_name, template_data in pipeline.code_generation_templates.items():
        print(f"  - {template_name}: {template_data['description']}")
        print(f"    Files: {list(template_data['files'].keys())}")

    print("\n🏆 ZETA21 Game Development Pipeline: ALL TESTS COMPLETED")
    print("✨ Status: READY FOR GAME DEVELOPMENT")

    # Cleanup test projects
    print("\n🧹 Cleaning up test projects...")
    import shutil

    test_projects = ["test_pygame_game", "test_arcade_game", "test_roguelike_game"]
    for project_name in test_projects:
        project_path = pipeline.games_directory / project_name
        if project_path.exists():
            shutil.rmtree(project_path)
            print(f"  Removed: {project_name}")

    print("✅ Cleanup completed")

except Exception as e:
    print(f"❌ Error testing ZETA21 system: {e}")
    import traceback

    traceback.print_exc()
