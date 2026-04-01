// [Ω:root:registry@loader] Module registration and dependency resolution
import { readFile } from 'fs/promises';
import { join } from 'path';
import type { ModuleInfo } from '../core/types';

interface ModuleRegistry {
  version: string;
  modules: Record<string, ModuleInfo>;
}

export async function setupModules(enabledModuleIds: string[]): Promise<Record<string, any>> {
  const registryPath = join(process.cwd(), 'registry', 'modules.json');
  const content = await readFile(registryPath, 'utf-8');
  const registry = JSON.parse(content) as ModuleRegistry;
  
  const modules: Record<string, any> = {};
  const resolved = new Set<string>();
  
  // Resolve dependencies recursively
  async function resolveModule(moduleId: string): Promise<void> {
    if (resolved.has(moduleId)) return;
    
    const moduleInfo = registry.modules[moduleId];
    if (!moduleInfo) {
      throw new Error(`Module not found: ${moduleId}`);
    }
    
    // Resolve dependencies first
    for (const depId of moduleInfo.dependencies) {
      await resolveModule(depId);
    }
    
    // Mock module loading (in real implementation, would import actual modules)
    modules[moduleId] = {
      id: moduleId,
      info: moduleInfo,
      status: 'loaded',
      loadTime: Date.now()
    };
    
    resolved.add(moduleId);
    console.log(`[REGISTRY] ✓ Loaded module: ${moduleId}`);
  }
  
  // Load all enabled modules
  for (const moduleId of enabledModuleIds) {
    await resolveModule(moduleId);
  }
  
  console.log(`[REGISTRY] ✓ Loaded ${resolved.size} modules with dependencies`);
  return modules;
}