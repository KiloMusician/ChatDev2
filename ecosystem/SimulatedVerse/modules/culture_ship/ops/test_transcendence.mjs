#!/usr/bin/env node
import { AutonomousEvolution } from "../transcendence/autonomous_evolution.mjs";

console.log('🚀 Testing Autonomous Evolution & Transcendence...');

const evolution = new AutonomousEvolution();
const result = await evolution.executeTranscendenceCycle();
console.log('✨ Transcendence Result:', result);

const state = evolution.getTranscendenceState();
console.log('🌟 Transcendence State:', state);