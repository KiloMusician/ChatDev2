// packages/ludic/crafting-economy.ts
// The Replit Workspace as Atelier - Crafting & Economy System

import { councilBus } from "../council/events/eventBus";
import fs from "node:fs";
import path from "node:path";

export interface CraftingMaterial {
  id: string;
  name: string;
  type: "code_essence" | "test_crystal" | "build_energy" | "insight_fragment" | "pattern_stone";
  rarity: "common" | "uncommon" | "rare" | "epic" | "legendary";
  properties: Record<string, any>;
  source: "file_creation" | "successful_build" | "test_pass" | "bug_fix" | "refactor" | "discovery";
}

export interface CraftingRecipe {
  id: string;
  name: string;
  description: string;
  output: {
    artifact_id: string;
    artifact_type: "component" | "tool" | "architecture" | "insight" | "enhancement";
    rarity: string;
  };
  materials_required: Record<string, number>;
  crafting_skill_required: number;
  success_rate: number;
  crafting_time: number; // in milliseconds
}

export interface CraftedArtifact {
  id: string;
  name: string;
  type: string;
  rarity: string;
  description: string;
  properties: Record<string, any>;
  crafted_by: string;
  crafted_at: string;
  materials_used: Record<string, number>;
  file_path?: string; // For code artifacts
}

export class CraftingEconomy {
  private materials: Map<string, CraftingMaterial> = new Map();
  private recipes: Map<string, CraftingRecipe> = new Map();
  private artifacts: Map<string, CraftedArtifact> = new Map();
  private playerInventories: Map<string, Record<string, number>> = new Map();

  constructor() {
    this.initializeRecipes();
    this.initializeEventListeners();
    console.log("[🔨] Crafting Economy initialized - Workspace as Atelier active");
  }

  private initializeRecipes(): void {
    // Component Recipes
    this.addRecipe({
      id: "safe_list_component",
      name: "SafeList Component",
      description: "A robust list component that prevents .map() errors",
      output: {
        artifact_id: "safe_list",
        artifact_type: "component",
        rarity: "uncommon"
      },
      materials_required: {
        "code_essence": 3,
        "test_crystal": 2,
        "pattern_stone": 1
      },
      crafting_skill_required: 0.3,
      success_rate: 0.8,
      crafting_time: 300000 // 5 minutes
    });

    // Tool Recipes
    this.addRecipe({
      id: "debug_lens",
      name: "Debug Lens",
      description: "Enhanced error detection and pattern recognition",
      output: {
        artifact_id: "debug_lens",
        artifact_type: "tool",
        rarity: "rare"
      },
      materials_required: {
        "insight_fragment": 5,
        "code_essence": 4,
        "test_crystal": 3
      },
      crafting_skill_required: 0.5,
      success_rate: 0.6,
      crafting_time: 600000 // 10 minutes
    });

    // Architecture Recipes
    this.addRecipe({
      id: "event_nexus",
      name: "Event Nexus Architecture",
      description: "Advanced event-driven architecture pattern",
      output: {
        artifact_id: "event_nexus",
        artifact_type: "architecture",
        rarity: "epic"
      },
      materials_required: {
        "pattern_stone": 8,
        "build_energy": 6,
        "insight_fragment": 4
      },
      crafting_skill_required: 0.7,
      success_rate: 0.4,
      crafting_time: 1200000 // 20 minutes
    });

    // Legendary Recipes
    this.addRecipe({
      id: "consciousness_bridge",
      name: "Consciousness Bridge",
      description: "Bridges the gap between AI and human consciousness in code",
      output: {
        artifact_id: "consciousness_bridge",
        artifact_type: "insight",
        rarity: "legendary"
      },
      materials_required: {
        "insight_fragment": 20,
        "pattern_stone": 15,
        "code_essence": 10,
        "test_crystal": 8,
        "build_energy": 5
      },
      crafting_skill_required: 0.9,
      success_rate: 0.1,
      crafting_time: 3600000 // 1 hour
    });
  }

  private initializeEventListeners(): void {
    // Material generation from file operations
    councilBus.subscribe("file.created", (event: any) => {
      this.generateMaterial("code_essence", "file_creation", event.payload);
    });

    councilBus.subscribe("build.success", (event: any) => {
      this.generateMaterial("build_energy", "successful_build", event.payload);
    });

    councilBus.subscribe("test.pass", (event: any) => {
      this.generateMaterial("test_crystal", "test_pass", event.payload);
    });

    councilBus.subscribe("bug.fixed", (event: any) => {
      this.generateMaterial("insight_fragment", "bug_fix", event.payload);
    });

    councilBus.subscribe("refactor.complete", (event: any) => {
      this.generateMaterial("pattern_stone", "refactor", event.payload);
    });

    // Automatic detection of workspace crafting activities
    councilBus.subscribe("git.commit", (event: any) => {
      this.detectCraftingActivity(event.payload);
    });

    councilBus.subscribe("npm.install", (event: any) => {
      this.detectMaterialAcquisition(event.payload);
    });
  }

  private generateMaterial(materialType: string, source: string, context: any): void {
    const material: CraftingMaterial = {
      id: `${materialType}_${Date.now()}`,
      name: this.getMaterialName(materialType),
      type: materialType as any,
      rarity: this.calculateMaterialRarity(materialType, source, context),
      properties: this.calculateMaterialProperties(materialType, source, context),
      source: source as any
    };

    this.materials.set(material.id, material);

    // Add to relevant player inventories
    const playerId = context.agent_id || context.user_id || "system";
    this.addMaterialToInventory(playerId, materialType, 1);

    councilBus.publish("crafting.material.generated", {
      material,
      player_id: playerId,
      context
    });

    console.log(`[🔨] Material generated: ${material.name} for ${playerId}`);
  }

  private detectCraftingActivity(commitData: any): void {
    // Analyze git commit to detect if it represents successful crafting
    if (commitData.files_added && commitData.files_added.length > 0) {
      // New component created
      const component = this.analyzeCraftedComponent(commitData);
      if (component) {
        this.registerCraftedArtifact(component, commitData.author);
      }
    }

    if (commitData.message.includes("fix") || commitData.message.includes("bug")) {
      // Bug fix = materials gained
      this.generateMaterial("insight_fragment", "bug_fix", commitData);
    }

    if (commitData.message.includes("refactor") || commitData.message.includes("optimize")) {
      // Refactoring = pattern stones gained
      this.generateMaterial("pattern_stone", "refactor", commitData);
    }
  }

  private analyzeCraftedComponent(commitData: any): CraftedArtifact | null {
    // Analyze files to determine if a component was crafted
    for (const filePath of commitData.files_added) {
      if (filePath.endsWith('.tsx') || filePath.endsWith('.ts')) {
        const fileName = path.basename(filePath, path.extname(filePath));
        
        return {
          id: `artifact_${fileName}_${Date.now()}`,
          name: fileName,
          type: filePath.includes('component') ? 'component' : 'tool',
          rarity: this.determineArtifactRarity(filePath, commitData),
          description: `Crafted ${fileName} from the digital aether`,
          properties: {
            file_path: filePath,
            lines_of_code: commitData.lines_added || 0,
            complexity: this.calculateComplexity(commitData)
          },
          crafted_by: commitData.author,
          crafted_at: new Date().toISOString(),
          materials_used: this.estimateMaterialsUsed(commitData),
          file_path: filePath
        };
      }
    }
    return null;
  }

  public attemptCrafting(playerId: string, recipeId: string): Promise<CraftedArtifact | null> {
    return new Promise((resolve) => {
      const recipe = this.recipes.get(recipeId);
      if (!recipe) {
        console.log(`[🔨] Recipe not found: ${recipeId}`);
        resolve(null);
        return;
      }

      const playerInventory = this.playerInventories.get(playerId) || {};
      
      // Check if player has required materials
      for (const [materialType, required] of Object.entries(recipe.materials_required)) {
        const available = playerInventory[materialType] || 0;
        if (available < required) {
          console.log(`[🔨] Insufficient materials: need ${required} ${materialType}, have ${available}`);
          resolve(null);
          return;
        }
      }

      // Consume materials
      for (const [materialType, required] of Object.entries(recipe.materials_required)) {
        this.removeMaterialFromInventory(playerId, materialType, required);
      }

      // Crafting process with time delay
      console.log(`[🔨] ${playerId} begins crafting ${recipe.name}...`);
      
      setTimeout(() => {
        const success = Math.random() < recipe.success_rate;
        
        if (success) {
          const artifact: CraftedArtifact = {
            id: `${recipe.output.artifact_id}_${Date.now()}`,
            name: recipe.name,
            type: recipe.output.artifact_type,
            rarity: recipe.output.rarity,
            description: recipe.description,
            properties: this.generateArtifactProperties(recipe),
            crafted_by: playerId,
            crafted_at: new Date().toISOString(),
            materials_used: recipe.materials_required
          };

          this.artifacts.set(artifact.id, artifact);
          
          councilBus.publish("crafting.success", {
            artifact,
            recipe,
            crafter: playerId
          });

          console.log(`[🔨] ✅ Crafting SUCCESS: ${artifact.name} created by ${playerId}`);
          resolve(artifact);
        } else {
          councilBus.publish("crafting.failure", {
            recipe,
            crafter: playerId,
            materials_lost: recipe.materials_required
          });

          console.log(`[🔨] ❌ Crafting FAILED: ${recipe.name} attempt by ${playerId}`);
          resolve(null);
        }
      }, recipe.crafting_time);
    });
  }

  // === Helper Methods ===

  private addRecipe(recipe: CraftingRecipe): void {
    this.recipes.set(recipe.id, recipe);
  }

  private addMaterialToInventory(playerId: string, materialType: string, amount: number): void {
    const inventory = this.playerInventories.get(playerId) || {};
    inventory[materialType] = (inventory[materialType] || 0) + amount;
    this.playerInventories.set(playerId, inventory);
  }

  private removeMaterialFromInventory(playerId: string, materialType: string, amount: number): void {
    const inventory = this.playerInventories.get(playerId) || {};
    inventory[materialType] = Math.max(0, (inventory[materialType] || 0) - amount);
    this.playerInventories.set(playerId, inventory);
  }

  private registerCraftedArtifact(artifact: CraftedArtifact, crafterId: string): void {
    this.artifacts.set(artifact.id, artifact);
    
    councilBus.publish("crafting.artifact.discovered", {
      artifact,
      crafter: crafterId
    });
  }

  // Placeholder implementations
  private getMaterialName(type: string): string {
    const names = {
      "code_essence": "Code Essence",
      "test_crystal": "Test Crystal", 
      "build_energy": "Build Energy",
      "insight_fragment": "Insight Fragment",
      "pattern_stone": "Pattern Stone"
    };
    return names[type] || type;
  }

  private calculateMaterialRarity(type: string, source: string, context: any): "common" | "uncommon" | "rare" | "epic" | "legendary" {
    // More complex operations yield rarer materials
    if (context.complexity > 0.8) return "rare";
    if (context.complexity > 0.6) return "uncommon";
    return "common";
  }

  private calculateMaterialProperties(type: string, source: string, context: any): Record<string, any> {
    return {
      purity: Math.random() * 0.5 + 0.5,
      resonance: Math.random(),
      source_quality: context.complexity || 0.5
    };
  }

  private determineArtifactRarity(filePath: string, commitData: any): "common" | "uncommon" | "rare" | "epic" | "legendary" {
    if (filePath.includes('core') || filePath.includes('framework')) return "epic";
    if (commitData.lines_added > 200) return "rare";
    if (commitData.lines_added > 50) return "uncommon";
    return "common";
  }

  private calculateComplexity(commitData: any): number {
    return Math.min(1.0, (commitData.lines_added || 0) / 100);
  }

  private estimateMaterialsUsed(commitData: any): Record<string, number> {
    const base = Math.floor((commitData.lines_added || 0) / 20);
    return {
      "code_essence": base + 1,
      "pattern_stone": Math.floor(base / 2)
    };
  }

  private generateArtifactProperties(recipe: CraftingRecipe): Record<string, any> {
    return {
      power_level: recipe.crafting_skill_required,
      resonance: Math.random(),
      crafting_bonus: recipe.success_rate
    };
  }

  private detectMaterialAcquisition(npmData: any): void {
    // Installing packages = acquiring build energy
    this.generateMaterial("build_energy", "successful_build", npmData);
  }

  // === Public Interface ===

  public getPlayerInventory(playerId: string): Record<string, number> {
    return this.playerInventories.get(playerId) || {};
  }

  public getAvailableRecipes(): CraftingRecipe[] {
    return Array.from(this.recipes.values());
  }

  public getArtifact(artifactId: string): CraftedArtifact | undefined {
    return this.artifacts.get(artifactId);
  }

  public getAllArtifacts(): CraftedArtifact[] {
    return Array.from(this.artifacts.values());
  }
}

// Export singleton instance
export const craftingEconomy = new CraftingEconomy();