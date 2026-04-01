# MOUNT(1) — Terminal Depths Man Page

## NAME
  mount — mount a real directory into the virtual filesystem

## SYNOPSIS
  mount <real-path> [<vfs-path>]

## DESCRIPTION
Overlays a real filesystem directory at a virtual path. Once mounted, ls,
cat, and cd operate on the real files transparently. If vfs-path is omitted,
the mount point is /mnt/<basename>.

## EXAMPLES
  mount /home/runner/workspace /repos/workspace
  mount state/repos/NuSyQ-Hub /repos/nusyq
  mount /tmp/exfil /exfil

## SEE ALSO
  harvest, repos, clone, ls

---
*Generated 2026-03-23*