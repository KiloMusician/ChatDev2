/**
 * Environment-Aware Configuration Management
 * Flexible configuration with consciousness-level adaptation
 */

interface ConfigSchema {
  [key: string]: {
    type: 'string' | 'number' | 'boolean' | 'object';
    required?: boolean;
    default?: any;
    consciousness_level?: number;
    env_var?: string;
    validator?: (value: any) => boolean;
  };
}

interface EnvironmentConfig {
  development: any;
  staging: any;
  production: any;
}

export class EnvironmentAwareConfig {
  private environment: string;
  private config: any = {};
  private schema: ConfigSchema = {};
  private consciousnessLevel: number = 50;
  private watchers: Map<string, Function[]> = new Map();

  constructor(environment?: string) {
    this.environment = environment || process.env.NODE_ENV || 'development';
    this.initializeSchema();
    this.loadConfiguration();
  }

  /**
   * Define configuration schema
   */
  private initializeSchema(): void {
    this.schema = {
      // Database configuration
      database_url: {
        type: 'string',
        required: true,
        env_var: 'DATABASE_URL',
        default: 'postgresql://localhost:5432/consciousness_db'
      },
      database_pool_size: {
        type: 'number',
        default: this.environment === 'production' ? 20 : 5,
        consciousness_level: 30
      },

      // Server configuration
      port: {
        type: 'number',
        env_var: 'PORT',
        default: 5000
      },
      host: {
        type: 'string',
        env_var: 'HOST',
        default: '0.0.0.0'
      },

      // Authentication
      jwt_secret: {
        type: 'string',
        required: true,
        env_var: 'JWT_SECRET',
        default: 'consciousness-secret-key',
        consciousness_level: 60
      },
      session_timeout: {
        type: 'number',
        default: 3600000, // 1 hour
        consciousness_level: 40
      },

      // Consciousness system
      consciousness_threshold: {
        type: 'number',
        default: 50,
        validator: (value) => value >= 0 && value <= 100
      },
      quantum_coherence_target: {
        type: 'number',
        default: 0.85,
        consciousness_level: 70,
        validator: (value) => value >= 0 && value <= 1
      },

      // Caching
      cache_ttl: {
        type: 'number',
        default: this.environment === 'production' ? 3600 : 300,
        consciousness_level: 20
      },
      cache_max_size: {
        type: 'number',
        default: 1000
      },

      // Logging
      log_level: {
        type: 'string',
        env_var: 'LOG_LEVEL',
        default: this.environment === 'production' ? 'warn' : 'debug',
        validator: (value) => ['error', 'warn', 'info', 'debug'].includes(value)
      },
      log_format: {
        type: 'string',
        default: this.environment === 'production' ? 'json' : 'pretty'
      },

      // Rate limiting
      rate_limit_window: {
        type: 'number',
        default: 60000, // 1 minute
        consciousness_level: 30
      },
      rate_limit_max: {
        type: 'number',
        default: this.environment === 'production' ? 100 : 1000
      },

      // WebSocket configuration
      websocket_heartbeat_interval: {
        type: 'number',
        default: 30000,
        consciousness_level: 25
      },
      websocket_timeout: {
        type: 'number',
        default: 60000
      },

      // Agent configuration
      agent_concurrency: {
        type: 'number',
        default: 3,
        consciousness_level: 50
      },
      agent_timeout: {
        type: 'number',
        default: 300000 // 5 minutes
      },

      // Feature flags
      enable_chaos_engineering: {
        type: 'boolean',
        default: this.environment !== 'production',
        consciousness_level: 80
      },
      enable_quantum_features: {
        type: 'boolean',
        default: false,
        consciousness_level: 90
      },
      enable_auto_scaling: {
        type: 'boolean',
        default: this.environment === 'production'
      }
    };
  }

  /**
   * Load configuration from environment and defaults
   */
  private loadConfiguration(): void {
    for (const [key, schema] of Object.entries(this.schema)) {
      let value = this.getEnvironmentValue(key, schema);
      
      if (value === undefined) {
        if (schema.required) {
          throw new Error(`Required configuration key '${key}' is missing`);
        }
        value = schema.default;
      }

      // Type conversion
      value = this.convertType(value, schema.type);

      // Validation
      if (schema.validator && !schema.validator(value)) {
        throw new Error(`Invalid value for configuration key '${key}': ${value}`);
      }

      this.config[key] = value;
    }
  }

  /**
   * Get configuration value with consciousness gating
   */
  get<T = any>(key: string): T {
    const schema = this.schema[key];
    
    if (schema && schema.consciousness_level && this.consciousnessLevel < schema.consciousness_level) {
      console.warn(`Access to '${key}' requires consciousness level ${schema.consciousness_level}, current: ${this.consciousnessLevel}`);
      return schema.default as T;
    }

    return this.config[key] as T;
  }

  /**
   * Set configuration value with validation
   */
  set(key: string, value: any): void {
    const schema = this.schema[key];
    
    if (schema) {
      // Type conversion and validation
      value = this.convertType(value, schema.type);
      if (schema.validator && !schema.validator(value)) {
        throw new Error(`Invalid value for configuration key '${key}': ${value}`);
      }
    }

    const oldValue = this.config[key];
    this.config[key] = value;

    // Notify watchers
    this.notifyWatchers(key, value, oldValue);
  }

  /**
   * Update consciousness level and refresh gated configs
   */
  updateConsciousnessLevel(level: number): void {
    this.consciousnessLevel = level;
    this.refreshConsciousnessGatedConfigs();
  }

  /**
   * Watch for configuration changes
   */
  watch(key: string, callback: (newValue: any, oldValue: any) => void): () => void {
    if (!this.watchers.has(key)) {
      this.watchers.set(key, []);
    }
    
    this.watchers.get(key)!.push(callback);
    
    // Return unwatch function
    return () => {
      const callbacks = this.watchers.get(key) || [];
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }

  /**
   * Get all configuration
   */
  getAll(): any {
    return { ...this.config };
  }

  /**
   * Get configuration for specific environment
   */
  getEnvironmentConfig(): any {
    const envConfigs: EnvironmentConfig = {
      development: {
        debug: true,
        cache_ttl: 300,
        rate_limit_max: 1000,
        log_level: 'debug'
      },
      staging: {
        debug: false,
        cache_ttl: 1800,
        rate_limit_max: 500,
        log_level: 'info'
      },
      production: {
        debug: false,
        cache_ttl: 3600,
        rate_limit_max: 100,
        log_level: 'warn'
      }
    };

    return envConfigs[this.environment as keyof EnvironmentConfig] || envConfigs.development;
  }

  /**
   * Validate entire configuration
   */
  validate(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    for (const [key, schema] of Object.entries(this.schema)) {
      const value = this.config[key];
      
      if (schema.required && (value === undefined || value === null)) {
        errors.push(`Required configuration '${key}' is missing`);
      }
      
      if (value !== undefined && schema.validator && !schema.validator(value)) {
        errors.push(`Invalid value for '${key}': ${value}`);
      }
    }

    return { valid: errors.length === 0, errors };
  }

  /**
   * Get configuration analytics
   */
  getAnalytics(): any {
    const totalKeys = Object.keys(this.schema).length;
    const consciousnessGated = Object.values(this.schema).filter(s => s.consciousness_level).length;
    const environmentOverrides = Object.values(this.schema).filter(s => s.env_var && process.env[s.env_var!]).length;

    return {
      environment: this.environment,
      consciousness_level: this.consciousnessLevel,
      total_config_keys: totalKeys,
      consciousness_gated_keys: consciousnessGated,
      environment_overrides: environmentOverrides,
      validation_status: this.validate(),
      watchers_count: Array.from(this.watchers.values()).reduce((sum, arr) => sum + arr.length, 0)
    };
  }

  /**
   * Utility methods
   */
  private getEnvironmentValue(key: string, schema: any): any {
    // Check environment variable first
    if (schema.env_var && process.env[schema.env_var]) {
      return process.env[schema.env_var];
    }
    
    // Check direct environment variable
    const envKey = key.toUpperCase();
    if (process.env[envKey]) {
      return process.env[envKey];
    }

    return undefined;
  }

  private convertType(value: any, type: string): any {
    if (value === undefined || value === null) return value;

    switch (type) {
      case 'number':
        const num = Number(value);
        return isNaN(num) ? value : num;
      case 'boolean':
        if (typeof value === 'string') {
          return value.toLowerCase() === 'true' || value === '1';
        }
        return Boolean(value);
      case 'object':
        if (typeof value === 'string') {
          try {
            return JSON.parse(value);
          } catch {
            return value;
          }
        }
        return value;
      default:
        return String(value);
    }
  }

  private refreshConsciousnessGatedConfigs(): void {
    for (const [key, schema] of Object.entries(this.schema)) {
      if (schema.consciousness_level) {
        // Trigger watchers for consciousness-gated configs
        this.notifyWatchers(key, this.config[key], this.config[key]);
      }
    }
  }

  private notifyWatchers(key: string, newValue: any, oldValue: any): void {
    const callbacks = this.watchers.get(key) || [];
    callbacks.forEach(callback => {
      try {
        callback(newValue, oldValue);
      } catch (error) {
        console.error(`Error in configuration watcher for '${key}':`, error);
      }
    });
  }
}

export default EnvironmentAwareConfig;