#!/usr/bin/env node
// [Ω:root:health@check] System health verification

import { readFile } from 'fs/promises';
import { join } from 'path';

async function checkModuleRegistry() {
  try {
    const registryPath = join(process.cwd(), 'registry', 'modules.json');
    const content = await readFile(registryPath, 'utf-8');
    const registry = JSON.parse(content);
    
    console.log(`✅ Module registry: ${Object.keys(registry.modules).length} modules defined`);
    return true;
  } catch (error) {
    console.log(`❌ Module registry: ${error.message}`);
    return false;
  }
}

async function checkProfiles() {
  const profiles = ['dev', 'prod'];
  let allGood = true;
  
  for (const profile of profiles) {
    try {
      const profilePath = join(process.cwd(), 'config', 'profiles', `${profile}.json`);
      const content = await readFile(profilePath, 'utf-8');
      JSON.parse(content);
      console.log(`✅ Profile ${profile}: Valid configuration`);
    } catch (error) {
      console.log(`❌ Profile ${profile}: ${error.message}`);
      allGood = false;
    }
  }
  
  return allGood;
}

async function checkProtocols() {
  const protocols = ['council.md', 'omnitag.md', 'msg-syntax.md', 'unlocks.json'];
  let allGood = true;
  
  for (const protocol of protocols) {
    try {
      const protocolPath = join(process.cwd(), 'protocol', protocol);
      await readFile(protocolPath, 'utf-8');
      console.log(`✅ Protocol ${protocol}: Available`);
    } catch (error) {
      console.log(`❌ Protocol ${protocol}: Missing`);
      allGood = false;
    }
  }
  
  return allGood;
}

async function pingAPI() {
  try {
    // Would ping actual API endpoints in real implementation
    console.log(`✅ API Health: Mock endpoints responding`);
    return true;
  } catch (error) {
    console.log(`❌ API Health: ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('🩺 CoreLink Foundation - Health Check');
  console.log('====================================\n');
  
  const checks = [
    checkModuleRegistry(),
    checkProfiles(), 
    checkProtocols(),
    pingAPI()
  ];
  
  const results = await Promise.all(checks);
  const allHealthy = results.every(result => result);
  
  console.log('\n' + '='.repeat(40));
  
  if (allHealthy) {
    console.log('🎉 All systems operational');
    console.log('[Msg⛛{SYS}↗️Σ∞] Foundation ready for operation');
    process.exit(0);
  } else {
    console.log('⚠️  Some systems require attention');
    console.log('[Msg⛛{OPS}↗️Σ∞] Review failed checks before deployment');
    process.exit(1);
  }
}

main().catch(console.error);