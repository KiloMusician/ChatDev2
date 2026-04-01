#!/usr/bin/env tsx
// SystemDev/scripts/capability_registry.ts
// Capability Registry - Harvest all packages, scripts, CLIs, and agent affordances

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

interface CapabilityRegistry {
  timestamp: string;
  bins: string[];
  scripts: Record<string, string>;
  agents: string[];
  breaths: string[];
  packages: {
    production: string[];
    development: string[];
    total_count: number;
  };
  godot_tools: string[];
  custom_scripts: Array<{
    path: string;
    executable: boolean;
    description?: string;
  }>;
  cli_tools: string[];
}

class CapabilityHarvester {
  private registry: CapabilityRegistry = {
    timestamp: new Date().toISOString(),
    bins: [],
    scripts: {},
    agents: [],
    breaths: [],
    packages: { production: [], development: [], total_count: 0 },
    godot_tools: [],
    custom_scripts: [],
    cli_tools: []
  };

  async harvest(): Promise<CapabilityRegistry> {
    console.log('🔍 Harvesting capability registry...');
    
    await this.harvestPackageJson();
    await this.harvestNodeModulesBins();
    await this.harvestCustomScripts();
    await this.harvestAgents();
    await this.harvestBreaths();
    await this.harvestGodotTools();
    await this.harvestCLITools();
    
    console.log(`📦 Found ${this.registry.packages.total_count} packages`);
    console.log(`🔧 Found ${this.registry.bins.length} binaries`);
    console.log(`🤖 Found ${this.registry.agents.length} agents`);
    console.log(`🌬️ Found ${this.registry.breaths.length} breaths`);
    
    return this.registry;
  }

  private async harvestPackageJson(): Promise<void> {
    try {
      const packageJson = JSON.parse(await fs.promises.readFile('package.json', 'utf-8'));
      
      // Extract scripts
      this.registry.scripts = packageJson.scripts || {};
      
      // Extract dependencies
      const deps = packageJson.dependencies || {};
      const devDeps = packageJson.devDependencies || {};
      
      this.registry.packages.production = Object.keys(deps);
      this.registry.packages.development = Object.keys(devDeps);
      this.registry.packages.total_count = Object.keys(deps).length + Object.keys(devDeps).length;
      
    } catch (error) {
      console.warn('⚠️ Could not read package.json');
    }
  }

  private async harvestNodeModulesBins(): Promise<void> {
    try {
      const binPath = 'node_modules/.bin';
      if (await this.exists(binPath)) {
        const bins = await fs.promises.readdir(binPath);
        this.registry.bins = bins.filter(bin => !bin.startsWith('.'));
      }
    } catch (error) {
      console.warn('⚠️ Could not scan node_modules/.bin');
    }
  }

  private async harvestCustomScripts(): Promise<void> {
    const scriptDirs = [
      'SystemDev/scripts',
      'ChatDev/scripts', 
      'GameDev/scripts',
      'scripts',
      'src/cli'
    ];

    for (const dir of scriptDirs) {
      await this.scanDirectory(dir);
    }
  }

  private async scanDirectory(dirPath: string): Promise<void> {
    try {
      if (!(await this.exists(dirPath))) return;
      
      const entries = await fs.promises.readdir(dirPath, { withFileTypes: true });
      
      for (const entry of entries) {
        if (entry.isFile()) {
          const fullPath = path.join(dirPath, entry.name);
          const isExecutable = await this.isExecutable(fullPath);
          
          if (isExecutable || entry.name.endsWith('.ts') || entry.name.endsWith('.js')) {
            const description = await this.extractDescription(fullPath);
            
            this.registry.custom_scripts.push({
              path: fullPath,
              executable: isExecutable,
              description
            });
          }
        } else if (entry.isDirectory() && !entry.name.startsWith('.')) {
          await this.scanDirectory(path.join(dirPath, entry.name));
        }
      }
    } catch (error) {
      // Directory doesn't exist or can't be read
    }
  }

  private async harvestAgents(): Promise<void> {
    const agentDirs = ['ChatDev/agents', 'src/agents', 'agent'];
    
    for (const dir of agentDirs) {
      try {
        if (!(await this.exists(dir))) continue;
        
        const entries = await fs.promises.readdir(dir);
        for (const entry of entries) {
          if (entry.includes('agent') || entry.includes('Agent')) {
            const agentName = entry.replace(/\.(ts|js|py)$/, '').replace(/^agent[_-]?/i, '');
            if (!this.registry.agents.includes(agentName)) {
              this.registry.agents.push(agentName);
            }
          }
        }
      } catch (error) {
        // Directory doesn't exist
      }
    }
    
    // Also check for known agent names in existing files
    const knownAgents = [
      'navigator', 'janitor', 'raven', 'artificer', 'alchemist', 
      'librarian', 'culture_ship', 'wizard', 'skeptic', 'guardian'
    ];
    
    for (const agent of knownAgents) {
      if (!this.registry.agents.includes(agent)) {
        this.registry.agents.push(agent);
      }
    }
  }

  private async harvestBreaths(): Promise<void> {
    // Known breath patterns from the system
    const knownBreaths = [
      'bootstrap', 'consolidation', 'cascade', 'recall', 'msgX', 'sage',
      'entropy', 'theater', 'issues', 'ship', 'temple', 'redstone',
      'anneal', 'deepmerge', 'rosetta', 'colony', 'symbiosis', 'zeta',
      'enemy', 'idle', 'boss', 'quantum_wink', 'culture_ship'
    ];
    
    this.registry.breaths = knownBreaths;
    
    // Scan for breath files
    const breathDirs = ['content/breaths', 'ChatDev/directives', 'SystemDev/breaths'];
    
    for (const dir of breathDirs) {
      try {
        if (!(await this.exists(dir))) continue;
        
        const entries = await fs.promises.readdir(dir);
        for (const entry of entries) {
          const breathName = entry.replace(/\.(md|json|ts|js)$/, '');
          if (!this.registry.breaths.includes(breathName)) {
            this.registry.breaths.push(breathName);
          }
        }
      } catch (error) {
        // Directory doesn't exist
      }
    }
  }

  private async harvestGodotTools(): Promise<void> {
    try {
      // Check for Godot executable
      const godotPaths = [
        '/usr/bin/godot',
        '/usr/local/bin/godot',
        'GameDev/engine/godot/bin/godot'
      ];
      
      for (const godotPath of godotPaths) {
        if (await this.exists(godotPath)) {
          this.registry.godot_tools.push('godot');
          break;
        }
      }
      
      // Check for GDScript tools
      if (this.registry.bins.includes('gdformat')) {
        this.registry.godot_tools.push('gdformat');
      }
      
      // Check for custom Godot scripts
      const godotScriptDirs = ['GameDev/engine/godot', 'GameDev/scripts'];
      for (const dir of godotScriptDirs) {
        if (await this.exists(dir)) {
          this.registry.godot_tools.push(`${dir}/*`);
        }
      }
    } catch (error) {
      // Godot tools not available
    }
  }

  private async harvestCLITools(): Promise<void> {
    const cliTools = [
      'git', 'npm', 'yarn', 'pnpm', 'tsx', 'node', 'python3', 'python',
      'curl', 'wget', 'jq', 'grep', 'find', 'sed', 'awk'
    ];
    
    for (const tool of cliTools) {
      try {
        execSync(`which ${tool}`, { stdio: 'ignore' });
        this.registry.cli_tools.push(tool);
      } catch (error) {
        // Tool not available
      }
    }
  }

  private async extractDescription(filePath: string): Promise<string | undefined> {
    try {
      const content = await fs.promises.readFile(filePath, 'utf-8');
      const lines = content.split('\n').slice(0, 10);
      
      for (const line of lines) {
        if (line.includes('//') && (line.includes('description') || line.includes('Purpose'))) {
          return line.replace(/^[\/\*\s]*/, '').replace(/\*\/$/, '').trim();
        }
      }
    } catch (error) {
      // Could not read file
    }
    return undefined;
  }

  private async isExecutable(filePath: string): Promise<boolean> {
    try {
      const stats = await fs.promises.stat(filePath);
      return !!(stats.mode & parseInt('111', 8));
    } catch (error) {
      return false;
    }
  }

  private async exists(path: string): Promise<boolean> {
    try {
      await fs.promises.access(path);
      return true;
    } catch {
      return false;
    }
  }
}

// Main execution
async function main() {
  const harvester = new CapabilityHarvester();
  const registry = await harvester.harvest();
  
  // Write capability registry
  const outputPath = 'SystemDev/reports/capabilities.json';
  await fs.promises.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.promises.writeFile(outputPath, JSON.stringify(registry, null, 2));
  
  console.log(`📋 Capability registry written to: ${outputPath}`);
  
  // Write receipt
  const receipt = {
    timestamp: new Date().toISOString(),
    operation: 'capability_registry_harvest',
    status: 'complete',
    capabilities_found: {
      packages: registry.packages.total_count,
      scripts: Object.keys(registry.scripts).length,
      bins: registry.bins.length,
      agents: registry.agents.length,
      breaths: registry.breaths.length,
      custom_scripts: registry.custom_scripts.length
    },
    registry_path: outputPath
  };
  
  const receiptPath = `SystemDev/receipts/capability_harvest_${Date.now()}.json`;
  await fs.promises.writeFile(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(`🧾 Receipt: ${receiptPath}`);
  return registry;
}

if (import.meta.url.endsWith(process.argv[1])) {
  main().catch(console.error);
}

export { CapabilityHarvester };