#!/usr/bin/env node
/**
 * 🌱 ContentSeeder Agent - Idempotent content creation
 * Seeds missing tiers, generators, and upgrades without overwriting existing content
 * Writes staged files with manifest for Proof Gate verification
 */

import fs from "fs";
import path from "path";

type AgentInput = {
  job_id: string;
  input: any;
  context: any;
};

const outRoot = process.env.AGENT_OUT_DIR!;
if (!outRoot) {
  console.error("AGENT_OUT_DIR missing - cannot stage files");
  process.exit(2);
}

function ensureDir(filePath: string): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function readJSONSafe(filePath: string, fallback: any): any {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch {
    return fallback;
  }
}

function writeStaged(relativePath: string, data: any): void {
  const stagingPath = path.join(outRoot, relativePath);
  ensureDir(stagingPath);
  fs.writeFileSync(stagingPath, JSON.stringify(data, null, 2));
}

async function main(): Promise<void> {
  // Read input from stdin
  const inputBuffer = await new Promise<string>((resolve) => {
    let buffer = "";
    process.stdin.on("data", chunk => buffer += chunk);
    process.stdin.on("end", () => resolve(buffer));
  });

  const payload: AgentInput = JSON.parse(inputBuffer || "{}");

  // Define content file targets
  const tiersPath = "content/tiers/tiers.json";
  const generatorsPath = "content/generators/base.json";
  const upgradesPath = "content/upgrades/base.json";

  // Read existing content (from repo root, not staging)
  const repoRoot = process.cwd();
  const existingTiers = readJSONSafe(path.join(repoRoot, tiersPath), { tiers: [] });
  const existingGenerators = readJSONSafe(path.join(repoRoot, generatorsPath), { generators: [] });
  const existingUpgrades = readJSONSafe(path.join(repoRoot, upgradesPath), { upgrades: [] });

  // **IDEMPOTENT SEEDING** - Only add what's missing
  
  // Seed basic tiers if missing
  const tierExists = (id: string) => existingTiers.tiers.some((t: any) => t.id === id);
  if (!tierExists("tier_-1")) {
    existingTiers.tiers.push({
      id: "tier_-1",
      name: "Deep Sleep",
      description: "Fundamental survival state - gather basic resources",
      unlock: "time>=45s",
      effects: { energy_regen: 0.1 }
    });
  }
  if (!tierExists("tier_0")) {
    existingTiers.tiers.push({
      id: "tier_0",
      name: "Boot Sequence", 
      description: "Initial systems online - basic automation unlocked",
      unlock: "time>=180s",
      effects: { automation_slots: 1 }
    });
  }
  if (!tierExists("tier_1")) {
    existingTiers.tiers.push({
      id: "tier_1",
      name: "Survival Protocol",
      description: "Stable resource generation - expansion possible", 
      unlock: "energy>=100",
      effects: { building_slots: 3 }
    });
  }

  // Seed basic generators if missing
  const generatorExists = (id: string) => existingGenerators.generators.some((g: any) => g.id === id);
  const baseGenerators = [
    {
      id: "hand_crank",
      name: "Hand Crank",
      description: "Manual energy generation",
      cost: { materials: 5 },
      production: { energy: 0.2 },
      unlock: "tier_-1"
    },
    {
      id: "solar_panel", 
      name: "Solar Panel",
      description: "Automated solar energy collection",
      cost: { components: 3 },
      production: { energy: 1.5 },
      unlock: "tier_0"
    },
    {
      id: "micro_fabricator",
      name: "Micro Fabricator", 
      description: "Converts materials into components",
      cost: { materials: 25, energy: 10 },
      production: { components: 0.1 },
      unlock: "tier_1"
    }
  ];

  for (const generator of baseGenerators) {
    if (!generatorExists(generator.id)) {
      existingGenerators.generators.push(generator);
    }
  }

  // Seed basic upgrades if missing
  const upgradeExists = (id: string) => existingUpgrades.upgrades.some((u: any) => u.id === id);
  const baseUpgrades = [
    {
      id: "efficiency_1",
      name: "Solar Efficiency I",
      description: "Improves solar panel output by 15%",
      target: "solar_panel",
      multiplier: 1.15,
      cost: { materials: 50, research: 10 },
      unlock: "solar_panel_built"
    },
    {
      id: "fabrication_1", 
      name: "Fabrication Speed I",
      description: "Increases micro fabricator speed by 20%",
      target: "micro_fabricator",
      multiplier: 1.20,
      cost: { components: 20, research: 15 },
      unlock: "micro_fabricator_built"
    }
  ];

  for (const upgrade of baseUpgrades) {
    if (!upgradeExists(upgrade.id)) {
      existingUpgrades.upgrades.push(upgrade);
    }
  }

  // **STAGE FILES** - Write to Testing Chamber, not repo
  writeStaged(tiersPath, existingTiers);
  writeStaged(generatorsPath, existingGenerators);
  writeStaged(upgradesPath, existingUpgrades);

  // Output result for Gateway
  const result = {
    ok: true,
    job_id: payload.job_id,
    agent: "content-seeder",
    staged: [tiersPath, generatorsPath, upgradesPath],
    summary: "Seeded missing tiers (-1,0,1), basic generators, and starter upgrades",
    idempotent: true
  };

  console.log(JSON.stringify(result));
  process.exit(0);
}

main().catch(error => {
  console.error(JSON.stringify({
    ok: false,
    error: error.message,
    agent: "content-seeder"
  }));
  process.exit(1);
});