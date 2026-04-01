# Msg⛛{X}::continue_compelling

## Directive: Continue Compelling Tasks

**Scope**: Current beacon roots (SystemDev, ChatDev, GameDev, PreviewUI)

**Sources**: 
- TODOs in code
- LSP errors and warnings  
- Git conflicts
- Receipt files with "needs_action": true
- Failed CI/CD checks
- System health warnings

## Hard Rules

1. **≤8 edits per cycle** - Maintain micro-cycle discipline
2. **≤400 lines changed** - Keep changes focused and reviewable  
3. **Generate receipt** - Every cycle must produce evidence
4. **Prefer smallest viable fix** - Don't over-engineer solutions

## Execution Logic

```
1. IF scan overload detected:
   → Fall back to targeted_provenance with --roots
   
2. IF git restricted (index.lock, etc):
   → Switch to Shell-first Git-Steward card
   
3. WHILE compelling items exist AND edits < 8:
   → Pick single most urgent item
   → Apply minimal fix
   → Test if possible
   → Document in receipt
   
4. ON success (≥6 clean edits across cycles):
   → Enqueue cascade event (Culture-Ship)
```

## Priority Order

1. **CRITICAL**: Blocking errors, build failures, server crashes
2. **HIGH**: TypeScript errors, test failures, security warnings  
3. **MEDIUM**: Linting issues, TODO comments, deprecation warnings
4. **LOW**: Code style, documentation, optimization opportunities

## Safety Protocols

- **Path-safe moves**: Use Artificer for file relocations
- **Idempotent operations**: No side effects on re-run
- **Receipt required**: Every cycle generates evidence trail
- **Zeta checks**: Boolean verification before proceeding
- **Anti-theater**: Only real, measurable progress

## Integration Points

**TipSynth**: Surface contextual hints on common failure patterns
**Capability Registry**: Use existing tools before writing new ones  
**RLCI Event Bus**: Publish progress to Culture-Ship coordination
**Location Beacons**: Respect quadrant-specific safe zones

## Escalation Paths

- **Module not found** → Artificer (import_rewriter)
- **Git conflicts** → Janitor (git_steward_playbook)
- **Mobile Preview issues** → Navigator (mobile_preview_hardening)
- **Persistent failures** → Raven (anomaly_investigation)

## Success Indicators

- Receipt shows "result": "ok"
- No new LSP errors introduced
- System health maintained  
- Progress toward larger goals
- Culture-Ship cascade triggers engaged

---

*This directive embodies the "continue with todos, errors, conflicts..." magic that enables autonomous productive grinding while maintaining receipts discipline and Culture-Ship integration.*