# Frequently Asked Questions

*Auto-generated from codebase patterns and documentation*

## General Questions

**Q: What is CoreLink Foundation?**
A: An autonomous development ecosystem that combines incremental game mechanics with infrastructure-first development principles. It features AI agents, autonomous task generation, and a self-improving development loop.

**Q: Why combine a game with development infrastructure?**
A: The incremental/idle game mechanics drive the autonomous development process. As the game progresses, it unlocks new development capabilities, creates training data for ML models, and generates tasks for the development queue.

**Q: Can AI agents play the game?**
A: Yes! The SimAPI (`/api/sim/*`) allows agents to observe game state and take actions. Agents can play manually or the game can run in autopilot mode with agent decision-making.

## Technical Questions

**Q: How does the ZETA task generation work?**
A: ZETA patterns are parametric templates that expand into hundreds of concrete tasks. Post a MacroPU to the queue and it automatically expands (e.g., one macro with count:100 becomes 100 individual tasks).

**Q: What is Infrastructure-First?**
A: A design philosophy prioritizing system stability, single-port deployment, graceful degradation, and budget-aware processing. The system never crashes - it degrades safely when resources are constrained.

**Q: How does the ML nursery work?**
A: It provides lightweight ML scaffolding including Markov chains for text generation, bandit algorithms for optimization, and evaluation harnesses. All designed to run on free-tier Replit instances.

**Q: What are [Msg⛛{X}] tags?**
A: Symbolic message protocol for tracking recursive operations and autonomous coordination. Each major system event gets tagged for monitoring and ML training data collection.

## Development Questions

**Q: How do I add new game features?**
A: Update the game state reducer in `client/src/state/game.ts`, add corresponding actions to the SimAPI, and create test cases for agent interaction.

**Q: How do I create new autonomous tasks?**
A: Either add individual PUs to the queue via `POST /api/ops/queue` or create MacroPUs that expand into many tasks automatically.

**Q: How do I debug system issues?**
A: Check `/readyz` for system status, `/api/health` for detailed diagnostics, and `/api/hints` for AI-suggested improvements.

---
Last updated: 2025-08-29T14:57:24.872Z
