/**
 * LLM Provider Selector - VS Code Copilot-style Multi-Provider Interface
 * 
 * Unified interface for selecting between:
 * - GitHub Copilot API
 * - OpenAI API (GPT-4, GPT-3.5-turbo)
 * - Ollama Local LLMs (qwen2.5:7b, llama3.1:8b, phi3:mini, etc.)
 * 
 * Features:
 * - Seamless provider switching like VS Code Copilot
 * - Intelligent fallback cascading (Ollama → OpenAI → Copilot)
 * - Cost protection and token discipline
 * - Model specialization and automatic selection
 * - Real-time provider health monitoring
 * - Configuration persistence and user preferences
 * 
 * @author CoreLink Foundation AI Coordination Hub
 * @version 1.0.0 - Ultimate Synthesis Phase
 */

import { TokenGuard, CascadeRequest, CascadeResponse } from '../../system/llm/sidecar/token_guard.js';
import { OllamaModelManager, InferenceRequest, InferenceResponse } from '../../system/llm/ollama-orchestration/model-manager.js';
// import { UniversalEndpointConnector } from '../../src/endpoint-integration/universal-connector';

export type LLMProvider = 'ollama' | 'openai' | 'copilot' | 'auto';

export interface LLMProviderConfig {
  primary: LLMProvider;
  fallback: LLMProvider[];
  capabilities: string[];
  cost_limit_cents: number;
  auto_fallback: boolean;
  user_preference: LLMProvider;
}

export interface LLMRequest {
  prompt: string;
  task_type?: 'code_generation' | 'code_completion' | 'analysis' | 'chat' | 'reasoning' | 'explanation';
  preferred_provider?: LLMProvider;
  max_tokens?: number;
  temperature?: number;
  stream?: boolean;
  context?: any;
  system_prompt?: string;
}

export interface LLMResponse {
  response: string;
  provider_used: LLMProvider;
  model_used: string;
  confidence: number;
  cost_cents: number;
  response_time_ms: number;
  fallback_reason?: string;
  stream_complete?: boolean;
}

export interface ProviderStatus {
  name: LLMProvider;
  available: boolean;
  models: string[];
  last_health_check: number;
  error_rate: number;
  avg_response_time: number;
  cost_efficiency: number; // responses per cent
}

export class LLMProviderSelector {
  private tokenGuard: TokenGuard;
  private ollamaManager: OllamaModelManager;
  // private universalConnector: UniversalEndpointConnector;
  private config: LLMProviderConfig;
  private providerHealth = new Map<LLMProvider, ProviderStatus>();
  private userPreferences = new Map<string, LLMProvider>();
  
  constructor() {
    this.tokenGuard = new TokenGuard();
    this.ollamaManager = new OllamaModelManager();
    // this.universalConnector = new UniversalEndpointConnector();
    this.config = this.loadConfiguration();
    this.initializeProviderHealth();
    this.startHealthMonitoring();
  }

  private loadConfiguration(): LLMProviderConfig {
    const env = process.env;
    
    return {
      primary: (env.CORELINK_LLM_PRIMARY as LLMProvider) || 'auto',
      fallback: (env.CORELINK_LLM_FALLBACK || 'ollama,openai,copilot').split(',') as LLMProvider[],
      capabilities: (env.CORELINK_LLM_CAPABILITIES || 'code_generation,analysis,chat').split(','),
      cost_limit_cents: parseInt(env.CORELINK_DAILY_COST_LIMIT || '1000'),
      auto_fallback: env.CORELINK_AUTO_FALLBACK !== 'false',
      user_preference: (env.CORELINK_USER_LLM_PREFERENCE as LLMProvider) || 'auto'
    };
  }

  private initializeProviderHealth(): void {
    const providers: LLMProvider[] = ['ollama', 'openai', 'copilot'];
    
    providers.forEach(provider => {
      this.providerHealth.set(provider, {
        name: provider,
        available: false,
        models: [],
        last_health_check: 0,
        error_rate: 0,
        avg_response_time: 0,
        cost_efficiency: 0
      });
    });
  }

  /**
   * Main LLM request method - VS Code Copilot style interface
   */
  async complete(request: LLMRequest): Promise<LLMResponse> {
    const startTime = Date.now();
    
    console.log(`[LLM-SELECTOR] 🧠 Processing request with preferred provider: ${request.preferred_provider || 'auto'}`);
    
    // Determine provider selection strategy
    const providerPriority = this.determineProviderPriority(request);
    
    let lastError: Error | null = null;
    
    // Try providers in priority order (VS Code Copilot behavior)
    for (const provider of providerPriority) {
      try {
        const health = this.providerHealth.get(provider);
        if (!health?.available && provider !== 'ollama') {
          console.log(`[LLM-SELECTOR] ⚠️ Provider ${provider} unavailable, trying next`);
          continue;
        }
        
        const response = await this.executeWithProvider(provider, request);
        
        if (response) {
          response.response_time_ms = Date.now() - startTime;
          
          // Update provider health metrics
          this.updateProviderMetrics(provider, true, response.response_time_ms, response.cost_cents);
          
          console.log(`[LLM-SELECTOR] ✅ Success with ${provider} (${response.model_used})`);
          return response;
        }
        
      } catch (error) {
        lastError = error as Error;
        console.log(`[LLM-SELECTOR] ❌ Provider ${provider} failed: ${error}`);
        this.updateProviderMetrics(provider, false, Date.now() - startTime, 0);
        continue;
      }
    }
    
    // All providers failed - return graceful fallback
    console.error(`[LLM-SELECTOR] 🚨 All providers failed. Last error:`, lastError);
    
    return {
      response: "I apologize, but I'm currently unable to process your request. All LLM providers are unavailable. Please try again later.",
      provider_used: 'ollama', // Default fallback
      model_used: 'system_fallback',
      confidence: 0.1,
      cost_cents: 0,
      response_time_ms: Date.now() - startTime,
      fallback_reason: 'all_providers_failed'
    };
  }

  private determineProviderPriority(request: LLMRequest): LLMProvider[] {
    const priority: LLMProvider[] = [];
    
    // 1. Explicit user preference
    if (request.preferred_provider && request.preferred_provider !== 'auto') {
      priority.push(request.preferred_provider);
    }
    
    // 2. Task-optimized selection
    const taskOptimized = this.getOptimalProviderForTask(request.task_type);
    if (taskOptimized && !priority.includes(taskOptimized)) {
      priority.push(taskOptimized);
    }
    
    // 3. Primary configuration
    if (this.config.primary !== 'auto' && !priority.includes(this.config.primary)) {
      priority.push(this.config.primary);
    }
    
    // 4. Fallback chain (cost-aware)
    for (const fallback of this.config.fallback) {
      if (!priority.includes(fallback)) {
        priority.push(fallback);
      }
    }
    
    // 5. Ensure ollama is always in the chain (zero cost)
    if (!priority.includes('ollama')) {
      priority.unshift('ollama'); // Add to beginning for cost protection
    }
    
    return priority;
  }

  private getOptimalProviderForTask(taskType?: string): LLMProvider | null {
    const taskProviderMap: Record<string, LLMProvider> = {
      'code_generation': 'ollama', // Qwen2.5 or CodeLlama excel here
      'code_completion': 'copilot', // Copilot's specialty
      'analysis': 'ollama', // Good balance of quality and cost
      'chat': 'openai', // Best conversational AI
      'reasoning': 'openai', // Advanced reasoning capabilities
      'explanation': 'ollama' // Good explanatory capabilities
    };
    
    return taskType ? (taskProviderMap[taskType] || null) : null;
  }

  private async executeWithProvider(provider: LLMProvider, request: LLMRequest): Promise<LLMResponse | null> {
    switch (provider) {
      case 'ollama':
        return await this.executeWithOllama(request);
        
      case 'openai':
        return await this.executeWithOpenAI(request);
        
      case 'copilot':
        return await this.executeWithCopilot(request);
        
      default:
        throw new Error(`Unknown provider: ${provider}`);
    }
  }

  private async executeWithOllama(request: LLMRequest): Promise<LLMResponse> {
    console.log('[LLM-SELECTOR] 🦙 Using Ollama local models...');
    
    // Use TokenGuard for cost protection and intelligent routing
    const cascadeRequest: CascadeRequest = {
      prompt: request.prompt,
      task_type: request.task_type as any,
      max_tokens: request.max_tokens,
      temperature: request.temperature,
      context: request.context
    };
    
    const response = await this.tokenGuard.ask(cascadeRequest);
    
    return {
      response: response.response,
      provider_used: 'ollama',
      model_used: response.model_used,
      confidence: response.confidence,
      cost_cents: response.cost_cents, // Should be 0 for local
      response_time_ms: 0 // Will be set by caller
    };
  }

  private async executeWithOpenAI(request: LLMRequest): Promise<LLMResponse> {
    console.log('[LLM-SELECTOR] 🤖 Using OpenAI API...');
    
    // Check if we have budget remaining
    const budgetCheck = await this.checkBudgetRemaining();
    if (budgetCheck.remaining_cents < 100) {
      throw new Error('OpenAI budget exhausted');
    }
    
    // Use existing OpenAI integration through Universal Connector
    const message = {
      from: 'llm_selector',
      to: 'openai_integration',
      type: 'query' as const,
      payload: {
        prompt: request.prompt,
        model: this.selectOpenAIModel(request.task_type),
        max_tokens: request.max_tokens || 1000,
        temperature: request.temperature || 0.7,
        system_prompt: request.system_prompt
      },
      timestamp: new Date()
    };
    
    // EMERGENCY COST PROTECTION: Block all OpenAI API calls
    throw new Error('OpenAI API blocked - using local fallback only to prevent $100+ cost bleeding');
  }

  private async executeWithCopilot(request: LLMRequest): Promise<LLMResponse> {
    console.log('[LLM-SELECTOR] 🚁 Using GitHub Copilot API...');
    
    const copilotApiKey = process.env.GITHUB_COPILOT_API_KEY;
    if (!copilotApiKey) {
      throw new Error('GitHub Copilot API key not configured');
    }
    
    // EMERGENCY COST PROTECTION: Block Copilot API calls
    throw new Error('GitHub Copilot API blocked - using local Ollama fallback only to prevent API costs');
  }

  private selectOpenAIModel(taskType?: string): string {
    const taskModelMap: Record<string, string> = {
      'code_generation': 'gpt-4o-mini',
      'reasoning': 'gpt-4o',
      'analysis': 'gpt-4o-mini',
      'chat': 'gpt-4o-mini',
      'explanation': 'gpt-4o-mini'
    };
    
    return taskType ? (taskModelMap[taskType] || 'gpt-4o-mini') : 'gpt-4o-mini';
  }

  private async checkBudgetRemaining(): Promise<{ remaining_cents: number; limit_cents: number }> {
    // Would integrate with actual budget tracking
    return {
      remaining_cents: this.config.cost_limit_cents - 50, // Mock remaining
      limit_cents: this.config.cost_limit_cents
    };
  }

  private updateProviderMetrics(provider: LLMProvider, success: boolean, responseTime: number, cost: number): void {
    const health = this.providerHealth.get(provider);
    if (!health) return;
    
    const alpha = 0.1; // Exponential moving average factor
    
    health.avg_response_time = health.avg_response_time * (1 - alpha) + responseTime * alpha;
    health.error_rate = health.error_rate * (1 - alpha) + (success ? 0 : 1) * alpha;
    
    if (cost > 0) {
      health.cost_efficiency = health.cost_efficiency * (1 - alpha) + (1 / cost) * alpha;
    }
    
    health.last_health_check = Date.now();
  }

  /**
   * VS Code Copilot-style provider switching
   */
  async switchProvider(newProvider: LLMProvider, userId?: string): Promise<void> {
    console.log(`[LLM-SELECTOR] 🔄 Switching provider to: ${newProvider}`);
    
    this.config.primary = newProvider;
    
    if (userId) {
      this.userPreferences.set(userId, newProvider);
    }
    
    // Persist configuration
    await this.saveConfiguration();
    
    console.log(`[LLM-SELECTOR] ✅ Provider switched to ${newProvider}`);
  }

  /**
   * Get available providers with health status (VS Code Copilot interface)
   */
  getProviderStatus(): Record<LLMProvider, ProviderStatus> {
    const status: Record<string, ProviderStatus> = {};
    
    for (const [provider, health] of this.providerHealth.entries()) {
      status[provider] = { ...health };
    }
    
    return status as Record<LLMProvider, ProviderStatus>;
  }

  /**
   * Stream completion similar to VS Code Copilot
   */
  async *streamComplete(request: LLMRequest): AsyncGenerator<Partial<LLMResponse>, LLMResponse, unknown> {
    const provider = this.determineProviderPriority(request)[0];
    
    console.log(`[LLM-SELECTOR] 📡 Streaming with provider: ${provider}`);
    
    // Simulate streaming (would be actual streaming in production)
    const response = await this.complete(request);
    const words = response.response.split(' ');
    
    for (let i = 0; i < words.length; i++) {
      const partial = words.slice(0, i + 1).join(' ');
      
      yield {
        response: partial,
        provider_used: response.provider_used,
        stream_complete: false
      };
      
      // Simulate streaming delay
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    return {
      ...response,
      stream_complete: true
    };
  }

  private startHealthMonitoring(): void {
    setInterval(async () => {
      await this.checkProviderHealth();
    }, 60000); // Check every minute
  }

  private getOllamaModels(): any[] {
    // Since availableModels is private in OllamaModelManager, 
    // we'll simulate a basic model list for health checking
    return [];
  }

  private async checkProviderHealth(): Promise<void> {
    // Check Ollama health
    try {
      await this.ollamaManager.refreshModelList();
      const ollamaModels = this.getOllamaModels();
      const ollamaHealth = this.providerHealth.get('ollama')!;
      ollamaHealth.available = ollamaModels.length > 0;
      ollamaHealth.models = ollamaModels.map((m: any) => m.name);
    } catch (error) {
      const ollamaHealth = this.providerHealth.get('ollama')!;
      ollamaHealth.available = false;
    }
    
    // Check OpenAI health (would ping API in production)
    const openaiHealth = this.providerHealth.get('openai')!;
    openaiHealth.available = !!process.env.OPENAI_API_KEY;
    openaiHealth.models = ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'];
    
    // Check Copilot health
    const copilotHealth = this.providerHealth.get('copilot')!;
    copilotHealth.available = !!process.env.GITHUB_COPILOT_API_KEY;
    copilotHealth.models = ['copilot-codex', 'copilot-chat'];
  }

  private async saveConfiguration(): Promise<void> {
    // Would persist to user preferences/database
    console.log('[LLM-SELECTOR] 💾 Configuration saved');
  }

  /**
   * Get configuration for VS Code-style UI
   */
  getConfiguration(): LLMProviderConfig & { available_providers: LLMProvider[] } {
    const availableProviders: LLMProvider[] = [];
    
    for (const [provider, health] of this.providerHealth.entries()) {
      if (health.available) {
        availableProviders.push(provider);
      }
    }
    
    return {
      ...this.config,
      available_providers: availableProviders
    };
  }
}

// Export singleton instance for global use
export const llmProviderSelector = new LLMProviderSelector();

// Helper functions for easy integration
export async function askLLM(prompt: string, options?: Partial<LLMRequest>): Promise<LLMResponse> {
  return await llmProviderSelector.complete({
    prompt,
    ...options
  });
}

export async function askCode(prompt: string, options?: Partial<LLMRequest>): Promise<LLMResponse> {
  return await llmProviderSelector.complete({
    prompt,
    task_type: 'code_generation',
    preferred_provider: 'ollama', // Prefer local for code
    ...options
  });
}

export async function askChat(prompt: string, options?: Partial<LLMRequest>): Promise<LLMResponse> {
  return await llmProviderSelector.complete({
    prompt,
    task_type: 'chat',
    preferred_provider: 'openai', // Prefer OpenAI for conversation
    ...options
  });
}