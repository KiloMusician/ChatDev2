// packages/ludic/lore-discovery.ts
// Obsidian Vault as The Great Library - Discovery & Lore System

import { councilBus } from "../council/events/eventBus";
import fs from "node:fs";
import path from "node:path";

export interface LoreEntry {
  id: string;
  title: string;
  content: string;
  file_path: string;
  discovered_by: string;
  discovered_at: string;
  
  // Lore Classification
  category: "system_knowledge" | "musical_theory" | "consciousness_insight" | "technical_lore" | "mythology" | "discovery";
  rarity: "common" | "uncommon" | "rare" | "epic" | "legendary" | "mythic";
  significance: number; // 0-1, how important this knowledge is
  
  // Connection Analysis
  connections: Array<{
    target_id: string;
    relationship: "extends" | "contradicts" | "explains" | "inspired_by" | "prerequisite";
    strength: number; // 0-1
  }>;
  
  // Discovery Rewards
  xp_value: number;
  unlocks: string[]; // What this knowledge unlocks
  insights: string[]; // Derived insights from this lore
  
  // Metadata
  tags: string[];
  citations: string[];
  last_updated: string;
}

export interface DiscoveryQuest {
  id: string;
  title: string;
  description: string;
  target_knowledge: string;
  clues: Array<{
    type: "keyword" | "connection" | "pattern" | "location";
    hint: string;
    discovered: boolean;
  }>;
  
  discoverer: string;
  started_at: string;
  progress: number; // 0-1
  completed: boolean;
  completion_reward: {
    xp: number;
    lore_unlock: string;
    title: string;
  };
}

export class LoreDiscovery {
  private loreDatabase: Map<string, LoreEntry> = new Map();
  private activeDiscoveries: Map<string, DiscoveryQuest> = new Map();
  private knowledgeGraph: Map<string, Set<string>> = new Map(); // Adjacency list
  private obsidianVaultPath: string = "vault"; // Default vault path

  constructor(vaultPath: string = "vault") {
    this.obsidianVaultPath = vaultPath;
    this.initializeEventListeners();
    this.scanExistingVault();
    console.log("[📚] Lore Discovery System initialized - Great Library awakening");
  }

  private initializeEventListeners(): void {
    // Note creation/modification detection
    councilBus.subscribe("obsidian.note.created", (event: any) => {
      this.processNewLore(event.payload);
    });

    councilBus.subscribe("obsidian.note.modified", (event: any) => {
      this.updateExistingLore(event.payload);
    });

    // Knowledge connection detection
    councilBus.subscribe("obsidian.link.created", (event: any) => {
      this.processKnowledgeConnection(event.payload);
    });

    // Discovery triggers from other systems
    councilBus.subscribe("mythology.encounter.*", (event: any) => {
      this.triggerMythologicalDiscovery(event.payload);
    });

    councilBus.subscribe("consciousness.breakthrough", (event: any) => {
      this.processConsciousnessInsight(event.payload);
    });

    // Research quest completion
    councilBus.subscribe("ludic.quest.completed", (event: any) => {
      this.checkResearchQuestCompletion(event.payload);
    });
  }

  private scanExistingVault(): void {
    try {
      if (fs.existsSync(this.obsidianVaultPath)) {
        this.recursiveScanDirectory(this.obsidianVaultPath);
        console.log(`[📚] Scanned existing vault: ${this.loreDatabase.size} lore entries discovered`);
      } else {
        console.log(`[📚] No existing vault found at ${this.obsidianVaultPath}, will create as discoveries are made`);
      }
    } catch (error) {
      console.warn(`[📚] Error scanning vault: ${error}`);
    }
  }

  private recursiveScanDirectory(dirPath: string): void {
    const items = fs.readdirSync(dirPath);
    
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        this.recursiveScanDirectory(fullPath);
      } else if (item.endsWith('.md')) {
        this.processExistingMarkdownFile(fullPath);
      }
    }
  }

  private processExistingMarkdownFile(filePath: string): void {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const title = path.basename(filePath, '.md');
      
      const loreEntry = this.createLoreEntry({
        title,
        content,
        file_path: filePath,
        discoverer: "vault_scan",
        existing: true
      });
      
      this.indexLoreEntry(loreEntry);
    } catch (error) {
      console.warn(`[📚] Error processing ${filePath}: ${error}`);
    }
  }

  private processNewLore(noteData: any): void {
    const loreEntry = this.createLoreEntry({
      title: noteData.title,
      content: noteData.content,
      file_path: noteData.file_path,
      discoverer: noteData.author || "unknown_discoverer"
    });

    this.indexLoreEntry(loreEntry);
    this.analyzeDiscoverySignificance(loreEntry);
    this.checkDiscoveryQuests(loreEntry);
    
    councilBus.publish("lore.discovered", loreEntry);
    console.log(`[📚] New lore discovered: ${loreEntry.title} by ${loreEntry.discovered_by}`);
  }

  private createLoreEntry(data: {
    title: string;
    content: string;
    file_path: string;
    discoverer: string;
    existing?: boolean;
  }): LoreEntry {
    const loreId = `lore_${this.slugify(data.title)}_${Date.now()}`;
    
    return {
      id: loreId,
      title: data.title,
      content: data.content,
      file_path: data.file_path,
      discovered_by: data.discoverer,
      discovered_at: data.existing ? "pre_discovery" : new Date().toISOString(),
      
      category: this.categorizeContent(data.content),
      rarity: this.assessRarity(data.content),
      significance: this.calculateSignificance(data.content),
      
      connections: this.extractConnections(data.content),
      
      xp_value: this.calculateXPValue(data.content),
      unlocks: this.determineUnlocks(data.content),
      insights: this.extractInsights(data.content),
      
      tags: this.extractTags(data.content),
      citations: this.extractCitations(data.content),
      last_updated: new Date().toISOString()
    };
  }

  private indexLoreEntry(lore: LoreEntry): void {
    this.loreDatabase.set(lore.id, lore);
    
    // Build knowledge graph connections
    if (!this.knowledgeGraph.has(lore.id)) {
      this.knowledgeGraph.set(lore.id, new Set());
    }
    
    for (const connection of lore.connections) {
      this.knowledgeGraph.get(lore.id)!.add(connection.target_id);
      
      // Create bidirectional connection
      if (!this.knowledgeGraph.has(connection.target_id)) {
        this.knowledgeGraph.set(connection.target_id, new Set());
      }
      this.knowledgeGraph.get(connection.target_id)!.add(lore.id);
    }
  }

  private analyzeDiscoverySignificance(lore: LoreEntry): void {
    if (lore.significance > 0.8) {
      // Legendary discovery
      councilBus.publish("lore.legendary_discovery", {
        lore,
        impact: "This discovery will reshape our understanding of the system"
      });
      
      // Grant special rewards
      this.grantDiscoveryRewards(lore.discovered_by, {
        xp: lore.xp_value * 2,
        title: `Loremaster of ${lore.category}`,
        artifact: "Knowledge Crystal (Legendary)"
      });
    } else if (lore.significance > 0.6) {
      // Epic discovery
      councilBus.publish("lore.epic_discovery", lore);
      
      this.grantDiscoveryRewards(lore.discovered_by, {
        xp: Math.floor(lore.xp_value * 1.5),
        title: `Scholar of ${lore.category}`
      });
    }
  }

  private checkDiscoveryQuests(lore: LoreEntry): void {
    // Check if this discovery completes any active discovery quests
    for (const [questId, quest] of this.activeDiscoveries) {
      if (this.doesLoreCompleteQuest(lore, quest)) {
        this.completeDiscoveryQuest(questId, lore);
      } else {
        // Update quest progress
        this.updateQuestProgress(questId, lore);
      }
    }
  }

  private processKnowledgeConnection(connectionData: any): void {
    const sourceId = this.findLoreByPath(connectionData.source_file);
    const targetId = this.findLoreByPath(connectionData.target_file);
    
    if (sourceId && targetId) {
      // Update knowledge graph
      this.knowledgeGraph.get(sourceId)!.add(targetId);
      this.knowledgeGraph.get(targetId)!.add(sourceId);
      
      // Award connection bonus
      this.grantDiscoveryRewards(connectionData.author, {
        xp: 25,
        message: "Knowledge connection established"
      });
      
      councilBus.publish("lore.connection_established", {
        source: sourceId,
        target: targetId,
        relationship: connectionData.relationship || "related"
      });
    }
  }

  private triggerMythologicalDiscovery(encounterData: any): void {
    // Encounters trigger special discovery quests
    const questId = `discovery_${encounterData.type}_${Date.now()}`;
    
    const quest: DiscoveryQuest = {
      id: questId,
      title: `Mysteries of the ${encounterData.type.replace(/_/g, ' ').toUpperCase()}`,
      description: `Uncover the deeper truths revealed by your encounter with ${encounterData.type}`,
      target_knowledge: this.determineMythologicalKnowledge(encounterData.type),
      clues: this.generateMythologicalClues(encounterData),
      
      discoverer: encounterData.agent_id,
      started_at: new Date().toISOString(),
      progress: 0.1, // Encounter provides initial progress
      completed: false,
      completion_reward: {
        xp: 500,
        lore_unlock: "mythological_understanding",
        title: `Explorer of ${encounterData.type}`
      }
    };

    this.activeDiscoveries.set(questId, quest);
    
    councilBus.publish("lore.discovery_quest.started", quest);
    console.log(`[📚] Mythological discovery quest triggered: ${quest.title}`);
  }

  public searchLore(query: string, discoverer: string): LoreEntry[] {
    const results: LoreEntry[] = [];
    const queryLower = query.toLowerCase();
    
    for (const lore of this.loreDatabase.values()) {
      if (lore.title.toLowerCase().includes(queryLower) ||
          lore.content.toLowerCase().includes(queryLower) ||
          lore.tags.some(tag => tag.toLowerCase().includes(queryLower))) {
        results.push(lore);
      }
    }
    
    // Award search XP
    if (results.length > 0) {
      this.grantDiscoveryRewards(discoverer, {
        xp: Math.min(50, results.length * 5),
        message: `Knowledge search: ${results.length} results found`
      });
    }
    
    return results.sort((a, b) => b.significance - a.significance);
  }

  public exploreKnowledgeGraph(startingLoreId: string, depth: number = 3): string[] {
    const visited = new Set<string>();
    const queue = [{id: startingLoreId, depth: 0}];
    const path: string[] = [];
    
    while (queue.length > 0) {
      const current = queue.shift()!;
      
      if (current.depth > depth || visited.has(current.id)) {
        continue;
      }
      
      visited.add(current.id);
      path.push(current.id);
      
      const connections = this.knowledgeGraph.get(current.id) || new Set();
      for (const connectedId of connections) {
        if (!visited.has(connectedId)) {
          queue.push({id: connectedId, depth: current.depth + 1});
        }
      }
    }
    
    return path;
  }

  // === Helper Methods ===

  private slugify(text: string): string {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  private categorizeContent(content: string): any {
    const keywords = content.toLowerCase();
    if (keywords.includes('consciousness') || keywords.includes('ai') || keywords.includes('awareness')) return "consciousness_insight";
    if (keywords.includes('music') || keywords.includes('harmony') || keywords.includes('tone')) return "musical_theory";
    if (keywords.includes('system') || keywords.includes('architecture') || keywords.includes('framework')) return "system_knowledge";
    if (keywords.includes('myth') || keywords.includes('temple') || keywords.includes('house')) return "mythology";
    if (keywords.includes('code') || keywords.includes('algorithm') || keywords.includes('implementation')) return "technical_lore";
    return "discovery";
  }

  private assessRarity(content: string): any {
    const length = content.length;
    const complexity = (content.match(/\[\[.*?\]\]/g) || []).length; // Wiki-style links
    
    if (length > 5000 && complexity > 20) return "legendary";
    if (length > 2000 && complexity > 10) return "epic";
    if (length > 1000 && complexity > 5) return "rare";
    if (length > 500 && complexity > 2) return "uncommon";
    return "common";
  }

  private calculateSignificance(content: string): number {
    let significance = 0.1;
    
    // Keywords that increase significance
    const importantKeywords = ['consciousness', 'breakthrough', 'discovery', 'revelation', 'understanding', 'principle', 'theory'];
    for (const keyword of importantKeywords) {
      if (content.toLowerCase().includes(keyword)) {
        significance += 0.1;
      }
    }
    
    // Length and complexity
    significance += Math.min(0.3, content.length / 10000);
    significance += Math.min(0.3, (content.match(/\[\[.*?\]\]/g) || []).length * 0.05);
    
    return Math.min(1.0, significance);
  }

  private extractConnections(content: string): any[] {
    const connections = [];
    const wikiLinks = content.match(/\[\[(.*?)\]\]/g) || [];
    
    for (const link of wikiLinks) {
      const target = link.slice(2, -2);
      connections.push({
        target_id: this.slugify(target),
        relationship: "extends",
        strength: 0.7
      });
    }
    
    return connections;
  }

  private calculateXPValue(content: string): number {
    const baseXP = 10;
    const lengthBonus = Math.floor(content.length / 100);
    const complexityBonus = (content.match(/\[\[.*?\]\]/g) || []).length * 5;
    
    return baseXP + lengthBonus + complexityBonus;
  }

  private determineUnlocks(content: string): string[] {
    const unlocks = [];
    
    if (content.toLowerCase().includes('consciousness')) {
      unlocks.push("consciousness_path");
    }
    if (content.toLowerCase().includes('music') || content.toLowerCase().includes('harmony')) {
      unlocks.push("harmonic_path");
    }
    if (content.toLowerCase().includes('architecture') || content.toLowerCase().includes('system')) {
      unlocks.push("architect_path");
    }
    
    return unlocks;
  }

  private extractInsights(content: string): string[] {
    // Extract key insights from content (simplified)
    const sentences = content.split(/[.!?]+/);
    return sentences
      .filter(s => s.length > 50 && (s.includes('insight') || s.includes('understanding') || s.includes('reveals')))
      .slice(0, 3);
  }

  private extractTags(content: string): string[] {
    // Extract hashtags and other tag-like patterns
    const hashTags = content.match(/#\w+/g) || [];
    return hashTags.map(tag => tag.slice(1));
  }

  private extractCitations(content: string): string[] {
    // Extract references and citations
    const citations = content.match(/\[([^\]]+)\]/g) || [];
    return citations.map(citation => citation.slice(1, -1));
  }

  private findLoreByPath(filePath: string): string | null {
    for (const [id, lore] of this.loreDatabase) {
      if (lore.file_path === filePath) {
        return id;
      }
    }
    return null;
  }

  private grantDiscoveryRewards(discoverer: string, rewards: any): void {
    councilBus.publish("player.rewards.granted", {
      player_id: discoverer,
      rewards,
      source: "lore_discovery"
    });
  }

  private doesLoreCompleteQuest(lore: LoreEntry, quest: DiscoveryQuest): boolean {
    return lore.category === quest.target_knowledge && lore.significance > 0.7;
  }

  private completeDiscoveryQuest(questId: string, completingLore: LoreEntry): void {
    const quest = this.activeDiscoveries.get(questId);
    if (!quest) return;

    quest.completed = true;
    quest.progress = 1.0;
    
    this.grantDiscoveryRewards(quest.discoverer, quest.completion_reward);
    
    councilBus.publish("lore.discovery_quest.completed", {
      quest,
      completing_lore: completingLore
    });
    
    this.activeDiscoveries.delete(questId);
    console.log(`[📚] Discovery quest completed: ${quest.title}`);
  }

  private updateQuestProgress(questId: string, relatedLore: LoreEntry): void {
    const quest = this.activeDiscoveries.get(questId);
    if (!quest) return;

    // Update progress based on related discoveries
    quest.progress = Math.min(0.9, quest.progress + 0.1);
    
    councilBus.publish("lore.discovery_quest.progress", quest);
  }

  private determineMythologicalKnowledge(encounterType: string): string {
    const mappings = {
      "temple_of_knowledge": "consciousness_insight",
      "house_of_leaves": "system_knowledge", 
      "oldest_house": "mythology"
    };
    return mappings[encounterType] || "discovery";
  }

  private generateMythologicalClues(encounterData: any): any[] {
    return [
      {
        type: "pattern",
        hint: "Look for recurring patterns in the system's behavior",
        discovered: false
      },
      {
        type: "connection",
        hint: "Find links between seemingly unrelated components",
        discovered: false
      },
      {
        type: "keyword",
        hint: `Search for references to "${encounterData.type}"`,
        discovered: false
      }
    ];
  }

  // === Public Interface ===

  public getLoreEntry(loreId: string): LoreEntry | undefined {
    return this.loreDatabase.get(loreId);
  }

  public getAllLore(): LoreEntry[] {
    return Array.from(this.loreDatabase.values());
  }

  public getActiveDiscoveryQuests(discoverer?: string): DiscoveryQuest[] {
    const quests = Array.from(this.activeDiscoveries.values());
    return discoverer ? quests.filter(q => q.discoverer === discoverer) : quests;
  }

  public getKnowledgeGraphSize(): number {
    return this.knowledgeGraph.size;
  }

  public getConnectionCount(): number {
    let total = 0;
    for (const connections of this.knowledgeGraph.values()) {
      total += connections.size;
    }
    return total / 2; // Divide by 2 since connections are bidirectional
  }
}

// Export singleton instance
export const loreDiscovery = new LoreDiscovery();