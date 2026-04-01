# NOTEKEEP(1) — Terminal Depths Man Page

## NAME
  notekeep — pentest note-keeping system (TCM Security method)

## SYNOPSIS
  notekeep [list|add <title> :: <content>|view <id>|tag <id> <tag>|export]

## DESCRIPTION
In-terminal note-keeping inspired by TCM Security's recommended tools:
CherryTree, OneNote, and Joplin. Good note-keeping is emphasised throughout
TCM's methodology as critical for professional reporting. Notes persist
across sessions.

## SUBCOMMANDS
  list                     List all notes
  add <title> :: <text>    Add a new note (use :: as separator)
  view <id>                View a specific note
  tag <id> <tag>           Add a tag to a note
  export                   Export all notes as formatted text

## EXAMPLES
  notekeep add "Port 8080" :: "Apache Tomcat 9.0.37 — CVE-2020-1938 possible"
  notekeep add "Credentials" :: "admin:Password123! from rockyou spray"
  notekeep list
  notekeep view 1
  notekeep tag 1 critical
  notekeep export

## SEE ALSO
  pentest, journal, report, portfolio

---
*Generated 2026-03-23 | Source: TCM Security note-keeping best practices*