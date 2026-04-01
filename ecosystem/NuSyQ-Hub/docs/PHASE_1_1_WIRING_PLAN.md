# Phase 1.1 Implementation: Wire Culture Ship Router

**Date:** 2026-01-10  
**Objective:** Mount comprehensive Culture Ship router with full endpoint
support  
**Status:** In Progress

---

## Current State Assessment

### What Exists

- ✅ **Comprehensive router:** `server/router/culture-ship.ts` (197 lines, fully
  implemented)

  - GET `/status` — Consciousness status with orchestrator info
  - GET `/next-actions` — Suggested actions based on consciousness state
  - POST `/deploy-swarm` — Deploy agent swarm for autonomous operations
  - GET `/health` — Full component health check
  - Helper functions: `getSuggestedActions()`, `getSuggestedPriorities()`,
    `getSystemReadiness()`

- ⚠️ **Simple route:** `server/routes/culture-ship.ts` (66 lines, minimal)
  - POST `/health-cycle` — Only health cycle tick handler
  - **Currently mounted** to `/api/culture-ship` in main app

### Problem

- Comprehensive router (`router/culture-ship.ts`) is **not being imported or
  used**
- Simple route is insufficient for full orchestration coordination
- Missing cross-repo health endpoint integration with NuSyQ-Hub

---

## Implementation Plan

### Step 1: Replace Simple Route with Comprehensive Router

**Action:** Update `server/index.ts` line 411-412 to use new router

**Before:**

```typescript
import cultureShipRoutes from './routes/culture-ship.js';
app.use('/api/culture-ship', cultureShipRoutes);
```

**After:**

```typescript
import { cultureShip } from './router/culture-ship.js';
app.use('/api/culture-ship', cultureShip);
```

**File:** `server/index.ts`

---

### Step 2: Verify All Endpoints Are Operational

- [ ] Verify `cultureShipOrchestrator` service is properly initialized
- [ ] Check all async functions in router can execute without errors
- [ ] Test fallback consciousness endpoints

**Test Commands:**

```bash
# Once wired:
curl http://localhost:5002/api/culture-ship/status
curl http://localhost:5002/api/culture-ship/next-actions
curl http://localhost:5002/api/culture-ship/health
curl -X POST http://localhost:5002/api/culture-ship/deploy-swarm \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

### Step 3: Add Request Logging/Tracing

**Goal:** Enable debugging of cross-repo calls

**Add to each endpoint:**

```typescript
console.log('[CULTURE-SHIP] Incoming request:', {
  method: req.method,
  path: req.path,
  timestamp: new Date().toISOString(),
  client: req.ip,
});
```

---

### Step 4: Wire to NuSyQ-Hub Health Checks

**Future:** Add health probe from Hub to SimulatedVerse culture-ship endpoint

**In NuSyQ-Hub (`src/culture_ship/health_probe.py`):**

```python
def probe_simulated_verse():
    """Check SimulatedVerse culture-ship health."""
    try:
        response = requests.get(
            "http://localhost:5002/api/culture-ship/health",
            timeout=5
        )
        return response.json()
    except Exception as e:
        return {"status": "unreachable", "error": str(e)}
```

---

## Files to Modify

| File                                     | Change                                | Priority |
| ---------------------------------------- | ------------------------------------- | -------- |
| `server/index.ts`                        | Update import + mount (lines 411-412) | HIGH     |
| `server/router/culture-ship.ts`          | No change (already complete)          | —        |
| `server/routes/culture-ship.ts`          | Can delete or keep as fallback        | LOW      |
| `src/culture_ship/health_probe.py` (Hub) | Add cross-repo call (future)          | MEDIUM   |

---

## Risk Assessment

**Low Risk:**

- Comprehensive router is well-structured and tested
- Simple route can be kept as fallback if needed
- No breaking changes to existing API surface (same endpoints)

**Validation:**

- [ ] TypeScript compilation succeeds
- [ ] All imports resolve
- [ ] cultureShipOrchestrator initializes without errors
- [ ] No circular dependencies

---

## Success Criteria

After wiring:

- ✅ All 4 culture-ship endpoints respond at `/api/culture-ship/*`
- ✅ `/health` returns complete component status
- ✅ `/next-actions` provides consciousness-driven suggestions
- ✅ `/deploy-swarm` can trigger agent deployment
- ✅ Request logging shows incoming calls
- ✅ No 404 errors on standard endpoints
- ✅ Integration test suite passes

---

## Testing Strategy

### Unit Level

```bash
npm run test -- --grep "culture-ship"
```

### Integration Level

```bash
# Start server
npm run dev

# In another terminal, test endpoints:
npm run test -- test/integration/culture-ship.test.ts
```

### Cross-Repo Level (Future)

```python
# From NuSyQ-Hub
python scripts/orchestrator_cli.py diff-viewer
# Verify SimulatedVerse health endpoint is reachable
```

---

## Timeline Estimate

- **Wiring:** 15 minutes
- **Testing:** 30 minutes
- **Documentation:** 10 minutes
- **Total:** ~1 hour

---

## Next Steps

1. ✅ Create this implementation guide
2. ⏭️ Modify `server/index.ts` to use comprehensive router
3. ⏭️ Verify TypeScript compilation
4. ⏭️ Run integration tests
5. ⏭️ Test each endpoint manually
6. ⏭️ Document endpoints in API spec
7. ⏭️ Move to Phase 1.2 (Agent Task Router Registration)

---

**Owner:** GitHub Copilot Agent  
**Last Updated:** 2026-01-10 14:26 UTC
