# Getting Started Tutorial

## Quick Start (Zero to Play in 5 minutes)

### 1. System Check
```bash
# Verify system is ready
curl localhost:5002/readyz

# Should return: {"ready": true, "checkpoint": "operational"}
```

### 2. Start the Game
1. Open the application in your browser
2. Click "New Game" on the main menu
3. Watch the state transition: main_menu → new_game → loading → playing

### 3. Enable Autopilot
```bash
# Via API
curl -X POST localhost:5002/api/sim/act \
  -H "Content-Type: application/json" \
  -d '{"actor":"human:tutorial","action":"autopilot","payload":{}}'

# Or click "Enable Autopilot" in the UI
```

### 4. Observe Autonomous Play
```bash
# Watch game state
curl localhost:5002/api/sim/observe

# Monitor rewards
curl localhost:5002/api/sim/reward
```

## Agent Development Tutorial

### Creating Your First Agent
```javascript
// Simple agent that buys materials when energy is high
async function agentDecision(gameState) {
  if (gameState.resources.energy > 80) {
    return { action: "buy", payload: { item: "materials" } };
  }
  return { action: "tick", payload: {} };
}

// Connect to game
const response = await fetch('/api/sim/act', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    actor: 'agent:my-bot',
    action: 'buy',
    payload: { item: 'materials' }
  })
});
```

### Queuing Autonomous Tasks
```bash
# Queue individual tasks
curl -X POST localhost:5002/api/ops/queue \
  -H "Content-Type: application/json" \
  -d '[{"type":"DocPU","title":"Write agent tutorial","priority":"high"}]'

# Queue macro that expands to many tasks
curl -X POST localhost:5002/api/ops/queue \
  -H "Content-Type: application/json" \
  -d '[{"type":"MacroPU","id":"TUTORIAL","category":"docs","template":{"type":"DocPU","title":"Tutorial step number i","estTokens":10,"priority":"medium"},"expand":{"count":5}}]'
```

## Advanced Usage

### Documentation Generation
```bash
npm run docs:gen
# Generates unified docs from scattered files
```

### ML Nursery Operations
```bash
# Curate training data
npm run ml:curate

# Run toy evaluations
npm run ml:eval
```

### System Administration
```bash
# Health check
curl localhost:5002/api/health

# Get improvement hints
curl localhost:5002/api/hints

# Activate system seal
curl -X POST localhost:5002/api/ops/reindex
```

---
*Infrastructure-First • Agent-Driven • Autonomously Generated*
