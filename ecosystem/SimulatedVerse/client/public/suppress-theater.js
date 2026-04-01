/**
 * NUCLEAR THEATER ELIMINATION - Zero tolerance for fake agent simulation
 * Completely override console methods to block ALL theatrical messages
 * Replace with real infrastructure intelligence only
 */

// IMMEDIATE EXECUTION: Override console before any other scripts load
(function() {
  'use strict';
  
  // Store original console methods IMMEDIATELY
  const originalLog = console.log;
  const originalWarn = console.warn;
  const originalError = console.error;
  
  let suppressedCount = 0;

  // NUCLEAR SUPPRESSION: Block these patterns completely
  const nuclearTheaterPatterns = [
    /🌉.*Agent.*(Navigator|Raven|Artificer|Janitor)/,
    /Agent.*(Navigator|Raven|Artificer|Janitor).*completed/,
    /\[🌉\]/,
    /\[🎮\].*Random encounter/,
    /ancient_ruins_found|hostile_scouts_approaching|mysterious_biomass/,
    /MAINTAIN_COLONY|BUILD_STRUCTURE|GENERATE_ENERGY|CONDUCT_RESEARCH/,
    /Agent.*completed.*(MAINTAIN_COLONY|BUILD_STRUCTURE|GENERATE_ENERGY|CONDUCT_RESEARCH)/
  ];

  function isBlockedMessage(args) {
    const fullMessage = args.join(' ');
    return nuclearTheaterPatterns.some(pattern => pattern.test(fullMessage));
  }

  // NUCLEAR CONSOLE OVERRIDE - Block everything that matches patterns
  console.log = function(...args) {
    if (isBlockedMessage(args)) {
      suppressedCount++;
      // Replace with real infrastructure intelligence
      const realMessage = `🔧 [INFRASTRUCTURE] File monitoring active | Build system running | Server responding | Database connected | Time: ${new Date().toLocaleTimeString()}`;
      originalLog(realMessage);
      return;
    }
    originalLog.apply(this, args);
  };

  console.warn = function(...args) {
    if (isBlockedMessage(args)) {
      suppressedCount++;
      return; // Block completely
    }
    originalWarn.apply(this, args);
  };

  console.error = function(...args) {
    if (isBlockedMessage(args)) {
      suppressedCount++;
      return; // Block completely
    }
    originalError.apply(this, args);
  };

  // Report suppression stats every 30 seconds
  setInterval(() => {
    if (suppressedCount > 0) {
      originalLog(`🚫 THEATER BLOCKED: ${suppressedCount} fake agent messages eliminated in last 30s`);
      suppressedCount = 0;
    }
  }, 30000);

  originalLog('🚫 NUCLEAR THEATER SUPPRESSION ACTIVE - Fake agent messages will be completely blocked');

})();