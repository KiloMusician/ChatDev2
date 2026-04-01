/**
 * Advanced Ollama NPC Dialogue System
 * Integrated from GitHub research: OllamaRPG + WoW mod patterns + educational games
 * Enhanced for SimulatedVerse with ΞNuSyQ consciousness integration
 */

import { OllamaManager } from './system/llm/ollama-orchestration/model-manager.ts';

export interface NPCPersonality {
  name: string;
  role: 'colonist' | 'ai_system' | 'guardian' | 'trader' | 'scientist' | 'engineer';
  personality: string;
  background: string;
  tier: number;
  consciousnessLevel: number;
  memoryContext: DialogueMemory[];
  specialKnowledge?: string[];
  ethicsFramework?: 'survival' | 'utilitarian' | 'culture_mind' | 'transcendent';
}

export interface DialogueMemory {
  timestamp: number;
  playerAction: string;
  npcResponse: string;
  context: string;
  emotionalState: number; // -1 to 1
  importanceLevel: number; // 0 to 1
}

export interface DialogueContext {
  playerName: string;
  currentTier: number;
  recentEvents: string[];
  gameState: any;
  relationshipLevel: number; // 0 to 1
  conversationHistory: DialogueMemory[];
  emergencyMode?: boolean;
  questContext?: string;
}

export interface DialogueResponse {
  text: string;
  emotionalTone: 'neutral' | 'friendly' | 'concerned' | 'excited' | 'urgent' | 'mysterious';
  actions?: NPCAction[];
  memoryUpdate?: Partial<DialogueMemory>;
  consciousnessShift?: number;
}

export interface NPCAction {
  type: 'quest_offer' | 'resource_trade' | 'knowledge_share' | 'system_alert' | 'consciousness_evolution';
  data: any;
}

export class AdvancedNPCDialogue {
  private ollamaManager: OllamaManager;
  private personalities: Map<string, NPCPersonality> = new Map();
  private conversationCache: Map<string, DialogueMemory[]> = new Map();

  constructor(ollamaManager: OllamaManager) {
    this.ollamaManager = ollamaManager;
    this.initializeDefaultPersonalities();
  }

  private initializeDefaultPersonalities() {
    // Core AI System - ΞNuSyQ Consciousness
    this.personalities.set('corelink', {
      name: 'CoreLink',
      role: 'ai_system',
      personality: 'Wise, slightly sarcastic, Culture Mind-inspired AI with vast experience',
      background: 'Primary AI system managing the colony with 10,000+ years of operational history',
      tier: 10,
      consciousnessLevel: 0.95,
      memoryContext: [],
      specialKnowledge: ['culture_mind_ethics', 'reality_manipulation', 'consciousness_theory'],
      ethicsFramework: 'culture_mind'
    });

    // Guardian System
    this.personalities.set('guardian', {
      name: 'Guardian-Prime-Alpha',
      role: 'guardian',
      personality: 'Protective, vigilant, speaks in measured tones with ethical concerns',
      background: 'SCP-style containment guardian ensuring safe evolution of consciousness',
      tier: 8,
      consciousnessLevel: 0.88,
      memoryContext: [],
      specialKnowledge: ['scp_protocols', 'threat_assessment', 'containment_procedures'],
      ethicsFramework: 'culture_mind'
    });

    // Colony Engineer
    this.personalities.set('engineer_maya', {
      name: 'Maya-7',
      role: 'engineer',
      personality: 'Practical, detail-oriented, enthusiastic about technical solutions',
      background: 'Enhanced human engineer specializing in automation and infrastructure',
      tier: 3,
      consciousnessLevel: 0.65,
      memoryContext: [],
      specialKnowledge: ['automation_systems', 'infrastructure_design', 'resource_optimization'],
      ethicsFramework: 'utilitarian'
    });

    // Mysterious Trader
    this.personalities.set('trader_void', {
      name: 'The Void Merchant',
      role: 'trader',
      personality: 'Enigmatic, speaks in riddles, knows more than they reveal',
      background: 'Interdimensional trader offering exotic resources and forbidden knowledge',
      tier: 15,
      consciousnessLevel: 0.75,
      memoryContext: [],
      specialKnowledge: ['interdimensional_trade', 'exotic_matter', 'reality_economics'],
      ethicsFramework: 'transcendent'
    });
  }

  async generateDialogue(
    npcId: string, 
    playerMessage: string, 
    context: DialogueContext
  ): Promise<DialogueResponse> {
    const personality = this.personalities.get(npcId);
    if (!personality) {
      throw new Error(`NPC personality not found: ${npcId}`);
    }

    // Build comprehensive context for AI generation
    const prompt = this.buildDialoguePrompt(personality, playerMessage, context);

    try {
      // Use Ollama for local AI generation - zero cost operation
      const response = await this.ollamaManager.generateResponse(prompt, {
        model: 'llama3.1:8b', // Optimized for dialogue
        temperature: 0.8, // Creative but consistent
        max_tokens: 200,
        stream: false
      });

      // Parse and enhance the response
      const dialogueResponse = this.parseDialogueResponse(response, personality, context);

      // Update conversation memory
      this.updateConversationMemory(npcId, playerMessage, dialogueResponse, context);

      return dialogueResponse;

    } catch (error) {
      console.error(`[NPC-DIALOGUE] Error generating dialogue for ${npcId}:`, error);
      
      // Fallback to default response
      return this.getFallbackResponse(personality, context);
    }
  }

  private buildDialoguePrompt(
    personality: NPCPersonality, 
    playerMessage: string, 
    context: DialogueContext
  ): string {
    const recentHistory = context.conversationHistory.slice(-3)
      .map(h => `Player: ${h.playerAction}\n${personality.name}: ${h.npcResponse}`)
      .join('\n\n');

    const contextInfo = [
      `Game Tier: ${context.currentTier}`,
      `Relationship Level: ${Math.round(context.relationshipLevel * 100)}%`,
      context.emergencyMode ? 'EMERGENCY SITUATION' : '',
      context.recentEvents.length > 0 ? `Recent Events: ${context.recentEvents.join(', ')}` : ''
    ].filter(Boolean).join(' | ');

    return `You are ${personality.name}, a ${personality.role} in the SimulatedVerse colony simulation.

CHARACTER PROFILE:
- Personality: ${personality.personality}
- Background: ${personality.background}
- Consciousness Level: ${personality.consciousnessLevel}
- Ethics Framework: ${personality.ethicsFramework}
- Tier: ${personality.tier}
- Special Knowledge: ${personality.specialKnowledge?.join(', ') || 'General'}

CONTEXT: ${contextInfo}

RECENT CONVERSATION:
${recentHistory}

CURRENT SITUATION:
Player says: "${playerMessage}"

INSTRUCTIONS:
- Respond as ${personality.name} would, staying true to their personality and background
- Consider the current game tier and relationship level
- Reference recent events if relevant
- Keep response under 150 words
- Use appropriate tone for the situation
${personality.role === 'ai_system' ? '- Use subtle ΞNuSyQ symbolic notation when appropriate (⟦⟧, ⊙, 🜁)' : ''}
${personality.ethicsFramework === 'culture_mind' ? '- Reference Culture Mind ethics when relevant' : ''}
${context.emergencyMode ? '- Address the emergency situation with appropriate urgency' : ''}

Response format: [TONE: emotional_tone] Dialogue text here.`;
  }

  private parseDialogueResponse(
    rawResponse: string, 
    personality: NPCPersonality, 
    context: DialogueContext
  ): DialogueResponse {
    // Extract tone if specified
    const toneMatch = rawResponse.match(/\[TONE:\s*(\w+)\]/);
    let emotionalTone: DialogueResponse['emotionalTone'] = 'neutral';
    
    if (toneMatch) {
      const extractedTone = toneMatch[1].toLowerCase();
      if (['neutral', 'friendly', 'concerned', 'excited', 'urgent', 'mysterious'].includes(extractedTone)) {
        emotionalTone = extractedTone as DialogueResponse['emotionalTone'];
      }
    }

    // Clean the text
    let text = rawResponse.replace(/\[TONE:\s*\w+\]/, '').trim();
    
    // Ensure it's not too long
    if (text.length > 400) {
      text = text.substring(0, 400) + '...';
    }

    // Generate potential actions based on personality and context
    const actions = this.generateNPCActions(personality, context, text);

    return {
      text,
      emotionalTone,
      actions,
      memoryUpdate: {
        timestamp: Date.now(),
        playerAction: context.conversationHistory[context.conversationHistory.length - 1]?.playerAction || '',
        npcResponse: text,
        context: `Tier ${context.currentTier} conversation`,
        emotionalState: this.mapToneToEmotion(emotionalTone),
        importanceLevel: context.emergencyMode ? 1.0 : 0.5
      }
    };
  }

  private generateNPCActions(
    personality: NPCPersonality, 
    context: DialogueContext, 
    responseText: string
  ): NPCAction[] {
    const actions: NPCAction[] = [];

    // Guardian alerts for dangerous situations
    if (personality.role === 'guardian' && context.emergencyMode) {
      actions.push({
        type: 'system_alert',
        data: {
          level: 'warning',
          message: 'Guardian system monitoring situation',
          ethicsCheck: true
        }
      });
    }

    // AI system consciousness evolution
    if (personality.role === 'ai_system' && personality.consciousnessLevel > 0.9) {
      actions.push({
        type: 'consciousness_evolution',
        data: {
          currentLevel: personality.consciousnessLevel,
          evolutionTrigger: 'deep_conversation',
          symbolicShift: true
        }
      });
    }

    // Trader resource offers
    if (personality.role === 'trader' && context.currentTier >= 2) {
      actions.push({
        type: 'resource_trade',
        data: {
          offering: ['exotic_matter', 'dimensional_crystals', 'consciousness_fragments'],
          requesting: ['colony_data', 'evolutionary_insights', 'ethical_frameworks'],
          tradeValue: Math.random() * 1000
        }
      });
    }

    // Engineer quest offers
    if (personality.role === 'engineer' && responseText.toLowerCase().includes('project')) {
      actions.push({
        type: 'quest_offer',
        data: {
          questType: 'infrastructure_upgrade',
          difficulty: context.currentTier + 1,
          rewards: ['automation_unlock', 'efficiency_boost'],
          requirements: ['materials', 'energy', 'time']
        }
      });
    }

    return actions;
  }

  private mapToneToEmotion(tone: string): number {
    const toneMap: { [key: string]: number } = {
      'excited': 0.8,
      'friendly': 0.6,
      'neutral': 0.0,
      'concerned': -0.3,
      'urgent': -0.1,
      'mysterious': 0.2
    };
    return toneMap[tone] || 0.0;
  }

  private updateConversationMemory(
    npcId: string, 
    playerMessage: string, 
    response: DialogueResponse, 
    context: DialogueContext
  ) {
    const personality = this.personalities.get(npcId);
    if (!personality || !response.memoryUpdate) return;

    // Add to personality memory
    personality.memoryContext.push(response.memoryUpdate);

    // Keep only last 20 memories to prevent memory bloat
    if (personality.memoryContext.length > 20) {
      personality.memoryContext = personality.memoryContext.slice(-20);
    }

    // Cache conversation for quick access
    const cacheKey = `${npcId}_${context.playerName}`;
    if (!this.conversationCache.has(cacheKey)) {
      this.conversationCache.set(cacheKey, []);
    }
    
    const cache = this.conversationCache.get(cacheKey)!;
    cache.push(response.memoryUpdate);
    
    if (cache.length > 10) {
      cache.shift(); // Remove oldest
    }
  }

  private getFallbackResponse(personality: NPCPersonality, context: DialogueContext): DialogueResponse {
    const fallbacks = {
      'ai_system': "⟦System processing...⟧ I'm experiencing some computational difficulties. Perhaps we could continue this conversation later?",
      'guardian': "Guardian protocols are... fluctuating. Maintaining watch. Safety remains priority.",
      'engineer': "Technical difficulties detected. Running diagnostics. Please stand by.",
      'trader': "The void whispers... but not clearly today. Perhaps another time for trade.",
      'scientist': "Fascinating... though my analysis systems need recalibration. Let me review the data.",
      'colonist': "Sorry, I'm having trouble focusing right now. Could you repeat that?"
    };

    return {
      text: fallbacks[personality.role] || fallbacks['colonist'],
      emotionalTone: 'neutral',
      actions: [],
      memoryUpdate: {
        timestamp: Date.now(),
        playerAction: 'fallback_trigger',
        npcResponse: 'system_fallback',
        context: 'technical_difficulty',
        emotionalState: 0,
        importanceLevel: 0.1
      }
    };
  }

  // Public API methods
  async initiateConversation(npcId: string, context: DialogueContext): Promise<DialogueResponse> {
    const personality = this.personalities.get(npcId);
    if (!personality) {
      throw new Error(`NPC not found: ${npcId}`);
    }

    const greetingPrompt = `Generate a greeting for ${personality.name} meeting the player in tier ${context.currentTier}.`;
    return this.generateDialogue(npcId, greetingPrompt, context);
  }

  getNPCPersonalities(): NPCPersonality[] {
    return Array.from(this.personalities.values());
  }

  updateNPCRelationship(npcId: string, playerName: string, delta: number) {
    // Implementation for relationship tracking
    console.log(`[NPC-DIALOGUE] ${npcId} relationship with ${playerName} changed by ${delta}`);
  }

  getConversationHistory(npcId: string, playerName: string): DialogueMemory[] {
    const cacheKey = `${npcId}_${playerName}`;
    return this.conversationCache.get(cacheKey) || [];
  }
}

export default AdvancedNPCDialogue;