import json
entries = [json.loads(line) for line in open(".substrate/registry.jsonl") if line.strip()]
print(f"Total entries: {len(entries)}")
print(f"\nLast 10 phases:")
for e in entries[-10:]:
    print(f"  {e.get('phase', 'N/A'):15} | {e.get('action', 'N/A')}")
