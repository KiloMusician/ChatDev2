# CoreLink Foundation - Quickstart Playbook
[Ω:root:docs@playbook]

## 🚀 One-Screen Setup

1. **Clone & Install**
   ```bash
   # Dependencies already installed in Replit
   # Run setup to create missing directories
   node scripts/setup.mjs
   ```

2. **Configure Environment**
   - Copy `.env.template` to `.env` 
   - Add secrets via Replit Secrets panel
   - Set `BOOT_PROFILE=dev`

3. **Run System**
   ```bash
   npm run dev        # Start development server
   npm run health     # System health check
   npm run council:check  # Validate SCP approvals
   ```

## 🎯 Key Commands

- `node scripts/setup.mjs` - Scaffold missing directories
- `node scripts/health-check.mjs` - System health verification
- `node tests/smoke.mjs` - Minimal boot test
- `node scripts/council-validator.mjs` - SCP approval validation

## 🏗️ Architecture

### Core Structure
- `/protocol/` - SCP Council governance and communication protocols
- `/registry/` - Module definitions and symbolic mappings
- `/bootstrap/` - System initialization and entry points
- `/config/` - Profile-based configuration management
- `/features/` - Feature-based module organization
- `/core/` - Shared primitives (no cross-feature imports)

### Key Files
- `bootstrap/init.ts` - 🜁 Single entry point for all initialization
- `protocol/council.md` - SCP Council roles and decision processes
- `protocol/omnitag.md` - OmniTag symbolic reference system
- `registry/modules.json` - Module dependency graph
- `registry/symbols.json` - Symbol → code mapping

## 🎮 Progression System

System unlocks features through epic tier progression:
- **Tier -1**: Deep Sleep ⟦⧉HIBERNATION⟧ (45s)
- **Tier 0**: System Boot ⟦⧉AWAKENING⟧ (3min)  
- **Tier 1**: Survival Protocols ⟦⧉FOUNDATION⟧ (10min)
- **Tier 2**: Expansion Framework ⟦⧉OUTPOST⟧ (30min)

See `/protocol/unlocks.json` for complete progression tree.

## 🛡️ SCP Council System

### Roles
- **SCP-ENG**: Engineering, architecture, performance
- **SCP-QA**: Quality gates, testing, regression prevention
- **SCP-UX**: Interface design, accessibility, user experience
- **SCP-OPS**: Infrastructure, secrets, token budgets
- **SCP-LORE**: Narrative consistency, progression unlocks

### Approval Process
1. Tag code with `[SCP-ROLE APPROVAL REQUIRED]`
2. Implement changes with proper OmniTag markers
3. Add approval stamp: `[SCP-ROLE APPROVED] ✓ Notes`
4. Run `npm run council:check` to validate

## 📡 Communication Protocols

### OmniTag Format
```
[Ω:<module-id>:<verb|state>:<optional-hint>]
```

### Council Messages
```
[Msg⛛{ROLE}↗️Σ∞] finding → location → action
```

### Symbolic Notation
```
🜁⊙⟦ΞΣΛΘΦ⟧ ÷ 🛠 {context}
```

## 🔧 Development Workflow

1. **Plan**: Use OmniTag to mark intentions
2. **Implement**: Follow feature folder structure
3. **Test**: Use health checks and smoke tests
4. **Review**: Get Council approvals for critical changes
5. **Deploy**: Validate with council checks

## 🚨 Emergency Protocols

- `SAFE_MODE=1` - Disables risky operations
- Panic Switch: Immediate rollback capability
- Council Override: Unanimous agreement required