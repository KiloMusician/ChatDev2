#!/usr/bin/env bash
set -euo pipefail
echo "[Rosetta] locating source & parsing…"
node scripts/rosetta_parse.mjs
echo "[Rosetta] sanity…"
node scripts/rosetta_sanity.mjs
echo "[Rosetta] done."