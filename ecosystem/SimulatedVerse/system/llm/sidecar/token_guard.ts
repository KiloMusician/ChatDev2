// Token Guard - Budget protection and intelligent routing for LLM requests
// Part of CoreLink Foundation sophisticated LLM cascade architecture

export interface CascadeRequest {
  prompt: string;
  task_type?: 'code_generation' | 'analysis' | 'chat' | 'reasoning';
  max_tokens?: number;
  temperature?: number;
  context?: any;
}

export interface CascadeResponse {
  response: string;
  model_used: string;
  confidence: number;
  cost_cents: number;
  backend: 'ollama' | 'openai' | 'heuristic';
}

export class TokenGuard {
  private budget_cents: number = 1000; // $10 daily limit
  private used_today: number = 0;

  async ask(request: CascadeRequest): Promise<CascadeResponse> {
    // Try Ollama first (zero cost)
    try {
      const ollamaResponse = await this.tryOllama(request);
      if (ollamaResponse) {
        return ollamaResponse;
      }
    } catch (error) {
      console.log('[TokenGuard] Ollama failed, trying OpenAI fallback');
    }

    // Fallback to OpenAI with budget protection
    if (this.used_today + 100 > this.budget_cents) {
      throw new Error('Budget protection: Daily limit would be exceeded');
    }

    try {
      return await this.tryOpenAI(request);
    } catch (error) {
      // Heuristic fallback
      return {
        response: 'System operational. Using heuristic fallback due to LLM unavailability.',
        model_used: 'heuristic_v1',
        confidence: 0.3,
        cost_cents: 0,
        backend: 'heuristic'
      };
    }
  }

  private async tryOllama(request: CascadeRequest): Promise<CascadeResponse | null> {
    // OLLAMA OFFLINE PROTECTION: Quick timeout and graceful fallback
    try {
      const controller = new AbortController();
      setTimeout(() => controller.abort(), 1000); // 1s timeout for offline Ollama
      
      const response = await fetch('http://127.0.0.1:11434/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'qwen2.5:7b-instruct',
          messages: [{ role: 'user', content: request.prompt }],
          stream: false
        }),
        signal: controller.signal
      });

      if (!response.ok) return null;

      const data = await response.json();
      return {
        response: data.message?.content || '',
        model_used: 'qwen2.5:7b-instruct',
        confidence: 0.8,
        cost_cents: 0,
        backend: 'ollama'
      };
    } catch (error) {
      console.log('[TokenGuard] Ollama unreachable (offline), using fallback');
      return null;
    }
  }

  private async tryOpenAI(request: CascadeRequest): Promise<CascadeResponse> {
    const key = process.env.OPENAI_API_KEY;
    if (!key) throw new Error('OpenAI API key not configured');

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: request.prompt }],
        max_tokens: request.max_tokens || 1024
      })
    });

    if (!response.ok) throw new Error(`OpenAI API error: ${response.status}`);

    const data = await response.json();
    const estimatedCost = (data.usage?.total_tokens || 1000) * 0.01; // Rough estimate
    this.used_today += estimatedCost;

    return {
      response: data.choices?.[0]?.message?.content || '',
      model_used: 'gpt-4o-mini',
      confidence: 0.9,
      cost_cents: estimatedCost,
      backend: 'openai'
    };
  }

  getBudgetStatus() {
    return {
      budget_cents: this.budget_cents,
      used_today: this.used_today,
      remaining: this.budget_cents - this.used_today
    };
  }
}