# VALIDATE(1) — Terminal Depths Man Page

## NAME
  validate — validate game content and configuration

## SYNOPSIS
  validate [challenges|scripts|agents|config|all]

## DESCRIPTION
Runs validation checks on generated content and configuration. challenge
validation ensures CTF challenges are solvable and correctly formed. script
validation checks syntax. Agent validation verifies YAML personality files.

## SUBCOMMANDS
  challenges   Validate all CTF challenge definitions
  scripts      Check all game scripts for syntax errors
  agents       Validate agent YAML personality files
  config       Validate configuration files
  all          Run all validation suites

## EXAMPLES
  validate
  validate challenges
  validate all

## SEE ALSO
  test, coverage, plugin, chug

---
*Generated 2026-03-23*