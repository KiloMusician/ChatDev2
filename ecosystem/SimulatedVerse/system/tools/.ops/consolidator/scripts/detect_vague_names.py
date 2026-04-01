#!/usr/bin/env python3
"""
Helper script for detecting vague file names
"""
import re
import sys

VAGUE = {"util","utils","helper","helpers","common","misc","tmp","new","final","copy","old","backup","index"}

def vague_score(name: str) -> float:
    """Calculate vague score for a filename (0=specific, 1=very vague)"""
    parts = name.replace(".", "/").split("/")
    base = parts[-1].lower()
    tokens = {t for t in re.split(r"[-_\.]", base) if t}
    if not tokens:
        return 1.0
    return len(tokens & VAGUE) / len(tokens)

def main():
    if len(sys.argv) < 2:
        print("Usage: python detect_vague_names.py <file_path>")
        return 1
    
    file_path = sys.argv[1]
    score = vague_score(file_path)
    
    print(f"File: {file_path}")
    print(f"Vague Score: {score:.2f}")
    
    if score > 0.5:
        print("⚠️  This filename is quite vague")
    elif score > 0.3:
        print("💡 This filename could be more specific")
    else:
        print("✅ This filename is appropriately specific")
    
    return 0

if __name__ == "__main__":
    exit(main())