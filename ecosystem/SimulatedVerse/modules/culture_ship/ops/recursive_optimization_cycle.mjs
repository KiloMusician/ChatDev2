#!/usr/bin/env node
import { RecursiveOptimizer } from "../optimization/recursive_optimizer.mjs";

console.log('⚡ Executing Recursive Optimization Cycle...');

const optimizer = new RecursiveOptimizer();

console.log('⚡ Phase 1: Nested Optimization...');
const optimizationResult = await optimizer.executeNestedOptimization();
console.log('✨ Optimization Result:', optimizationResult);

console.log('📊 Recursive Optimization State:');
const optimizationState = optimizer.getOptimizationState();
console.log('✨ State:', optimizationState);

console.log('\n✅ Recursive Optimization Complete!');
console.log(`   Layers Optimized: ${optimizationResult.layers_optimized}`);
console.log(`   Total Efficiency Gain: ${optimizationResult.total_efficiency_gain}`);
console.log(`   Avg Efficiency: ${optimizationState.avg_efficiency}`);