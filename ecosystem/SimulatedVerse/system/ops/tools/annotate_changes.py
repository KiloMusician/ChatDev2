#!/usr/bin/env python3
import json
import argparse
import glob
import os
import datetime
ap=argparse.ArgumentParser()
ap.add_argument('--plans', nargs='+', required=True)
ap.add_argument('--dry-run', default='1')
a=ap.parse_args()
dry=a.dry_run=='1'

notes=[]
for p in a.plans:
    for path in glob.glob(p):
        try:
            notes.append((path, json.load(open(path))))
        except: pass

# Infrastructure-First: read-analyze-evolve pattern
reports_dir = 'docs/reports'
os.makedirs(reports_dir, exist_ok=True)
report_path = os.path.join(reports_dir, 'change-notes.md')

# Read existing report if it exists
existing_content = ''
if os.path.exists(report_path):
    with open(report_path, 'r') as r:
        existing_content = r.read()
    print(f"Evolving existing report: {report_path}")

with open(report_path, 'w') as w:
    w.write(f"# Change Notes (Updated: {datetime.datetime.utcnow().isoformat()}Z)\n\n")
    if existing_content and 'Previous Analysis:' not in existing_content:
        w.write("## Previous Analysis:\n" + existing_content + "\n\n")
    w.write("## Current Analysis:\n\n")
    for path, obj in notes:
        w.write(f"### {path}\n\n```json\n{json.dumps(obj, indent=2)}\n```\n\n")