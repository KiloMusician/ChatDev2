// Obsidian Vault Integration for CoreLink Foundation
// Transforms the knowledge base into a navigable Obsidian vault

import fs from "node:fs";
import path from "node:path";
import { glob } from "glob";

interface ObsidianVaultConfig {
  vaultPath: string;
  enableBacklinks: boolean;
  enableTagSync: boolean;
  autoIndex: boolean;
}

interface VaultMap {
  folders: Record<string, string[]>;
  tags: Record<string, string[]>;
  backlinks: Record<string, string[]>;
  lastSync: string;
}

export class ObsidianVaultManager {
  private config: ObsidianVaultConfig;
  
  constructor(config: Partial<ObsidianVaultConfig> = {}) {
    this.config = {
      vaultPath: "vault",
      enableBacklinks: true,
      enableTagSync: true,
      autoIndex: true,
      ...config
    };
  }
  
  async syncToVault(): Promise<VaultMap> {
    const vaultPath = this.config.vaultPath;
    fs.mkdirSync(vaultPath, { recursive: true });
    
    // Create vault structure mirroring docs/
    const vaultMap: VaultMap = {
      folders: {},
      tags: {},
      backlinks: {},
      lastSync: new Date().toISOString()
    };
    
    // Sync documentation files
    await this.syncDocsToVault(vaultMap);
    
    // Sync knowledge base files
    await this.syncKnowledgeBase(vaultMap);
    
    // Generate index files
    await this.generateVaultIndex(vaultMap);
    
    return vaultMap;
  }
  
  private async syncDocsToVault(vaultMap: VaultMap) {
    const docFiles = await glob("docs/**/*.md");
    
    for (const docFile of docFiles) {
      const relativePath = path.relative("docs", docFile);
      const vaultFile = path.join(this.config.vaultPath, relativePath);
      
      // Ensure vault subdirectory exists
      fs.mkdirSync(path.dirname(vaultFile), { recursive: true });
      
      // Read and enhance content for Obsidian
      const content = fs.readFileSync(docFile, 'utf8');
      const enhancedContent = this.enhanceForObsidian(content, docFile);
      
      // Write to vault (read-analyze-evolve pattern)
      if (fs.existsSync(vaultFile)) {
        const existing = fs.readFileSync(vaultFile, 'utf8');
        if (existing === enhancedContent) continue; // No changes needed
      }
      
      fs.writeFileSync(vaultFile, enhancedContent);
      
      // Track in vault map
      const folder = path.dirname(relativePath);
      if (!vaultMap.folders[folder]) vaultMap.folders[folder] = [];
      vaultMap.folders[folder].push(path.basename(relativePath));
    }
  }
  
  private async syncKnowledgeBase(vaultMap: VaultMap) {
    // Sync knowledge base content
    const kbFiles = await glob("kb/**/*.md");
    
    for (const kbFile of kbFiles) {
      const relativePath = path.relative("kb", kbFile);
      const vaultFile = path.join(this.config.vaultPath, "knowledge-base", relativePath);
      
      fs.mkdirSync(path.dirname(vaultFile), { recursive: true });
      
      const content = fs.readFileSync(kbFile, 'utf8');
      const enhancedContent = this.enhanceForObsidian(content, kbFile);
      
      if (fs.existsSync(vaultFile)) {
        const existing = fs.readFileSync(vaultFile, 'utf8');
        if (existing === enhancedContent) continue;
      }
      
      fs.writeFileSync(vaultFile, enhancedContent);
    }
  }
  
  private enhanceForObsidian(content: string, originalPath: string): string {
    let enhanced = content;
    
    if (this.config.enableBacklinks) {
      // Add metadata header
      const metadata = `---
source: ${originalPath}
updated: ${new Date().toISOString()}
tags: [corelink, ${this.extractTagsFromPath(originalPath).join(', ')}]
---

`;
      enhanced = metadata + enhanced;
      
      // Convert relative links to Obsidian-style links
      enhanced = enhanced.replace(/\[([^\]]+)\]\(([^)]+\.md)\)/g, (match, text, link) => {
        const linkName = path.basename(link, '.md');
        return `[[${linkName}|${text}]]`;
      });
    }
    
    return enhanced;
  }
  
  private extractTagsFromPath(filePath: string): string[] {
    const parts = filePath.split('/');
    const tags: string[] = [];
    
    // Extract meaningful tags from path structure
    if (parts.includes('docs')) tags.push('documentation');
    if (parts.includes('agents')) tags.push('agent-system');
    if (parts.includes('temple')) tags.push('temple-knowledge');
    if (parts.includes('council')) tags.push('council-system');
    if (parts.includes('lore')) tags.push('narrative');
    
    return tags;
  }
  
  private async generateVaultIndex(vaultMap: VaultMap) {
    const indexContent = `# CoreLink Foundation Vault

Last synced: ${vaultMap.lastSync}

## Folder Structure

${Object.entries(vaultMap.folders)
  .map(([folder, files]) => `### ${folder}\n${files.map(f => `- [[${path.basename(f, '.md')}]]`).join('\n')}`)
  .join('\n\n')}

## Navigation

- [[Temple Navigation]] - Knowledge temple structure
- [[Council System]] - Decision-making protocols  
- [[Multi LLM Provider]] - AI orchestration system

## Quick Access

- Recent updates: ${Object.keys(vaultMap.folders).slice(0, 5).map(f => `[[${f}]]`).join(' • ')}
- Core systems: [[Agents]] • [[Infrastructure]] • [[Game State]]
`;

    const indexPath = path.join(this.config.vaultPath, "README.md");
    fs.writeFileSync(indexPath, indexContent);
    
    // Create Obsidian configuration
    const obsidianConfig = {
      "enabledPlugins": ["graph", "backlink", "tag-pane"],
      "theme": "obsidian",
      "showInlineTitle": true,
      "useMarkdownLinks": false
    };
    
    const configDir = path.join(this.config.vaultPath, ".obsidian");
    fs.mkdirSync(configDir, { recursive: true });
    fs.writeFileSync(
      path.join(configDir, "app.json"), 
      JSON.stringify(obsidianConfig, null, 2)
    );
  }
}

export const obsidianVaultManager = new ObsidianVaultManager();