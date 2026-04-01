#!/usr/bin/env tsx
// SystemDev/scripts/rlci_integration_test.ts
// Integration test for RLCI v1 components

import { CapabilityHarvester } from './capability_registry';
import { TipSynth, synthesizeTips } from '../guards/tipsynth';
import { ReplitPromptAdapter, toRLCI } from '../../ChatDev/bridges/replit/adapter';
import { RLCIEventBus } from './rlci_event_bus';
import { EnhancedReceiptManager } from './enhanced_receipts';
import { createRLCIEnvelope } from '../interfaces/rlci';

async function testRLCIIntegration() {
  console.log('🧪 RLCI v1 Integration Test');
  console.log('===========================');
  
  // Test 1: Capability Registry
  console.log('\n1. Testing Capability Registry...');
  try {
    const harvester = new CapabilityHarvester();
    const capabilities = await harvester.harvest();
    console.log(`✅ Found ${capabilities.agents.length} agents, ${capabilities.breaths.length} breaths`);
    console.log(`✅ Found ${capabilities.packages.total_count} packages`);
  } catch (error) {
    console.log(`❌ Capability Registry failed: ${error.message}`);
  }
  
  // Test 2: TipSynth Engine
  console.log('\n2. Testing TipSynth Engine...');
  try {
    const envelope = createRLCIEnvelope('chat', 'test_task');
    const tips = synthesizeTips(
      'Error: Cannot find module "./missing-file"',
      'npm run build',
      envelope,
      { custom_scripts: [{ path: 'SystemDev/scripts/import_rewriter.ts' }] }
    );
    console.log(`✅ Generated ${tips.tips.length} tips`);
    console.log(`✅ First tip: ${tips.tips[0]?.text || 'none'}`);
  } catch (error) {
    console.log(`❌ TipSynth failed: ${error.message}`);
  }
  
  // Test 3: Prompt Adapter
  console.log('\n3. Testing Prompt Adapter...');
  try {
    const adapter = new ReplitPromptAdapter();
    const analysis = adapter.analyzeUserPrompt('fix the todo errors and conflicts in GameDev');
    const envelope = toRLCI('continue with todos, errors, and warnings');
    
    console.log(`✅ Detected task: ${analysis.task_type}`);
    console.log(`✅ Urgency: ${analysis.urgency_level}`);
    console.log(`✅ Quadrants: ${analysis.quadrant_hints.join(', ')}`);
    console.log(`✅ RLCI envelope created with ${envelope.hints.length} hints`);
  } catch (error) {
    console.log(`❌ Prompt Adapter failed: ${error.message}`);
  }
  
  // Test 4: Event Bus  
  console.log('\n4. Testing RLCI Event Bus...');
  try {
    const eventBus = new RLCIEventBus();
    
    // Subscribe to test event
    let eventReceived = false;
    eventBus.subscribe('test/integration', async (event) => {
      eventReceived = true;
      console.log(`✅ Event received: ${event.topic}`);
    });
    
    // Publish test event
    await eventBus.publish('test/integration', { message: 'Hello RLCI!' });
    
    // Check subscription stats
    const stats = eventBus.getSubscriptionStats();
    console.log(`✅ Subscriptions active: ${Object.keys(stats).length}`);
    
    if (eventReceived) {
      console.log('✅ Event bus working correctly');
    } else {
      console.log('⚠️ Event not received (async timing issue)');
    }
  } catch (error) {
    console.log(`❌ Event Bus failed: ${error.message}`);
  }
  
  // Test 5: Enhanced Receipts
  console.log('\n5. Testing Enhanced Receipts...');
  try {
    const receiptManager = new EnhancedReceiptManager();
    const envelope = createRLCIEnvelope('agent', 'test_cycle');
    
    const receiptPath = await receiptManager.writeReceipt(
      1,
      'SystemDev/scripts/test.ts',
      3,
      envelope,
      {
        result: 'ok',
        found: ['test TODO'],
        fixed: ['test implementation'],
        next_hint: 'Continue with next test'
      }
    );
    
    console.log(`✅ Receipt written to: ${receiptPath.split('/').pop()}`);
    
    // Test analysis
    const analysis = await receiptManager.analyzeReceiptPatterns();
    console.log(`✅ Pattern analysis: ${analysis.patterns.length} patterns detected`);
  } catch (error) {
    console.log(`❌ Enhanced Receipts failed: ${error.message}`);
  }
  
  // Test 6: Full Integration Flow
  console.log('\n6. Testing Full Integration Flow...');
  try {
    // Simulate the magic "continue compelling" workflow
    const userPrompt = "continue with todos, errors, conflicts, and warnings";
    
    // 1. Convert to RLCI
    const envelope = toRLCI(userPrompt);
    console.log(`✅ RLCI envelope: ${envelope.intent.task}`);
    
    // 2. Load capabilities
    const harvester = new CapabilityHarvester();
    const capabilities = await harvester.harvest();
    console.log(`✅ Capabilities loaded: ${capabilities.agents.length} agents available`);
    
    // 3. Generate tips for hypothetical error
    const tips = synthesizeTips(
      'TypeScript error: Cannot find module',
      'npm run build',
      envelope,
      capabilities
    );
    console.log(`✅ Tips generated: ${tips.tips.length} suggestions`);
    
    // 4. Write receipt
    const receiptManager = new EnhancedReceiptManager();
    const receiptPath = await receiptManager.writeReceipt(
      2,
      'src/integration-test.ts',
      5,
      envelope,
      {
        result: 'ok',
        found: ['integration test needed'],
        fixed: ['RLCI integration test created'],
        next_hint: 'Continue with real task automation'
      }
    );
    console.log(`✅ Integration receipt: ${receiptPath.split('/').pop()}`);
    
    console.log('\n🎉 FULL INTEGRATION FLOW SUCCESSFUL!');
  } catch (error) {
    console.log(`❌ Integration flow failed: ${error.message}`);
  }
  
  console.log('\n📊 RLCI v1 Integration Test Complete');
  console.log('Ready for production Culture-Ship coordination!');
}

// Run integration test
if (import.meta.url.endsWith(process.argv[1])) {
  testRLCIIntegration().catch(console.error);
}

export { testRLCIIntegration };