---
name: repo-smart-search
description:
  Smart-search skill template for repository keyword lookup and ranked results.
---

# Repo Smart Search (skill)

Purpose: quickly run a targeted repository keyword search and return ranked file
hits with short excerpts.

Example (shell):

```bash
python -m src.search.smart_search keyword "<term>" --limit 50 --json > /tmp/search_results.json
jq '.[0:10] | .[] | {path: .path, score: .score, excerpt: .excerpt}' /tmp/search_results.json
```

Integration note: call this skill from an agent when you need zero-token context
before invoking a model.
