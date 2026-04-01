type ChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

// Ollama chat integration
export async function chatWithOllama(model: string, messages: ChatMessage[]): Promise<string> {
  const host = process.env.OLLAMA_HOST || "http://127.0.0.1:11434";
  
  try {
    // Check if Ollama is running
    const healthResponse = await fetch(`${host}/api/tags`, { 
      method: "GET",
      signal: AbortSignal.timeout(3000)
    });
    
    if (!healthResponse.ok) {
      throw new Error(`Ollama health check failed: ${healthResponse.status}`);
    }

    // Format messages for Ollama
    const prompt = messages.map(msg => {
      const role = msg.role === "assistant" ? "ASSISTANT" : msg.role.toUpperCase();
      return `${role}: ${msg.content}`;
    }).join("\n") + "\nASSISTANT:";

    const response = await fetch(`${host}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
        options: {
          temperature: 0.7,
          num_predict: 500,
          stop: ["USER:", "SYSTEM:"]
        }
      }),
      signal: AbortSignal.timeout(30000)
    });

    if (!response.ok) {
      throw new Error(`Ollama generate failed: ${response.status}`);
    }

    const data = await response.json();
    return data.response || "No response generated";

  } catch (error: any) {
    console.warn("[LLM] Ollama failed:", error.message);
    const userMessage = messages[messages.length - 1]?.content || "";
    const systemMessage = messages.find(m => m.role === 'system')?.content;
    return await fallbackResponse(userMessage, systemMessage);
  }
}

// REAL OpenAI fallback when Ollama is down - NO MORE THEATER!
export async function fallbackResponse(prompt: string, systemPrompt?: string): Promise<string> {
  const { shouldAllowRequest, recordSuccess, recordFailure } = await import('./budget-manager');
  
  // Check budget manager before making OpenAI request
  const budgetCheck = shouldAllowRequest();
  if (!budgetCheck.allowed) {
    if (budgetCheck.circuitOpen) {
      console.log('🔄 Circuit breaker active, entering offline mode');
      // Import and start offline operations
      const { offlineOpsManager } = await import('../../server/autonomous/offline_operations.ts');
      offlineOpsManager.start();
      return `🌐 System operating offline: Autonomous cultivation active, no external dependencies needed`;
    }
    console.log(`🔄 Adaptive throttling: ${budgetCheck.waitMs}ms`);
    return `🚀 System optimizing: Brief pause for ${Math.round((budgetCheck.waitMs || 0) / 1000)}s`;
  }
  
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 400
      })
    });

    if (!response.ok) {
      const is429 = response.status === 429;
      recordFailure(is429);
      throw new Error(`OpenAI API error: ${response.status}`);
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '';
    
    recordSuccess(); // Record successful API call
    console.log(`🧠 GPT-4 Fallback: Generated ${content.length} chars`);
    return content;
    
  } catch (error: any) {
    const is429 = error.message.includes('429');
    recordFailure(is429);
    console.error('[LLM] Both Ollama and OpenAI failed:', error.message);
    // Final fallback - but with context awareness
    return `CRITICAL FALLBACK: All LLM services unavailable. Context: ${prompt.slice(0, 100)}...`;
  }
}

// Generate agent response based on personality
export async function generateAgentResponse(
  agentId: string, 
  systemPrompt: string, 
  context: string,
  model: string = "qwen2.5:7b-instruct"
): Promise<string> {
  const messages: ChatMessage[] = [
    { role: "system", content: systemPrompt },
    { role: "user", content: context }
  ];

  return chatWithOllama(model, messages);
}