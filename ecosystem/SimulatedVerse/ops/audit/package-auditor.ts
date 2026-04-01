#!/usr/bin/env tsx
import { execSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { classify } from "./classifiers";

function listPkgs() {
  try {
    const result = execSync("npm ls --json --depth=0", { encoding: "utf8" });
    return JSON.parse(result);
  } catch (e) {
    console.error("Failed to get package list:", (e as Error).message);
    return { dependencies: {} };
  }
}

function generateProposals(packages: any[]) {
  const proposals: any[] = [];
  
  for (const pkg of packages) {
    if (pkg.confidence < 0.6) continue; // Skip uncertain classifications
    
    let proposal;
    switch (pkg.category) {
      case "game/engine":
        proposal = {
          ts: Date.now(),
          source: "package-auditor",
          package: pkg.name,
          category: pkg.category,
          title: `Integrate ${pkg.name} for enhanced gameplay rendering`,
          pu: {
            id: `game-engine-${pkg.name}-integration`,
            priority: 70,
            labels: ["gameplay", "rendering", "enhancement"],
            proofs: [`${pkg.name} package installed and available`, "game engine integration patterns documented"],
            actions: [`create gameplay/${pkg.name}-integration.ts`, `wire into existing game systems`, "test rendering performance"],
            acceptance: ["gameplay engine responds to user interactions", "performance benchmarks meet standards", "no conflicts with existing systems"]
          }
        };
        break;
        
      case "llm/agents":
        proposal = {
          ts: Date.now(),
          source: "package-auditor",
          package: pkg.name,
          category: pkg.category,
          title: `Enhance agent intelligence with ${pkg.name}`,
          pu: {
            id: `llm-agent-${pkg.name}-enhancement`,
            priority: 85,
            labels: ["agents", "llm", "intelligence"],
            proofs: [`${pkg.name} package available`, "agent framework supports extensions"],
            actions: [`extend packages/council/agents.ts with ${pkg.name}`, "test enhanced reasoning capabilities", "update agent prompts"],
            acceptance: ["agents demonstrate improved reasoning", "no regression in response times", "council bus remains stable"]
          }
        };
        break;
        
      case "ops/orchestration":
        proposal = {
          ts: Date.now(),
          source: "package-auditor",
          package: pkg.name,
          category: pkg.category,
          title: `Strengthen autonomous operations with ${pkg.name}`,
          pu: {
            id: `ops-orchestration-${pkg.name}`,
            priority: 80,
            labels: ["ops", "orchestration", "autonomy"],
            proofs: [`${pkg.name} installed`, "orchestration patterns established"],
            actions: [`integrate ${pkg.name} into ops/orchestrator/`, "enhance PU queue processing", "add scheduling capabilities"],
            acceptance: ["queue processing remains stable", "scheduling works reliably", "no memory leaks or hangs"]
          }
        };
        break;
        
      default:
        // Generate generic integration proposal
        proposal = {
          ts: Date.now(),
          source: "package-auditor",
          package: pkg.name,
          category: pkg.category,
          title: `Explore ${pkg.name} integration opportunities`,
          pu: {
            id: `explore-${pkg.name}-integration`,
            priority: 50,
            labels: ["exploration", pkg.category.split("/")[0]],
            proofs: [`${pkg.name} package available`, "classification confidence sufficient"],
            actions: [`research ${pkg.name} capabilities`, "identify integration points", "create proof-of-concept"],
            acceptance: ["research completed", "integration potential assessed", "decision documented"]
          }
        };
    }
    
    if (proposal) proposals.push(proposal);
  }
  
  return proposals;
}

export async function auditPackages() {
  console.log("[audit] Starting package audit...");
  
  const packageInfo = listPkgs();
  const deps = packageInfo.dependencies || {};
  
  const packages = Object.entries(deps).map(([name, info]: [string, any]) => {
    const classification = classify(name);
    return {
      name,
      version: info.version || "unknown",
      kind: "npm",
      ...classification
    };
  });
  
  // Sort by confidence and category
  packages.sort((a, b) => b.confidence - a.confidence);
  
  const catalog = {
    generated_at: new Date().toISOString(),
    packages
  };
  
  // Write catalog
  writeFileSync("../../reports/packages.catalog.json", JSON.stringify(catalog, null, 2));
  console.log(`[audit] Cataloged ${packages.length} packages`);
  
  // Generate integration proposals
  const proposals = generateProposals(packages);
  const proposalLines = proposals.map(p => JSON.stringify(p)).join("\n");
  writeFileSync("../../reports/integration_proposals.ndjson", proposalLines);
  console.log(`[audit] Generated ${proposals.length} integration proposals`);
  
  return catalog;
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  auditPackages();
}