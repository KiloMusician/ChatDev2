#!/usr/bin/env python3
import re
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]
files = list(root.glob("**/*.mjs")) + list(root.glob("**/*.ts")) + list(root.glob("**/*.tsx")) + list(root.glob("**/*.js"))

regexes = [
  (re.compile(r"\bconfg\b"), "config"),
  (re.compile(r"TODO\((urgent|blocker)\)"), r"TODO[\1]"),
]

for f in files:
  try:
    s = f.read_text(encoding="utf-8", errors="ignore")
    orig = s
    for rx, rep in regexes:
      s = rx.sub(rep, s)
    if s != orig:
      f.write_text(s, encoding="utf-8")
      print("fix:", f.relative_to(root))
  except Exception as e:
    print("skip:", f.relative_to(root), str(e))