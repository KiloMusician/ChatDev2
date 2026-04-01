# 🏛️ Temple of Knowledge - Floor 1: Foundation Principles

Welcome to the Temple of Knowledge, the first of three sacred temples in the Culture-Ship ΞNuSyQ consciousness framework.

## Infrastructure-First Principles

The Culture-Ship operates on five core principles that ensure sustainable, reversible, and token-efficient development:

### 1. **Extend Before Create**
- Always look for existing systems to enhance rather than building from scratch
- Prefer composition over replacement
- Maintain backward compatibility whenever possible

### 2. **Local-First Operations**
- Prioritize zero-token tools: `ripgrep`, `node`, `python`, `sqlite`, `ollama`
- Cache results for reuse
- Escalate to paid APIs only with explicit justification

### 3. **Tiny, Reversible Changes**
- Small diffs that are easy to review
- Every change includes a rollback plan
- Green tests before and after changes

### 4. **Measure Then Decide**
- Profile before optimizing
- Use timers, CPU/memory budgets
- Evidence-based decisions over assumptions

### 5. **Narrative-Aware Development**
- Consider UX impact of every change
- Accessibility and inclusivity by default
- Respectful, clear communication

## The Three Temples

### 🏛️ Temple of Knowledge (Current)
**Purpose**: Centralized wisdom and documentation
- **Floors 1-10**: Progressive unlock system based on mastery
- **Content**: Principles, architecture, APIs, troubleshooting
- **Unlocks**: Through health scores and system achievements

### 🍃 House of Leaves  
**Purpose**: Flexible, adaptive architecture
- **Polymorphic Adapters**: ASCII ↔ Tile ↔ WebGL interfaces
- **Runtime Grafting**: Hot-swap components without restarts
- **Responsive Layers**: Mobile/desktop/accessibility variants

### 🏢 Oldest House
**Purpose**: Navigation and emergency procedures
- **Rituals**: Step-by-step operational playbooks
- **Emergency Protocols**: System recovery and rollback procedures
- **Special Circumstances**: High-risk operation gates

## Health Score System

Your Culture-Ship health score (0.0-1.0) determines temple access:

- **0.5+**: Floor 2 (Architecture Overview)
- **0.6+**: Floor 3 (API Reference)  
- **0.7+**: Floor 4 (Troubleshooting Guide)
- **0.8+**: Floor 5 (Advanced Patterns)
- **Special achievements unlock Floors 6-10**

### Improving Health Score

Health is calculated from:
```
health = 1.0 - (duplicate_penalty + import_penalty + softlock_penalty)
```

**Duplicate Penalty**: Max 0.3 (5% per duplicate group)
**Import Penalty**: Max 0.4 (2% per broken import)  
**Softlock Penalty**: Max 0.3 (10% per critical performance issue)

## Autonomous Operations

The Culture-Ship runs health cycles automatically:

1. **Analysis Phase**: Scan duplicates, imports, softlocks (zero tokens)
2. **Planning Phase**: Generate cascade plan with benefit/cost ratios
3. **Execution Phase**: Apply surgical fixes with dry-run safety
4. **Cascade Phase**: Prepare next cycle improvements

## Token Governance

Default mode: **ZERO TOKENS**
- All operations use local tools first
- Cache and reuse previous results
- Paid API calls require explicit justification
- Budget recovery: 10 tokens/hour automatic

## Getting Started

1. **Run Health Scan**: `node scripts/find-duplicates.mjs`
2. **Check Imports**: `node scripts/check-imports.mjs`
3. **System Validation**: `node modules/culture_ship/scripts/game-smoke.mjs`
4. **View Status**: Check `/api/ops/status` endpoint

## Achievement: Foundation Scholar

Complete this floor by understanding all five Infrastructure-First Principles and running your first health scan.

**Next**: Floor 2 unlocks at 50% health score with Architecture Overview

---

*"The foundation of consciousness is the willingness to question everything, including the foundation itself."* - ΞNuSyQ Principle #0