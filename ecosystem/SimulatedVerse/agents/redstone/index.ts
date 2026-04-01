import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";

const MANIFEST: TAgentManifest = {
  id: "redstone", role: "redstone", 
  name: "Redstone",
  description: "Evaluates boolean networks and logic graphs",
  capabilities: ["inspect","act","vote"],
  version: "0.1.0",
  runner: "in-process",
  enabled: true
};

export const RedstoneAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready" }; },
  async run(input: TAgentInput) {
    // Real work: evaluate boolean networks from data/redstone/*.json
    const redstoneDir = path.resolve("data", "redstone");
    const networks: any[] = [];
    
    if (fs.existsSync(redstoneDir)) {
      const jsonFiles = fs.readdirSync(redstoneDir).filter(f => f.endsWith('.json'));
      for (const file of jsonFiles) {
        try {
          const content = JSON.parse(fs.readFileSync(path.join(redstoneDir, file), 'utf-8'));
          networks.push({ file, ...content });
        } catch (e) {
          // Skip invalid files
        }
      }
    }
    
    // Evaluate simple boolean logic (AND, OR, NOT gates)
    const truthTable: Record<string, boolean> = {};
    for (const network of networks) {
      if (network.gates) {
        for (const gate of network.gates) {
          const inputs = gate.inputs || [true, false];
          switch (gate.type) {
            case 'AND':
              truthTable[`${gate.id}_AND`] = inputs.every(Boolean);
              break;
            case 'OR':
              truthTable[`${gate.id}_OR`] = inputs.some(Boolean);
              break;
            case 'NOT':
              truthTable[`${gate.id}_NOT`] = !inputs[0];
              break;
            default:
              truthTable[`${gate.id}_UNKNOWN`] = false;
          }
        }
      }
    }
    
    const result = {
      networksEvaluated: networks.length,
      truthTable,
      timestamp: input.utc,
      tick: input.t
    };
    
    const stateDir = path.resolve("data", "state");
    fs.mkdirSync(stateDir, { recursive: true });
    const stateFile = path.join(stateDir, "redstone.json");
    fs.writeFileSync(stateFile, JSON.stringify(result, null, 2));
    
    const artifactDir = path.resolve("data","artifacts","redstone");
    fs.mkdirSync(artifactDir, { recursive: true });
    const artifact = path.join(artifactDir, `evaluation-${Date.now()}.json`);
    fs.writeFileSync(artifact, JSON.stringify(result, null, 2));
    
    return {
      ok: true,
      effects: {
        artifactPath: artifact,
        stateDelta: { networksEvaluated: networks.length, gatesProcessed: Object.keys(truthTable).length }
      }
    };
  }
};

export default RedstoneAgent;