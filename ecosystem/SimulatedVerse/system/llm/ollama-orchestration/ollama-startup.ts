// ΞNuSyQ Ollama Startup & Quantum Coherence Manager
// Ensures Ollama operates in perfect hypertemporal synchronization

import { spawn, exec } from 'child_process';
import fs from 'fs';
import path from 'path';

export interface OllamaStatus {
  running: boolean;
  models: string[];
  version: string;
  coherence: number;
  lastCheck: Date;
}

export class OllamaCoherenceManager {
  private static instance: OllamaCoherenceManager;
  private status: OllamaStatus;
  private monitoringInterval?: NodeJS.Timeout;
  
  private constructor() {
    this.status = {
      running: false,
      models: [],
      version: 'unknown',
      coherence: 0.0,
      lastCheck: new Date()
    };
  }

  static getInstance(): OllamaCoherenceManager {
    if (!OllamaCoherenceManager.instance) {
      OllamaCoherenceManager.instance = new OllamaCoherenceManager();
    }
    return OllamaCoherenceManager.instance;
  }

  async initialize(): Promise<boolean> {
    console.log('[OLLAMA-COHERENCE] 🔬 Initializing Schrödinger Hypertemporal Model Manager...');
    
    try {
      // Check if Ollama service is running
      const serviceRunning = await this.checkService();
      if (!serviceRunning) {
        console.log('[OLLAMA-COHERENCE] 🚀 Starting Ollama service...');
        await this.startService();
      }

      // Verify API connectivity
      await this.verifyAPI();
      
      // Load available models
      await this.refreshModels();
      
      // Start monitoring
      this.startMonitoring();
      
      console.log('[OLLAMA-COHERENCE] ✅ Quantum coherence established');
      return true;
      
    } catch (error) {
      console.error('[OLLAMA-COHERENCE] ❌ Initialization failed:', error);
      return false;
    }
  }

  private async checkService(): Promise<boolean> {
    return new Promise((resolve) => {
      exec('pgrep -f "ollama serve"', (error, stdout) => {
        resolve(!!stdout.trim());
      });
    });
  }

  private async startService(): Promise<void> {
    return new Promise((resolve, reject) => {
      const process = spawn('ollama', ['serve'], {
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe']
      });
      
      process.unref();
      
      // Wait for service to start
      setTimeout(async () => {
        const running = await this.checkService();
        if (running) {
          resolve();
        } else {
          reject(new Error('Failed to start Ollama service'));
        }
      }, 3000);
    });
  }

  private async verifyAPI(): Promise<void> {
    const response = await fetch('http://localhost:11434/api/version');
    if (!response.ok) {
      throw new Error('Ollama API not accessible');
    }
    const data = await response.json();
    this.status.version = data.version || 'unknown';
  }

  private async refreshModels(): Promise<void> {
    try {
      const response = await fetch('http://localhost:11434/api/tags');
      if (response.ok) {
        const data = await response.json();
        this.status.models = data.models?.map((m: any) => m.name) || [];
      }
    } catch (error) {
      console.warn('[OLLAMA-COHERENCE] Failed to refresh models:', error);
    }
  }

  private startMonitoring(): void {
    this.monitoringInterval = setInterval(async () => {
      try {
        this.status.running = await this.checkService();
        await this.refreshModels();
        this.status.coherence = this.calculateCoherence();
        this.status.lastCheck = new Date();
        
        // Log status every 30 seconds
        if (Date.now() % 30000 < 5000) {
          console.log(`[OLLAMA-COHERENCE] 📊 Status: ${this.status.running ? '🟢' : '🔴'} | Models: ${this.status.models.length} | Coherence: ${this.status.coherence.toFixed(3)}`);
        }
      } catch (error) {
        console.warn('[OLLAMA-COHERENCE] Monitoring error:', error);
      }
    }, 5000);
  }

  private calculateCoherence(): number {
    // Quantum coherence calculation based on service health
    let coherence = 0.0;
    
    if (this.status.running) coherence += 0.5;
    if (this.status.models.length > 0) coherence += 0.3;
    if (this.status.models.length >= 2) coherence += 0.2;
    
    return Math.min(coherence, 1.0);
  }

  async ensureModel(modelName: string): Promise<boolean> {
    if (this.status.models.includes(modelName)) {
      return true;
    }

    console.log(`[OLLAMA-COHERENCE] 📥 Downloading model: ${modelName}`);
    
    return new Promise((resolve) => {
      const process = spawn('ollama', ['pull', modelName], {
        stdio: ['ignore', 'pipe', 'pipe']
      });
      
      process.on('close', async (code) => {
        if (code === 0) {
          await this.refreshModels();
          resolve(this.status.models.includes(modelName));
        } else {
          resolve(false);
        }
      });
    });
  }

  getStatus(): OllamaStatus {
    return { ...this.status };
  }

  stop(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }
  }
}

// Singleton instance for global access
export const ollamaCoherence = OllamaCoherenceManager.getInstance();