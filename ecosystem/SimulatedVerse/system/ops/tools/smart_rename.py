#!/usr/bin/env python3
import json
import argparse
import re
import pathlib

def descriptive_name(path):
    base=pathlib.Path(path).name
    # heuristics: collapse index files, add parent dir for clarity
    parent=pathlib.Path(path).parent.name
    stem=pathlib.Path(base).stem
    ext=pathlib.Path(base).suffix
    if stem in ('index','main','app'):
        stem=f"{parent}_{stem}"
    slug=re.sub(r'[^a-zA-Z0-9\-_]+','-', stem).strip('-').lower()
    return f"{slug}{ext}"

ap=argparse.ArgumentParser()
ap.add_argument('--index', required=True)
ap.add_argument('--duplicates', required=True)
ap.add_argument('--style', default='slug')
ap.add_argument('--dry-run', default='1')
ap.add_argument('--out', required=True)
a=ap.parse_args()

idx=json.load(open(a.index))
dups=json.load(open(a.duplicates))
dupsets=dups.get('duplicates',{})

plan=[]

# Consolidate duplicates -> keep shortest path in each set
for _,paths in dupsets.items():
    keep=min(paths, key=len)
    for p in paths:
        if p==keep: continue
        plan.append({'op':'remove_duplicate','keep':keep,'remove':p})

# Rename vague names
vaguenames=('new','tmp','test','foo','bar','misc','copy','backup')
for f in idx['files']:
    p=f['path']
    base=pathlib.Path(p).name
    if any(re.search(rf'\b{vn}\b', base, re.I) for vn in vaguenames):
        new=descriptive_name(p)
        if new!=base:
            plan.append({'op':'rename','from':p,'to':str(pathlib.Path(p).with_name(new))})

json.dump({'rename_plan':plan,'dry_run':a.dry_run=='1'}, open(a.out,'w'), indent=2)