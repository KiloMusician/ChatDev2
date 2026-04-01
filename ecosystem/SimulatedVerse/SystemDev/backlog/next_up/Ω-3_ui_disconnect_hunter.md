# Card Ω-3 — UI Disconnect Hunter

**Goal**: Find and eliminate "old UI" appearance issues using repository graph analysis

**Priority**: HIGH - Resolves Samsung S23 mobile preview conflicts

## Steps (≤8 edits)

- [ ] **1. Repository Graph Scan**: Execute repo.graph.ts to map all UI entrypoints
- [ ] **2. Competing Routes Detection**: Identify multiple index.html and conflicting static routes  
- [ ] **3. Preview Target Analysis**: Map /preview, /play, and static serving conflicts
- [ ] **4. Stale Build Detection**: Find outdated dist/, build/, docs/ serving old UI
- [ ] **5. Preview Map Generation**: Create PreviewUI/preview-map.json with canonical targets
- [ ] **6. Environment Toggle**: Implement PREVIEW_TARGET=latest|pinned switching
- [ ] **7. Mobile Cache-Busting**: Ensure Samsung S23 gets fresh UI without browser cache
- [ ] **8. Integration Test**: Verify new UI loads consistently across all entry points

## Repository Analysis Commands

```bash
# Deep repository scan
tsx SystemDev/scripts/repo.graph.ts

# Find competing UI entrypoints  
find . -name "index.html" -not -path "*/node_modules/*" | head -10

# Check static serving conflicts
grep -r "express.static" server/ --include="*.ts" --include="*.js"

# Preview routing analysis
curl -I http://localhost:5000/preview/status
curl -I http://localhost:5000/preview/health
```

## Preview Map Generation

```json
// PreviewUI/preview-map.json
{
  "canonical_targets": {
    "latest": "http://localhost:5173",
    "pinned": "http://localhost:4173", 
    "mobile_safe": "PreviewUI/web/godot/mobile-safe",
    "culture_ship": "dist/public"
  },
  "routing_priority": [
    "mobile_safe",
    "latest", 
    "pinned",
    "culture_ship"
  ],
  "samsung_s23_optimized": true,
  "cache_busting": "aggressive",
  "last_updated": "ISO_TIMESTAMP"
}
```

## Environment Toggle Implementation

```bash
# Switch to mobile-safe UI
export PREVIEW_TARGET=latest
export PREVIEW_FLAVOR=web:PreviewUI/web

# Test pinned build stability  
export PREVIEW_TARGET=pinned
export PREVIEW_FLAVOR=static:dist/public

# Verify routing
curl -s http://localhost:5000/preview/ | head -5
```

## Success Criteria

✅ Repository graph identifies all UI entrypoints and conflicts  
✅ Preview map shows canonical routing without ambiguity  
✅ PREVIEW_TARGET environment variable controls UI selection  
✅ Samsung S23 mobile browser loads CoreLink Foundation UI consistently  
✅ No "old UI" flickers or stale cache issues  
✅ Preview router health checks pass for all targets

## Receipt Pattern

```json
{
  "breath": "ui_disconnect_hunter", 
  "ok": true,
  "details": {
    "ui_entrypoints_found": 4,
    "conflicts_resolved": 2,
    "preview_targets_active": ["latest", "pinned"],
    "mobile_cache_busting": "operational",
    "samsung_s23_compatibility": "verified"
  },
  "ts": "ISO_TIMESTAMP",
  "edit_count": 5
}
```