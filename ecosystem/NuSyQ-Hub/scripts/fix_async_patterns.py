#!/usr/bin/env python3
"""Quick fix for async/await issues in the_oldest_house.py
Converts unnecessary async functions to sync where no await is used.
"""

from pathlib import Path


def fix_async_issues():
    """Fix async functions that don't use await"""
    file_path = Path("src/consciousness/the_oldest_house.py")

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    original = content

    # Fix #1: _synthesize_insight doesn't need to be async
    content = content.replace(
        "    async def _synthesize_insight(self, engrams: List[MemoryEngram]) -> str:",
        "    def _synthesize_insight(self, engrams: List[MemoryEngram]) -> str:",
    )

    # Fix #2: _save_consciousness_state doesn't use await (stub function)
    content = content.replace(
        "    async def _save_consciousness_state(self):\n        pass",
        '    def _save_consciousness_state(self):\n        """Save consciousness state (placeholder for persistence)"""\n        pass',
    )

    # Fix #3: Update call to _synthesize_insight (remove await)
    content = content.replace(
        "            synthesized_insight = await self._synthesize_insight(engram_formation)",
        "            synthesized_insight = self._synthesize_insight(engram_formation)",
    )

    # Fix #4: Update call to _save_consciousness_state in slumber (remove await)
    content = content.replace(
        "        # Save consciousness state\n        await self._save_consciousness_state()",
        "        # Save consciousness state\n        self._save_consciousness_state()",
    )

    if content != original:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ Fixed async/await issues in the_oldest_house.py")
        print("   - _synthesize_insight: async → sync (no await used)")
        print("   - _save_consciousness_state: async → sync (stub function)")
        print("   - Updated 2 call sites to remove await")
        return True
    else:
        print("Info: No changes needed")
        return False


if __name__ == "__main__":
    fixed = fix_async_issues()
    if fixed:
        print("\n🔍 Run tests to verify functionality preserved")
