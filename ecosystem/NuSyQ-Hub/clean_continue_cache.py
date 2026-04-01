"""Safely clean Continue.dev cache while preserving configuration.

This script:
1. Backs up config.ts
2. Deletes cache/session files
3. Restores config.ts
4. Provides instructions for reloading VS Code
"""

import shutil
from datetime import datetime
from pathlib import Path


def clean_continue_cache():
    """Clean Continue.dev cache files safely."""
    continue_dir = Path.home() / ".continue"

    if not continue_dir.exists():
        print("❌ Continue.dev directory not found")
        return

    print("🧹 Cleaning Continue.dev cache...")
    print(f"Directory: {continue_dir}")

    # Files to preserve
    preserve_files = ["config.ts", "config.json", ".continuerc.json"]

    # Create backup
    backup_dir = continue_dir / "backup_before_clean"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = continue_dir / f"backup_{timestamp}"

    print(f"\n📦 Creating backup at: {backup_dir}")
    backup_dir.mkdir(exist_ok=True)

    # Backup config files
    for preserve_file in preserve_files:
        file_path = continue_dir / preserve_file
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / preserve_file)
            print(f"  ✅ Backed up: {preserve_file}")

    # Files/directories to delete
    cache_patterns = ["dev_data", "index", "sessions", "*.sqlite", "*.db", "*.log", ".cache"]

    deleted_count = 0
    print("\n🗑️  Deleting cache files...")

    for item in continue_dir.iterdir():
        # Skip preserved files
        if item.name in preserve_files:
            print(f"  ⏭️  Skipping: {item.name}")
            continue

        # Skip backup directory
        if item.name.startswith("backup_"):
            continue

        # Delete cache files/directories
        should_delete = False
        for pattern in cache_patterns:
            if pattern.startswith("*"):
                # Wildcard pattern
                if item.name.endswith(pattern[1:]):
                    should_delete = True
            elif item.name.startswith(pattern) or item.name == pattern:
                should_delete = True

        if should_delete:
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"  🗑️  Deleted directory: {item.name}")
                else:
                    item.unlink()
                    print(f"  🗑️  Deleted file: {item.name}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {item.name}: {e}")

    print(f"\n✅ Cleanup complete! Deleted {deleted_count} items")
    print(f"📦 Backup saved at: {backup_dir}")

    # Next steps
    print("\n" + "=" * 80)
    print("NEXT STEPS TO FIX 'WONKY OUTPUT'")
    print("=" * 80)
    print("\n1. RELOAD VS CODE WINDOW")
    print("   a. Press: Ctrl+Shift+P")
    print("   b. Type: 'Developer: Reload Window'")
    print("   c. Press: Enter")
    print("   → This forces Continue.dev to rebuild its cache")

    print("\n2. TEST CONTINUE.DEV AGAIN")
    print("   a. Open Continue.dev chat (Ctrl+L)")
    print("   b. Try a simple prompt: 'Write a Python hello world function'")
    print("   c. Check if output quality improved")

    print("\n3. IF STILL WONKY:")
    print("   a. Check VS Code Output panel:")
    print("      - View → Output")
    print("      - Select 'Continue' from dropdown")
    print("   b. Look for error messages")
    print("   c. Try different model (starcoder2:15b instead of qwen2.5-coder)")

    print("\n4. STREAMING vs NON-STREAMING ISSUE")
    print("   → Investigation found 217-char discrepancy")
    print("   → May need to update Continue.dev extension")
    print("   → Or adjust model parameters in config.ts")

    print("\n5. IF PROBLEM PERSISTS:")
    print("   a. Update Continue.dev extension:")
    print("      - Extensions → Continue.dev → Update")
    print("   b. Check for VS Code updates")
    print("   c. Restart Ollama service:")
    print("      - In PowerShell: ollama serve")

    print("\n" + "=" * 80)
    print(f"✅ Cache cleaned! Backup at: {backup_dir}")
    print("=" * 80)


if __name__ == "__main__":
    clean_continue_cache()
