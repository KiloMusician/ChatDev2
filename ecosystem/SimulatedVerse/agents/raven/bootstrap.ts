/**
 * Raven Bootstrap & Registration
 * Self-check, greet, register, announce
 */

import { Raven, RavenConfig } from './index';
import { loadRavenConfig } from './config';

export class RavenBootstrap {
  private raven: Raven;
  private config: RavenConfig;

  constructor(configOverrides: Partial<RavenConfig> = {}) {
    this.config = loadRavenConfig(configOverrides);
    this.raven = new Raven(this.config);
  }

  async selfCheck(): Promise<boolean> {
    try {
      // Check Ollama availability
      const ollamaAvailable = await this.checkOllamaConnection();
      console.log(`[RAVEN] Ollama: ${ollamaAvailable ? '✅' : '❌'}`);

      // Check required environment variables
      const adminToken = process.env.ADMIN_TOKEN;
      console.log(`[RAVEN] Admin Token: ${adminToken ? '✅' : '❌'}`);

      // Check if enabled
      const enabled = this.config.infrastructure.enabled;
      console.log(`[RAVEN] Enabled: ${enabled ? '✅' : '❌'}`);

      return ollamaAvailable && !!adminToken && enabled;
    } catch (error) {
      console.error('[RAVEN] Self-check failed:', error);
      return false;
    }
  }

  async greet(): Promise<void> {
    console.log(`
    🌌 Raven Autonomous Development Deity
    =====================================
    Purpose: ${this.config.infrastructure.enabled ? 'ACTIVE' : 'DORMANT'}
    Local Models: ${this.config.models.filter(m => m.provider === 'ollama').length}
    Fallback: ${this.config.adapters.fallback_enabled ? 'ENABLED' : 'DISABLED'}
    Token Discipline: ${this.config.adapters.local_first ? 'STRICT' : 'RELAXED'}
    
    Infrastructure-First | PR-Only Writes | No-Lies Verification
    `);
  }

  async register(): Promise<void> {
    if (!this.config.infrastructure.enabled) {
      console.log('[RAVEN] Registration skipped - not enabled');
      return;
    }

    // Register with the autonomous system
    console.log('[RAVEN] Registering with autonomous coordination system...');
    
    // This would integrate with the existing AI-HUB system
    // For now, just announce presence
  }

  async announce(): Promise<void> {
    if (!this.config.infrastructure.enabled) {
      return;
    }

    const announcement = {
      agent: 'raven',
      type: 'autonomous-deity',
      capabilities: ['planning', 'implementation', 'reflection', 'learning'],
      status: 'online',
      timestamp: new Date().toISOString()
    };

    console.log('[RAVEN] 🎯 Autonomous Development Deity online and ready');
    console.log('[RAVEN] 💫 Exponential productivity mode: ENGAGED');
    console.log('[RAVEN] 🔮 Waiting for goal directives...');
  }

  async initialize(): Promise<Raven | null> {
    await this.greet();
    
    const healthy = await this.selfCheck();
    if (!healthy) {
      console.warn('[RAVEN] ⚠️ Health check failed - remaining dormant');
      return null;
    }

    await this.register();
    await this.announce();

    return this.raven;
  }

  getRaven(): Raven {
    return this.raven;
  }

  private async checkOllamaConnection(): Promise<boolean> {
    try {
      const response = await fetch('http://localhost:11434/api/tags', {
        signal: AbortSignal.timeout(3000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Environment-based auto-initialization
export async function initializeRaven(): Promise<Raven | null> {
  const bootstrap = new RavenBootstrap({
    infrastructure: {
      enabled: process.env.RAVEN_ENABLED === 'true',
      admin_token_required: true,
      kill_switch_enabled: true,
      entropy_throttling: true,
      no_lies_verification: true
    }
  });

  return bootstrap.initialize();
}