#!/usr/bin/env python3
# Vacuum-mode deduplication (no external deps)
import os
import hashlib
import json

def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""): 
                h.update(chunk)
        return h.hexdigest()
    except: return None

def main():
    exclude = {".git", "node_modules", ".cache", ".attic", ".quarantine", "models"}
    hash_map = {}
    
    for root, dirs, files in os.walk("."):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in exclude]
        
        for f in files:
            path = os.path.join(root, f)
            try:
                if os.path.getsize(path) < 1_000_000:  # 1MB limit
                    h = sha256_file(path)
                    if h: hash_map.setdefault(h, []).append(path)
            except OSError:
                continue  # Skip broken symlinks
    
    dupes = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    
    os.makedirs("ops/receipts", exist_ok=True)
    with open("ops/receipts/vacuum_dupes.json", "w") as w:
        json.dump(dupes, w, indent=2)
    
    print(f"✅ Found {sum(len(v)-1 for v in dupes.values())} duplicate files")
    print("📋 Receipt: ops/receipts/vacuum_dupes.json")

if __name__ == "__main__": 
    main()