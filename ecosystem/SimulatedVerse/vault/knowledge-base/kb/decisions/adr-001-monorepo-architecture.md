---
source: kb/kb/decisions/adr-001-monorepo-architecture.md
updated: 2025-08-30T05:30:30.632Z
tags: [corelink, ]
---

# ADR-001: Monorepo Architecture with Event Bus

**Date**: 2025-08-27  
**Status**: Accepted  
**Deciders**: Development Team  

## Context

The KPulse ecosystem needs to integrate multiple complex systems (game engine, storyteller, RepoPilot, UI clients, analytics) while maintaining clean boundaries and enabling self-improvement loops.

## Decision

We will adopt a monorepo structure with event-bus-first communication:

```
kpulse/
├─ apps/          # Core services (engine, repopilot, storyteller)
├─ clients/       # UI clients (godot, cli, web)
├─ shared/        # Common types, bus contracts, utilities
├─ content/       # Self-spawning directives and schemas
├─ kb/           # Knowledge base (this vault)
├─ analysis/     # Jupyter notebooks and datasets
└─ scripts/      # Development and validation tools
```

## Rationale

### Benefits
- **Single Source of Truth**: All code versioned together
- **Shared Types**: TypeScript types consistent across all components
- **Event Bus**: Clean separation with observable interactions
- **Self-Improvement**: RepoPilot can analyze entire codebase
- **Cultivation Loops**: Gameplay → Analytics → Insights → Code → Gameplay

### Trade-offs
- Larger repository size
- More complex build coordination
- Requires disciplined dependency management

## Implementation

1. **Event Bus**: WebSocket JSON-RPC on port 7070
2. **Package Management**: pnpm workspaces for efficiency
3. **Build System**: Parallel builds with proper dependency order
4. **CI/CD**: Comprehensive validation including UI audit
5. **Documentation**: Auto-generated from code and embedded in KB

## Success Metrics

- All UI elements connected to event handlers (0 dead buttons)
- RepoPilot successfully answers architecture questions
- Directive system spawns valid content at Tier 8+
- Analytics feeds back into development decisions

## Review Date

Monthly review to assess if monorepo structure still serves our needs as the ecosystem grows.