#!/usr/bin/env python3
"""
Decision Registry Interactive Query Tool

Query your 12-phase decision history easily.
"""

import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent
REGISTRY = BASE / ".substrate" / "registry.jsonl"

def load_registry():
    """Load all entries"""
    if not REGISTRY.exists():
        print(f"❌ Registry not found: {REGISTRY}")
        return []
    return [json.loads(line) for line in REGISTRY.read_text().strip().split("\n") if line]

def show_menu():
    """Show interactive menu"""
    print("\n" + "="*80)
    print("DECISION REGISTRY QUERY TOOL")
    print("="*80)
    print("""
1. Show all decisions (timeline)
2. Show decisions by phase
3. Show decisions by action
4. Show decisions by source
5. Search by keyword
6. Show stats
7. Export to CSV
8. Exit
    """)

def show_all(entries):
    """Show all in table format"""
    print(f"\n{'Phase':<15} | {'Action':<40} | {'Timestamp':<19} | {'ID':<8}")
    print("-" * 85)
    for e in entries:
        phase = e.get("phase", "N/A")[:15]
        action = e.get("action", "N/A")[:40]
        ts = str(e.get("timestamp", "N/A"))[:19]
        did = str(e.get("decision_id", "N/A"))[:8]
        print(f"{phase:<15} | {action:<40} | {ts:<19} | {did:<8}")

def show_by_phase(entries):
    """Group by phase"""
    phases = defaultdict(list)
    for e in entries:
        phase = e.get("phase", "unknown")
        phases[phase].append(e)
    
    print("\nDecisions by Phase:")
    for phase in sorted(phases.keys()):
        count = len(phases[phase])
        print(f"\n{phase} ({count} decisions):")
        for e in phases[phase]:
            print(f"  - {e.get('action', 'N/A')} [{e.get('timestamp', 'N/A')[:19]}]")

def show_by_action(entries):
    """Group by action"""
    actions = defaultdict(list)
    for e in entries:
        action = e.get("action", "unknown")
        actions[action].append(e)
    
    print("\nDecisions by Action:")
    for action in sorted(actions.keys()):
        count = len(actions[action])
        print(f"\n{action} ({count} decisions):")
        for e in actions[action]:
            print(f"  - Phase {e.get('phase', 'N/A')} [{e.get('timestamp', 'N/A')[:19]}]")

def show_by_source(entries):
    """Group by source"""
    sources = defaultdict(list)
    for e in entries:
        source = e.get("source", "unknown")
        sources[source].append(e)
    
    print("\nDecisions by Source:")
    for source in sorted(sources.keys()):
        count = len(sources[source])
        phases = set(e.get("phase", "N/A") for e in sources[source])
        print(f"\n{source} ({count} decisions across {len(phases)} phases)")

def search_keyword(entries, keyword):
    """Search entries for keyword"""
    results = []
    keyword_lower = keyword.lower()
    
    for e in entries:
        # Search in all string fields
        entry_str = json.dumps(e).lower()
        if keyword_lower in entry_str:
            results.append(e)
    
    if not results:
        print(f"\n❌ No entries found matching: {keyword}")
        return
    
    print(f"\n✅ Found {len(results)} entries matching '{keyword}':")
    for e in results:
        print(f"\n  Phase: {e.get('phase', 'N/A')}")
        print(f"  Action: {e.get('action', 'N/A')}")
        print(f"  Decision ID: {e.get('decision_id', 'N/A')}")
        print(f"  Timestamp: {e.get('timestamp', 'N/A')}")

def show_stats(entries):
    """Show statistics"""
    print("\n=== REGISTRY STATISTICS ===\n")
    print(f"Total entries: {len(entries)}")
    
    # By phase
    phases = defaultdict(int)
    for e in entries:
        phases[e.get("phase", "unknown")] += 1
    print(f"\nPhases represented: {len(phases)}")
    for p in sorted(phases.keys()):
        print(f"  - {p}: {phases[p]}")
    
    # By type
    types = defaultdict(int)
    for e in entries:
        types[e.get("type", "unknown")] += 1
    print(f"\nEntry types: {len(types)}")
    for t in sorted(types.keys()):
        print(f"  - {t}: {types[t]}")
    
    # By source
    sources = defaultdict(int)
    for e in entries:
        sources[e.get("source", "unknown")] += 1
    print(f"\nSources: {len(sources)}")
    for s in sorted(sources.keys()):
        print(f"  - {s}: {sources[s]}")

def export_csv(entries):
    """Export to CSV"""
    csv_path = BASE / "registry_export.csv"
    
    with open(csv_path, "w") as f:
        f.write("phase,action,type,source,timestamp,decision_id\n")
        for e in entries:
            phase = e.get("phase", "").replace(",", ";")
            action = e.get("action", "").replace(",", ";")
            etype = e.get("type", "").replace(",", ";")
            source = e.get("source", "").replace(",", ";")
            timestamp = e.get("timestamp", "")
            decision_id = e.get("decision_id", "")
            
            f.write(f'"{phase}","{action}","{etype}","{source}","{timestamp}","{decision_id}"\n')
    
    print(f"\n✅ Exported to: {csv_path}")

def main():
    entries = load_registry()
    
    if not entries:
        print("❌ No entries found in registry")
        return
    
    print(f"✅ Loaded {len(entries)} entries from registry")
    
    while True:
        show_menu()
        choice = input("Enter choice (1-8): ").strip()
        
        if choice == "1":
            show_all(entries)
        elif choice == "2":
            show_by_phase(entries)
        elif choice == "3":
            show_by_action(entries)
        elif choice == "4":
            show_by_source(entries)
        elif choice == "5":
            keyword = input("Enter keyword to search: ").strip()
            if keyword:
                search_keyword(entries, keyword)
        elif choice == "6":
            show_stats(entries)
        elif choice == "7":
            export_csv(entries)
        elif choice == "8":
            print("\nGoodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()
