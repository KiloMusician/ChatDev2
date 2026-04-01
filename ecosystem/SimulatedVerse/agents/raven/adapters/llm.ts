/**
 * Raven LLM Adapters
 * Local (Ollama) → paid fallback (gated)
 * Token discipline and routing
 */

import { LLMModelConfig, RavenAdapterConfig } from '../../../raven.config';

export interface LLMRequest {
  prompt: string;
  context?: any;
  max_tokens?: number;
  temperature?: number;
  task_type: 'planning' | 'implementation' | 'reflection' | 'analysis';
}

export interface LLMResponse {
  content: string;
  tokens_used: number;
  cost: number;
  model_used: string;
  provider: string;
  latency_ms: number;
}

export class OllamaAdapter {
  private endpoint: string;
  
  constructor(endpoint: string = 'http://localhost:11434') {
    this.endpoint = endpoint;
  }

  async generate(model: string, request: LLMRequest): Promise<LLMResponse> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${this.endpoint}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          prompt: request.prompt,
          options: {
            num_predict: request.max_tokens || 4096,
            temperature: request.temperature || 0.7
          },
          stream: false
        })
      });

      if (!response.ok) {
        throw new Error(`Ollama request failed: ${response.statusText}`);
      }

      const data = await response.json();
      const latency = Date.now() - startTime;

      return {
        content: data.response,
        tokens_used: data.eval_count || 0,
        cost: 0, // Local models are free
        model_used: model,
        provider: 'ollama',
        latency_ms: latency
      };
    } catch (error) {
      throw new Error(`Ollama generation failed: ${error.message}`);
    }
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.endpoint}/api/tags`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

export class OpenAIAdapter {
  private apiKey: string;
  
  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async generate(model: string, request: LLMRequest): Promise<LLMResponse> {
    const startTime = Date.now();
    
    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify({
          model,
          messages: [{ role: 'user', content: request.prompt }],
          max_tokens: request.max_tokens || 4096,
          temperature: request.temperature || 0.7
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI request failed: ${response.statusText}`);
      }

      const data = await response.json();
      const latency = Date.now() - startTime;

      return {
        content: data.choices[0].message.content,
        tokens_used: data.usage.total_tokens,
        cost: data.usage.total_tokens * 0.00015, // gpt-4o-mini pricing
        model_used: model,
        provider: 'openai',
        latency_ms: latency
      };
    } catch (error) {
      throw new Error(`OpenAI generation failed: ${error.message}`);
    }
  }
}

export class RavenAdapters {
  private config: RavenAdapterConfig;
  private models: LLMModelConfig[];
  private ollamaAdapter: OllamaAdapter;
  private openaiAdapter?: OpenAIAdapter;
  private requestCache: Map<string, LLMResponse> = new Map();
  
  // Add llm property for easier access
  public llm: {
    generatePlan: (request: any) => Promise<any>;
    generateImplementation: (pu: any) => Promise<any>;
    generateReflection: (action: any, outcome: any, metrics: any) => Promise<any>;
    analyzePatterns: (reflections: any[]) => Promise<any>;
    updatePlanningStrategies: (patterns: any) => Promise<void>;
  };

  constructor(config: RavenAdapterConfig, models: LLMModelConfig[]) {
    this.config = config;
    this.models = models;
    this.ollamaAdapter = new OllamaAdapter();
    
    // Only initialize paid adapters if fallback is enabled
    if (config.fallback_enabled && process.env.OPENAI_API_KEY) {
      this.openaiAdapter = new OpenAIAdapter(process.env.OPENAI_API_KEY);
    }

    // Initialize llm proxy
    this.llm = {
      generatePlan: this.generatePlan.bind(this),
      generateImplementation: this.generateImplementation.bind(this),
      generateReflection: this.generateReflection.bind(this),
      analyzePatterns: this.analyzePatterns.bind(this),
      updatePlanningStrategies: this.updatePlanningStrategies.bind(this)
    };
  }

  async generatePlan(request: any): Promise<any> {
    const llmRequest: LLMRequest = {
      prompt: this.buildPlanningPrompt(request),
      task_type: 'planning',
      max_tokens: 4096
    };

    return this.routeRequest(llmRequest);
  }

  async generateImplementation(pu: any): Promise<any> {
    const llmRequest: LLMRequest = {
      prompt: this.buildImplementationPrompt(pu),
      task_type: 'implementation',
      max_tokens: 4096
    };

    return this.routeRequest(llmRequest);
  }

  async generateReflection(action: any, outcome: any, metrics: any): Promise<any> {
    const llmRequest: LLMRequest = {
      prompt: this.buildReflectionPrompt(action, outcome, metrics),
      task_type: 'reflection',
      max_tokens: 2048
    };

    return this.routeRequest(llmRequest);
  }

  async analyzePatterns(reflections: any[]): Promise<any> {
    const llmRequest: LLMRequest = {
      prompt: this.buildAnalysisPrompt(reflections),
      task_type: 'analysis',
      max_tokens: 2048
    };

    return this.routeRequest(llmRequest);
  }

  async updatePlanningStrategies(patterns: any): Promise<void> {
    // Update internal planning strategies based on learned patterns
    // This would involve updating prompts, weights, etc.
  }

  private async routeRequest(request: LLMRequest): Promise<any> {
    const cacheKey = this.getCacheKey(request);
    
    // Check cache first
    if (this.requestCache.has(cacheKey)) {
      return this.requestCache.get(cacheKey);
    }

    const modelName = this.config.llm_routing[request.task_type];
    const model = this.models.find(m => m.name === modelName);
    
    if (!model) {
      throw new Error(`Model ${modelName} not found for task ${request.task_type}`);
    }

    let response: LLMResponse;

    try {
      if (model.provider === 'ollama') {
        response = await this.ollamaAdapter.generate(model.name, request);
      } else if (model.provider === 'openai' && this.openaiAdapter) {
        if (!this.config.fallback_enabled) {
          throw new Error('Paid fallback is disabled');
        }
        response = await this.openaiAdapter.generate(model.name, request);
      } else {
        throw new Error(`Unsupported provider: ${model.provider}`);
      }

      // Cache successful responses
      this.requestCache.set(cacheKey, response);
      
      return response;
    } catch (error) {
      if (this.config.local_first && model.provider === 'ollama' && this.config.fallback_enabled) {
        // Try fallback to paid model
        const fallbackModel = this.models.find(m => m.provider === 'openai');
        if (fallbackModel && this.openaiAdapter) {
          console.warn(`Local model failed, falling back to ${fallbackModel.name}`);
          response = await this.openaiAdapter.generate(fallbackModel.name, request);
          this.requestCache.set(cacheKey, response);
          return response;
        }
      }
      throw error;
    }
  }

  private buildPlanningPrompt(request: any): string {
    return `Plan the following goal into atomic PUs:

Goal: ${request.goal}
Constraints: ${request.constraints.join(', ')}
Max Nodes: ${request.max_nodes}

Break this down into specific, testable tasks. Each PU should:
- Have clear acceptance criteria
- Be implementable in a single PR
- Include required artifacts and tests
- Have a rollback plan

Return structured JSON with PU array.`;
  }

  private buildImplementationPrompt(pu: any): string {
    return `Implement the following PU:

Title: ${pu.title}
Description: ${pu.description}
Acceptance Criteria: ${pu.acceptance_criteria.join('\n')}

Generate specific code changes, tests, and documentation.
Return structured implementation plan.`;
  }

  private buildReflectionPrompt(action: any, outcome: any, metrics: any): string {
    return `Analyze this completed action:

Action: ${action.pr_title}
Outcome: ${outcome.status}
Metrics: ${JSON.stringify(metrics)}

What lessons can be learned? What should be improved?
Return structured reflection with lessons and improvements.`;
  }

  private buildAnalysisPrompt(reflections: any[]): string {
    return `Analyze these reflections for patterns:

${reflections.map(r => `- ${r.lessons.join(', ')}`).join('\n')}

What patterns emerge? What should be changed in policies or strategies?
Return structured pattern analysis.`;
  }

  private getCacheKey(request: LLMRequest): string {
    return Buffer.from(JSON.stringify({
      prompt: request.prompt.substring(0, 100), // First 100 chars
      task_type: request.task_type,
      max_tokens: request.max_tokens
    })).toString('base64');
  }
}