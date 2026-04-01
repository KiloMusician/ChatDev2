// [Ω:root:config@guards] Environment validation and safety checks

interface SecretConfig {
  required: string[];
  optional: string[];
}

/**
 * Validates that all required secrets are present for the active profile
 * Throws descriptive errors if missing critical configuration
 */
export async function validateSecrets(requiredSecrets: string[]): Promise<Record<string, string>> {
  const secrets: Record<string, string> = {};
  const missing: string[] = [];
  
  for (const secretName of requiredSecrets) {
    const value = process.env[secretName];
    if (!value) {
      missing.push(secretName);
    } else {
      secrets[secretName] = value;
    }
  }
  
  if (missing.length > 0) {
    const errorMsg = [
      `❌ Missing required secrets: ${missing.join(', ')}`,
      ``,
      `Add these to your Replit Secrets:`,
      ...missing.map(name => `  ${name}=<your-value>`),
      ``,
      `See /docs/SECRETS.md for setup guidance`
    ].join('\n');
    
    throw new Error(errorMsg);
  }
  
  console.log(`[GUARDS] ✓ All ${requiredSecrets.length} required secrets validated`);
  return secrets;
}

/**
 * Implements panic switch - disables risky operations when SAFE_MODE=1
 */
export function isPanicMode(): boolean {
  return process.env.SAFE_MODE === '1' || process.env.NODE_ENV === 'production';
}

/**
 * Rate limiting guard for external API calls
 */
export class RateLimiter {
  private calls: number[] = [];
  
  constructor(
    private maxCalls: number,
    private windowMs: number
  ) {}
  
  canMakeCall(): boolean {
    const now = Date.now();
    this.calls = this.calls.filter(time => now - time < this.windowMs);
    
    if (this.calls.length >= this.maxCalls) {
      return false;
    }
    
    this.calls.push(now);
    return true;
  }
  
  getStats() {
    const now = Date.now();
    const recent = this.calls.filter(time => now - time < this.windowMs);
    return {
      callsInWindow: recent.length,
      maxCalls: this.maxCalls,
      windowMs: this.windowMs,
      canCall: recent.length < this.maxCalls
    };
  }
}

/**
 * Circuit breaker for external dependencies
 */
export class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  
  constructor(
    private failureThreshold: number = 5,
    private timeoutMs: number = 60000
  ) {}
  
  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.timeoutMs) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is OPEN - operation blocked');
      }
    }
    
    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess() {
    this.failures = 0;
    this.state = 'closed';
  }
  
  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    
    if (this.failures >= this.failureThreshold) {
      this.state = 'open';
    }
  }
  
  getState() {
    return {
      state: this.state,
      failures: this.failures,
      threshold: this.failureThreshold
    };
  }
}