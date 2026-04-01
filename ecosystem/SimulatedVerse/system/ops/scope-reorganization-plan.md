# CoreLink Foundation - Scope-Based Reorganization Plan

## Current Challenge
Repository feels scattered with components affecting different scopes mixed together.

## Proposed Structure by Scope of Effect

### 🌍 **global/** - System-Wide Effects (affects everything)
- Core infrastructure, configuration, and cross-cutting concerns
- Files that impact the entire ecosystem

#### Candidates:
- `src/nusyq-framework/` → `global/core/nusyq-framework/`
- `src/guardian/` → `global/safety/guardian/`
- `src/context-management/` → `global/core/context-management/`
- `src/endpoint-integration/` → `global/core/endpoint-integration/`
- `bootstrap/` → `global/core/bootstrap/`
- `config/` → `global/config/`
- `shared/` → `global/shared/`
- `policies/` → `global/safety/policies/`

### ⚙️ **system/** - Workspace/Infrastructure Only
- Development tools, workspace management, platform integration
- Files that only affect the development environment

#### Candidates:
- `tools/` - Development utilities
- `scripts/` - Build and deployment scripts
- `sidecar/` - Token discipline and LLM orchestration
- `orchestrator/` - Task orchestration
- `agent/` - Development automation

### 🎮 **game/** - Gameplay-Specific Only
- All gameplay logic, UI, and game-specific features
- Files that only affect the actual game experience

#### Candidates:
- `client/` - Game frontend
- `server/` - Game backend
- `apps/` - Game services
- `content/` - Game content and assets
- `views/` - Game view logic
- `engine/` - Game engine components

### 📚 **knowledge/** - Documentation and Analysis
- Documentation, knowledge base, analysis notebooks
- Reference materials and research

#### Candidates:
- `kb/` - Knowledge base (Obsidian vault)
- `analysis/` - Jupyter notebooks and datasets
- `structures/` - Knowledge structures

## Benefits of This Organization
1. **Clear separation of concerns** - Easy to understand what affects what
2. **Reduced cognitive load** - Developers know where to look for specific types of changes
3. **Better dependency management** - Clear hierarchy (global → system → game)
4. **Easier maintenance** - Changes to one scope don't accidentally affect others

## Implementation Strategy
1. **Phase 1 - Manual Planning** (Due to git restrictions)
   - Use ops/tools/smart_rename.py for safe file moves
   - Create detailed mapping of current → new structure
   
2. **Phase 2 - Import Reference Updates**
   - Use ops/tools/update_references.py for automatic import fixing
   - Test after each major move to ensure functionality
   
3. **Phase 3 - Placeholder Resolution**
   - Address 36 placeholder files during reorganization
   - Focus on core files: temple_boot.py, scp-containment.ts, etc.
   
4. **Phase 4 - Validation**
   - Ensure all workflows still function
   - Run automated tests after reorganization

## Immediate Next Steps
1. Start with `mkdir` commands to create new structure
2. Move files in small batches with import updates
3. Test functionality after each batch

## Placeholder Files to Address (36 total)
Most are in .pythonlibs (external dependencies) but these core ones need attention:
- `temple_boot.py`
- `src/nusyq-framework/scp-containment.ts`
- `scripts/ztp-demo.py`
- `ui_ascii/widgets/minimap.py`
- `sidecar/bootstrap.py`
- `engine/cascade_event.py`
- `agent/quest_runner.ts`