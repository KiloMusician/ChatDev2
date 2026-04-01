/**
 * VS Code Copilot-style Interface Implementation
 * 
 * Replicates the exact experience of VS Code Copilot's multi-provider selection
 * with seamless integration into CoreLink Foundation's ecosystem.
 * 
 * Features:
 * - Provider selection dropdown (Copilot, OpenAI, Ollama)
 * - Real-time provider switching
 * - Status indicators and health monitoring
 * - Cost tracking and budget alerts
 * - Model-specific completions
 * - Streaming responses with cancel support
 * 
 * @author CoreLink Foundation AI Coordination Hub
 * @version 1.0.0 - Ultimate Synthesis Phase
 */

import { llmProviderSelector, LLMRequest, LLMResponse, LLMProvider, ProviderStatus } from './llm-provider-selector.js';
import { EventEmitter } from 'events';

export interface CopilotInterfaceConfig {
  enabled: boolean;
  show_provider_selector: boolean;
  auto_switch_on_failure: boolean;
  cost_warnings: boolean;
  streaming_enabled: boolean;
  default_provider: LLMProvider;
}

export interface CompletionContext {
  file_type?: string;
  language?: string;
  cursor_position?: number;
  surrounding_code?: string;
  user_intent?: 'completion' | 'generation' | 'explanation' | 'chat';
}

export class VSCodeCopilotInterface extends EventEmitter {
  private config: CopilotInterfaceConfig;
  private activeCompletions = new Map<string, AbortController>();
  private completionHistory: Array<{ request: LLMRequest; response: LLMResponse; timestamp: number }> = [];
  private currentProvider: LLMProvider = 'auto';
  
  constructor() {
    super();
    this.config = this.loadConfig();
    this.currentProvider = this.config.default_provider;
    this.startStatusMonitoring();
  }

  private loadConfig(): CopilotInterfaceConfig {
    return {
      enabled: process.env.CORELINK_COPILOT_ENABLED !== 'false',
      show_provider_selector: process.env.CORELINK_SHOW_PROVIDER_SELECTOR !== 'false',
      auto_switch_on_failure: process.env.CORELINK_AUTO_SWITCH !== 'false',
      cost_warnings: process.env.CORELINK_COST_WARNINGS !== 'false',
      streaming_enabled: process.env.CORELINK_STREAMING !== 'false',
      default_provider: (process.env.CORELINK_DEFAULT_PROVIDER as LLMProvider) || 'auto'
    };
  }

  /**
   * Main completion method - mirrors VS Code Copilot's complete() function
   */
  async complete(
    prompt: string, 
    context?: CompletionContext,
    options?: Partial<LLMRequest>
  ): Promise<LLMResponse> {
    
    if (!this.config.enabled) {
      throw new Error('Copilot interface disabled');
    }

    const completionId = this.generateCompletionId();
    const abortController = new AbortController();
    this.activeCompletions.set(completionId, abortController);

    try {
      console.log(`[COPILOT-INTERFACE] 🧠 Starting completion with provider: ${this.currentProvider}`);
      
      // Emit start event (VS Code Copilot behavior)
      this.emit('completion:start', { id: completionId, provider: this.currentProvider });

      // Build request with context
      const request: LLMRequest = {
        prompt: this.enhancePromptWithContext(prompt, context),
        task_type: this.inferTaskType(context),
        preferred_provider: this.currentProvider === 'auto' ? undefined : this.currentProvider,
        ...options
      };

      // Check cost warnings before expensive operations
      if (this.config.cost_warnings) {
        await this.checkCostWarnings(request);
      }

      // Execute completion
      const response = await llmProviderSelector.complete(request);

      // Store in history
      this.completionHistory.push({
        request,
        response,
        timestamp: Date.now()
      });

      // Keep history size reasonable
      if (this.completionHistory.length > 100) {
        this.completionHistory = this.completionHistory.slice(-50);
      }

      console.log(`[COPILOT-INTERFACE] ✅ Completion successful with ${response.provider_used}`);
      
      // Emit completion event
      this.emit('completion:success', { 
        id: completionId, 
        provider: response.provider_used,
        cost: response.cost_cents,
        response_time: response.response_time_ms
      });

      return response;

    } catch (error) {
      console.error(`[COPILOT-INTERFACE] ❌ Completion failed:`, error);
      
      // Emit error event
      this.emit('completion:error', { id: completionId, error });

      // Auto-switch provider on failure if enabled
      if (this.config.auto_switch_on_failure && this.currentProvider !== 'ollama') {
        console.log('[COPILOT-INTERFACE] 🔄 Auto-switching to fallback provider...');
        await this.switchToFallbackProvider();
      }

      throw error;

    } finally {
      this.activeCompletions.delete(completionId);
    }
  }

  /**
   * Stream completion with real-time updates (VS Code Copilot streaming)
   */
  async *streamComplete(
    prompt: string,
    context?: CompletionContext,
    options?: Partial<LLMRequest>
  ): AsyncGenerator<Partial<LLMResponse>, LLMResponse, unknown> {
    
    if (!this.config.streaming_enabled) {
      // Fallback to regular completion
      const response = await this.complete(prompt, context, options);
      yield response;
      return response;
    }

    const completionId = this.generateCompletionId();
    
    try {
      console.log(`[COPILOT-INTERFACE] 📡 Starting stream completion...`);
      
      this.emit('stream:start', { id: completionId, provider: this.currentProvider });

      const request: LLMRequest = {
        prompt: this.enhancePromptWithContext(prompt, context),
        task_type: this.inferTaskType(context),
        preferred_provider: this.currentProvider === 'auto' ? undefined : this.currentProvider,
        stream: true,
        ...options
      };

      // Use provider selector's streaming capability
      const streamGenerator = llmProviderSelector.streamComplete(request);
      
      for await (const chunk of streamGenerator) {
        // Emit stream chunk event
        this.emit('stream:chunk', { id: completionId, chunk });
        yield chunk;
      }

      // Final result from generator return
      const finalResult = await streamGenerator.next();
      const response = finalResult.value as LLMResponse;

      this.emit('stream:complete', { 
        id: completionId, 
        provider: response.provider_used,
        total_time: response.response_time_ms
      });

      return response;

    } catch (error) {
      this.emit('stream:error', { id: completionId, error });
      throw error;
    }
  }

  /**
   * Switch provider (VS Code Copilot dropdown behavior)
   */
  async switchProvider(newProvider: LLMProvider): Promise<void> {
    const oldProvider = this.currentProvider;
    
    console.log(`[COPILOT-INTERFACE] 🔄 Switching provider: ${oldProvider} → ${newProvider}`);
    
    // Cancel active completions
    await this.cancelAllActiveCompletions();
    
    // Switch provider
    this.currentProvider = newProvider;
    await llmProviderSelector.switchProvider(newProvider);
    
    // Emit provider change event
    this.emit('provider:changed', { 
      from: oldProvider, 
      to: newProvider,
      timestamp: Date.now()
    });
    
    console.log(`[COPILOT-INTERFACE] ✅ Provider switched to ${newProvider}`);
  }

  /**
   * Get provider status for UI display (VS Code Copilot status bar)
   */
  getProviderStatus(): Record<LLMProvider, ProviderStatus & { is_current: boolean }> {
    const baseStatus = llmProviderSelector.getProviderStatus();
    const enhancedStatus: Record<string, ProviderStatus & { is_current: boolean }> = {};
    
    for (const [provider, status] of Object.entries(baseStatus)) {
      enhancedStatus[provider] = {
        ...status,
        is_current: provider === this.currentProvider
      };
    }
    
    return enhancedStatus as Record<LLMProvider, ProviderStatus & { is_current: boolean }>;
  }

  /**
   * Get completion suggestions (VS Code Copilot suggestions panel)
   */
  async getSuggestions(
    prompt: string,
    context?: CompletionContext,
    count: number = 3
  ): Promise<LLMResponse[]> {
    
    console.log(`[COPILOT-INTERFACE] 💡 Generating ${count} suggestions...`);
    
    const suggestions: LLMResponse[] = [];
    
    // Generate multiple suggestions with slight variations
    for (let i = 0; i < count; i++) {
      try {
        const response = await this.complete(prompt, context, {
          temperature: 0.7 + (i * 0.1), // Vary temperature for diversity
          max_tokens: 150
        });
        
        suggestions.push(response);
        
        // Small delay between suggestions
        await new Promise(resolve => setTimeout(resolve, 100));
        
      } catch (error) {
        console.warn(`[COPILOT-INTERFACE] Failed to generate suggestion ${i + 1}:`, error);
      }
    }
    
    return suggestions;
  }

  /**
   * Cancel active completion (VS Code Copilot Escape key behavior)
   */
  async cancelCompletion(completionId?: string): Promise<void> {
    if (completionId) {
      const controller = this.activeCompletions.get(completionId);
      if (controller) {
        controller.abort();
        this.activeCompletions.delete(completionId);
        this.emit('completion:cancelled', { id: completionId });
        console.log(`[COPILOT-INTERFACE] ❌ Cancelled completion: ${completionId}`);
      }
    } else {
      // Cancel all active completions
      await this.cancelAllActiveCompletions();
    }
  }

  private async cancelAllActiveCompletions(): Promise<void> {
    console.log(`[COPILOT-INTERFACE] ❌ Cancelling ${this.activeCompletions.size} active completions...`);
    
    for (const [id, controller] of this.activeCompletions.entries()) {
      controller.abort();
      this.emit('completion:cancelled', { id });
    }
    
    this.activeCompletions.clear();
  }

  private enhancePromptWithContext(prompt: string, context?: CompletionContext): string {
    if (!context) return prompt;
    
    let enhancedPrompt = prompt;
    
    // Add language context
    if (context.language) {
      enhancedPrompt = `[${context.language}] ${enhancedPrompt}`;
    }
    
    // Add surrounding code for better context
    if (context.surrounding_code) {
      enhancedPrompt = `Context:\n${context.surrounding_code}\n\nRequest: ${enhancedPrompt}`;
    }
    
    return enhancedPrompt;
  }

  private inferTaskType(context?: CompletionContext): LLMRequest['task_type'] {
    if (!context) return 'chat';
    
    if (context.user_intent) {
      const intentMap: Record<string, LLMRequest['task_type']> = {
        'completion': 'code_completion',
        'generation': 'code_generation',
        'explanation': 'explanation',
        'chat': 'chat'
      };
      return intentMap[context.user_intent] || 'chat';
    }
    
    // Infer from file type
    if (context.file_type) {
      const codeFileTypes = ['ts', 'js', 'py', 'java', 'cpp', 'rs', 'go'];
      if (codeFileTypes.includes(context.file_type)) {
        return 'code_generation';
      }
    }
    
    return 'chat';
  }

  private async checkCostWarnings(request: LLMRequest): Promise<void> {
    if (request.preferred_provider === 'ollama') {
      return; // No cost for local models
    }
    
    // Would implement actual cost estimation and warnings
    const estimatedCost = this.estimateRequestCost(request);
    
    if (estimatedCost > 50) { // 50 cents threshold
      this.emit('cost:warning', { 
        estimated_cost: estimatedCost,
        provider: request.preferred_provider,
        message: `This request may cost approximately ${estimatedCost} cents`
      });
    }
  }

  private estimateRequestCost(request: LLMRequest): number {
    // Simple cost estimation (would be more sophisticated in production)
    const baseTokens = request.prompt.length / 4; // Rough token estimation
    const maxTokens = request.max_tokens || 1000;
    const totalTokens = baseTokens + maxTokens;
    
    const costPerToken = {
      'openai': 0.002, // cents per token (GPT-4o-mini)
      'copilot': 0.001, // Generally cheaper
      'ollama': 0.0    // Free local models
    };
    
    const provider = request.preferred_provider || 'openai';
    return totalTokens * (costPerToken[provider] || 0.002);
  }

  private async switchToFallbackProvider(): Promise<void> {
    const fallbackOrder: LLMProvider[] = ['ollama', 'openai', 'copilot'];
    const currentIndex = fallbackOrder.indexOf(this.currentProvider);
    
    if (currentIndex < fallbackOrder.length - 1) {
      const nextProvider = fallbackOrder[currentIndex + 1];
      await this.switchProvider(nextProvider);
    }
  }

  private generateCompletionId(): string {
    return `completion_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private startStatusMonitoring(): void {
    setInterval(() => {
      const status = this.getProviderStatus();
      this.emit('status:update', status);
    }, 30000); // Every 30 seconds
  }

  /**
   * Get completion statistics (VS Code Copilot analytics)
   */
  getCompletionStats(): {
    total_completions: number;
    success_rate: number;
    avg_response_time: number;
    total_cost_cents: number;
    provider_usage: Record<LLMProvider, number>;
  } {
    const stats = {
      total_completions: this.completionHistory.length,
      success_rate: 0,
      avg_response_time: 0,
      total_cost_cents: 0,
      provider_usage: {} as Record<LLMProvider, number>
    };
    
    if (this.completionHistory.length === 0) {
      return stats;
    }
    
    let totalResponseTime = 0;
    let totalCost = 0;
    const providerCounts: Record<string, number> = {};
    
    for (const entry of this.completionHistory) {
      totalResponseTime += entry.response.response_time_ms;
      totalCost += entry.response.cost_cents;
      
      const provider = entry.response.provider_used;
      providerCounts[provider] = (providerCounts[provider] || 0) + 1;
    }
    
    stats.success_rate = 1.0; // All entries in history are successful
    stats.avg_response_time = totalResponseTime / this.completionHistory.length;
    stats.total_cost_cents = totalCost;
    stats.provider_usage = providerCounts as Record<LLMProvider, number>;
    
    return stats;
  }

  /**
   * Export interface state for persistence
   */
  exportState(): any {
    return {
      config: this.config,
      current_provider: this.currentProvider,
      completion_history: this.completionHistory.slice(-10), // Last 10 completions
      stats: this.getCompletionStats()
    };
  }
}

// Export singleton instance
export const vscodeInterface = new VSCodeCopilotInterface();

// Easy integration functions
export async function copilotComplete(prompt: string, context?: CompletionContext): Promise<LLMResponse> {
  return await vscodeInterface.complete(prompt, context);
}

export async function copilotStreamComplete(prompt: string, context?: CompletionContext) {
  return vscodeInterface.streamComplete(prompt, context);
}

export async function copilotSwitchProvider(provider: LLMProvider): Promise<void> {
  return await vscodeInterface.switchProvider(provider);
}