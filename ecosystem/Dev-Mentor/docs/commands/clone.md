# CLONE(1) — Terminal Depths Man Page

## NAME
  clone — clone a git repository and mount it in the virtual filesystem

## SYNOPSIS
  clone <url>

## DESCRIPTION
Clones a real git repository into state/repos/ and auto-mounts it at
/repos/<name> in the virtual filesystem. Requires GITHUB_TOKEN for private
repositories. The repository is then accessible via cat, ls, and cd.

## EXAMPLES
  clone https://github.com/org/repo.git
  clone https://github.com/NuSyQ/NuSyQ-Hub.git

## SEE ALSO
  git, harvest, repos, mount

---
*Generated 2026-03-23*