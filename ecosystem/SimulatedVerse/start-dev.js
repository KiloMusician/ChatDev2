#!/usr/bin/env node

// Temporary workaround script to start the development server
// without using tsx which has dependency conflicts

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Set environment
process.env.NODE_ENV = 'development';

// Start with ts-node and ESM loader
const child = spawn('node', [
  '--loader', 
  'ts-node/esm',
  '--experimental-specifier-resolution=node',
  join(__dirname, 'server/index.ts')
], {
  stdio: 'inherit',
  env: process.env
});

child.on('close', (code) => {
  process.exit(code);
});

child.on('error', (err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});