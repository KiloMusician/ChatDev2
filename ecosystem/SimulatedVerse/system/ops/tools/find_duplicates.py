#!/usr/bin/env python3
import json
import argparse
from collections import defaultdict
ap=argparse.ArgumentParser()
ap.add_argument('--index',required=True)
ap.add_argument('--out',required=True)
a=ap.parse_args()

idx=json.load(open(a.index))
byhash=defaultdict(list)
for f in idx['files']:
    h=f.get('hash')
    if not h: continue
    byhash[h].append(f['path'])

dups={h:paths for h,paths in byhash.items() if len(paths)>1}
json.dump({'duplicates':dups}, open(a.out,'w'), indent=2)