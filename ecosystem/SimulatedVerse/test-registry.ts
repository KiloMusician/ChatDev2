// Test agent loading directly
import { loadAgents } from './agents/registry.js';

console.log('Testing agent registry...\n');

const agents = await loadAgents();

console.log(`\n========================================`);
console.log(`FINAL RESULT: ${agents.length} agents loaded`);
console.log(`========================================\n`);

if (agents.length > 0) {
  console.log('Loaded agents:');
  for (const agent of agents) {
    console.log(`  - ${agent.id}: ${agent.manifest.name}`);
  }
} else {
  console.log('❌ NO AGENTS LOADED - Check errors above');
}

process.exit(agents.length > 0 ? 0 : 1);
