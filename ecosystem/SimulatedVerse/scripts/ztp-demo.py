#!/usr/bin/env python3
"""
ZTP Demo - Zero-Token Productivity Protocol Demonstration
"""

import os
import sys

sys.path.append('sidecar')

from bootstrap import BM25, council_route, expand, generate_quests, summarize


def demo_council():
    print("🛡️ SCP Council Decision Engine")
    print("=" * 50)
    
    actions = council_route()
    if not actions:
        print("✅ No council actions required - codebase is clean!")
        return
    
    for action in actions:
        print("\n📋 Rule Triggered:")
        print(f"   Condition: {action['rule']['if']}")
        print(f"   Actions: {', '.join(action['actions'])}")
        print(f"   Files: {', '.join(action['hits'][:3])}{'...' if len(action['hits']) > 3 else ''}")

def demo_search():
    print("\n🔍 BM25 Tokenless Search")
    print("=" * 50)
    
    # Initialize BM25 with current codebase
    import glob
    files = [p for p in glob.glob("**/*.py", recursive=True) if os.path.isfile(p)]
    texts = [open(p, "r", errors="ignore").read() for p in files]
    
    if not texts:
        print("No Python files found to index")
        return
    
    bm = BM25(texts)
    
    # Demo searches
    queries = ["TODO FIXME", "class function", "import json", "SCP Council"]
    
    for query in queries:
        print(f"\n🎯 Query: '{query}'")
        hits = bm.score(query)[:3]
        for score, i in hits:
            if i < len(files):
                snippet = summarize(texts[i], 2)
                print(f"   📄 {files[i]} (score: {score:.2f})")
                print(f"      {snippet[:100]}...")

def demo_templates():
    print("\n📝 Template System")
    print("=" * 50)
    
    # Demo template expansion
    template = "Hello {{Name}}! Welcome to {{Project}} - Faction: {{Faction}}"
    slots = {
        "Name": "Agent",
        "Project": "CoreLink Foundation", 
        "Faction": "⚖️ Council"
    }
    
    result = expand(template, slots)
    print(f"Template: {template}")
    print(f"Result: {result}")

def demo_quests():
    print("\n🎯 Quest System")
    print("=" * 50)
    
    quests = generate_quests()
    if not quests:
        print("✅ No quests available - codebase is in excellent shape!")
        return
    
    for quest in quests:
        print(f"\n🏆 {quest['title']}")
        print(f"   📋 {quest['description']}")
        print(f"   🎁 Reward: {quest['reward']}")
        print(f"   ⚡ Actions: {', '.join(quest['actions'])}")

def main():
    print("🚀 ΣΛΘΦΞ Zero-Token Productivity Protocol Demo")
    print("=" * 60)
    
    demo_council()
    demo_search()
    demo_templates()
    demo_quests()
    
    print("\n" + "=" * 60)
    print("🎉 Demo complete! Run 'python sidecar/ztp_server.py' for web interface.")

if __name__ == "__main__":
    main()