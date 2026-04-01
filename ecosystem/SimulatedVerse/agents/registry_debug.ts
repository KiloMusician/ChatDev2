// agents/registry.ts
import fs from "node:fs";
import path from "node:path";
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
      console.log(`[Registry] Loading ${dir}: manifest data =`, manifestData);
      
      const manifest = AgentManifest.parse(manifestData);
      
      // Import module
      const modulePath = path.resolve(ix);
      console.log(`[Registry] Importing ${dir} from: ${modulePath}`);
      const module = await import(modulePath);
      
      // Try to find agent implementation
      const impl: Agent = module.default || 
                          module[`${dir.charAt(0).toUpperCase() + dir.slice(1)}Agent`] ||
                          module[`${dir}Agent`] ||
                          module.agent ||
                          module[Object.keys(module)[0]];
      
      if (!impl) {
        console.warn(`[Registry] No agent implementation found in ${dir}. Module keys:`, Object.keys(module));
        continue;
      }
      
      // Validate agent interface
      if (typeof impl.run !== 'function') {
        console.warn(`[Registry] Agent ${dir} missing run() method`);
        continue;
      }
      
      if (typeof impl.manifest !== 'function') {
        console.warn(`[Registry] Agent ${dir} missing manifest() method`);
        continue;
      }
      
      const agentId = manifest.id || dir;
      console.log(`[Registry] ✅ Successfully loaded agent: ${agentId}`);
      
      out.push({ id: agentId, manifest, impl });
      
    } catch (error) {
      console.error(`[Registry] Failed to load agent ${dir}:`, error);
      if (error instanceof Error) {
        console.error(`[Registry]   Error message: ${error.message}`);
        console.error(`[Registry]   Stack trace:`, error.stack);
      }
    }
  }
  
  console.log(`[Registry] Total agents loaded: ${out.length}`);
  return out;
}
