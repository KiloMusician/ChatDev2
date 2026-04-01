# WGET(1) — Terminal Depths Man Page

## NAME
  wget — retrieve files from simulated remote hosts

## SYNOPSIS
  wget <url>

## DESCRIPTION
Simulates downloading files from in-game remote hosts. URLs matching known
game hosts (nexus-core, chimera-node, lattice.dark) return narrative payloads
or challenge files. External URLs are sandboxed.

## EXAMPLES
  wget http://nexus-core/payload.bin
  wget http://chimera-node/manifest.json
  wget http://lattice.dark/.hidden/fragments/f007.enc

## SEE ALSO
  curl, hack, scan, recon

---
*Generated 2026-03-23*