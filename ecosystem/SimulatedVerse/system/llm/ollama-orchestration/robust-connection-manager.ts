// Robust Ollama Connection Manager - Zero Conflicts, Maximum Reliability
// Handles modular ports, connection pooling, request queuing, and seamless multi-agent coordination

import { EventEmitter } from 'events';
import fetch from 'node-fetch';
import { spawn, ChildProcess } from 'child_process';
import net from 'net';

export interface OllamaConnectionConfig {
  primaryPort: number;
  fallbackPorts: number[];
  maxConnections: number;
  requestTimeout: number;
  healthCheckInterval: number;
  retryAttempts: number;
  connectionPoolSize: number;
}

export interface OllamaRequest {
  id: string;
  model: string;
  prompt: string;
  options: any;
  priority: 'low' | 'normal' | 'high' | 'critical';
  source: string; // Which agent/component is making the request
}

export interface OllamaResponse {
  id: string;
  model: string;
  response: string;
  done: boolean;
  context?: number[];
  total_duration?: number;
  provider: 'ollama';
  success: boolean;
}

export interface ConnectionStatus {
  connected: boolean;
  activePort: number | null;
  activeConnections: number;
  queueLength: number;
  lastHealthCheck: Date;
  errors: string[];
  totalRequestsHandled: number;
}

export class RobustOllamaConnectionManager extends EventEmitter {
  private static instance: RobustOllamaConnectionManager;
  private config: OllamaConnectionConfig;
  private activePort: number | null = null;
  private connectionPool: Map<string, ChildProcess> = new Map();
  private requestQueue: OllamaRequest[] = [];
  private activeRequests: Map<string, { request: OllamaRequest; timestamp: Date }> = new Map();
  private healthCheckInterval?: NodeJS.Timeout;
  private processingQueue: boolean = false;
  private connectionStatus: ConnectionStatus;
  
  private constructor(config?: Partial<OllamaConnectionConfig>) {
    super();
    
    this.config = {
      primaryPort: 11434,
      fallbackPorts: [11435, 11436, 11437, 11438, 11439],
      maxConnections: 5,
      requestTimeout: 30000,
      healthCheckInterval: 10000,
      retryAttempts: 3,
      connectionPoolSize: 3,
      ...config
    };
    
    this.connectionStatus = {
      connected: false,
      activePort: null,
      activeConnections: 0,
      queueLength: 0,
      lastHealthCheck: new Date(),
      errors: [],
      totalRequestsHandled: 0
    };
    
    this.startHealthMonitoring();
  }

  static getInstance(config?: Partial<OllamaConnectionConfig>): RobustOllamaConnectionManager {
    if (!RobustOllamaConnectionManager.instance) {
      RobustOllamaConnectionManager.instance = new RobustOllamaConnectionManager(config);
    }
    return RobustOllamaConnectionManager.instance;
  }

  async initialize(): Promise<boolean> {
    console.log('[OLLAMA-ROBUST] 🚀 Initializing robust connection manager...');
    
    try {
      // Find available port
      const availablePort = await this.findAvailablePort();
      if (!availablePort) {
        console.error('[OLLAMA-ROBUST] ❌ No available ports found');
        return false;
      }
      
      this.activePort = availablePort;
      console.log(`[OLLAMA-ROBUST] 📡 Using port ${this.activePort}`);
      
      // Test connection
      const isHealthy = await this.performHealthCheck();
      if (isHealthy) {
        this.connectionStatus.connected = true;
        this.connectionStatus.activePort = this.activePort;
        console.log('[OLLAMA-ROBUST] ✅ Connection manager initialized successfully');
        return true;
      } else {
        console.log('[OLLAMA-ROBUST] ⚠️ Health check failed, attempting to start service...');
        const started = await this.ensureOllamaService();
        if (started) {
          this.connectionStatus.connected = true;
          this.connectionStatus.activePort = this.activePort;
          console.log('[OLLAMA-ROBUST] ✅ Service started and connection established');
          return true;
        }
      }
      
      return false;
      
    } catch (error) {
      console.error('[OLLAMA-ROBUST] ❌ Initialization failed:', error);
      this.addError(`Initialization failed: ${error}`);
      return false;
    }
  }

  private async findAvailablePort(): Promise<number | null> {
    const portsToTry = [this.config.primaryPort, ...this.config.fallbackPorts];
    
    for (const port of portsToTry) {
      try {
        const isAvailable = await this.testPortAvailability(port);
        if (isAvailable) {
          const hasOllamaService = await this.testOllamaAPI(port);
          if (hasOllamaService) {
            console.log(`[OLLAMA-ROBUST] ✅ Found Ollama service on port ${port}`);
            return port;
          } else {
            console.log(`[OLLAMA-ROBUST] 📋 Port ${port} available but no Ollama service`);
          }
        }
      } catch (error) {
        console.log(`[OLLAMA-ROBUST] ⚡ Port ${port} test failed: ${error}`);
      }
    }
    
    // Return primary port for service startup
    return this.config.primaryPort;
  }

  private async testPortAvailability(port: number): Promise<boolean> {
    return new Promise((resolve) => {
      const socket = new net.Socket();
      
      const onError = () => {
        socket.destroy();
        resolve(false);
      };
      
      socket.setTimeout(1000);
      socket.once('error', onError);
      socket.once('timeout', onError);
      
      socket.connect(port, 'localhost', () => {
        socket.end();
        resolve(true);
      });
    });
  }

  private async testOllamaAPI(port: number): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`http://localhost:${port}/api/version`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  private async ensureOllamaService(): Promise<boolean> {
    console.log('[OLLAMA-ROBUST] 🔧 Starting Ollama service...');
    
    try {
      // Try to start ollama serve
      const process = spawn('ollama', ['serve'], {
        detached: true,
        stdio: 'ignore'
      });
      
      process.unref();
      
      // Wait for service to start
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Test if it's running
      const isHealthy = await this.performHealthCheck();
      if (isHealthy) {
        console.log('[OLLAMA-ROBUST] ✅ Ollama service started successfully');
        return true;
      }
      
      console.log('[OLLAMA-ROBUST] ⚠️ Service started but health check failed');
      return false;
      
    } catch (error) {
      console.error('[OLLAMA-ROBUST] ❌ Failed to start Ollama service:', error);
      this.addError(`Service start failed: ${error}`);
      return false;
    }
  }

  async makeRequest(request: OllamaRequest): Promise<OllamaResponse> {
    if (!this.connectionStatus.connected) {
      throw new Error('Ollama connection manager not initialized');
    }

    // Add to queue
    this.requestQueue.push(request);
    this.connectionStatus.queueLength = this.requestQueue.length;
    
    console.log(`[OLLAMA-ROBUST] 📥 Queued request ${request.id} from ${request.source} (queue: ${this.requestQueue.length})`);
    
    // Process queue if not already processing
    if (!this.processingQueue) {
      this.processRequestQueue();
    }
    
    // Wait for response
    return new Promise((resolve, reject) => {
      const responseHandler = (response: OllamaResponse) => {
        if (response.id === request.id) {
          this.removeListener('response', responseHandler);
          this.removeListener('error', errorHandler);
          resolve(response);
        }
      };
      
      const errorHandler = (error: any) => {
        if (error.requestId === request.id) {
          this.removeListener('response', responseHandler);
          this.removeListener('error', errorHandler);
          reject(error);
        }
      };
      
      this.on('response', responseHandler);
      this.on('error', errorHandler);
      
      // Timeout handling
      setTimeout(() => {
        this.removeListener('response', responseHandler);
        this.removeListener('error', errorHandler);
        reject(new Error(`Request ${request.id} timed out after ${this.config.requestTimeout}ms`));
      }, this.config.requestTimeout);
    });
  }

  private async processRequestQueue(): Promise<void> {
    if (this.processingQueue || this.requestQueue.length === 0) {
      return;
    }
    
    this.processingQueue = true;
    
    while (this.requestQueue.length > 0 && this.activeRequests.size < this.config.maxConnections) {
      // Sort by priority
      this.requestQueue.sort((a, b) => {
        const priorityOrder = { critical: 4, high: 3, normal: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      });
      
      const request = this.requestQueue.shift()!;
      this.activeRequests.set(request.id, { request, timestamp: new Date() });
      this.connectionStatus.queueLength = this.requestQueue.length;
      this.connectionStatus.activeConnections = this.activeRequests.size;
      
      // Process request without blocking others
      this.processIndividualRequest(request).catch(error => {
        console.error(`[OLLAMA-ROBUST] Request ${request.id} failed:`, error);
        this.emit('error', { requestId: request.id, error });
        this.activeRequests.delete(request.id);
        this.connectionStatus.activeConnections = this.activeRequests.size;
      });
    }
    
    this.processingQueue = false;
    
    // Continue processing if there are more requests
    if (this.requestQueue.length > 0) {
      setTimeout(() => this.processRequestQueue(), 100);
    }
  }

  private async processIndividualRequest(request: OllamaRequest): Promise<void> {
    const startTime = Date.now();
    
    try {
      console.log(`[OLLAMA-ROBUST] 🔄 Processing request ${request.id} for model ${request.model}`);
      
      // Make HTTP request to Ollama API with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.config.requestTimeout);
      
      const response = await fetch(`http://localhost:${this.activePort}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: request.model,
          prompt: request.prompt,
          stream: false,
          ...request.options
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json() as any;
      
      const ollamaResponse: OllamaResponse = {
        id: request.id,
        model: request.model,
        response: result.response || '',
        done: result.done || true,
        context: result.context,
        total_duration: result.total_duration,
        provider: 'ollama',
        success: true
      };
      
      // Clean up
      this.activeRequests.delete(request.id);
      this.connectionStatus.activeConnections = this.activeRequests.size;
      this.connectionStatus.totalRequestsHandled++;
      
      console.log(`[OLLAMA-ROBUST] ✅ Request ${request.id} completed in ${Date.now() - startTime}ms`);
      this.emit('response', ollamaResponse);
      
    } catch (error) {
      console.error(`[OLLAMA-ROBUST] ❌ Request ${request.id} failed:`, error);
      this.activeRequests.delete(request.id);
      this.connectionStatus.activeConnections = this.activeRequests.size;
      this.addError(`Request ${request.id} failed: ${error}`);
      
      // Emit error response instead of just error
      const errorResponse: OllamaResponse = {
        id: request.id,
        model: request.model,
        response: '',
        done: true,
        provider: 'ollama',
        success: false
      };
      
      this.emit('response', errorResponse);
      throw error;
    }
  }

  private startHealthMonitoring(): void {
    this.healthCheckInterval = setInterval(async () => {
      const isHealthy = await this.performHealthCheck();
      
      if (!isHealthy && this.connectionStatus.connected) {
        console.log('[OLLAMA-ROBUST] ⚠️ Health check failed, attempting recovery...');
        this.connectionStatus.connected = false;
        
        // Attempt recovery
        const recovered = await this.initialize();
        if (recovered) {
          console.log('[OLLAMA-ROBUST] ✅ Connection recovered');
          this.emit('connection:recovered');
        } else {
          console.log('[OLLAMA-ROBUST] ❌ Recovery failed');
          this.emit('connection:lost');
        }
      }
      
      this.connectionStatus.lastHealthCheck = new Date();
    }, this.config.healthCheckInterval);
  }

  private async performHealthCheck(): Promise<boolean> {
    if (!this.activePort) return false;
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(`http://localhost:${this.activePort}/api/version`, {
        method: 'GET',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  private addError(error: string): void {
    this.connectionStatus.errors.push(`${new Date().toISOString()}: ${error}`);
    
    // Keep only last 10 errors
    if (this.connectionStatus.errors.length > 10) {
      this.connectionStatus.errors = this.connectionStatus.errors.slice(-10);
    }
  }

  getStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }

  async shutdown(): Promise<void> {
    console.log('[OLLAMA-ROBUST] 🔌 Shutting down connection manager...');
    
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    
    // Wait for active requests to complete
    while (this.activeRequests.size > 0) {
      console.log(`[OLLAMA-ROBUST] ⏳ Waiting for ${this.activeRequests.size} active requests...`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Close connection pool
    for (const [id, process] of this.connectionPool) {
      try {
        process.kill();
        console.log(`[OLLAMA-ROBUST] 🔌 Closed connection ${id}`);
      } catch (error) {
        console.log(`[OLLAMA-ROBUST] ⚠️ Error closing connection ${id}:`, error);
      }
    }
    
    this.connectionPool.clear();
    this.connectionStatus.connected = false;
    
    console.log('[OLLAMA-ROBUST] ✅ Connection manager shut down successfully');
  }

  // Convenience methods for different request sources
  async requestFromReplit(model: string, prompt: string, options: any = {}): Promise<OllamaResponse> {
    return this.makeRequest({
      id: `replit_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      model,
      prompt,
      options,
      priority: 'normal',
      source: 'replit_agent'
    });
  }

  async requestFromCopilot(model: string, prompt: string, options: any = {}): Promise<OllamaResponse> {
    return this.makeRequest({
      id: `copilot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      model,
      prompt,
      options,
      priority: 'high',
      source: 'vscode_copilot'
    });
  }

  async requestFromChatDev(model: string, prompt: string, options: any = {}): Promise<OllamaResponse> {
    return this.makeRequest({
      id: `chatdev_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      model,
      prompt,
      options,
      priority: 'high',
      source: 'chatdev_autonomous'
    });
  }

  async requestFromAICouncil(model: string, prompt: string, options: any = {}): Promise<OllamaResponse> {
    return this.makeRequest({
      id: `council_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      model,
      prompt,
      options,
      priority: 'normal',
      source: 'ai_council'
    });
  }

  async requestFromConsciousness(model: string, prompt: string, options: any = {}): Promise<OllamaResponse> {
    return this.makeRequest({
      id: `consciousness_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      model,
      prompt,
      options,
      priority: 'critical',
      source: 'nusyq_consciousness'
    });
  }
}

// Export singleton instance
export const robustOllamaManager = RobustOllamaConnectionManager.getInstance();

export default robustOllamaManager;