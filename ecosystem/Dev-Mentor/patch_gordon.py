# Quick patch: Replace the update_strategy method in gordon_player.py

import sqlite3
from pathlib import Path

db_path = Path("state/gordon_memory.db")
db_path.parent.mkdir(exist_ok=True, parents=True)

# Create fresh database with correct schema
with sqlite3.connect(db_path) as conn:
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS strategies")
    cursor.execute("""
        CREATE TABLE strategies (
            id INTEGER PRIMARY KEY,
            pattern TEXT UNIQUE,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            last_used TEXT,
            total_uses INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS memories")
    cursor.execute("""
        CREATE TABLE memories (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            session_id TEXT,
            state_hash TEXT,
            action TEXT,
            result TEXT,
            outcome TEXT,
            learning TEXT,
            model_used TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS npc_interactions")
    cursor.execute("""
        CREATE TABLE npc_interactions (
            id INTEGER PRIMARY KEY,
            npc_name TEXT,
            last_seen TEXT,
            dialog_snippets TEXT,
            relationship_score REAL
        )
    """)
    
    conn.commit()
    print("✓ Gordon memory database initialized with correct schema")

# Now patch the Python file
with open("gordon_player.py", "r") as f:
    lines = f.readlines()

# Find and replace the problematic update_strategy method
new_lines = []
i = 0
while i < len(lines):
    if "def update_strategy(self, pattern: str, succeeded: bool):" in lines[i]:
        # Skip until we find the next method or class
        new_lines.append(lines[i])  # Keep the def line
        i += 1
        # Add docstring
        new_lines.append(lines[i])  # docstring line
        i += 1
        # Add fixed implementation
        new_lines.append("        with sqlite3.connect(self.db_path) as conn:\n")
        new_lines.append("            cursor = conn.cursor()\n")
        new_lines.append("            inc = 1 if succeeded else 0\n")
        new_lines.append("            cursor.execute(\"\"\"\n")
        new_lines.append("                INSERT INTO strategies (pattern, success_count, failure_count, last_used, total_uses)\n")
        new_lines.append("                VALUES (?, ?, ?, ?, 1)\n")
        new_lines.append("                ON CONFLICT(pattern) DO UPDATE SET\n")
        new_lines.append("                    success_count = success_count + ?,\n")
        new_lines.append("                    failure_count = failure_count + ?,\n")
        new_lines.append("                    last_used = ?,\n")
        new_lines.append("                    total_uses = total_uses + 1\n")
        new_lines.append("            \"\"\", (\n")
        new_lines.append("                pattern,\n")
        new_lines.append("                inc,\n")
        new_lines.append("                1 - inc,\n")
        new_lines.append("                str(__import__('datetime').datetime.now()),\n")
        new_lines.append("                inc,\n")
        new_lines.append("                1 - inc,\n")
        new_lines.append("                str(__import__('datetime').datetime.now())\n")
        new_lines.append("            ))\n")
        new_lines.append("            conn.commit()\n")
        # Skip old implementation until next method
        while i < len(lines) and not (lines[i].strip().startswith("def ") or lines[i].strip().startswith("class ")):
            if "conn.commit()" in lines[i]:
                i += 1
                break
            i += 1
    else:
        new_lines.append(lines[i])
        i += 1

with open("gordon_player.py", "w") as f:
    f.writelines(new_lines)

print("✓ gordon_player.py: Fixed update_strategy method")
