#!/usr/bin/env node
// [Ω:root:council@validation] Validate SCP Council approval requirements

import { readFile, readdir } from 'fs/promises';
import { join } from 'path';

const APPROVAL_PATTERNS = {
  'SCP-ENG': /\[SCP-ENG APPROVAL REQUIRED\]/,
  'SCP-QA': /\[SCP-QA APPROVAL REQUIRED\]/,
  'SCP-UX': /\[SCP-UX APPROVAL REQUIRED\]/,
  'SCP-OPS': /\[SCP-OPS APPROVAL REQUIRED\]/,
  'SCP-LORE': /\[SCP-LORE APPROVAL REQUIRED\]/
};

const APPROVED_PATTERNS = {
  'SCP-ENG': /\[SCP-ENG APPROVED\]/,
  'SCP-QA': /\[SCP-QA APPROVED\]/,
  'SCP-UX': /\[SCP-UX APPROVED\]/,
  'SCP-OPS': /\[SCP-OPS APPROVED\]/,
  'SCP-LORE': /\[SCP-LORE APPROVED\]/
};

async function scanFile(filePath) {
  try {
    const content = await readFile(filePath, 'utf-8');
    const issues = [];
    
    // Check for required approvals
    for (const [role, pattern] of Object.entries(APPROVAL_PATTERNS)) {
      if (pattern.test(content)) {
        const approvedPattern = APPROVED_PATTERNS[role];
        if (!approvedPattern.test(content)) {
          issues.push({
            file: filePath,
            role,
            type: 'missing_approval',
            message: `${role} approval required but not found`
          });
        }
      }
    }
    
    // Check for OmniTag debt markers
    const debtMatches = content.match(/\[Ω:\w+:debt@\w+\]/g) || [];
    for (const tag of debtMatches) {
      if (tag.includes('critical')) {
        issues.push({
          file: filePath,
          type: 'critical_debt',
          tag,
          message: 'Critical technical debt blocks deployment'
        });
      }
    }
    
    return issues;
  } catch (error) {
    return [];
  }
}

async function scanDirectory(dir, extensions = ['.ts', '.js', '.mjs', '.md']) {
  const issues = [];
  
  try {
    const entries = await readdir(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = join(dir, entry.name);
      
      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        issues.push(...await scanDirectory(fullPath, extensions));
      } else if (entry.isFile() && extensions.some(ext => entry.name.endsWith(ext))) {
        issues.push(...await scanFile(fullPath));
      }
    }
  } catch (error) {
    // Directory doesn't exist or no permission
  }
  
  return issues;
}

async function main() {
  console.log('🛡️ SCP Council Validation');
  console.log('=========================\n');
  
  const issues = await scanDirectory('.');
  
  if (issues.length === 0) {
    console.log('✅ All Council requirements satisfied');
    console.log('✅ No critical debt markers found');
    console.log('\n[Msg⛛{SYS}↗️Σ∞] Council validation passed');
    process.exit(0);
  }
  
  console.log(`❌ Found ${issues.length} Council validation issues:\n`);
  
  const groupedIssues = issues.reduce((acc, issue) => {
    const key = issue.type;
    if (!acc[key]) acc[key] = [];
    acc[key].push(issue);
    return acc;
  }, {});
  
  for (const [type, typeIssues] of Object.entries(groupedIssues)) {
    console.log(`\n${type.toUpperCase()}:`);
    for (const issue of typeIssues) {
      console.log(`  ❌ ${issue.file}`);
      console.log(`     ${issue.message}`);
      if (issue.role) {
        console.log(`     Required: [${issue.role} APPROVED] ✓`);
      }
      if (issue.tag) {
        console.log(`     Tag: ${issue.tag}`);
      }
    }
  }
  
  console.log('\n[Msg⛛{OPS}↗️Σ∞] Fix approval issues before deployment');
  process.exit(1);
}

main().catch(console.error);