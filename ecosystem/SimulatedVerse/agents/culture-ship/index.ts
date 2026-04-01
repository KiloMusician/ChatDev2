import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";

const MANIFEST: TAgentManifest = {
  id: "culture-ship", role: "culture-ship",
  name: "Culture Ship",
  description: "Composes lore and narrative elements from documentation",
  capabilities: ["compose","index","inspect"],
  version: "0.1.0",
  runner: "in-process",
  enabled: true
};

interface TheaterAuditData {
  project?: string;
  score?: number;
  hits?: number;
  lines?: number;
  patterns?: {
    console_spam?: number;
    fake_progress?: number;
    todo_comments?: number;
    [key: string]: number | undefined;
  };
}

export const CultureShipAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready" }; },
  async run(input: TAgentInput) {
    // Check if this is a theater audit request
    const metadata = input.metadata as TheaterAuditData | undefined;
    console.log(`[Culture Ship] Input metadata:`, JSON.stringify(metadata, null, 2));
    console.log(`[Culture Ship] Has score: ${metadata?.score !== undefined}`);
    console.log(`[Culture Ship] Has patterns: ${metadata?.patterns !== undefined}`);
    const isTheaterAudit = metadata?.score !== undefined && metadata?.patterns !== undefined;
    console.log(`[Culture Ship] Is theater audit: ${isTheaterAudit}`);
    
    if (isTheaterAudit) {
      // Generate proof-gated PUs for theater cleanup
      return await generateTheaterCleanupPUs(input, metadata!);
    } else {
      // Default: Generate lore documentation
      return await generateLoreDocumentation(input);
    }
  }
};

async function generateTheaterCleanupPUs(input: TAgentInput, audit: TheaterAuditData) {
  const pus: any[] = [];
  const project = audit.project || "Unknown";
  const score = audit.score || 0;
  const patterns = audit.patterns || {};
  
  console.log(`[Culture Ship] 🎭 Theater audit for ${project}: score=${score}`);
  
  // Generate RefactorPUs for each pattern type
  if (patterns.console_spam && patterns.console_spam > 0) {
    pus.push({
      id: `pu.theater.console.${input.t}`,
      phase: "cleanup",
      type: "RefactorPU",
      priority: patterns.console_spam > 100 ? "high" : "medium",
      title: `Remove ${patterns.console_spam} console spam statements in ${project}`,
      proof: [
        `grep -r "console.log" | wc -l shows reduction`,
        `Theater score decreases after changes`,
        `No functionality changes, only cleanup`
      ],
      category: "theater-reduction",
      project: project
    });
  }
  
  if (patterns.fake_progress && patterns.fake_progress > 0) {
    pus.push({
      id: `pu.theater.progress.${input.t}`,
      phase: "cleanup",
      type: "RefactorPU",
      priority: patterns.fake_progress > 200 ? "high" : "medium",
      title: `Remove ${patterns.fake_progress} fake progress bars in ${project}`,
      proof: [
        `Verify replaced with real progress tracking or removed`,
        `Theater score improves`,
        `UX not degraded`
      ],
      category: "theater-reduction",
      project: project
    });
  }
  
  if (patterns.todo_comments && patterns.todo_comments > 1000) {
    pus.push({
      id: `pu.theater.todos.${input.t}`,
      phase: "cleanup",
      type: "DocPU",
      priority: "medium",
      title: `Convert ${patterns.todo_comments} TODO comments to tracked issues in ${project}`,
      proof: [
        `TODOs moved to issue tracker or removed`,
        `Theater score decreases`,
        `No important todos lost`
      ],
      category: "theater-reduction",
      project: project
    });
  }
  
  // Generate theater reduction report
  const puDir = path.resolve("data", "pus");
  fs.mkdirSync(puDir, { recursive: true });
  const puFile = path.join(puDir, `theater-cleanup-${input.t}.json`);
  fs.writeFileSync(puFile, JSON.stringify(pus, null, 2));
  
  console.log(`[Culture Ship] ✅ Generated ${pus.length} proof-gated PUs for theater cleanup`);
  
  return {
    ok: true,
    effects: {
      artifactPath: puFile,
      stateDelta: {
        pusGenerated: pus.length,
        theaterScore: score,
        project: project,
        pus: pus
      }
    }
  };
}

async function generateLoreDocumentation(input: TAgentInput) {
  // Original lore generation logic
  const docsRoot = path.resolve("docs");
  const headings: string[] = [];
  
  if (fs.existsSync(docsRoot)) {
    const mdFiles = fs.readdirSync(docsRoot, { recursive: true })
      .filter((f: any) => typeof f === 'string' && f.endsWith('.md'));
    
    for (const file of mdFiles) {
      try {
        const content = fs.readFileSync(path.join(docsRoot, file as string), 'utf-8');
        const lines = content.split('\n');
        for (const line of lines) {
          if (line.startsWith('# ') || line.startsWith('## ')) {
            headings.push(line.replace(/^#+\s*/, '').trim());
          }
        }
      } catch (e) {
        // Skip invalid files
      }
    }
  }
  
  const loreContent = `# CoreLink Foundation - Cycle ${input.t}

*Generated by Culture Ship at ${new Date(input.utc).toISOString()}*

## The Foundation's Knowledge Web

${headings.slice(0, 10).map(h => `- **${h}**: A node in the ever-expanding knowledge matrix`).join('\n')}

## Current State

- **Autonomous Tasks**: Processing at light speed through the Foundation's neural pathways
- **Knowledge Nodes**: ${headings.length} documented concepts discovered
- **System Entropy**: ${input.entropy.toFixed(3)} (stable quantum foam)
- **Budget Flow**: ${(input.budget * 100).toFixed(1)}% capacity remaining

*The Culture Ship weaves these threads into the grand tapestry of autonomous development...*
`;
  
  const loreDir = path.resolve("docs", "lore");
  fs.mkdirSync(loreDir, { recursive: true });
  const loreFile = path.join(loreDir, `lore-${input.t}.md`);
  fs.writeFileSync(loreFile, loreContent);
  
  return {
    ok: true,
    effects: {
      artifactPath: loreFile,
      stateDelta: { loreGenerated: true, headingsProcessed: headings.length }
    }
  };
}

export default CultureShipAgent;
