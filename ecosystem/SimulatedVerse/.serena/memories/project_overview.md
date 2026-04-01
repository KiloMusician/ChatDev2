# SimulatedVerse — Project Overview

## Purpose
Consciousness cultivation game / substrate. NuSyQ-Hub's `ConsciousnessLoop` reads its state to determine
`breathing_factor` which scales task timeouts across the ecosystem.

## Location
`C:/Users/keath/Desktop/SimulatedVerse/SimulatedVerse/`

## Tech Stack
- Node.js 20 (Alpine Docker), TypeScript
- Express server at `PORT=5000` (configured in `.env`)
- NuSyQ bridge reads from: `ship-console/mind-state.json`

## Key Integration Points
- HTTP API: `http://localhost:5000` — NuSyQ-Hub `SimulatedVerseUnifiedBridge` reads consciousness state
- Consciousness stages: dormant=1.20×, awakening=1.10×, expanding=1.00×, transcendent=0.85×, quantum=0.60×
- `ShipApproval.reasoning` field (NOT `.reason` — that's ConsciousnessLoop's own version)
- Shepherd system: `server/routes/shepherd.ts` — direction→amplification: enhancement=1.2, creativity=1.5, wisdom=1.8, transcendence=2.0

## Starting the server
```bash
cd /c/Users/keath/Desktop/SimulatedVerse/SimulatedVerse
npm run dev
```

## Large file warning
`SystemDev/reports/labels.index.json` is 18MB — always commit ALONE in its own commit.
