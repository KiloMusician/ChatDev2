from __future__ import annotations
import subprocess
import os
import re
from typing import Dict, List
from difflib import SequenceMatcher

TODO_PAT = re.compile(r"\b(TODO|FIXME|XXX)\b", re.IGNORECASE)

def fd(glob: str, root: str=".") -> List[str]:
    try:
        out = subprocess.check_output(["fd", "--hidden", "--glob", glob, root], text=True)
        return [p.strip() for p in out.splitlines() if p.strip()]
    except Exception:
        # Fallback to Python os.walk if fd absent
        results=[]
        glob.replace("**/","").replace("*","")
        for r,_,files in os.walk(root):
            for f in files:
                if f.endswith(tuple([".py",".ts",".tsx",".js",".mjs",".md",".json",".yml"])):
                    results.append(os.path.join(r,f))
        return results

def count_todos(paths: List[str]) -> int:
    n=0
    for p in paths:
        try:
            with open(p,"r",encoding="utf-8",errors="ignore") as f:
                for line in f:
                    if TODO_PAT.search(line): n += 1
        except: pass
    return n

def detect_duplicates(dirpaths: List[str]) -> Dict[str, List[str]]:
    # naive duplicate detector by filename stem
    seen: Dict[str, List[str]] = {}
    for root in dirpaths:
        for r,_,files in os.walk(root):
            for f in files:
                stem = os.path.splitext(f)[0].lower()
                seen.setdefault(stem, []).append(os.path.join(r,f))
    return {k:v for k,v in seen.items() if len(v)>1}

def fuzzy_exists(name: str, search_roots: List[str]) -> bool:
    candidates=[]
    for root in search_roots:
        for r,_,files in os.walk(root):
            for f in files:
                ratio = SequenceMatcher(None, name.lower(), f.lower()).ratio()
                if ratio > 0.85: candidates.append(os.path.join(r,f))
    return len(candidates)>0

def git_dirty_files() -> List[str]:
    try:
        out = subprocess.check_output(["git","status","--porcelain"], text=True)
        return [l.strip().split()[-1] for l in out.splitlines() if l.strip()]
    except Exception:
        return []

def test_command() -> List[str]:
    # adjust for your stack
    if os.path.exists("pytest.ini") or os.path.exists("tests"):
        return ["python","-m","pytest","-q"]
    elif os.path.exists("package.json"):
        return ["npm","test"]
    elif os.path.exists("tools/simbot.mjs"):
        return ["node","tools/simbot.mjs"]
    return ["python","-V"]