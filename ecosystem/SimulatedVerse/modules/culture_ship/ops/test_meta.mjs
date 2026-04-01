#!/usr/bin/env node
import { MetaOptimizer } from "../emergence/meta_optimizer.mjs";

console.log('🔮 Testing Meta-Optimization Cycle...');

const optimizer = new MetaOptimizer();
const result = await optimizer.executeMetaOptimizationCycle();
console.log('✨ Meta-Cycle Result:', result);

const state = optimizer.getMetaState();
console.log('🌟 Meta-State:', state);