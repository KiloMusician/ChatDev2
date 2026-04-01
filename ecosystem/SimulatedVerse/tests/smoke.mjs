#!/usr/bin/env node
// [Ω:root:test@smoke] Minimal boot test to verify system integrity

import { boot } from '../bootstrap/init.js';

async function smokeTest() {
  console.log('🔥 Smoke Test - Minimal System Boot');
  console.log('===================================\n');
  
  try {
    const bootContext = await boot('dev');
    
    console.log('✅ Boot successful');
    console.log(`✅ Profile: ${bootContext.profile}`);
    console.log(`✅ Modules: ${Object.keys(bootContext.modules).join(', ')}`);
    console.log(`✅ Fingerprint: ${bootContext.fingerprint}`);
    console.log(`✅ Boot time: ${Date.now() - bootContext.startTime}ms`);
    
    console.log('\n[Msg⛛{SYS}↗️Σ∞] Smoke test passed - core systems functional');
    return true;
    
  } catch (error) {
    console.log(`❌ Boot failed: ${error.message}`);
    console.log('\n[Msg⛛{OPS}↗️Σ∞] Smoke test failed - check system integrity');
    return false;
  }
}

smokeTest()
  .then(success => process.exit(success ? 0 : 1))
  .catch(error => {
    console.error('💥 Smoke test crashed:', error);
    process.exit(1);
  });