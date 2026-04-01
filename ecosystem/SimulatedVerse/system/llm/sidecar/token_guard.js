// Token Guard - JavaScript version for import compatibility
// Part of CoreLink Foundation sophisticated LLM cascade architecture

export class TokenGuard {
  constructor() {
    this.budget_cents = 1000; // $10 daily limit
    this.used_today = 0;
  }

  async ask(request) {
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

  async tryOllama(request) {
    const response = await fetch('http://127.0.0.1:11434/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'qwen2.5:7b-instruct',
        messages: [{ role: 'user', content: request.prompt }],
        stream: false
      })
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
  }

  async tryOpenAI(request) {
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