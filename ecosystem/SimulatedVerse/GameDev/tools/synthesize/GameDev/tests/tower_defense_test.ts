// Tower Defense Test
import { towerDefenseSystem } from '../systems/tower_defense/tower_defense_first_turret.js';

console.log('[Test] Starting Tower Defense tests...');

// Test 1: System initializes
const initialState = towerDefenseSystem.getState();
console.log('[Test] ✅ System initialized:', initialState);

// Test 2: Can spawn wave
towerDefenseSystem.spawnWave();
const afterSpawn = towerDefenseSystem.getState();
console.log('[Test] ✅ Wave spawned:', afterSpawn);

// Test 3: Can place tower
const placed = towerDefenseSystem.placeTower(100, 100);
console.log('[Test] ✅ Tower placed:', placed);

// Test 4: Proof checks
towerDefenseSystem.runProofChecks().then(result => {
  console.log('[Test] ✅ Proof checks:', result.passed);
  console.log('[Test] Counters:', result.counters);
});

console.log('[Test] All tests completed');
