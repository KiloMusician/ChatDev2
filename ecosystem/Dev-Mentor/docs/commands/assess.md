# ASSESS(1) — Terminal Depths Man Page

## NAME
  assess — skills gap assessment (Cybrary Learn·Practice·Prove model)

## SYNOPSIS
  assess [<topic>|results|reset]

## DESCRIPTION
Run a skills assessment to identify knowledge gaps and get personalised
learning recommendations. Based on the Cybrary Learn→Practice→Prove model.
Scores below 70% trigger focused recommendations.

## TOPICS
  networking     OSI model, TCP/IP, subnetting, ports, routing
  linux          Permissions, processes, bash, systemctl, cron
  web-security   OWASP Top 10, SQLi, XSS, CSRF, auth flaws
  cryptography   Symmetric/asymmetric, hashing, PKI, TLS, RSA
  recon          Passive/active OSINT, DNS enum, Shodan, Maltego
  exploitation   Buffer overflow, Metasploit, CVEs, payloads
  blue-team      SIEM, log analysis, IR, threat hunting, IOCs
  forensics      Memory forensics, imaging, timeline, chain of custody
  malware        Static/dynamic analysis, sandbox evasion, YARA
  cloud          IAM, S3 security, container escapes, serverless

## SUBCOMMANDS
  <topic>    Take assessment for that topic (earns XP)
  results    View all scores and recommendations
  reset      Clear all assessment history

## EXAMPLES
  assess networking
  assess web-security
  assess results

## SEE ALSO
  path, career, mitre, learn, certify

---
*Generated 2026-03-23 | Source: Cybrary · Springboard*