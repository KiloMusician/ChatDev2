#!/usr/bin/env python3
import json
import argparse
import os
import re
import pathlib

ap=argparse.ArgumentParser()
ap.add_argument('--plan', required=True)
ap.add_argument('--dry-run', default='1')
a=ap.parse_args()
plan=json.load(open(a.plan))
dry=a.dry_run=='1'

# naive but effective textual ref updates for common imports/paths
def apply_text(path, subs):
    try:
        with open(path,'r',errors='ignore') as f: txt=f.read()
    except: return False
    orig=txt
    for old,new in subs:
        # import statements, require, TS/JS/CS/PY, markdown links, yaml refs
        txt=re.sub(rf'(\bfrom\s+[\'"]){re.escape(old)}([\'"])', rf'\1{new}\2', txt)
        txt=re.sub(rf'(\brequire\(\s*[\'"]){re.escape(old)}([\'"]\s*\))', rf'\1{new}\2', txt)
        txt=re.sub(rf'(\()\s*{re.escape(old)}(\))', rf'\1{new}\2', txt)
        txt=re.sub(rf'(\[.+?\]\()({re.escape(old)})(\))', rf'\1{new}\3', txt)
    if txt!=orig:
        if not dry:
            with open(path,'w') as w: w.write(txt)
        return True
    return False

subs=[]
removals=[]
for step in plan.get('rename_plan',[]):
    if step['op']=='rename':
        subs.append((step['from'], step['to']))
    elif step['op']=='remove_duplicate':
        removals.append(step['remove'])

# rename files
changed_files=set()
for old,new in subs:
    if not dry:
        os.makedirs(str(pathlib.Path(new).parent), exist_ok=True)
        os.rename(old, new)
    changed_files.add(old); changed_files.add(new)

# update references in all text files
def iter_files():
    for root,_,files in os.walk('.'):
        if root.startswith('./.git'): continue
        for f in files:
            path=os.path.join(root,f)
            if os.path.getsize(path)>2_000_000: continue
            yield path

touched=[]
for path in iter_files():
    if apply_text(path, subs): touched.append(path)

# remove dupes
for r in removals:
    if not dry and os.path.exists(r):
        os.remove(r)

json.dump({'ref_updates':touched,'dry_run':dry}, open('_reports/ref_updates.json','w'), indent=2)
print(f"Updated {len(touched)} files (dry={dry}).")