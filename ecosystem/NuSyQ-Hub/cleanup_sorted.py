#!/usr/bin/env python3
"""Remove redundant list() calls from sorted() in systems.py"""

with open("src/api/systems.py") as f:
    content = f.read()

# Replace redundant list() calls
content = content.replace("sorted(list(all_achievements))", "sorted(all_achievements)")
content = content.replace("sorted(list(all_features))", "sorted(all_features)")

with open("src/api/systems.py", "w") as f:
    f.write(content)

print("✅ Removed redundant list() calls")
