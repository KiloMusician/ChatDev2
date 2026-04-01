import json
entries = [json.loads(line) for line in open(".substrate/registry.jsonl") if line.strip()]
print("\n=== DECISION REGISTRY QUERY ===\n")
for e in entries:
    print(f"{e.get('phase', 'N/A'):15} | {e.get('action', 'N/A'):40} | {e.get('timestamp', 'N/A')[:19]}")
