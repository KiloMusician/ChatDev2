# GIT(1) — Terminal Depths Man Page

## NAME
  git — real git operations on mounted repositories and the workspace

## SYNOPSIS
  git <subcommand> [args...]

## DESCRIPTION
Wraps real git subprocess calls. In Replit, operates on the workspace
repository. In Docker with harvest enabled, also operates on mounted NuSyQ
ecosystem repos. Write operations (push, commit) require write-mode enabled.

## SUBCOMMANDS
  git status              Working tree status
  git log [--oneline]     Commit history
  git diff [<file>]       Show unstaged changes
  git pull                Fast-forward from remote
  git fetch               Fetch without merging
  git branch              List branches
  git clone <url>         Clone a repository into state/repos/
  git commit -m <msg>     Stage all and commit (write mode)
  git push                Push to remote (write mode, consent required)
  git write enable        Enable write mode
  git write disable       Disable write mode

## EXAMPLES
  git status
  git log --oneline
  git diff app/game_engine/commands.py
  git write enable
  git commit -m "fix: mole clue gating"

## SEE ALSO
  repos, harvest, clone, mount

---
*Generated 2026-03-23*