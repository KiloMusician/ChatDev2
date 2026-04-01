#!/usr/bin/env bash
# Diagnostic script to run inside the devcontainer to verify workspace mounts
set -euo pipefail

echo "=== Diagnose mounts and workspace layout ==="
echo "Container user: $(whoami)"
echo "Current dir: $(pwd)"
echo "Listing /workspaces:"
ls -la /workspaces || true

echo
echo "Mount info (proc/mounts):"
if [ -f /proc/mounts ]; then
  grep workspaces /proc/mounts || true
else
  mount | grep workspaces || true
fi

echo
echo "Check specific workspaces paths:"
for p in /workspaces/NuSyQ-Hub /workspaces/NuSyQ /workspaces/SimulatedVerse; do
  if [ -d "$p" ]; then
    echo "OK: $p -> contents:"
    ls -la "$p" | sed -n '1,10p'
  else
    echo "MISSING: $p"
  fi
done

echo
echo "Docker info (if available):"
if command -v docker >/dev/null 2>&1; then
  docker info --format '{{json .}}' | sed -n '1,10p' || true
else
  echo "docker CLI not available inside container"
fi

echo
echo "Done. Paste this output back into the issue if any mount is missing."
