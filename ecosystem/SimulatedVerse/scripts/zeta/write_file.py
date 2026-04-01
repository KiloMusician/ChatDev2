#!/usr/bin/env python3
import argparse
import pathlib

p = argparse.ArgumentParser()
p.add_argument("--path", required=True)
p.add_argument("--content", required=True)
a = p.parse_args()
dest = pathlib.Path(a.path)
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(a.content, encoding="utf-8")
print(f"Wrote {dest}")