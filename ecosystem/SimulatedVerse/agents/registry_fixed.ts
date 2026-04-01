// agents/registry.ts
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import yaml from "yaml";
import { z } from "zod";
import { Agent, AgentManifest } from "../shared/agents/contract.js";

const ROOT = path.resolve("agents");

export type LoadedAgent = { id: string; manifest: z.infer<typeof AgentManifest>; impl: Agent };

export async function loadAgents(): Promise<LoadedAgent[]> {
  const out: LoadedAgent[] = [];
  
  console.log(`[Registry] Loading agents from: ${ROOT}`);
  
  if (!fs.existsSync(ROOT)) {
    console.warn(`[Registry] Agents directory not found: ${ROOT}`);
    return out;
  }
  
  const dirs = fs.readdirSync(ROOT);
  console.log(`[Registry] Found ${dirs.length} potential agent directories`);
  
  for (const dir of dirs) {
    const agentDir = path.join(ROOT, dir);
    
    // Skip non-directories
    try {
      if (!fs.statSync(agentDir).isDirectory()) {
        continue;
      }
    } catch {
      continue;
    }
    
    const mf = path.join(agentDir, "manifest.yaml");
    const ix = path.join(agentDir, "index.ts");
    
    const hasManifest = fs.existsSync(mf);
    const hasIndex = fs.existsSync(ix);
    
    if (!hasManifest || !hasIndex) {
      console.log(`[Registry] Skipping ${dir}: manifest=${hasManifest}, index=${hasIndex}`);
      continue;
    }
    
    try {
      // Parse manifest
      const manifestContent = fs.readFileSync(mf, "utf-8");
      const manifestData = yaml.parse(manifestContent);
      console.log(`[Registry] Loading ${dir}: ${manifestData.name || manifestData.id}`);
      
      const manifest = AgentManifest.parse(manifestData);
      
      // Convert Windows path to file:// URL for ESM import
      const modulePath = path.resolve(ix);
      const moduleURL = pathToFileURL(modulePath).href;
      console.log(`[Registry] Importing ${dir} from: ${moduleURL}`);
      
      const module = await import(moduleURL);
      
      // Try to find agent implementation
      // Common patterns: default export, NameAgent, nameAgent, agent
      const capitalizedDir = dir.charAt(0).toUpperCase() + dir.slice(1).replace(/-(.)/g, (_, c) => c.toUpperCase());
      
      const impl: Agent = module.default || 
                          module[`${capitalizedDir}Agent`] ||
                          module[`${dir}Agent`] ||
                          module.agent ||
                          module[Object.keys(module)[0]];
      
      if (!impl) {
        console.warn(`[Registry] No agent implementation found in ${dir}. Module keys:`, Object.keys(module));
        continue;
      }
      
      // Validate agent interface
      if (typeof impl.run !== 'function') {
        console.warn(`[Registry] Agent ${dir} missing run() method. Has:`, Object.keys(impl));
        continue;
      }
      
      if (typeof impl.manifest !== 'function') {
        console.warn(`[Registry] Agent ${dir} missing manifest() method. Has:`, Object.keys(impl));
        continue;
      }
      
      const agentId = manifest.id || dir;
      console.log(`[Registry] ✅ Successfully loaded agent: ${agentId}`);
      
      out.push({ id: agentId, manifest, impl });
      
    } catch (error) {
      console.error(`[Registry] ❌ Failed to load agent ${dir}:`, error instanceof Error ? error.message : error);
      if (error instanceof Error && error.stack) {
        const relevantStack = error.stack.split('\n').slice(0, 3).join('\n');
        console.error(`[Registry]   Stack:`, relevantStack);
      }
    }
  }
  
  console.log(`[Registry] ========================================`);
  console.log(`[Registry] Total agents loaded: ${out.length}/${dirs.filter(d => {
    try { return fs.statSync(path.join(ROOT, d)).isDirectory(); } catch { return false; }
  }).length}`);
  console.log(`[Registry] ========================================`);
  
  return out;
}
