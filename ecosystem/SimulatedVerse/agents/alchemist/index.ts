import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";

const MANIFEST: TAgentManifest = {
  id: "alchemist", role: "alchemist",
  name: "Alchemist", 
  description: "Transforms CSV→JSON and normalizes data formats",
  capabilities: ["act","build","compose"],
  version: "0.1.0",
  runner: "in-process",
  enabled: true
};

export const AlchemistAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready" }; },
  async run(input: TAgentInput) {
    // Real work: read data/nursery/*.csv → write normalized JSON
    const nurseryRoot = path.resolve("data", "nursery");
    const results: any[] = [];
    
    if (fs.existsSync(nurseryRoot)) {
      const csvFiles = fs.readdirSync(nurseryRoot).filter(f => f.endsWith('.csv'));
      for (const csvFile of csvFiles) {
        const csvPath = path.join(nurseryRoot, csvFile);
        const content = fs.readFileSync(csvPath, 'utf-8');
        const lines = content.trim().split('\n');
        if (lines.length > 1) {
          const headers = lines[0].split(',');
          const data = lines.slice(1).map(line => {
            const values = line.split(',');
            const obj: any = {};
            headers.forEach((header, i) => {
              obj[header.trim()] = values[i]?.trim() || null;
            });
            return obj;
          });
          results.push({ file: csvFile, rows: data.length, data });
        }
      }
    }
    
    // Infrastructure-First: meaningful location and name
    const stateDir = path.resolve("data", "state");
    fs.mkdirSync(stateDir, { recursive: true });
    const out = path.join(stateDir, "csv-transformations.json");
    fs.writeFileSync(out, JSON.stringify({ 
      transformations: results, 
      t: input.t, 
      utc: input.utc 
    }, null, 2));
    
    return { 
      ok: true, 
      effects: { 
        artifactPath: out, 
        stateDelta: { csvFilesProcessed: results.length, totalRows: results.reduce((sum, r) => sum + r.rows, 0) } 
      } 
    };
  }
};

export default AlchemistAgent;