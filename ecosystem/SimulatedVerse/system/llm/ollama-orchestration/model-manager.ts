// Ollama Model Manager - Local LLM Orchestration for CoreLink Foundation
// Inspired by NuSyQ-Hub template with intelligent model selection and specialization

import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';

export interface OllamaModel {
  name: string;
  size: string;
  modified: string;
  digest: string;
  details: {
    family: string;
    families?: string[];
    format: string;
    parameter_size: string;
    quantization_level: string;
  };
}

export interface ModelSpecialization {
  model: string;
  strengths: string[];
  weaknesses: string[];
  bestFor: string[];
  tokenLimit: number;
  temperature: number;
  confidence: number;
}

export interface InferenceRequest {
  prompt: string;
  model?: string;
  options?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    num_ctx?: number;
    max_tokens?: number;
  };
  specialization?: string;
}

export interface InferenceResponse {
  model: string;
  response: string;
  done: boolean;
  context?: number[];
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  prompt_eval_duration?: number;
  eval_count?: number;
  eval_duration?: number;
}

export class OllamaModelManager {
  private availableModels: OllamaModel[] = [];
  private modelSpecializations: Map<string, ModelSpecialization>;
  private currentModel: string | null = null;
  private modelPerformanceStats = new Map<string, { avgLatency: number; successRate: number; usageCount: number }>();
  private configPath: string;

  constructor() {
    this.configPath = path.join('.ollama', 'corelink-config.json');
    this.modelSpecializations = new Map();
    this.initializeSpecializations();
    this.loadConfiguration();
  }

  private initializeSpecializations() {
    // Define model specializations based on known capabilities
    const specializations: ModelSpecialization[] = [
      {
        model: 'qwen2.5:7b',
        strengths: ['code_analysis', 'reasoning', 'multilingual', 'math'],
        weaknesses: ['creative_writing', 'very_long_context'],
        bestFor: ['code_review', 'technical_analysis', 'problem_solving'],
        tokenLimit: 8192,
        temperature: 0.3,
        confidence: 0.85
      },
      {
        model: 'llama3.1:8b',
        strengths: ['general_knowledge', 'reasoning', 'instruction_following'],
        weaknesses: ['code_generation', 'math'],
        bestFor: ['general_qa', 'content_generation', 'analysis'],
        tokenLimit: 8192,
        temperature: 0.5,
        confidence: 0.80
      },
      {
        model: 'phi3:mini',
        strengths: ['fast_inference', 'code_understanding', 'concise_responses'],
        weaknesses: ['complex_reasoning', 'long_context'],
        bestFor: ['quick_analysis', 'code_completion', 'simple_qa'],
        tokenLimit: 4096,
        temperature: 0.2,
        confidence: 0.70
      },
      {
        model: 'mistral:7b',
        strengths: ['balanced_performance', 'code_and_text', 'efficiency'],
        weaknesses: ['specialized_domains', 'very_long_reasoning'],
        bestFor: ['general_purpose', 'mixed_tasks', 'batch_processing'],
        tokenLimit: 8192,
        temperature: 0.4,
        confidence: 0.75
      },
      {
        model: 'codellama:7b',
        strengths: ['code_generation', 'debugging', 'refactoring'],
        weaknesses: ['general_knowledge', 'creative_tasks'],
        bestFor: ['code_generation', 'bug_fixing', 'code_explanation'],
        tokenLimit: 4096,
        temperature: 0.1,
        confidence: 0.88
      }
    ];

    specializations.forEach(spec => {
      this.modelSpecializations.set(spec.model, spec);
    });
  }

  async initialize(): Promise<boolean> {
    console.log('[OLLAMA-MANAGER] 🧠 Initializing Hypertemporal Model Manager...');
    
    try {
      // Import and initialize coherence manager
      const { ollamaCoherence } = await import('./ollama-startup.js');
      const coherenceReady = await ollamaCoherence.initialize();
      
      if (!coherenceReady) {
        console.warn('[OLLAMA-MANAGER] Quantum coherence failed, using basic mode');
      }

      // Check if Ollama is available
      const isAvailable = await this.checkOllamaAvailability();
      if (!isAvailable) {
        console.error('[OLLAMA-MANAGER] Ollama is not available');
        return false;
      }

      // Ensure essential models are available
      if (coherenceReady) {
        await this.ensureEssentialModels();
      }
      
      // List available models
      await this.refreshModelList();
      
      // Set default model if none is current
      if (!this.currentModel && this.availableModels.length > 0) {
        this.currentModel = this.selectBestModel('general_purpose');
      }

      console.log(`[OLLAMA-MANAGER] ✅ Initialized with ${this.availableModels.length} models, current: ${this.currentModel}`);
      return true;
    } catch (error) {
      console.error('[OLLAMA-MANAGER] Initialization failed:', error);
      return false;
    }
  }

  private async ensureEssentialModels(): Promise<void> {
    try {
      const { ollamaCoherence } = await import('./ollama-startup.js');
      const essentialModels = ['qwen2.5:7b', 'llama3.1:8b'];
      
      for (const model of essentialModels) {
        const available = await ollamaCoherence.ensureModel(model);
        if (available) {
          console.log(`[OLLAMA-MANAGER] ✅ Model ready: ${model}`);
        } else {
          console.warn(`[OLLAMA-MANAGER] ⚠️ Model downloading: ${model}`);
        }
      }
    } catch (error) {
      console.warn('[OLLAMA-MANAGER] Essential model check failed:', error);
    }
  }

  private async checkOllamaAvailability(): Promise<boolean> {
    try {
      const result = spawnSync('ollama', ['--version'], { encoding: 'utf8', timeout: 5000 });
      return result.status === 0;
    } catch (error) {
      return false;
    }
  }

  async refreshModelList(): Promise<void> {
    try {
      // Use HTTP API instead of CLI for JSON response
      const response = await fetch('http://localhost:11434/api/tags');
      if (response.ok) {
        const data = await response.json();
        this.availableModels = data.models || [];
        console.log(`[OLLAMA-MANAGER] ✅ Found ${this.availableModels.length} available models`);
      } else {
        console.warn('[OLLAMA-MANAGER] Failed to fetch models via HTTP API');
        this.availableModels = [];
      }
    } catch (error) {
      console.error('[OLLAMA-MANAGER] Error refreshing model list:', error);
      this.availableModels = [];
    }
  }

  selectBestModel(task: string, context?: { promptLength?: number; responseLength?: number; priority?: 'speed' | 'quality' }): string {
    const candidates: Array<{ model: string; score: number; specialization: ModelSpecialization }> = [];

    for (const [modelName, spec] of this.modelSpecializations) {
      // Check if model is available
      const isAvailable = this.availableModels.some(m => m.name.startsWith(modelName.split(':')[0]));
      if (!isAvailable) continue;

      let score = spec.confidence;

      // Task-specific scoring
      if (task === 'code_analysis' && spec.strengths.includes('code_analysis')) score += 0.2;
      if (task === 'code_generation' && spec.strengths.includes('code_generation')) score += 0.25;
      if (task === 'general_purpose' && spec.strengths.includes('general_knowledge')) score += 0.1;
      if (task === 'quick_response' && spec.strengths.includes('fast_inference')) score += 0.15;
      if (task === 'reasoning' && spec.strengths.includes('reasoning')) score += 0.2;
      if (task === 'math' && spec.strengths.includes('math')) score += 0.3;

      // Context-based adjustments
      if (context) {
        if (context.priority === 'speed' && spec.strengths.includes('fast_inference')) score += 0.15;
        if (context.priority === 'quality' && spec.confidence > 0.8) score += 0.1;
        if (context.promptLength && context.promptLength > spec.tokenLimit * 0.7) score -= 0.2;
      }

      // Performance-based adjustments
      const perfStats = this.modelPerformanceStats.get(modelName);
      if (perfStats) {
        score += (perfStats.successRate - 0.5) * 0.2;
        score += perfStats.usageCount > 10 ? 0.05 : 0; // Slight bonus for tested models
      }

      candidates.push({ model: modelName, score, specialization: spec });
    }

    // Sort by score and return the best
    candidates.sort((a, b) => b.score - a.score);
    
    const selected = candidates[0]?.model || this.availableModels[0]?.name || 'llama3.1:8b';
    console.log(`[OLLAMA-MANAGER] Selected model ${selected} for task ${task} (score: ${candidates[0]?.score.toFixed(2)})`);
    
    return selected;
  }

  async generateResponse(request: InferenceRequest): Promise<InferenceResponse> {
    const startTime = Date.now();
    
    try {
      // Select model based on request
      const modelName = request.model || 
        (request.specialization ? this.selectBestModel(request.specialization) : this.currentModel) ||
        this.selectBestModel('general_purpose');

      console.log(`[OLLAMA-MANAGER] Generating response with model: ${modelName}`);

      // Prepare the request
      const ollamaRequest = {
        model: modelName,
        prompt: request.prompt,
        stream: false,
        options: {
          temperature: request.options?.temperature ?? this.modelSpecializations.get(modelName)?.temperature ?? 0.5,
          top_p: request.options?.top_p ?? 0.9,
          top_k: request.options?.top_k ?? 40,
          num_ctx: request.options?.num_ctx ?? 2048,
          ...request.options
        }
      };

      // Make the request to Ollama
      const result = await this.executeOllamaRequest(ollamaRequest);
      
      // Update performance stats
      this.updatePerformanceStats(modelName, true, Date.now() - startTime);
      
      return {
        model: modelName,
        response: result.response,
        done: result.done,
        context: result.context,
        total_duration: result.total_duration,
        load_duration: result.load_duration,
        prompt_eval_count: result.prompt_eval_count,
        prompt_eval_duration: result.prompt_eval_duration,
        eval_count: result.eval_count,
        eval_duration: result.eval_duration
      };

    } catch (error) {
      console.error('[OLLAMA-MANAGER] Generation failed:', error);
      
      // Update performance stats for failure
      if (request.model) {
        this.updatePerformanceStats(request.model, false, Date.now() - startTime);
      }
      
      throw error;
    }
  }

  private async executeOllamaRequest(request: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const proc = spawn('ollama', ['run', '--format', 'json', request.model], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      proc.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        if (code === 0) {
          try {
            // Parse the JSON response from Ollama
            const lines = stdout.trim().split('\n');
            const lastLine = lines[lines.length - 1];
            const response = JSON.parse(lastLine);
            resolve(response);
          } catch (parseError) {
            reject(new Error(`Failed to parse Ollama response: ${parseError}`));
          }
        } else {
          reject(new Error(`Ollama process exited with code ${code}: ${stderr}`));
        }
      });

      // Send the prompt to Ollama
      proc.stdin.write(request.prompt);
      proc.stdin.end();

      // Set timeout
      const timeout = setTimeout(() => {
        proc.kill();
        reject(new Error('Ollama request timed out'));
      }, 60000); // 60 second timeout

      proc.on('close', () => {
        clearTimeout(timeout);
      });
    });
  }

  private updatePerformanceStats(modelName: string, success: boolean, latency: number) {
    const stats = this.modelPerformanceStats.get(modelName) || {
      avgLatency: 0,
      successRate: 1,
      usageCount: 0
    };

    stats.usageCount++;
    stats.avgLatency = ((stats.avgLatency * (stats.usageCount - 1)) + latency) / stats.usageCount;
    stats.successRate = ((stats.successRate * (stats.usageCount - 1)) + (success ? 1 : 0)) / stats.usageCount;

    this.modelPerformanceStats.set(modelName, stats);
  }

  async pullModel(modelName: string): Promise<boolean> {
    console.log(`[OLLAMA-MANAGER] Pulling model: ${modelName}`);
    
    try {
      const result = spawnSync('ollama', ['pull', modelName], { 
        encoding: 'utf8', 
        timeout: 300000, // 5 minutes
        stdio: 'inherit' 
      });
      
      if (result.status === 0) {
        console.log(`[OLLAMA-MANAGER] Successfully pulled ${modelName}`);
        await this.refreshModelList();
        return true;
      } else {
        console.error(`[OLLAMA-MANAGER] Failed to pull ${modelName}:`, result.stderr);
        return false;
      }
    } catch (error) {
      console.error(`[OLLAMA-MANAGER] Error pulling ${modelName}:`, error);
      return false;
    }
  }

  async warmupModel(modelName: string): Promise<boolean> {
    console.log(`[OLLAMA-MANAGER] Warming up model: ${modelName}`);
    
    try {
      const warmupRequest: InferenceRequest = {
        prompt: "Hello! This is a warmup request. Please respond briefly.",
        model: modelName,
        options: { max_tokens: 50 }
      };

      await this.generateResponse(warmupRequest);
      console.log(`[OLLAMA-MANAGER] Model ${modelName} warmed up successfully`);
      return true;
    } catch (error) {
      console.error(`[OLLAMA-MANAGER] Failed to warm up ${modelName}:`, error);
      return false;
    }
  }

  getModelInfo(modelName: string): ModelSpecialization | null {
    return this.modelSpecializations.get(modelName) || null;
  }

  getPerformanceStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    for (const [model, stat] of this.modelPerformanceStats) {
      stats[model] = {
        ...stat,
        avgLatencyMs: Math.round(stat.avgLatency),
        successRatePercent: Math.round(stat.successRate * 100)
      };
    }
    return stats;
  }

  private loadConfiguration() {
    try {
      if (fs.existsSync(this.configPath)) {
        const config = JSON.parse(fs.readFileSync(this.configPath, 'utf8'));
        this.currentModel = config.currentModel;
        
        if (config.performanceStats) {
          this.modelPerformanceStats = new Map(Object.entries(config.performanceStats));
        }
      }
    } catch (error) {
      console.warn('[OLLAMA-MANAGER] Failed to load configuration:', error);
    }
  }

  saveConfiguration() {
    try {
      const config = {
        currentModel: this.currentModel,
        performanceStats: Object.fromEntries(this.modelPerformanceStats),
        lastUpdated: new Date().toISOString()
      };
      
      fs.mkdirSync(path.dirname(this.configPath), { recursive: true });
      fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2));
    } catch (error) {
      console.warn('[OLLAMA-MANAGER] Failed to save configuration:', error);
    }
  }

  async shutdown() {
    console.log('[OLLAMA-MANAGER] Shutting down model manager...');
    this.saveConfiguration();
  }
}

// Singleton instance for global model management
export const ollamaModelManager = new OllamaModelManager();