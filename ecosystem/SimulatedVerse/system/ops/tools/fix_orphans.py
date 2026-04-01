#!/usr/bin/env python3
import json
import argparse
import os
import re
import pathlib
ap=argparse.ArgumentParser()
ap.add_argument('--index', required=True)
ap.add_argument('--dry-run', default='1')
ap.add_argument('--out', required=True)
a=ap.parse_args()
idx=json.load(open(a.index))
dry=a.dry_run=='1'

# quick heuristic: find imports to missing files -> create stubs with TODO docstring
missing=set()
for f in idx['files']:
    p=f['path']; lang=f.get('lang')
    if lang in ('js','ts','tsx','jsx','py','svelte','cs','gd'):
        try:
            txt=open(p,'r',errors='ignore').read(200000)
        except: 
            continue
        # super-lightweight import capture
        for m in re.finditer(r'from\s+[\'"](.+?)[\'"]', txt):
            ref=m.group(1)
            # relative only
            if ref.startswith('.'):
                candidate=str(pathlib.Path(p).parent.joinpath(ref))
                if not any(os.path.exists(candidate+ext) for ext in ('','.ts','.tsx','.js','.jsx','.py','.svelte','.cs','.gd')):
                    missing.add(candidate+'.ts')  # choose a canonical stub ext
if missing:
    os.makedirs('stubs', exist_ok=True)
created=[]
for m in sorted(missing):
    if not dry:
        with open(m,'w') as w:
            w.write('/** Auto-stub created by fix_orphans.py — replace with real module. */\n')
    created.append(m)
json.dump({'created_stubs':created,'dry_run':dry}, open(a.out,'w'), indent=2)