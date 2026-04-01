#!/usr/bin/env python3
"""Quick test of game pipeline during audit"""

from src.game_development.zeta21_game_pipeline import GameDevPipeline

print("=" * 60)
print("GAME PIPELINE AUDIT TEST")
print("=" * 60)

p = GameDevPipeline(workspace_path='.')
print("\n✓ Pipeline initialized")
print(f"  PyGame: {p.pygame_available}")
print(f"  Arcade: {p.arcade_available}")

# Test AI idea generation
print("\n📚 Testing AI idea generation...")
try:
    idea = p.generate_ai_game_idea("puzzle")
    print(f"✓ Generated idea: {idea['title']}")
    print(f"  Framework: {idea['suggested_framework']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test game creation
print("\n🎮 Testing game project creation...")
try:
    result = p.create_new_game_project('test_audit_game', framework='pygame', template='basic')
    print("✓ Game created successfully")
    if isinstance(result, dict):
        print(f"  Result keys: {list(result.keys())}")
        for key, val in result.items():
            if not isinstance(val, (dict, list)):
                print(f"    {key}: {val}")
    else:
        print(f"  Result: {result}")
except FileExistsError:
    print("⚠️ Game already exists, skipping creation")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
