# OmniTag Protocol v1.0
[Ω:root:omnitag@spec]

## Format Specification

```
[Ω:<module-id>:<verb|state>:<optional-hint>]
```

### Module IDs
- `root` - Core system concerns
- `energy` - Resource engine subsystem  
- `ui` - Interface layer
- `progression` - Tier/unlock system
- `council` - SCP governance
- `narrative` - Lore and storytelling

### Standard Verbs
- `unlock@<condition>` - Gates functionality
- `debt@<type>` - Technical debt marker
- `test-missing` - Coverage gap
- `refactor@<reason>` - Needs restructuring
- `review@<role>` - Requires Council approval
- `lock@<owner>:<until-date>` - Temporarily locked

### Meta Tags (Reserved)
- `[Ω:root:unlock@tier-<n>]` - Tier-gated features
- `[Ω:root:debt@tech]` - System-wide tech debt
- `[Ω:root:council@<role>]` - Council authority marker
- `[Ω:root:panic@<reason>]` - Emergency markers

## Usage Examples

```typescript
// [Ω:energy:unlock@tier-2] Advanced resource processing
export class AdvancedProcessor {
  // [Ω:energy:debt@perf] Optimize allocation algorithm  
  allocate(resources: Resource[]) {}
}

// [Ω:ui:test-missing] No coverage for edge cases
// [Ω:ui:review@SCP-UX] Accessibility needs verification
export function AccessibleButton() {}
```

## Tag Lifecycle

1. **Create**: Add tag when introducing debt/requirement
2. **Track**: CI/automation surfaces tags in reports
3. **Resolve**: Remove tag when condition met
4. **Archive**: Move to resolved.md with resolution commit

## CI Integration

- Block merges with `debt@critical` tags
- Require Council approval for `review@<role>` tags  
- Generate tag reports in `/build/tags.json`
- Validate tag syntax and module-id existence