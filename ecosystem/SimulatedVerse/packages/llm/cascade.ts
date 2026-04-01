export type Msg = { role: "system" | "user" | "assistant", content: string };

export async function chat(messages: Msg[], opts?: { json?: boolean; model?: string }) {
  const { shouldAllowRequest, recordSuccess, recordFailure } = await import('./budget-manager');
  
  // Check budget before making LLM gateway request
  const budgetCheck = shouldAllowRequest();
  if (!budgetCheck.allowed) {
    throw new Error(`Rate limited: ${budgetCheck.circuitOpen ? 'Circuit breaker open' : 'Wait ' + Math.round((budgetCheck.waitMs || 0) / 1000) + 's'}`);
  }
  
  try {
    const body = { messages, json: !!opts?.json, model: opts?.model };
    const r = await fetch(process.env.LLM_GATEWAY_URL || "http://127.0.0.1:4455/llm/chat", {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(30000)
    });
    
    if (!r.ok) {
      const is429 = r.status === 429;
      recordFailure(is429);
      throw new Error(`llm-gateway ${r.status}`);
    }
    
    recordSuccess();
    return r.json() as Promise<{ backend: "ollama" | "openai", content: string }>;
  } catch (error: any) {
    const is429 = error.message.includes('429');
    recordFailure(is429);
    throw error;
  }
}