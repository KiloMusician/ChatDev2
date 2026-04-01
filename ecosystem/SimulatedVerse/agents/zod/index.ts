import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";

const MANIFEST: TAgentManifest = {
  id: "zod", role: "zod",
  name: "Zod",
  description: "Validates schemas across data files and reports violations",
  capabilities: ["inspect","vote","patch"],
  version: "0.1.0", 
  runner: "in-process",
  enabled: true
};

export const ZodAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready" }; },
  async run(input: TAgentInput) {
    // Real work: validate schemas across /data/*.json
    const dataRoot = path.resolve("data");
    const violations: any[] = [];
    const validFiles: any[] = [];
    
    if (fs.existsSync(dataRoot)) {
      const findJsonFiles = (dir: string): string[] => {
        const files: string[] = [];
        const items = fs.readdirSync(dir);
        for (const item of items) {
          const fullPath = path.join(dir, item);
          const stat = fs.statSync(fullPath);
          if (stat.isDirectory()) {
            files.push(...findJsonFiles(fullPath));
          } else if (item.endsWith('.json')) {
            files.push(fullPath);
          }
        }
        return files;
      };
      
      const jsonFiles = findJsonFiles(dataRoot);
      for (const file of jsonFiles) {
        try {
          const content = fs.readFileSync(file, 'utf-8');
          const parsed = JSON.parse(content);
          
          // Basic schema validation checks
          const issues: string[] = [];
          if (typeof parsed !== 'object') issues.push('Root is not object');
          if (Array.isArray(parsed) && parsed.some(item => typeof item !== 'object')) {
            issues.push('Array contains non-objects');
          }
          
          if (issues.length > 0) {
            violations.push({ file: path.relative(dataRoot, file), issues });
          } else {
            validFiles.push({ file: path.relative(dataRoot, file), valid: true });
          }
        } catch (e) {
          violations.push({ file: path.relative(dataRoot, file), issues: ['Invalid JSON'] });
        }
      }
    }
    
    const report = {
      totalFiles: validFiles.length + violations.length,
      validFiles: validFiles.length,
      violations: violations.length,
      details: { validFiles, violations },
      t: input.t,
      utc: input.utc
    };
    
    const stateDir = path.resolve("data", "state");
    fs.mkdirSync(stateDir, { recursive: true });
    const reportFile = path.join(stateDir, "schema-report.json");
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));
    
    // Infrastructure-First: schema report is already in logical location
    return {
      ok: true,
      effects: {
        artifactPath: reportFile,
        stateDelta: { filesValidated: report.totalFiles, violationsFound: violations.length }
      }
    };
  }
};

export default ZodAgent;