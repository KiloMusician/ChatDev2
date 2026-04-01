# HARVEST(1) — Terminal Depths Man Page

## NAME
  harvest — clone NuSyQ ecosystem repos and mount them

## SYNOPSIS
  harvest

## DESCRIPTION
Clones the full NuSyQ ecosystem (NuSyQ-Hub, SimulatedVerse, NuSyQ-Ultimate)
into state/repos/ using GITHUB_TOKEN and auto-mounts them at /repos/ in the
virtual filesystem. Docker: runs entrypoint harvest. Replit: calls
POST /api/admin/harvest.

## EXAMPLES
  harvest

## SEE ALSO
  repos, clone, mount, git

---
*Generated 2026-03-23*