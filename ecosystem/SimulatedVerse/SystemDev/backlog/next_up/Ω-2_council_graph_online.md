# Card Ω-2 — Council Graph Online

**Goal**: Wire council.graph.ts into existing Navigator Breath and emit Culture-Ship events

**Priority**: HIGH - Core deterministic micro-cycle integration

## Steps (≤8 edits)

- [ ] **1. CLI Wrapper**: Create SystemDev/scripts/run_council.ts for easy execution
- [ ] **2. Express Integration**: Add /api/council/run endpoint to server/routes.ts  
- [ ] **3. Navigator Integration**: Connect council graph to existing Navigator agent
- [ ] **4. Council Bus Events**: Ensure council:run events reach Culture-Ship HUD
- [ ] **5. Receipt Persistence**: Verify council receipts save to SystemDev/receipts/
- [ ] **6. Error Handling**: Implement graceful fallbacks for missing dependencies
- [ ] **7. Performance Tuning**: Configure queue concurrency for mobile (Samsung S23)
- [ ] **8. Culture HUD Display**: Show council execution status in game interface

## Implementation

```typescript
// SystemDev/scripts/run_council.ts
#!/usr/bin/env tsx
import { runCouncilOnce } from "./council.graph.js";

const mode = process.argv[2] || "audit";
const quadrants = process.argv.slice(3);

runCouncilOnce({ mode, quadrants }).then(result => {
  console.log(`Council execution complete: ${result.receipts?.length || 0} breaths`);
  process.exit(0);
}).catch(error => {
  console.error("Council execution failed:", error);
  process.exit(1);
});
```

```typescript
// server/routes.ts addition
app.post("/api/council/run", async (req, res) => {
  try {
    const { mode = "audit", quadrants = ["SystemDev"] } = req.body;
    const result = await runCouncilOnce({ mode, quadrants });
    res.json({ success: true, result });
  } catch (error) {
    res.status(500).json({ error: String(error) });
  }
});
```

## Commands

```bash
# Direct execution
tsx SystemDev/scripts/run_council.ts audit SystemDev ChatDev

# Via API
curl -X POST http://localhost:5000/api/council/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"audit","quadrants":["SystemDev","GameDev"]}'

# Check receipts
ls -la SystemDev/receipts/bootstrap_*.json
```

## Success Criteria

✅ Council graph executes deterministically through all Breaths  
✅ Council:run events appear in Culture-Ship HUD  
✅ Receipt files generated in SystemDev/receipts/ with proper schemas  
✅ API endpoint responds correctly with execution summary  
✅ Navigator agent can trigger council cycles based on system state  
✅ Mobile performance acceptable (≤2 concurrent operations)

## Receipt Pattern

```json
{
  "breath": "council_online",
  "ok": true,
  "details": {
    "api_endpoint_active": true,
    "navigator_integration": true,
    "culture_hud_events": true,
    "receipt_persistence": true,
    "mobile_performance": "acceptable"
  },
  "ts": "ISO_TIMESTAMP",
  "edit_count": 3
}
```