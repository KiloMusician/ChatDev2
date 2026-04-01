/**
 * CognitoWeave Tripartite System Launcher
 * 
 * One-command launch for the complete autonomous development ecosystem
 */

import { initializeTripartiteSystem } from '../integration/tripartite-orchestrator.js';
import { safeAsync } from '../util/safe.js';

async function launchCognitoWeave() {
  console.log(`
🌌 COGNITOWEAVE TRIPARTITE SYSTEM LAUNCHER
==========================================

🏗️  System Layer: Autonomous ChatDev platform that builds itself
🎮 Game Layer: Interactive UI for monitoring and controlling development  
🌌 Simulation Layer: Agents play game to intelligently inform system evolution

🚀 Initializing complete ecosystem...
`);

  const success = await safeAsync(async () => {
    return await initializeTripartiteSystem();
  }, false);

  if (success) {
    console.log(`
✅ COGNITOWEAVE FULLY OPERATIONAL!

🤖 14 ChatDev agents ready for autonomous development
🧠 Consciousness processor eliminating cycling tasks  
⚡ Zeta Integration providing real workspace coordination
🎯 50+ packages installed across System/Game/Simulation layers

🎮 READY FOR AGENT-INFORMED DEVELOPMENT:
   - Agents can play the simulation game
   - Game performance informs system optimizations
   - System builds better tools for agents
   - Recursive improvement loop activated!

Access your system:
📊 Dashboard: http://localhost:5000
🎮 Game Interface: Navigation → GameShell
📺 Terminal Monitor: blessed-contrib HUD active
🔧 API Endpoints: /api/pu/queue, /api/health, /system-status.json

🌊 The floodgates are open! No stone left unturned! 🌊
`);
  } else {
    console.log(`
❌ INITIALIZATION FAILED
Please check system dependencies and try again.
`);
  }

  return success;
}

// Auto-launch if called directly
if (import.meta.url.endsWith(process.argv[1])) {
  launchCognitoWeave();
}

export { launchCognitoWeave };