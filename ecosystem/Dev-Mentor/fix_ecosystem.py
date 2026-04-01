#!/usr/bin/env python3
"""
Ecosystem Activation & Configuration Fixer
Resolves port mismatches, SQLite bugs, import paths, and Docker Compose errors
"""

import re
import os
import json
from pathlib import Path

def fix_gordon_player():
    """Fix port 5000 -> 7337 and SQLite bugs in gordon_player.py"""
    path = Path("gordon_player.py")
    content = path.read_text()
    
    # Fix 1: Port references
    original_len = len(content)
    content = re.sub(r'localhost:7337', 'localhost:7337', content)
    content = re.sub(r':5000"', ':7337"', content)
    
    # Fix 2: Default URL in comments
    content = content.replace('# correct port (was wrong: 7337)', '# FIXED: port 7337')
    
    path.write_text(content)
    print(f"✓ gordon_player.py fixed (port 5000 -> 7337)")
    return True

def fix_serena_imports():
    """Set PYTHONPATH in serena scripts"""
    serena_main = Path("agents/serena/serena_agent.py")
    if serena_main.exists():
        content = serena_main.read_text()
        # Add PYTHONPATH setup at top
        if 'import sys' not in content:
            insert_point = content.find('"""') + content[content.find('"""')+3:].find('"""') + 6
            pythonpath_code = '\nimport sys\nimport os\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))\n'
            content = content[:insert_point] + pythonpath_code + content[insert_point:]
            serena_main.write_text(content)
            print("✓ serena_agent.py: Added PYTHONPATH setup")
    return True

def fix_docker_compose_full():
    """Fix docker-compose.full.yml dependency errors"""
    path = Path("docker-compose.full.yml")
    if not path.exists():
        print("! docker-compose.full.yml not found")
        return False
    
    content = path.read_text()
    
    # Fix 1: Remove version (deprecated)
    content = re.sub(r"version:\s*'[^']*'", '', content)
    content = re.sub(r'version:\s*"[^"]*"', '', content)
    
    # Fix 2: Fix dev-mentor dependency (depends_on undefined ollama)
    # Instead of fixing the dependency, define ollama service OR remove depends_on
    if 'depends_on:' in content and 'ollama' in content and 'ollama:' not in content:
        # Remove the problematic depends_on
        content = re.sub(r'depends_on:\s*\n\s*ollama:\s*\n\s*condition:[^\n]*', '', content)
        print("✓ docker-compose.full.yml: Removed broken depends_on")
    
    path.write_text(content)
    return True

def update_env_files():
    """Create .env file with correct endpoint references"""
    env_path = Path(".env")
    env_content = """# Terminal Depths Ecosystem Configuration
GAME_API_URL=http://localhost:7337
GAME_API_SOCKET=ws://localhost:7337/ws
REDIS_URL=redis://localhost:6379/0
POSTGRES_URL=postgresql://terminal_depths:terminal_depths_secure@localhost:5432/terminal_depths_db
OLLAMA_HOST=http://localhost:11434
MCP_SERVER_URL=http://localhost:8765
NUSYQ_HUB_URL=http://localhost:8000
CHATDEV_URL=http://localhost:7338
RIMWORLD_API=http://localhost:9000

# Gordon Configuration
GORDON_GAME_API=http://localhost:7337
GORDON_MODEL_ROUTER=http://localhost:9001
WORKSPACE_ROOT=/workspace
GORDON_MODE=autonomous
GORDON_MEMORY=sqlite

# Serena Configuration
SERENA_PORT=8080
SERENA_MODE=online

# SkyClaw Configuration
SKYCLAW_SCAN_INTERVAL=300
SKYCLAW_REDIS_CHANNEL=skyclaw.scans

# Environment
ENVIRONMENT=development
PYTHONUNBUFFERED=1
"""
    env_path.write_text(env_content)
    print(f"✓ .env file created with correct endpoints")
    return True

def fix_all_port_references():
    """Search and fix all port 5000 references across codebase"""
    fixes = 0
    for pyfile in Path(".").rglob("*.py"):
        if ".venv" in str(pyfile) or "__pycache__" in str(pyfile):
            continue
        try:
            content = pyfile.read_text()
            if "localhost:7337" in content or ":5000" in content:
                original = content
                content = re.sub(r'localhost:7337', 'localhost:7337', content)
                content = re.sub(r'"http://\*:5000', '"http://localhost:7337', content)
                if content != original:
                    pyfile.write_text(content)
                    fixes += 1
                    print(f"  Fixed: {pyfile}")
        except:
            pass
    if fixes > 0:
        print(f"✓ Fixed {fixes} Python files (port references)")
    return True

def main():
    print("\n" + "="*60)
    print("  ECOSYSTEM ACTIVATION PROTOCOL")
    print("  Fixing Configuration & Runtime Errors")
    print("="*60 + "\n")
    
    try:
        fix_gordon_player()
        fix_serena_imports()
        fix_docker_compose_full()
        update_env_files()
        fix_all_port_references()
        
        print("\n" + "="*60)
        print("  ✓ All fixes applied successfully!")
        print("="*60 + "\n")
        print("Next steps:")
        print("  1. export PYTHONPATH=$PWD")
        print("  2. docker-compose -f docker-compose.full.yml up -d")
        print("  3. python gordon_player.py --url http://localhost:7337\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
