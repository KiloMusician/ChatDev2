#!/usr/bin/env tsx

/**
 * Emergency Budget System Reset & Health Check
 * Use this to restore system function if budget constraints are blocking operations
 */

import { emergencyReset, getBudgetStatus, recordSuccess } from '../packages/llm/budget-manager';

console.log('🔧 Budget System Health Check & Reset Tool');
console.log('============================================');

// Show current status
console.log('\n📊 Current Budget Status:');
const status = getBudgetStatus();
console.log(`  Requests Used: ${status.requestsUsed}`);
console.log(`  Requests Remaining: ${status.requestsRemainingDisplay}/${status.totalCapacity}`); 
console.log(`  Base Capacity: ${status.baseCapacity}, Adaptive Capacity: ${status.totalCapacity}`);
console.log(`  System Health: ${status.systemHealth}`);
console.log(`  Consecutive Failures: ${status.consecutiveFailures}`);

if (status.consecutiveFailures > 0) {
  console.log('\n🚨 System needs recovery! Applying emergency reset...');
  emergencyReset();
  
  // Verify reset worked
  const newStatus = getBudgetStatus();
  console.log('\n✅ After Reset:');
  console.log(`  System Health: ${newStatus.systemHealth}`);
  console.log(`  Adaptive Capacity: ${newStatus.totalCapacity}/min`);
  console.log(`  Failures Reset: ${newStatus.consecutiveFailures}`);
} else {
  console.log('\n✅ System is healthy! No reset needed.');
  console.log('   Budget optimizations are working correctly.');
}

// Test adaptive scaling
console.log('\n🧪 Testing Adaptive Scaling:');
recordSuccess(); // Simulate successful request
const healthyStatus = getBudgetStatus(); 
console.log(`  Healthy capacity: ${healthyStatus.totalCapacity}/min (${healthyStatus.totalCapacity > healthyStatus.baseCapacity ? 'SCALED UP' : 'NORMAL'})`);