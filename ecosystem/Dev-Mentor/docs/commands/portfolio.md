# PORTFOLIO(1) — Terminal Depths Man Page

## NAME
  portfolio — professional portfolio of completed work (Coursera/Springboard)

## SYNOPSIS
  portfolio [add <item>|export|clear]

## DESCRIPTION
Tracks your completed certifications, capstones, pentest engagements, and
CTF achievements. Modelled on Coursera portfolio projects and Springboard's
job-guarantee portfolio requirements. Export generates a formatted report.

## SUBCOMMANDS
  (no args)       View full portfolio
  add <item>      Manually add a completed item
  export          Generate formatted portfolio report
  clear           Clear manual entries

## EXAMPLES
  portfolio
  portfolio add "Completed OWASP Juice Shop full assessment"
  portfolio export

## AUTO-POPULATED BY
  pentest report   — adds pentest engagement
  capstone submit  — adds completed capstone
  certify claim    — adds certificate
  path next        — tracks path completion

## SEE ALSO
  certify, pentest, capstone, review

---
*Generated 2026-03-23 | Source: Coursera · Springboard · Udemy*