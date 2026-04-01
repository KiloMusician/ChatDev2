import fs from "node:fs";
import path from "node:path";

const VAULT = process.env.OBSIDIAN_VAULT_DIR || "obsidian_vault";

export function writeNote(relPath: string, md: string) {
  const full = path.join(VAULT, relPath);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  
  // Infrastructure-First: read-analyze-evolve pattern
  if (fs.existsSync(full)) {
    const existing = fs.readFileSync(full, 'utf8');
    if (existing.trim() !== md.trim()) {
      console.log(`[Obsidian] evolving existing note: ${relPath}`);
    } else {
      console.log(`[Obsidian] note unchanged: ${relPath}`);
      return; // No changes needed
    }
  }
  
  fs.writeFileSync(full, md);
  console.log(`[Obsidian] note written: ${relPath}`);
}

export function createChatDevNote(taskId: string, pipelineId: string, outputs: any[]) {
  const timestamp = new Date().toISOString().split('T')[0];
  const frontmatter = `---
aliases: [${taskId}]
tags: [ChatDev, Pipeline, ${pipelineId}]
created: ${timestamp}
path: /Codex/ChatDev/Pipelines/${pipelineId}.md
---

`;

  let content = frontmatter;
  content += `# ChatDev Pipeline: ${pipelineId}\n\n`;
  content += `**Task ID:** ${taskId}\n`;
  content += `**Generated:** ${new Date().toLocaleString()}\n\n`;
  
  content += `## Pipeline Outputs\n\n`;
  outputs.forEach((output, index) => {
    content += `### Stage ${index + 1}: ${output.result.agent}\n\n`;
    content += `**Output Type:** ${output.stage.output}\n\n`;
    content += `${output.result.notes}\n\n`;
    if (output.result.promptExcerpt) {
      content += `*Prompt excerpt: ${output.result.promptExcerpt}...*\n\n`;
    }
  });

  content += `## Links\n\n`;
  content += `- [[Operations/Codex]]\n`;
  content += `- [[Colony/HUD]]\n`;
  content += `- [[Pantheon/Index]]\n\n`;

  // Infrastructure-First: meaningful name in logical location
  writeNote(`Codex/ChatDev/Pipelines/${pipelineId}.md`, content);
  return content;
}