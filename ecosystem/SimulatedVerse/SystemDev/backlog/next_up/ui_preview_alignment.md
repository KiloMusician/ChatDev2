# UI Preview Alignment (Quadpartite)

## Card A — Map Reality (≤8 edits)
- [ ] Run: tsx SystemDev/scripts/audit_preview.ts
- [ ] Open resulting SystemDev/reports/preview_audit_*.json
- [ ] Note preferred entrypoint (envSwitch.recommendation.preferred)

## Card B — Flip Preview (≤8 edits)
- [ ] Update .replit run to use switcher:
      run = "PREVIEW_FLAVOR=${PREVIEW_FLAVOR:-web:PreviewUI/web} tsx SystemDev/scripts/preview_switcher.ts"
- [ ] Set Secrets → PREVIEW_FLAVOR to preferred (e.g., web:PreviewUI/web)

## Card C — Bust Caches (≤8 edits)
- [ ] If findings.service_workers.length > 0:
      Add `no-store` headers (already in switcher) and increment CACHE_VERSION token
- [ ] On your S23, refresh with hard reload in Replit App (or open Preview in external browser)

## Card D — Godot Bridge (≤8 edits)
- [ ] If GameDev/engine/godot export found: ensure not mounted to same root as web.
- [ ] Serve Godot at `kind=godot:GameDev/engine/godot/export` via PREVIEW_FLAVOR toggle when testing.

## Card E — Conflict Triage (≤8 edits)
- [ ] If conflicts.index_conflict|shadowing found:
      Choose one: keep PreviewUI/web as source-of-truth; re-point legacy `docs/` or `public/` to subpath
      (no deletes; only path decisions + receipts)

## Card F — Receipt & Cascade (≤8 edits)
- [ ] Commit SystemDev/reports/* + this run card updated with decisions
- [ ] Trigger ΞΘΛΔ_temple and ΞΘΛΔ_ship breaths for alignment reports