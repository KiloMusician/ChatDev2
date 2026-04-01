# ARCH(1) — Terminal Depths Man Page

## NAME
  arch — architecture challenge modules (OpenSecurityTraining2-inspired)

## SYNOPSIS
  arch [list|start <code>|submit <answer>|hint|status]

## DESCRIPTION
Low-level systems security challenges modelled on OpenSecurityTraining2 (OST2)
course codes. Master x86-64 assembly, ARM, firmware, symbolic analysis, and
advanced debugging. All 6 modules completed earns Architecture Master.

## MODULES
  Arch1001    x86-64 Assembly Fundamentals (+300 XP)
  Arch2001    ARM Assembly (+350 XP)
  Dbg2011     Intermediate Debugging (+300 XP)
  RE3201      Symbolic Analysis (+500 XP)
  Arch4001    UEFI Firmware Attack & Defense (+600 XP)
  Dbg1015     Introductory Hardware Simulation (+250 XP)

## SUBCOMMANDS
  list              List all modules and progress
  start <code>      Begin a module (shows challenge)
  submit <answer>   Submit your answer
  hint              Get a hint for current challenge
  status            Module completion overview

## EXAMPLES
  arch list
  arch start Arch1001
  arch hint
  arch submit rax
  arch start Dbg2011
  arch submit bt

## ACHIEVEMENTS
  All 6 modules complete → Architecture Master (+300 XP bonus)

## SEE ALSO
  ctf, capstone, gdb, strings, hexdump, objdump

---
*Generated 2026-03-23 | Source: OpenSecurityTraining2 (OST2)*