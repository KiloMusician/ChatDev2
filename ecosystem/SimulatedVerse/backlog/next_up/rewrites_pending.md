# Import Rewrite Pending - BOSS D Execution

## Status: Path Alias Configuration Required

### 🎯 Objective
Convert relative import spaghetti (`../../../`) to clean aliases (`@game/engine`) across 20+ files.

### 📋 Files Requiring Rewrites (Detected)

**High Priority** (Clear path mappings):
- `PreviewUI/web/hooks/useOnboarding.ts` - `../services/` → `@ui/services/`
- `packages/qadra/council-bridge.ts` - `./types.js` → package-local (acceptable)
- `application-services/storyteller/src/gradient.ts` 
- `application-services/repopilot/src/llm.ts`
- `packages/godot/bridge.ts`

**Requires Investigation**:
- `packages/consciousness/*` files - may need new `@consciousness/` alias
- `packages/agents/*` files - may use `@agents/` alias
- `packages/llm/brain.ts` - may need `@llm/` alias

### 🔧 Configuration Updates Needed

1. **vite.config.ts**: Add comprehensive aliases from SystemDev/scripts/path_alias_map.json
2. **tsconfig.json**: Add matching path mappings
3. **Run import rewriter**: Execute edge_import_rewrite.ts after config updates

### ⚡ Execution Plan - IN PROGRESS

**Phase 1**: ✅ Updated tsconfig.json with comprehensive aliases (vite.config.ts protected)
**Phase 2**: ✅ Manual targeted rewrites on high-priority files
- ✅ PreviewUI/web/hooks/useOnboarding.ts - relative → @ui/* aliases
- ✅ application-services/repopilot/src/llm.ts - fixed recursive import + @shared alias
**Phase 3**: Verify compilation and runtime behavior  
**Phase 4**: Document successful rewrites with receipts

### 🎯 Completed Rewrites
- PreviewUI/web/hooks/useOnboarding.ts: `../services/` → `@ui/web/services/`
- application-services/repopilot/src/llm.ts: Fixed recursive path + `../../../shared/` → `@shared/`

### 🚨 Zeta Compliance
- All rewrites are reversible via git
- Only apply where target files exist
- Generate receipts for each rewrite group
- Maintain separation between Dev Menu and Game code