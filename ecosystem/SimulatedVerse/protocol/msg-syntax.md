# Msg Protocol for Council Communications
[Ω:root:council@protocol]

## Message Format

```
[Msg⛛{ROLE}↗️Σ∞] <finding> → <location> → <action>
```

### Role Codes
- `ENG` - Engineering concerns
- `QA` - Quality/testing issues  
- `UX` - User experience problems
- `OPS` - Operations/infrastructure
- `LORE` - Narrative consistency
- `AI` - Token optimization/AI usage

### Symbols
- `⛛` - Council authority marker
- `↗️` - Points to action/solution
- `Σ∞` - System-wide impact indicator
- `→` - Flows from finding to location to action

## Usage Examples

```
[Msg⛛{ENG}↗️Σ∞] Performance regression in resource engine → energy/core.ts:45-67 → Implement memoization

[Msg⛛{QA}↗️Σ∞] Missing test coverage for edge cases → ui/components/Modal.tsx → Add integration tests

[Msg⛛{LORE}↗️Σ∞] Timeline inconsistency in tier unlocks → protocol/unlocks.json:tier-5 → Reorder prerequisites

[Msg⛛{OPS}↗️Σ∞] Token budget exceeded → ai/prompts/large-context.ts → Implement prompt caching

[Msg⛛{AI}↗️Σ∞] Context bloat in code generation → Use symbolic refs instead of inline code
```

## Console Integration

Messages auto-render with colors in terminal:
- `⛛` - Red (authority)
- `ROLE` - Role-specific color (ENG=blue, QA=green, etc.)
- `↗️Σ∞` - Yellow (attention)
- File paths - Underlined, clickable in supporting terminals

## Automated Parsing

```typescript
// Auto-extract Msg entries from comments/commits
const msgPattern = /\[Msg⛛\{(\w+)\}↗️Σ∞\] (.+?) → (.+?) → (.+)/g;

// Generate Council agenda from recent Msg entries
// Surface in HUD as action items
// Track resolution via commit references
```