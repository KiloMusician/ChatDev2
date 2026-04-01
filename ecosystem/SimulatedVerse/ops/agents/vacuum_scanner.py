#!/usr/bin/env python3
# Vacuum-mode TODO/FIXME scanner (no external deps)
import os
import re
import json

def scan_file(path):
    patterns = [
        r'\b(TODO|FIXME|XXX|HACK|WIP|TBD)\b',
        r'console\.log\(',
        r'print\(',
        r'debugger;?',
        r'throw new Error\(["\']TODO'
    ]
    
    try:
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
            
        issues = []
        for i, line in enumerate(content.split('\n'), 1):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "line": i, 
                        "text": line.strip()[:100],
                        "pattern": pattern
                    })
        return issues
    except: return []

def main():
    exclude = {".git", "node_modules", ".cache", ".attic", ".quarantine"}
    results = {}
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude]
        
        for f in files:
            if f.endswith(('.ts', '.js', '.py', '.gd', '.tsx', '.jsx')):
                path = os.path.join(root, f)
                issues = scan_file(path)
                if issues: results[path] = issues
    
    os.makedirs("ops/receipts", exist_ok=True)
    with open("ops/receipts/vacuum_scan.json", "w") as w:
        json.dump(results, w, indent=2)
    
    total = sum(len(issues) for issues in results.values())
    print(f"✅ Scanned {len(results)} files with {total} issues")
    print("📋 Receipt: ops/receipts/vacuum_scan.json")

if __name__ == "__main__": 
    main()