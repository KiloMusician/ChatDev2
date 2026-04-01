# SCP Council Protocol v1.0
[Ω:root:council@authority]

## Council Roles & Responsibilities

- **SCP-ENG**: Engineering decisions, architecture, performance budgets
- **SCP-QA**: Quality gates, test coverage, regression prevention  
- **SCP-UX**: Interface design, accessibility, user experience flows
- **SCP-OPS**: Infrastructure, secrets, token budgets, deployment
- **SCP-LORE**: Narrative consistency, progression unlocks, world-building

## Decision Ladder

1. **Individual**: Single-role decisions within module ownership
2. **Consultation**: Cross-module impacts require affected role input
3. **Consensus**: Breaking changes need majority Council agreement
4. **Veto**: Any role can block if it violates their domain safety

## Approval Gates

### Critical Changes (Require SCP-OPS approval)
- Token budget > 10k/day
- External API integrations
- Security-sensitive code
- Production deployments

### Architecture Changes (Require SCP-ENG + affected roles)
- Module boundary changes
- Core protocol modifications
- Performance-critical paths

### Narrative Changes (Require SCP-LORE approval)
- Unlock tree modifications
- Lore timeline conflicts
- Progression pacing changes

## Council Stamps

```
[SCP-ENG APPROVED] ✓ Architecture sound, performance budget met
[SCP-QA APPROVED] ✓ Tests pass, coverage >80%, golden fixtures updated
[SCP-UX APPROVED] ✓ Accessibility verified, user flow coherent
[SCP-OPS APPROVED] ✓ Security cleared, deployment ready
[SCP-LORE APPROVED] ✓ Narrative consistent, progression logical
```

## Emergency Protocols

**SAFE_MODE=1**: Disables AI calls, automation, external APIs
**PANIC_SWITCH**: Rolls back to last stable checkpoint
**COUNCIL_OVERRIDE**: Requires unanimous agreement (extreme cases only)