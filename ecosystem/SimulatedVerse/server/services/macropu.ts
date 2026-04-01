import { z } from "zod";

// **MACROPU EXPANSION SYSTEM** - Turn 20 macros into 1000 tasks
const MacroPUSchema = z.object({
  type: z.literal("MacroPU"),
  id: z.string().min(1),
  title: z.string().min(1),
  category: z.enum(["game","agents","docs","infra","ml","perf","a11y","tests","obsidian","jupyter","ascii","lore"]),
  template: z.object({
    type: z.enum(["RefactorPU","TestPU","DocPU","PerfPU","UXPU","DataPU","OpsPU","AgentPU","GamePU"]),
    title: z.string(),                    // may contain ${i} and ${name}
    estTokens: z.number().int().min(1),
    priority: z.enum(["low","medium","high","critical"])
  }),
  expand: z.object({
    count: z.number().int().min(1).max(2000),
    names: z.array(z.string()).optional()
  }),
  tags: z.array(z.string()).optional()
});

export type MacroPU = z.infer<typeof MacroPUSchema>;

export function expandMacroPU(macro: MacroPU): any[] {
  const { template, expand, tags = [], category, id } = macro;
  const out: any[] = [];
  
  // Generate names if not provided
  const names = expand.names ?? Array.from(
    { length: expand.count }, 
    (_, i) => `Item${String(i + 1).padStart(3, '0')}`
  );
  
  // Create individual tasks
  names.slice(0, expand.count).forEach((name, i) => {
    const taskId = `${id}-${String(i + 1).padStart(3, '0')}`;
    const taskTitle = template.title
      .replace(/\$\{i\}/g, String(i + 1))
      .replace(/\$\{name\}/g, name)
      .replace(/\$\{id\}/g, taskId);
    
    out.push({
      type: template.type,
      id: taskId,
      title: taskTitle,
      estTokens: template.estTokens,
      priority: template.priority,
      phase: "foundational",
      cost: template.estTokens,
      deps: [],
      steps: [
        `Identify requirements for ${taskTitle}`,
        `Implement core functionality`,
        `Test and validate implementation`,
        `Emit [Msg⛛{${taskId}}] completion signal`
      ],
      status: "queued",
      entropy: ((i * 7 + category.charCodeAt(0)) % 20) / 10, // Deterministic entropy for ML ranking
      createdAt: Date.now(),
      tags: [
        ...tags,
        category,
        "expanded",
        `macro:${id}`,
        `batch:${Math.floor(i / 50)}` // Group into batches of 50
      ],
      _v: 1
    });
  });
  
  return out;
}

export function validateMacroPU(input: any): { success: true; data: MacroPU } | { success: false; error: any } {
  const result = MacroPUSchema.safeParse(input);
  return result.success ? { success: true, data: result.data } : { success: false, error: result.error };
}

// **PREDEFINED MACRO TEMPLATES** - Ready-to-use expansions
export const MACRO_TEMPLATES = {
  GAME_STRUCTURE: {
    type: "MacroPU" as const,
    id: "G-STRUCT",
    title: "Game Structure Sweep",
    category: "game" as const,
    template: {
      type: "RefactorPU" as const,
      title: "Normalize module folder ${i} (${name})",
      estTokens: 22,
      priority: "high" as const
    },
    expand: {
      count: 60,
      names: [
        "Scene", "Signals", "UI", "Economy", "Research", "Automation", 
        "Quests", "ASCII-HUD", "SaveLoad", "Balancing", "VFX", "SFX", 
        "Input", "Map", "NPC", "Jobs", "Items", "Craft", "Trade", "Zones",
        "Perf", "A11y", "Docs", "Tests", "Telemetry", "ECS", "Story", 
        "Events", "Upgrades", "Meta", "UI-Settings", "Keybinds", "Tooltips",
        "Hotbar", "Build", "Pathing", "Fog", "Lighting", "Particles", 
        "Shaders", "Spawn", "Loot", "Waves", "Boss", "Weather", "Seasons",
        "Time", "Calendar", "Mail", "Chat", "Guild", "Market", "Auction",
        "Contracts", "Raids", "Dungeons", "Factions", "Diplomacy", "Artifacts", "Relics"
      ]
    },
    tags: ["infrastructure", "core"]
  },
  
  AGENT_PLAYBOOKS: {
    type: "MacroPU" as const,
    id: "A-AGENTS", 
    title: "Agent Playbooks",
    category: "agents" as const,
    template: {
      type: "DocPU" as const,
      title: "Author agent playbook ${i}: ${name}",
      estTokens: 12,
      priority: "medium" as const
    },
    expand: {
      count: 40,
      names: [
        "Alpha-Navigator", "Beta-Builder", "Gamma-Orchestrator", "Delta-Reviewer",
        "Epsilon-Profiler", "Zeta-Refactor", "Eta-Docs", "Theta-Tester",
        "Iota-UX", "Kappa-Perf", "Lambda-Lore", "Mu-ASCII", "Nu-Quest",
        "Xi-Research", "Omicron-Balancer", "Pi-Saver", "Rho-Exporter",
        "Sigma-Importer", "Tau-Observer", "Upsilon-Guardian", "Phi-Archivist",
        "Chi-Ritual", "Psi-Telemetry", "Omega-Admin", "Colony-Mediator",
        "Tinkerer", "Librarian", "Quartermaster", "Alchemist", "Sage",
        "Scout", "Smith", "Warden", "Herald", "Cartographer", "Prospector",
        "Botanist", "Miner", "Artisan", "Bard"
      ]
    },
    tags: ["ai", "coordination"]
  },
  
  ML_NURSERY: {
    type: "MacroPU" as const,
    id: "ML-NURSERY",
    title: "ML nursery scaffolds", 
    category: "ml" as const,
    template: {
      type: "TestPU" as const,
      title: "Create ML toy eval ${i}: ${name}",
      estTokens: 16,
      priority: "medium" as const
    },
    expand: {
      count: 40,
      names: [
        "n-gram baseline", "Markov chain text", "rule-based tutor", "goal bandit",
        "delta heuristics", "simple embed index", "pagerank lore", "policy table",
        "score shaping", "curriculum 1", "curriculum 2", "prompt fuser",
        "few-shot librarian", "compression check", "style transfer rules",
        "reward logger", "offline replay buffer", "experience cache", "rollout tracer",
        "trace viewer", "annotation checklist", "PII scrubber", "seed splitter",
        "dataset manifest", "prompt manifest", "run manifest", "scorecard",
        "leaderboard", "drift detector", "regression guard", "seed reproducibility",
        "sampler", "metric aggregator", "NDJSON loader", "vocab builder",
        "mini tokenizer", "toy LM char", "toy LM word", "noise injector", "eval harness"
      ]
    },
    tags: ["machine-learning", "evaluation"]
  }
};

// **STATISTICS AND MONITORING**
export function getMacroStats() {
  const templates = Object.values(MACRO_TEMPLATES);
  const totalTasks = templates.reduce((sum, template) => sum + template.expand.count, 0);
  
  return {
    templates: templates.length,
    totalExpandableTasks: totalTasks,
    categories: Array.from(new Set(templates.map(t => t.category))),
    avgTasksPerMacro: Math.round(totalTasks / templates.length)
  };
}