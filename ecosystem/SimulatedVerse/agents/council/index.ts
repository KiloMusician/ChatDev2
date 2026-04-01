import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";

const MANIFEST: TAgentManifest = {
  id: "council", role: "council",
  name: "Council",
  description: "Merges agent votes and builds consensus decisions",
  capabilities: ["vote","inspect","compose"],
  version: "0.1.0",
  runner: "in-process",
  enabled: true
};

export const CouncilAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready" }; },
  async run(input: TAgentInput) {
    // Real work: read data/state/votes/*.json, compute consensus
    const votesDir = path.resolve("data", "state", "votes");
    const votes: any[] = [];
    
    if (fs.existsSync(votesDir)) {
      const voteFiles = fs.readdirSync(votesDir).filter(f => f.endsWith('.json'));
      for (const file of voteFiles) {
        try {
          const content = JSON.parse(fs.readFileSync(path.join(votesDir, file), 'utf-8'));
          votes.push({ file, ...content });
        } catch (e) {
          // Skip invalid files
        }
      }
    }
    
    const consensus = {
      totalVotes: votes.length,
      decisions: votes.reduce((acc, vote) => {
        if (vote.decision) acc[vote.decision] = (acc[vote.decision] || 0) + 1;
        return acc;
      }, {} as Record<string, number>),
      lastUpdated: input.utc,
      tick: input.t
    };
    
    const councilStateDir = path.resolve("data", "state");
    fs.mkdirSync(councilStateDir, { recursive: true });
    const councilFile = path.join(councilStateDir, "council.json");
    fs.writeFileSync(councilFile, JSON.stringify(consensus, null, 2));
    
    const artifactDir = path.resolve("data","artifacts","council");
    fs.mkdirSync(artifactDir, { recursive: true });
    const artifact = path.join(artifactDir, `consensus-${Date.now()}.json`);
    fs.writeFileSync(artifact, JSON.stringify(consensus, null, 2));
    
    return {
      ok: true,
      effects: {
        artifactPath: artifact,
        stateDelta: { consensusBuilt: true, votesProcessed: votes.length }
      }
    };
  }
};

export default CouncilAgent;