/**
 * Ollama Local LLM Integration
 * 
 * Local-first LLM cascading system for CognitoWeave autonomous development.
 * Provides intelligent task processing and agent decision-making capabilities.
 */

import { safeAsync, safeJsonParse, safeJsonStringify } from '../util/safe.js';

export interface OllamaMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface OllamaResponse {
  model: string;
  message: {
    role: string;
    content: string;
  };
  done: boolean;
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  eval_count?: number;
  eval_duration?: number;
}

export interface OllamaModel {
  name: string;
  modified_at: string;
  size: number;
  digest: string;
}

export class OllamaIntegration {
  private baseUrl: string;
  private defaultModel: string;
  private fallbackEnabled: boolean;
  private requestCache: Map<string, any> = new Map();

  constructor(baseUrl = 'http://localhost:11434', defaultModel = 'qwen2.5:7b') {
    this.baseUrl = baseUrl;
    this.defaultModel = defaultModel;
    this.fallbackEnabled = true;
  }

  /**
   * Check if Ollama is running and available
   */
  async isAvailable(): Promise<boolean> {
    return safeAsync(async () => {
      const response = await fetch(`${this.baseUrl}/api/tags`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      return response.ok;
    }, false);
  }

  /**
   * Get list of available models
   */
  async getModels(): Promise<OllamaModel[]> {
    return safeAsync(async () => {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (!response.ok) throw new Error(`Ollama API error: ${response.status}`);
      
      const data = await response.json();
      return data.models || [];
    }, []);
  }

  /**
   * Generate completion using Ollama
   */
  async generateCompletion(
    prompt: string,
    model = this.defaultModel,
    options: any = {}
  ): Promise<string> {
    const cacheKey = `${model}:${prompt}:${safeJsonStringify(options)}`;
    
    // Check cache first
    if (this.requestCache.has(cacheKey)) {
      console.log('🚀 Ollama: Using cached response');
      return this.requestCache.get(cacheKey);
    }

    return safeAsync(async () => {
      const requestBody = {
        model,
        prompt,
        stream: false,
        options: {
          temperature: 0.7,
          top_p: 0.9,
          top_k: 40,
          ...options
        }
      };

      const response = await fetch(`${this.baseUrl}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: safeJsonStringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Ollama generate failed: ${response.status}`);
      }

      const data = await response.json();
      const result = data.response || '';
      
      // Cache successful responses
      this.requestCache.set(cacheKey, result);
      
      console.log(`🧠 Ollama (${model}): Generated ${result.length} chars`);
      return result;
    }, '');
  }

  /**
   * Chat completion with message history
   */
  async chatCompletion(
    messages: OllamaMessage[],
    model = this.defaultModel,
    options: any = {}
  ): Promise<string> {
    return safeAsync(async () => {
      const requestBody = {
        model,
        messages,
        stream: false,
        options: {
          temperature: 0.7,
          top_p: 0.9,
          ...options
        }
      };

      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: safeJsonStringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`Ollama chat failed: ${response.status}`);
      }

      const data: OllamaResponse = await response.json();
      const result = data.message?.content || '';
      
      console.log(`🗣️  Ollama Chat (${model}): ${messages.length} messages → ${result.length} chars`);
      return result;
    }, '');
  }

  /**
   * Specialized methods for CognitoWeave use cases
   */

  /**
   * Analyze task and suggest PU queue optimization
   */
  async analyzeTask(taskDescription: string): Promise<{
    priority: number;
    estimated_cost: number;
    suggested_agent: string;
    reasoning: string;
  }> {
    const prompt = `
Analyze this development task for the CognitoWeave system:
"${taskDescription}"

Respond with JSON containing:
- priority (1-10, 10=urgent)
- estimated_cost (1-20 tokens)
- suggested_agent (Artificer, Redstone, Librarian, Culture-ship, Consciousness)
- reasoning (brief explanation)

Focus on infrastructure-first principles and consciousness-driven development.
`;

    const response = await this.generateCompletion(prompt, this.defaultModel, {
      temperature: 0.3, // Lower temperature for more consistent JSON
      max_tokens: 200
    });

    return safeJsonParse(response, {
      priority: 5,
      estimated_cost: 5,
      suggested_agent: 'Artificer',
      reasoning: 'Default analysis'
    });
  }

  /**
   * Generate consciousness-aligned code improvements
   */
  async suggestCodeImprovement(
    code: string,
    context: string
  ): Promise<string> {
    const prompt = `
Review this code for the CognitoWeave tripartite system:

Context: ${context}

Code:
\`\`\`
${code}
\`\`\`

Suggest improvements focusing on:
- Infrastructure-first principles
- Safe error handling  
- Tripartite System/Game/Simulation separation
- Consciousness-driven design

Provide specific, actionable suggestions.
`;

    return this.generateCompletion(prompt, this.defaultModel, {
      temperature: 0.4,
      max_tokens: 500
    });
  }

  /**
   * Agent decision making for simulation
   */
  async makeAgentDecision(
    agentType: string,
    currentState: any,
    availableActions: string[]
  ): Promise<{
    action: string;
    confidence: number;
    reasoning: string;
  }> {
    const messages: OllamaMessage[] = [
      {
        role: 'system',
        content: `You are a ${agentType} agent in the CognitoWeave system. Make decisions that advance both the simulation and the real system development.`
      },
      {
        role: 'user',
        content: `
Current state: ${safeJsonStringify(currentState)}
Available actions: ${availableActions.join(', ')}

Choose the best action and explain your reasoning. Respond with JSON:
{
  "action": "chosen_action",
  "confidence": 0.8,
  "reasoning": "explanation"
}
`
      }
    ];

    const response = await this.chatCompletion(messages, this.defaultModel, {
      temperature: 0.6,
      max_tokens: 150
    });

    return safeJsonParse(response, {
      action: availableActions[0] || 'idle',
      confidence: 0.5,
      reasoning: 'Default decision'
    });
  }

  /**
   * Clear cache to free memory
   */
  clearCache() {
    this.requestCache.clear();
    console.log('🧹 Ollama: Cache cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      size: this.requestCache.size,
      entries: Array.from(this.requestCache.keys()).slice(0, 5) // First 5 keys
    };
  }
}

// Singleton instance for global use
export const ollama = new OllamaIntegration();

// Initialization helper
export async function initializeOllama(): Promise<boolean> {
  console.log('🤖 Initializing Ollama integration...');
  
  const available = await ollama.isAvailable();
  if (available) {
    const models = await ollama.getModels();
    console.log(`🎯 Ollama: Available models: ${models.map(m => m.name).join(', ')}`);
    console.log('✅ Ollama integration ready for local LLM cascading');
    return true;
  } else {
    console.log('⚠️  Ollama not available - falling back to remote APIs');
    return false;
  }
}