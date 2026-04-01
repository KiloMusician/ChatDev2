// LLM Budget Manager - Exponential backoff and rate limiting
// Autonomous repair for 429 rate limit storms

let requestCount = 0;
let lastResetTime = Date.now();
let consecutiveFailures = 0;
let lastFailureTime = 0;

const RATE_LIMITS = {
  requestsPerMinute: 30,      // 10x increase - intelligent scaling
  backoffMultiplier: 1.5,     // Gentler exponential backoff
  maxBackoffMs: 60000,        // 1 minute max (faster recovery)
  resetWindowMs: 60000,       // 1 minute window for faster reset
  circuitBreakAt: 15          // More resilient before circuit break
};

export function shouldAllowRequest(): { allowed: boolean; waitMs?: number; circuitOpen?: boolean } {
  const now = Date.now();
  
  // Circuit breaker - open circuit if too many failures
  if (consecutiveFailures >= RATE_LIMITS.circuitBreakAt) {
    const circuitResetMs = lastFailureTime + RATE_LIMITS.maxBackoffMs;
    if (now < circuitResetMs) {
      return { 
        allowed: false, 
        waitMs: circuitResetMs - now,
        circuitOpen: true 
      };
    } else {
      // Reset circuit after max backoff period
      consecutiveFailures = Math.floor(RATE_LIMITS.circuitBreakAt / 3);
      console.log(`💚 Budget system recovered, failures reduced to ${consecutiveFailures}`);
    }
  }
  
  // Reset window if needed
  if (now - lastResetTime > RATE_LIMITS.resetWindowMs) {
    requestCount = 0;
    lastResetTime = now;
  }
  
  // Check adaptive rate limit
  const currentRateLimit = getAdaptiveRateLimit();
  if (requestCount >= currentRateLimit) {
    const waitMs = RATE_LIMITS.resetWindowMs - (now - lastResetTime);
    return { allowed: false, waitMs };
  }
  
  // Check exponential backoff
  if (consecutiveFailures > 0) {
    const backoffMs = Math.min(
      1000 * Math.pow(RATE_LIMITS.backoffMultiplier, consecutiveFailures - 1),
      RATE_LIMITS.maxBackoffMs
    );
    
    if (now - lastFailureTime < backoffMs) {
      const waitMs = backoffMs - (now - lastFailureTime);
      return { allowed: false, waitMs };
    }
  }
  
  requestCount++;
  return { allowed: true };
}

export function recordSuccess() {
  consecutiveFailures = 0;
}

// Emergency reset function to restore system immediately
export function emergencyReset() {
  consecutiveFailures = 0;
  requestCount = 0;
  lastResetTime = Date.now();
  lastFailureTime = 0;
  console.log('🚀 Emergency budget reset: System restored to full capacity');
}

// Check if we're in quota exceeded state
export function isQuotaExceeded(): boolean {
  return consecutiveFailures >= RATE_LIMITS.circuitBreakAt;
}

// Disable throttling when working offline
export function setOfflineMode(enabled: boolean) {
  if (enabled) {
    consecutiveFailures = 0;
    requestCount = 0;
    console.log('🌐 Offline mode enabled: LLM throttling disabled');
  }
}

// Adaptive scaling based on success patterns
export function getAdaptiveRateLimit(): number {
  const baseRate = RATE_LIMITS.requestsPerMinute;
  
  // If system is healthy (no recent failures), allow more throughput
  if (consecutiveFailures === 0) {
    return Math.min(baseRate * 2, 60); // Up to 2x or 60/min max
  }
  
  // If experiencing some failures, scale down gracefully
  if (consecutiveFailures < 5) {
    return Math.max(baseRate * 0.75, 10); // 75% but never below 10/min
  }
  
  // Default conservative rate during problems
  return baseRate;
}

export function recordFailure(is429 = false) {
  if (is429) {
    consecutiveFailures++;
    lastFailureTime = Date.now();
    console.log(`⚠️ Rate limit #${consecutiveFailures}/${RATE_LIMITS.circuitBreakAt}, adaptive backoff: ${Math.round(Math.min(1000 * Math.pow(RATE_LIMITS.backoffMultiplier, consecutiveFailures - 1), RATE_LIMITS.maxBackoffMs) / 1000)}s`);
  }
}

export function getBudgetStatus() {
  const now = Date.now();
  const adaptiveRate = getAdaptiveRateLimit();
  return {
    requestsUsed: requestCount,
    requestsRemaining: adaptiveRate - requestCount,
    requestsRemainingDisplay: Math.max(adaptiveRate - requestCount, 0),
    totalCapacity: adaptiveRate,
    baseCapacity: RATE_LIMITS.requestsPerMinute,
    consecutiveFailures,
    windowResetIn: RATE_LIMITS.resetWindowMs - (now - lastResetTime),
    backoffActiveUntil: consecutiveFailures > 0 ? 
      lastFailureTime + Math.min(1000 * Math.pow(RATE_LIMITS.backoffMultiplier, consecutiveFailures - 1), RATE_LIMITS.maxBackoffMs) : 0,
    systemHealth: consecutiveFailures === 0 ? 'excellent' : 
                  consecutiveFailures < 5 ? 'good' : 
                  consecutiveFailures < 10 ? 'degraded' : 'recovering'
  };
}

// OLLAMA OFFLINE ADAPTATION: Force recovery when Ollama unavailable
export function ollamaOfflineAdaptation(): void {
  // Reset circuit breaker to allow heuristic fallbacks
  consecutiveFailures = Math.min(consecutiveFailures, RATE_LIMITS.circuitBreakAt - 5);
  console.log('🔄 Ollama offline adaptation - enabling heuristic fallbacks');
}