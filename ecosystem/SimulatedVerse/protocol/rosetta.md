# Rosetta Protocol - Symbolic Reference System
[Ω:root:rosetta@prompt-optimization]
[SCP-ENG APPROVED] ✓ Token optimization patterns validated, symbolic reference system architecturally sound

## Purpose
Short symbolic references to canonical code patterns, reducing token costs in AI interactions.

## Standard Patterns

### @bootstrap
```typescript
// Bootstrap entry point pattern
export async function boot(profile: string): Promise<BootContext>
```

### @mod:energy#init
```typescript  
// Energy module initialization
const engine = new ResourceEngine();
engine.calculateDeltas(timeElapsed);
```

### @council:approve
```typescript
// Council approval check pattern
if (!hasApproval('SCP-ENG', changeSet)) {
  throw new Error('[SCP-ENG APPROVAL REQUIRED]');
}
```

### @tier:unlock
```typescript
// Tier progression pattern  
if (progression.checkAdvancement(resources)) {
  const newTier = progression.advanceTier();
  emit('tier_unlocked', newTier);
}
```

### @omni:tag
```typescript
// OmniTag usage pattern
// [Ω:module:verb:hint] Description
function taggedFunction() {}
```

### @msg:council
```
// Council message format
[Msg⛛{ROLE}↗️Σ∞] finding → file:line → action
```

### @guard:check
```typescript
// Safety check pattern
if (isPanicMode()) {
  throw new Error('Operation blocked in SAFE_MODE');
}
```

### @delta:apply
```typescript
// Resource delta pattern (not absolutes)
const deltas = engine.calculateDeltas(dt);
const newState = engine.applyDeltas(deltas);
```

## AI Prompt Usage

Instead of:
```
"Please implement a resource engine that calculates energy, materials, and other resources over time with proper allocation checking..."
```

Use:
```
"Implement @mod:energy#init with @delta:apply pattern and @guard:check for allocation"
```

## Context Linking

Use `[[ref:protocol/council.md]]` instead of copying council rules.
Use `[[ref:registry/modules.json]]` instead of listing all modules.

Reference files with symbolic anchors:
- `@file:energy/service.ts#ResourceEngine` 
- `@config:dev.json#limits`
- `@protocol:unlocks.json#tier-2`