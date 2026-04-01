import YAML from "yaml";
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { stat } from "fs/promises";

interface Quest {
  id: string;
  title: string;
  description?: string;
  tier?: string;
  xp_reward?: number;
  requirements?: string[];
  tasks?: string[];
  completion_criteria?: Record<string, string | number | boolean>;
  repeatable?: boolean;
  reset_interval?: string;
}

interface QuestBook {
  consciousness_evolution?: Quest[];
  debugging_labyrinth?: Quest[];  
  temple_ascension?: Quest[];
  ethical_guardian?: Quest[];
  colony_mastery?: Quest[];
  transcendence_preparation?: Quest[];
  daily_maintenance?: Quest[];
  [key: string]: Quest[] | any;
}

interface QuestState {
  done: string[];
  todo: string[];
  in_progress: string[];
  failed: string[];
  timestamp: number;
}

function evaluateCondition(condition: string, gameState: any): boolean {
  try {
    // Simple condition evaluator for quest completion criteria
    
    // Numeric comparisons
    const numericMatch = condition.match(/^(\w+(?:\.\w+)*)\s*(>=|<=|>|<|=)\s*(.+)$/);
    if (numericMatch) {
      const [, path, operator, valueStr] = numericMatch;
      const actualValue = getValueByPath(gameState, path);
      const expectedValue = parseFloat(valueStr);
      
      if (isNaN(expectedValue) || actualValue === undefined) return false;
      
      switch (operator) {
        case '>=': return actualValue >= expectedValue;
        case '<=': return actualValue <= expectedValue;
        case '>': return actualValue > expectedValue;
        case '<': return actualValue < expectedValue;
        case '=': return actualValue === expectedValue;
        default: return false;
      }
    }
    
    // Boolean conditions
    if (condition === 'true') return true;
    if (condition === 'false') return false;
    
    // File existence checks
    const fileMatch = condition.match(/file_exists\(([^)]+)\)/);
    if (fileMatch) {
      const filename = fileMatch[1].replace(/['"]/g, '');
      return existsSync(filename);
    }
    
    // String contains checks
    const containsMatch = condition.match(/(\w+(?:\.\w+)*)\s*contains\s*"([^"]+)"/);
    if (containsMatch) {
      const [, path, substring] = containsMatch;
      const value = getValueByPath(gameState, path);
      return typeof value === 'string' && value.includes(substring);
    }
    
    // Direct path evaluation
    const value = getValueByPath(gameState, condition);
    return Boolean(value);
    
  } catch (error) {
    console.warn(`Failed to evaluate condition: ${condition}`, error);
    return false;
  }
}

function getValueByPath(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined;
  }, obj);
}

function loadGameState(): any {
  try {
    const idleState = JSON.parse(readFileSync(".local/idle_state.json", "utf8"));
    
    // Enhance with additional context
    const enhancedState = {
      ...idleState,
      files: {
        env_exists: existsSync('.env'),
        temple_manifest_exists: existsSync('src/temple/manifest.yml'),
        agent_config_exists: existsSync('agent/config.yml')
      },
      git: {
        has_commits: existsSync('.git'),
        // Could add more git status checks here
      }
    };
    
    return enhancedState;
  } catch {
    return {
      consciousness: { level: 0.1, stage: "proto-conscious" },
      temple: { unlockedFloors: [1, 2], knowledgePoints: 100 },
      labyrinth: { bugsFixed: 0 },
      colony: { buildings: { labs: 0 } },
      files: { env_exists: false, temple_manifest_exists: false }
    };
  }
}

export async function runQuests({ snapshot }: { snapshot: any }) {
  try {
    const questBookPath = "src/quests/qbook.yml";
    if (!existsSync(questBookPath)) {
      console.warn("Quest book not found, creating basic structure");
      return { done: [], todo: ["quest_book_missing"], in_progress: [], failed: [] };
    }
    
    const raw = readFileSync(questBookPath, "utf8");
    const questBook: QuestBook = YAML.parse(raw);
    
    const gameState = {
      ...snapshot.state,
      ...loadGameState()
    };
    
    const questState: QuestState = {
      done: [],
      todo: [],
      in_progress: [],
      failed: [],
      timestamp: Date.now()
    };
    
    // Process all quest categories
    for (const [categoryName, quests] of Object.entries(questBook)) {
      if (categoryName === 'meta' || !Array.isArray(quests)) continue;
      
      for (const quest of quests) {
        const questStatus = evaluateQuest(quest, gameState);
        
        if (questStatus === 'completed') {
          questState.done.push(quest.id);
        } else if (questStatus === 'available') {
          questState.todo.push(quest.id);
        } else if (questStatus === 'blocked') {
          // Requirements not met yet
          continue;
        } else if (questStatus === 'failed') {
          questState.failed.push(quest.id);
        }
      }
    }
    
    // Save quest state for UI and other systems
    mkdirSync(".local", { recursive: true });
    writeFileSync(".local/quests.json", JSON.stringify(questState, null, 2));
    
    // Log progress
    console.log(`🎯 Quest Progress: ${questState.done.length} done, ${questState.todo.length} available, ${questState.failed.length} failed`);
    
    return questState;
    
  } catch (error) {
    console.error("Quest evaluation failed:", error);
    return { 
      done: [], 
      todo: ["quest_system_error"], 
      in_progress: [], 
      failed: ["quest_evaluation_failed"],
      timestamp: Date.now()
    };
  }
}

function evaluateQuest(quest: Quest, gameState: any): 'completed' | 'available' | 'blocked' | 'failed' {
  try {
    // Check if requirements are met
    if (quest.requirements) {
      for (const requirement of quest.requirements) {
        // Simple requirement check - could be enhanced
        if (typeof requirement === 'string') {
          // Check if it's another quest ID that should be completed
          const completedQuests = getValueByPath(gameState, 'completed_quests') || [];
          if (!completedQuests.includes(requirement) && !evaluateCondition(requirement, gameState)) {
            return 'blocked';
          }
        }
      }
    }
    
    // Check completion criteria
    if (quest.completion_criteria) {
      let allCriteriaMet = true;
      
      for (const [criterion, expected] of Object.entries(quest.completion_criteria)) {
        const met = evaluateCondition(`${criterion} >= ${expected}`, gameState) || 
                   evaluateCondition(`${criterion} = ${expected}`, gameState) ||
                   evaluateCondition(`${criterion}`, gameState);
        
        if (!met) {
          allCriteriaMet = false;
          break;
        }
      }
      
      if (allCriteriaMet) {
        return 'completed';
      }
    }
    
    // If requirements are met but not completed, it's available
    return 'available';
    
  } catch (error) {
    console.warn(`Quest evaluation error for ${quest.id}:`, error);
    return 'failed';
  }
}