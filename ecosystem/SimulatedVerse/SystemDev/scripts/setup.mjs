#!/usr/bin/env node
// [Ω:root:setup@scaffold] Bootstrap missing directories and files

import { mkdir, writeFile, access } from 'fs/promises';
import { join } from 'path';

const REQUIRED_DIRS = [
  'protocol',
  'registry', 
  'bootstrap',
  'config/profiles',
  'features',
  'core/types',
  'core/errors',
  'core/events', 
  'core/time',
  'ui/ascii',
  'ui/components',
  'assets/ascii',
  'assets/fonts',
  'docs',
  'scripts',
  'sims',
  'build',
  'state',
  'content',
  'dev'
];

const TEMPLATE_FILES = {
  '.env.template': `# CoreLink Foundation - Environment Template
# Copy to .env and fill in values

# Profile Selection
BOOT_PROFILE=dev

# Optional API Keys (add to Replit Secrets)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Development Flags
DEBUG=false
TRACE=false
SAFE_MODE=false`,

  'docs/PLAYBOOK.md': `# CoreLink Foundation - Quickstart Playbook

## 🚀 One-Screen Setup

1. **Clone & Install**
   \`\`\`bash
   npm install
   npm run setup
   \`\`\`

2. **Configure Environment**
   - Copy \`.env.template\` to \`.env\`
   - Add secrets via Replit Secrets panel
   - Set \`BOOT_PROFILE=dev\`

3. **Run System**
   \`\`\`bash
   npm run dev
   \`\`\`

## 🎯 Key Commands

- \`npm run health\` - System health check
- \`npm run graph\` - Dependency visualization  
- \`npm run fix\` - Auto-fix linting and formatting
- \`npm run council:check\` - Validate SCP approvals

## 🏗️ Architecture

- \`/protocol/\` - SCP Council governance and communication
- \`/registry/\` - Module definitions and symbol mapping
- \`/features/\` - Feature-based module organization
- \`/core/\` - Shared primitives (no cross-feature imports)

## 🎮 Progression System

System unlocks features through tier progression:
- Tier -1: Deep Sleep (45s)
- Tier 0: System Boot (3min)  
- Tier 1: Survival Protocols (10min)
- Tier 2: Expansion Framework (30min)

See \`/protocol/unlocks.json\` for full progression tree.`,

  'docs/SECRETS.md': `# Secret Configuration Guide

## Required Secrets (Production)
- \`DATABASE_URL\` - PostgreSQL connection string
- \`JWT_SECRET\` - Authentication token signing key

## Optional Secrets (Development)
- \`OPENAI_API_KEY\` - AI functionality (fallback to mock)
- \`ANTHROPIC_API_KEY\` - Alternative AI provider
- \`SENTRY_DSN\` - Error monitoring (development optional)

## Setup in Replit
1. Click "Secrets" in sidebar
2. Add key-value pairs (no quotes needed)
3. Restart application after adding secrets

## Mock Mode
Set \`FAKE_MODE=true\` to use mock providers when secrets are missing.
This allows development without external API dependencies.`,

  'dev/scratch.md': `# Development Scratch Pad
<!-- This file resets each session - use for temporary notes -->

## Current Session Notes
- 

## Quick References
- Council Msg: [Msg⛛{ROLE}↗️Σ∞] finding → location → action
- OmniTag: [Ω:module:verb:hint]
- Symbol: 🜁⊙⟦ΞΣΛΘΦ⟧ ÷ 🛠 {context}`
};

async function ensureDir(path) {
  try {
    await access(path);
  } catch {
    await mkdir(path, { recursive: true });
    console.log(`✓ Created directory: ${path}`);
  }
}

async function ensureFile(path, content) {
  try {
    await access(path);
  } catch {
    await writeFile(path, content);
    console.log(`✓ Created file: ${path}`);
  }
}

async function main() {
  console.log('🜁 CoreLink Foundation - Project Setup');
  console.log('=====================================\n');
  
  // Create required directories
  for (const dir of REQUIRED_DIRS) {
    await ensureDir(dir);
  }
  
  // Create template files
  for (const [filePath, content] of Object.entries(TEMPLATE_FILES)) {
    await ensureFile(filePath, content);
  }
  
  console.log('\n✓ Project scaffold complete!');
  console.log('\nNext steps:');
  console.log('1. Copy .env.template to .env');
  console.log('2. Add any required secrets via Replit Secrets');  
  console.log('3. Run: npm run dev');
  console.log('\nSee docs/PLAYBOOK.md for detailed guidance.');
}

main().catch(console.error);