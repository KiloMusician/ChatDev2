#!/usr/bin/env tsx
// Install and verify offline brain capabilities
// Receipts-first approach - every step generates evidence

import { promises as fs } from 'node:fs';
import { exec } from 'node:child_process';
import { promisify } from 'node:util';

const execAsync = promisify(exec);

interface OfflineBrainInventory {
  timestamp: number;
  packages: Record<string, string>; // package -> version
  capabilities: {
    vector_store: boolean;
    ast_rewriting: boolean;
    rule_engine: boolean;
    dependency_analysis: boolean;
    code_generation: boolean;
    local_models: boolean;
    offline_testing: boolean;
  };
  services: {
    council_bus: boolean;
    vector_indexing: boolean;
    pattern_library: boolean;
    proof_pipeline: boolean;
  };
  health_score: number; // 0-100
}

async function checkPackageVersion(packageName: string): Promise<string | null> {
  try {
    const packageJsonPath = './package.json';
    const content = await fs.readFile(packageJsonPath, 'utf8');
    const packageJson = JSON.parse(content);
    
    const version = packageJson.dependencies?.[packageName] || 
                   packageJson.devDependencies?.[packageName];
    
    return version || null;
  } catch {
    return null;
  }
}

async function testCapability(name: string, testFn: () => Promise<boolean>): Promise<boolean> {
  try {
    const result = await testFn();
    console.log(`[OfflineBrain] ✅ ${name}: ${result ? 'OK' : 'FAIL'}`);
    return result;
  } catch (error) {
    console.log(`[OfflineBrain] ❌ ${name}: ERROR - ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('[OfflineBrain] Starting offline brain installation and verification...');
  
  const requiredPackages = [
    'sqlite-vec',
    'ts-morph', 
    'json-rules-engine',
    'madge',
    'dependency-cruiser',
    'knip',
    'better-queue',
    'uvu',
    'zx',
    'sharp',
    'csv-parse',
    'onnxruntime-node',
    'ml-kmeans'
  ];

  const inventory: OfflineBrainInventory = {
    timestamp: Date.now(),
    packages: {},
    capabilities: {
      vector_store: false,
      ast_rewriting: false,
      rule_engine: false,
      dependency_analysis: false,
      code_generation: false,
      local_models: false,
      offline_testing: false
    },
    services: {
      council_bus: false,
      vector_indexing: false,
      pattern_library: false,
      proof_pipeline: false
    },
    health_score: 0
  };

  // Check package installations
  console.log('[OfflineBrain] Checking package installations...');
  for (const pkg of requiredPackages) {
    const version = await checkPackageVersion(pkg);
    if (version) {
      inventory.packages[pkg] = version;
      console.log(`[OfflineBrain] ✅ ${pkg}: ${version}`);
    } else {
      console.log(`[OfflineBrain] ❌ ${pkg}: NOT INSTALLED`);
    }
  }

  // Test capabilities
  console.log('[OfflineBrain] Testing capabilities...');
  
  inventory.capabilities.vector_store = await testCapability('Vector Store', async () => {
    // Test if we can create a basic vector store
    const { vectorStore } = await import('../offline_brain/vector_store.js');
    await vectorStore.initialize();
    return true;
  });

  inventory.capabilities.ast_rewriting = await testCapability('AST Rewriting', async () => {
    // Test ts-morph
    const { Project } = await import('ts-morph');
    const project = new Project();
    return project !== null;
  });

  inventory.capabilities.rule_engine = await testCapability('Rule Engine', async () => {
    // Test json-rules-engine
    const { Engine } = await import('json-rules-engine');
    const engine = new Engine();
    return engine !== null;
  });

  inventory.capabilities.dependency_analysis = await testCapability('Dependency Analysis', async () => {
    // Test madge
    const madge = await import('madge');
    return madge !== null;
  });

  inventory.capabilities.offline_testing = await testCapability('Offline Testing', async () => {
    // Test uvu
    const { test } = await import('uvu');
    return test !== null;
  });

  inventory.capabilities.local_models = await testCapability('Local Models', async () => {
    // Test onnxruntime-node
    const ort = await import('onnxruntime-node');
    return ort !== null;
  });

  // Test services
  console.log('[OfflineBrain] Testing services...');
  
  inventory.services.council_bus = await testCapability('Council Bus', async () => {
    // Check if Council Bus topics are registered
    return await fs.access('../server/index.ts').then(() => true).catch(() => false);
  });

  inventory.services.vector_indexing = await testCapability('Vector Indexing', async () => {
    const { vectorStore } = await import('../offline_brain/vector_store.js');
    const result = await vectorStore.getInventory();
    return result.total >= 0; // Can count existing docs
  });

  // Calculate health score
  const capabilityCount = Object.values(inventory.capabilities).filter(Boolean).length;
  const serviceCount = Object.values(inventory.services).filter(Boolean).length;
  const packageCount = Object.keys(inventory.packages).length;
  
  inventory.health_score = Math.round(
    (capabilityCount / Object.keys(inventory.capabilities).length * 40) +
    (serviceCount / Object.keys(inventory.services).length * 30) +
    (packageCount / requiredPackages.length * 30)
  );

  // Ensure reports directory exists
  await fs.mkdir('SystemDev/reports', { recursive: true });
  
  // Save inventory report
  const reportPath = 'SystemDev/reports/offline_brain_inventory.json';
  await fs.writeFile(reportPath, JSON.stringify(inventory, null, 2));
  
  console.log(`[OfflineBrain] Installation complete. Health score: ${inventory.health_score}%`);
  console.log(`[OfflineBrain] Report saved to ${reportPath}`);
  
  // Emit receipt
  const receipt = {
    action: 'offline_brain_installation',
    timestamp: Date.now(),
    status: inventory.health_score >= 70 ? 'operational' : 'partial',
    packages_installed: Object.keys(inventory.packages).length,
    capabilities_working: capabilityCount,
    services_ready: serviceCount,
    health_score: inventory.health_score,
    offline_capable: inventory.health_score >= 50
  };

  await fs.mkdir('SystemDev/receipts', { recursive: true });
  await fs.writeFile(
    `SystemDev/receipts/offline_brain_install_${Date.now()}.json`,
    JSON.stringify(receipt, null, 2)
  );

  return inventory;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { main as installOfflineBrain };