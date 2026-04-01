import { Proposal } from "../../shared/schemas/proposal.js";

type CompileResult = {
  proposalId: string;
  pus: any[];
  artifacts: { path: string; content: string }[];
  prPlan?: { branch: string; labels: string[] };
  budget: { estTokens: number; costTier: "free"|"low"|"med"|"high" };
  scp: { markdown: string; containment: string; description: string };
};

export function compileProposal(input: unknown): CompileResult {
  const p = Proposal.parse(input) as any;
  // Default empty commands if no RSEV data available  
  const cmds: any[] = [];
  const pus: any[] = [];
  const artifacts: {path: string; content: string}[] = [];
  let prBranch: string | undefined;
  let prLabels: string[] = ["agent", "proposal"];

  // SCP render (for docs & Obsidian)
  const scpDoc = renderScpMarkdown(p);
  artifacts.push({ path: `docs/proposals/${p.id}.md`, content: scpDoc });

  // Convert RSEV ops → PUs / artifacts  
  // NOTE: RSEV parser disabled, using proposal metadata directly
  /*
  for (const c of cmds) {
    switch (c.op) {
      case "ADD_FILE":
        artifacts.push({ path: c.path, content: c.content });
        break;
        
      case "PATCH_FILE":
        pus.push({
          id: `${p.id}-patch-${Date.now()}`,
          type: "RefactorPU",
          title: `Patch: ${c.path}`,
          files: [{ path: c.path, content: c.patch, mode: "patch" }],
          priority: p.priority,
          phase: 'implementation',
          estTokens: 20,
          source: { kind: "proposal", proposalId: p.id, section: "patches" }
        });
        break;
        
      case "TEST":
        pus.push({
          id: `${p.id}-test-${c.name}`,
          type: "TestPU",
          title: `Test: ${c.name}`,
          commands: [c.run],
          priority: p.priority,
          phase: 'implementation',
          estTokens: 15,
          source: { kind: "proposal", proposalId: p.id, section: "tests" }
        });
        break;
        
      case "GAME_SIM":
        pus.push({
          id: `${p.id}-sim-${c.ticks}`,
          type: "GamePU",
          title: `Game self-play ${c.ticks} ticks`,
          commands: [`curl -sS localhost:${process.env.PORT||5000}/api/game/sim?ticks=${c.ticks}`],
          priority: "high",
          phase: "expansion",
          estTokens: Math.ceil(c.ticks / 10),
          runner: "system",
          source: { kind:"proposal", proposalId: p.id, section: "experiments" }
        });
        break;
        
      case "OPEN_PR":
        prBranch = c.branch; 
        prLabels = c.labels ?? prLabels;
        break;
        
      case "RUN":
        pus.push({
          id: `${p.id}-run-${Date.now()}`,
          type: "OpsPU",
          title: `Run: ${c.cmd}`,
          commands: [c.cmd],
          estTokens: 5,
          source: { kind:"proposal", proposalId: p.id, section:"ops" }
        });
        break;
        
      case "AGENT_MACRO":
        pus.push({
          id: `${p.id}-macro-${c.name}`,
          type: "AgentPU",
          title: `Agent Macro: ${c.name}`,
          commands: [`curl -sS localhost:${process.env.PORT||5000}/api/agents/macro/${c.name}`, JSON.stringify(c.args || {})],
          estTokens: 25,
          source: { kind:"proposal", proposalId: p.id, section:"agents" }
        });
        break;
        
      case "NOTEBOOK":
        artifacts.push({
          path: c.path,
          content: `{
  "cells": [
    {
      "cell_type": "markdown",
      "source": ["# ${p.title}\\n\\nGenerated from proposal ${p.id}"]
    },
    {
      "cell_type": "code",
      "source": ["# Analysis Implementation\\n\\nimport pandas as pd\\nimport matplotlib.pyplot as plt\\n\\n# Load and analyze data\\ndata = pd.read_csv('data.csv')\\nprint(data.describe())\\n\\n# Create visualization\\nplt.figure(figsize=(10,6))\\nplt.plot(data)\\nplt.title('Analysis Results')\\nplt.show()"],
      "execution_count": null,
      "outputs": []
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "${c.kernel || 'Python 3'}",
      "language": "python",
      "name": "python3"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 4
}`
        });
        break;
        
      case "OBSIDIAN_SYNC":
        // Create link for Obsidian vault
        artifacts.push({
          path: c.path,
          content: `---
tags: [proposal, ${p.meta.bindings.tags.join(', ')}]
id: ${p.id}
phase: ${'implementation'}
---

# ${p.title}

> Auto-synced from proposal system

## Quick Links
- [[${p.id}]] - Main proposal
- Status: ${'implementation'}
- Priority: ${p.priority}

## Description
${p.description.body}

## Containment
${p.containment.body}
`
        });
        break;
    }
  }
  */

  // Budget estimate
  const estTokens = 50 + artifacts.length * 2; // Fixed estimate since RSEV disabled
  const costTier = estTokens < 50 ? "low" : estTokens < 200 ? "med" : "high";

  return {
    proposalId: p.id,
    pus,
    artifacts,
    prPlan: prBranch ? { branch: prBranch, labels: prLabels } : undefined,
    budget: { estTokens, costTier },
    scp: {
      markdown: scpDoc,
      containment: p.description, // Use description as containment fallback
      description: p.description
    }
  };
}

// SCP-style markdown renderer
function renderScpMarkdown(p: any): string {
  const createdAt = p.createdAt ?? p.created_at ?? Date.now();
  const updatedAt = p.updatedAt ?? p.updated_at ?? Date.now();
  const description = p.description ?? '';
  return `---
id: ${p.id}
title: ${p.title}
priority: ${p.priority ?? 'normal'}
status: ${p.status ?? 'pending'}
type: ${p.type ?? 'proposal'}
author: ${p.author ?? 'system'}
created: ${new Date(createdAt).toISOString()}
updated: ${new Date(updatedAt).toISOString()}
---

# ${p.title} (${p.id})

**Priority:** ${p.priority ?? 'normal'}  
**Status:** ${p.status ?? 'pending'}  
**Type:** ${p.type ?? 'proposal'}  
**Author:** ${p.author ?? 'system'}

## Description
${description}

## Metadata
${p.metadata ? Object.entries(p.metadata).map(([k, v]) => `- **${k}:** ${v}`).join('\n') : '_No additional metadata_'}

---
*Generated by CoreLink Foundation Proposal System*
*Infrastructure-First • Culture-Ship Aligned • Budget-Disciplined*
`;
}
