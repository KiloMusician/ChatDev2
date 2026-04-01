# ZETA_TODO_SYNC.md

## Purpose
Automate recurring updates between the quest/task system and MASTER_ZETA_TODO.md. This file documents the sync protocol and provides a checklist for integration.

---

## Sync Protocol
- [ ] On each agent swarm cycle, parse `quest_log.jsonl` for all quests with status "pending" or "active"
- [ ] Update MASTER_ZETA_TODO.md with any new or changed quests
- [ ] Mark completed quests as done in MASTER_ZETA_TODO.md
- [ ] Log sync actions and deltas in this file for traceability

## Integration Checklist
- [ ] Implement script to parse quest_log.jsonl and update MASTER_ZETA_TODO.md
- [ ] Schedule script to run on agent swarm or CI cycle
- [ ] Add sync status to agent dashboard/report
- [ ] Document protocol in knowledge base

---

*This file is auto-generated and maintained by the agent swarm. Do not edit manually unless instructed.*
