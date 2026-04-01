#!/usr/bin/env python
"""Check if CLI commands are implemented."""

with open("nq") as f:
    content = f.read()

# Count command definitions
commands = ["cmd_connector", "cmd_workflow", "cmd_test_loop", "cmd_protocol"]
found = 0
for cmd in commands:
    if f"def {cmd}" in content:
        print(f"✅ {cmd} defined")
        found += 1
    else:
        print(f"❌ {cmd} NOT found")

# Check main() has commands dict
if "'connector'" in content:
    print("✅ 'connector' command registered in dict")
    found += 1
else:
    print("❌ 'connector' command NOT registered")

print(f"\nResult: {found}/5 CLI checks passed")

# Quick line count of nq file
lines = content.count("\n")
print(f"nq file: {lines} lines")
