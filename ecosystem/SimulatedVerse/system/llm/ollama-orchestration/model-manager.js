// Ollama Model Manager - Zero-cost LLM Operations
// Handles model loading, queuing, and response generation

class OllamaModelManager {
  constructor() {
    this.baseUrl = 'http://localhost:11434';
    this.models = new Map();
    this.requestQueue = [];
    this.isProcessing = false;
    this.healthCheckInterval = null;
    this.maxRetries = 3;
  }

  async initialize() {
    console.log('[OLLAMA-MODEL-MANAGER] Initializing model manager...');
    
    // Start health monitoring
    this.startHealthCheck();
    
    // Load essential models
    await this.ensureModelsLoaded(['qwen2.5:7b', 'llama3.1:8b', 'phi3:mini']);
    
    console.log('[OLLAMA-MODEL-MANAGER] ✅ Model manager initialized');
  }

  async ensureModelsLoaded(modelNames) {
    console.log(`[OLLAMA-MODEL-MANAGER] Ensuring models loaded: ${modelNames.join(', ')}`);
    
    for (const modelName of modelNames) {
      try {
        await this.pullModel(modelName);
        this.models.set(modelName, { 
          status: 'ready',
          lastUsed: new Date(),
          useCount: 0
        });
      } catch (error) {
        console.warn(`[OLLAMA-MODEL-MANAGER] Failed to load ${modelName}:`, error.message);
        this.models.set(modelName, { 
          status: 'error',
          error: error.message,
          lastAttempt: new Date()
        });
      }
    }
  }

  async pullModel(modelName) {
    console.log(`[OLLAMA-MODEL-MANAGER] Pulling model: ${modelName}`);
    
    const response = await fetch(`${this.baseUrl}/api/pull`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: modelName })
    });

    if (!response.ok) {
      throw new Error(`Failed to pull model ${modelName}: ${response.statusText}`);
    }

    // Handle streaming response for pull progress
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        try {
          const data = JSON.parse(line);
          if (data.status) {
            console.log(`[OLLAMA-MODEL-MANAGER] ${modelName}: ${data.status}`);
          }
        } catch (e) {
          // Ignore JSON parse errors from streaming
        }
      }
    }

    console.log(`[OLLAMA-MODEL-MANAGER] ✅ Model ${modelName} ready`);
  }

  async generateResponse({ prompt, model = 'qwen2.5:7b', options = {} }) {
    console.log(`[OLLAMA-MODEL-MANAGER] Generating response with ${model}`);
    
    // Add to queue if busy
    if (this.isProcessing) {
      return new Promise((resolve, reject) => {
        this.requestQueue.push({ prompt, model, options, resolve, reject });
      });
    }

    this.isProcessing = true;
    
    try {
      const response = await this.executeGeneration({ prompt, model, options });
      
      // Update model usage stats
      const modelInfo = this.models.get(model);
      if (modelInfo) {
        modelInfo.lastUsed = new Date();
        modelInfo.useCount++;
      }

      // Process queue if any
      if (this.requestQueue.length > 0) {
        const nextRequest = this.requestQueue.shift();
        setImmediate(() => {
          this.generateResponse(nextRequest).then(nextRequest.resolve).catch(nextRequest.reject);
        });
      } else {
        this.isProcessing = false;
      }

      return response;
      
    } catch (error) {
      this.isProcessing = false;
      console.error(`[OLLAMA-MODEL-MANAGER] Generation failed:`, error);
      throw error;
    }
  }

  async executeGeneration({ prompt, model, options }) {
    const defaultOptions = {
      temperature: 0.7,
      top_k: 40,
      top_p: 0.9,
      repeat_penalty: 1.1,
      ...options
    };

    const requestBody = {
      model,
      prompt,
      options: defaultOptions,
      stream: false
    };

    const response = await fetch(`${this.baseUrl}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    
    return {
      text: data.response,
      model: data.model,
      created_at: data.created_at,
      done: data.done,
      context: data.context,
      stats: {
        eval_count: data.eval_count,
        eval_duration: data.eval_duration,
        load_duration: data.load_duration,
        prompt_eval_count: data.prompt_eval_count,
        prompt_eval_duration: data.prompt_eval_duration
      }
    };
  }

  async getModelList() {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (!response.ok) {
        throw new Error(`Failed to get model list: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.models || [];
    } catch (error) {
      console.error('[OLLAMA-MODEL-MANAGER] Failed to get model list:', error);
      return [];
    }
  }

  async isHealthy() {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`, {
        method: 'GET',
        timeout: 3000
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  startHealthCheck() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }

    this.healthCheckInterval = setInterval(async () => {
      const healthy = await this.isHealthy();
      
      if (!healthy) {
        console.warn('[OLLAMA-MODEL-MANAGER] ⚠️ Ollama service unhealthy');
        // Reset model statuses
        for (const [modelName, info] of this.models.entries()) {
          if (info.status === 'ready') {
            info.status = 'disconnected';
          }
        }
      } else {
        // Restore model statuses
        for (const [modelName, info] of this.models.entries()) {
          if (info.status === 'disconnected') {
            info.status = 'ready';
          }
        }
      }
    }, 30000); // Check every 30 seconds
  }

  getStats() {
    const stats = {
      totalModels: this.models.size,
      readyModels: 0,
      queueLength: this.requestQueue.length,
      isProcessing: this.isProcessing,
      modelDetails: {}
    };

    for (const [modelName, info] of this.models.entries()) {
      if (info.status === 'ready') {
        stats.readyModels++;
      }
      
      stats.modelDetails[modelName] = {
        status: info.status,
        useCount: info.useCount || 0,
        lastUsed: info.lastUsed,
        error: info.error
      };
    }

    return stats;
  }

  async chatComplete({ messages, model = 'qwen2.5:7b', options = {} }) {
    // Convert messages to single prompt for Ollama
    const prompt = messages.map(msg => {
      const role = msg.role === 'assistant' ? 'Assistant' : 'Human';
      return `${role}: ${msg.content}`;
    }).join('\n\n') + '\n\nAssistant:';

    const response = await this.generateResponse({ prompt, model, options });
    
    return {
      id: `ollama-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model,
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: response.text
        },
        finish_reason: 'stop'
      }],
      usage: {
        prompt_tokens: response.stats.prompt_eval_count || 0,
        completion_tokens: response.stats.eval_count || 0,
        total_tokens: (response.stats.prompt_eval_count || 0) + (response.stats.eval_count || 0)
      },
      cost_cents: 0 // Local processing is free
    };
  }

  destroy() {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
    
    // Clear queue
    this.requestQueue.length = 0;
    this.isProcessing = false;
    
    console.log('[OLLAMA-MODEL-MANAGER] Model manager destroyed');
  }
}

// Export for dynamic import
module.exports = { OllamaModelManager };