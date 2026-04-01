#!/usr/bin/env python3
import json
import hashlib
import os
import re
import argparse
import pathlib

PLACEHOLDER_PAT = re.compile(r'\b(TODO|FIXME|WIP|PLACEHOLDER|TBD|LATER)\b', re.I)

def sha1(path):
    h=hashlib.sha1()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def sniff_lang(path):
    ext = pathlib.Path(path).suffix.lower()
    return {
        '.ts':'ts','.tsx':'tsx','.js':'js','.jsx':'jsx','.py':'py','.rs':'rust',
        '.cs':'cs','.go':'go','.sh':'sh','.json':'json','.yml':'yml','.yaml':'yml',
        '.md':'md','.toml':'toml','.cfg':'cfg','.ini':'ini','.svelte':'svelte',
        '.gd':'gd','.ipynb':'ipynb'
    }.get(ext, ext or 'unknown')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--files', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()

    with open(args.files) as f:
        files=[line.strip() for line in f if line.strip()]

    idx=[]
    for p in files:
        if p.startswith('./.git/') or p.startswith('.git/'): continue
        if not os.path.isfile(p): continue
        try:
            size=os.path.getsize(p)
            # skip huge binaries from analysis
            if size>8_000_000: 
                idx.append({'path':p,'size':size,'lang':'binary','hash':None,'has_placeholder':False})
                continue
            lang=sniff_lang(p)
            h=sha1(p)
            has_placeholder=False
            if lang not in ('binary','png','jpg','gif','pdf','zip'):
                with open(p,'r',errors='ignore') as r:
                    txt=r.read(60000)
                    has_placeholder=bool(PLACEHOLDER_PAT.search(txt))
            idx.append({'path':p,'size':size,'lang':lang,'hash':h,'has_placeholder':has_placeholder})
        except Exception as e:
            idx.append({'path':p,'error':str(e)})

    with open(args.out,'w') as w:
        json.dump({'files':idx}, w, indent=2)

if __name__=='__main__':
    main()