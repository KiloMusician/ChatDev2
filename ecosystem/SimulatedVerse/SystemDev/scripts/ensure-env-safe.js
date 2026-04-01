#!/usr/bin/env node
// Hard kill any AI/token path. Keeps spend at $0.
const forbidden = [
  'OPENAI_API_KEY','ANTHROPIC_API_KEY','REPLIT_AI','REPLIT_MODELS',
  'GOOGLE_API_KEY','AZURE_OPENAI_KEY','CLAUDE_API_KEY','GEMINI_API_KEY',
  'HUGGINGFACE_API_TOKEN','COHERE_API_KEY','AI21_API_KEY','TOGETHER_API_KEY'
];

let tripped = false;

for (const k of forbidden) {
  if (process.env[k]) { 
    tripped = true; 
    console.error(`[ZERO-AI] 🚨 ${k} detected; refusing to run.`); 
  }
}

if (process.env.REPLIT_AI || process.env.REPLIT_AGENT) { 
  tripped = true; 
  console.error(`[ZERO-AI] 🚨 Replit Agent/AI not allowed.`); 
}

// Check for any suspicious AI-related env vars
const suspiciousPatterns = [
  /.*API.*KEY.*/i,
  /.*TOKEN.*AI.*/i,
  /.*AI.*TOKEN.*/i,
  /.*MODEL.*API.*/i
];

Object.keys(process.env).forEach(key => {
  if (suspiciousPatterns.some(pattern => pattern.test(key))) {
    console.warn(`[ZERO-AI] ⚠️  Suspicious env var: ${key} (check if AI-related)`);
  }
});

if (tripped) { 
  console.error(`[ZERO-AI] ❌ External AI detected - aborting to prevent costs`);
  console.error(`[ZERO-AI] 💰 Zero-token mode enforced - remove AI keys to proceed`);
  process.exit(1); 
}

console.log('[ZERO-AI] ✅ OK: no external AI configured - $0.00 mode active');
console.log('[ZERO-AI] 🤖 Local rule-based agent ready');

// Write safety flag
import { writeFileSync, mkdirSync } from 'fs';
mkdirSync('.agent', { recursive: true });
writeFileSync('.agent/zero_token_verified', `${Date.now()}`);