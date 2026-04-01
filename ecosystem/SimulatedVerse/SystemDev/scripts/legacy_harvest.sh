#!/usr/bin/env bash
set -euo pipefail
ROOT=${1:-"."}
YAML="ops/legacy_repos.yaml"
mkdir -p legacy
python3 - <<'PY'
import yaml, sys, os, subprocess, json
with open("ops/legacy_repos.yaml") as f:
    cfg = yaml.safe_load(f)
os.makedirs("legacy", exist_ok=True)
for r in cfg.get("repos", []):
    d = os.path.join("legacy", r["name"])
    if not os.path.exists(d):
        try:
            subprocess.run(["git","clone","--no-checkout",r["url"],d], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[legacy_harvest] WARNING: Failed to clone {r['url']}: {e}")
            continue
    try:
        os.chdir(d)
        subprocess.run(["git","sparse-checkout","init","--cone"], check=True)
        pats = r.get("sparse", [])
        if pats:
            subprocess.run(["git","sparse-checkout","set", *pats], check=True)
        subprocess.run(["git","checkout"], check=True)
        os.chdir("../..")
        print(f"[legacy_harvest] ✅ {r['name']}")
    except subprocess.CalledProcessError as e:
        print(f"[legacy_harvest] WARNING: Failed to process {r['name']}: {e}")
        os.chdir("../..")
print("[legacy_harvest] done")
PY