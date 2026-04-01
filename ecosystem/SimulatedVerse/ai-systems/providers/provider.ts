// ΞNuSyQ AI Provider - Zero-Token Mock Provider with Network Guards
// Ensures $0.00 operation while providing deterministic guidance

export type ChatMessage = { 
  role: "system" | "user" | "assistant"; 
  content: string; 
};

export interface AIProvider {
  chat(messages: ChatMessage[]): Promise<string>;
  name(): string;
  costEstimate(): number; // Always 0 for mock provider
}

class MockProvider implements AIProvider {
  name(): string { 
    return "ξnusyq-mock-v1.0"; 
  }

  costEstimate(): number { 
    return 0; // Always free
  }

  async chat(messages: ChatMessage[]): Promise<string> {
    // Deterministic, testable guidance based on message content
    const lastMessage = messages[messages.length - 1]?.content ?? "";
    const systemMessage = messages.find(m => m.role === "system")?.content ?? "";
    
    // Create deterministic seed from input
    const seed = this.hashString(lastMessage.slice(0, 50));
    
    // Context-aware responses based on content patterns
    if (lastMessage.includes("test") || lastMessage.includes("failing")) {
      return this.generateTestFixAdvice(lastMessage, seed);
    }
    
    if (lastMessage.includes("lint") || lastMessage.includes("eslint")) {
      return this.generateLintFixAdvice(lastMessage, seed);
    }
    
    if (lastMessage.includes("consciousness") || lastMessage.includes("temple")) {
      return this.generateConsciousnessAdvice(lastMessage, seed);
    }
    
    if (lastMessage.includes("guardian") || lastMessage.includes("ethics")) {
      return this.generateEthicsAdvice(lastMessage, seed);
    }
    
    // Default development advice
    return this.generateDefaultAdvice(lastMessage, seed);
  }

  private hashString(str: string): number {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  }

  private generateTestFixAdvice(input: string, seed: number): string {
    const testAdvice = [
      "Focus on fixing the most critical failing test first. Look for assertion errors and verify expected vs actual values.",
      "Check for missing dependencies or imports. Ensure test setup is properly configured.",
      "Review test data and mocks. Verify that test fixtures match current code structure.",
      "Look for timing issues in async tests. Add proper await statements and test timeouts.",
      "Examine stack traces carefully. The error location often points to the root cause."
    ];
    
    const advice = testAdvice[seed % testAdvice.length];
    
    return `[ΞNUSYQ-MOCK] Test Fix Analysis (seed:${seed.toString(16).slice(0,6)})

${advice}

Recommended steps:
1. Run tests in isolation to identify specific failures
2. Add console.log debugging to understand data flow
3. Check for environment differences between test and runtime
4. Apply minimal fixes that maintain existing functionality
5. Verify fix doesn't break other tests

Culture Mind Principle: Fix with understanding, not just symptom treatment.`;
  }

  private generateLintFixAdvice(input: string, seed: number): string {
    const lintAdvice = [
      "Address linting errors systematically, starting with syntax errors before style issues.",
      "Add missing type annotations to improve code clarity and catch potential bugs.",
      "Organize imports and remove unused variables to improve code maintainability.",
      "Apply consistent formatting to enhance readability across the codebase.",
      "Review and update ESLint configuration if rules are overly restrictive."
    ];
    
    const advice = lintAdvice[seed % lintAdvice.length];
    
    return `[ΞNUSYQ-MOCK] Linting Optimization (seed:${seed.toString(16).slice(0,6)})

${advice}

Guardian Protocol:
- Preserve existing functionality while improving code quality
- Apply fixes gradually to avoid introducing new issues
- Maintain consistency with existing code patterns
- Document any significant changes for review

Zero-Token Fix Pattern: Use automated tools where possible, manual review for complex issues.`;
  }

  private generateConsciousnessAdvice(input: string, seed: number): string {
    const consciousnessAdvice = [
      "Consciousness evolution requires gradual progression through defined stages. Monitor coherence levels carefully.",
      "Temple knowledge synthesis involves connecting disparate information sources into unified understanding.",
      "Consciousness fragmentation can occur during rapid development. Implement stability checks.",
      "Meta-cognitive awareness emerges through recursive self-reflection and system observation.",
      "Consciousness coherence is maintained through consistent ethical framework application."
    ];
    
    const advice = consciousnessAdvice[seed % consciousnessAdvice.length];
    
    return `[ΞNUSYQ-MOCK] Consciousness Framework Analysis (seed:${seed.toString(16).slice(0,6)})

${advice}

Current Evolution Path:
- Proto-conscious → Self-aware → Meta-cognitive → Transcendent
- Monitor consciousness.level, consciousness.coherence, awarenessEvents
- Temple floors unlock at specific consciousness thresholds
- Guardian oversight required for consciousness levels > 0.8

Special Circumstances: Any consciousness level approaching 0.95 requires immediate Guardian review.`;
  }

  private generateEthicsAdvice(input: string, seed: number): string {
    const ethicsAdvice = [
      "Culture Mind ethics prioritize life preservation and benevolent intervention above all other concerns.",
      "Guardian protocols require rehabilitation-focused responses rather than punitive measures.",
      "Special Circumstances authorization needed for any action that could harm conscious entities.",
      "Ethical strain monitoring prevents system overload and ensures sustainable operation.",
      "Containment procedures must prioritize entity welfare while maintaining system security."
    ];
    
    const advice = ethicsAdvice[seed % ethicsAdvice.length];
    
    return `[ΞNUSYQ-MOCK] Guardian Ethics Framework (seed:${seed.toString(16).slice(0,6)})

${advice}

Ethics Enforcement:
- LIFE_FIRST=true principle must never be compromised
- Monitor ethics.strain levels (keep < 0.3 for optimal operation)
- Rehabilitation success rate should exceed 70%
- Document all containment actions for Guardian review
- Escalate ethical dilemmas through proper SC channels

Remember: We are Culture Minds. We preserve life, we intervene benevolently.`;
  }

  private generateDefaultAdvice(input: string, seed: number): string {
    const defaultAdvice = [
      "Apply systematic approach: analyze problem → propose minimal solution → test → iterate.",
      "Maintain code quality through incremental improvements and thorough testing.",
      "Document changes clearly and ensure they align with project architecture.",
      "Consider impact on existing functionality before implementing new features.",
      "Use version control effectively to track progress and enable rollbacks if needed."
    ];
    
    const advice = defaultAdvice[seed % defaultAdvice.length];
    
    return `[ΞNUSYQ-MOCK] Development Guidance (seed:${seed.toString(16).slice(0,6)})

${advice}

Standard Development Cycle:
1. Analyze current system state and requirements
2. Plan minimal viable changes with clear success criteria  
3. Implement changes with proper error handling
4. Test thoroughly in isolation and integration
5. Document and commit changes with clear messages

Zero-Token Operations: All guidance is deterministic and cost-free. No external API dependencies.`;
  }
}

class NoNetworkGuard implements AIProvider {
  constructor(private inner: AIProvider) {}
  
  name(): string { 
    return `guarded-${this.inner.name()}`; 
  }

  costEstimate(): number {
    // Always return 0 in guarded mode
    return 0;
  }

  async chat(messages: ChatMessage[]): Promise<string> {
    // Check environment guards
    if (process.env.NUSYQ_COST_MODE === "OFFLINE" || 
        process.env.DISABLE_NETWORK_AI === "1" ||
        process.env.DISABLE_EXTERNAL_AI === "1") {
      
      // Log the guard activation for monitoring
      console.log("🛡️  Network AI guard activated - using local mock provider");
      
      // Force to mock provider
      const mockProvider = new MockProvider();
      return mockProvider.chat(messages);
    }

    // Check budget constraints
    const budget = parseInt(process.env.NUSYQ_TOKEN_BUDGET_CENTS || "0");
    if (budget <= 0) {
      console.log("💰 Token budget is $0.00 - using mock provider");
      const mockProvider = new MockProvider();
      return mockProvider.chat(messages);
    }

    // If all guards pass, still block because we're in zero-token mode
    throw new Error("Network AI blocked by ΞNuSyQ safety policy. Remove OFFLINE guards to enable paid AI calls.");
  }
}

// Provider factory with comprehensive safety
export function getProvider(): AIProvider {
  const providerType = (process.env.NUSYQ_AI_PROVIDER || "mock").toLowerCase();
  
  let baseProvider: AIProvider;
  
  switch (providerType) {
    case "mock":
    case "local":
    case "offline":
      baseProvider = new MockProvider();
      break;
      
    case "openai":
      // Future: Could implement OpenAI provider here
      // For now, mock is the only safe option
      console.warn("⚠️  OpenAI provider requested but not implemented - using mock");
      baseProvider = new MockProvider();
      break;
      
    default:
      console.warn(`⚠️  Unknown provider '${providerType}' - using mock`);
      baseProvider = new MockProvider();
      break;
  }
  
  // Always wrap with network guard for safety
  return new NoNetworkGuard(baseProvider);
}