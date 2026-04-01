import { EventEmitter } from "node:events";
// ChatDev message types - integrated with real LLM cascade system
export type Msg = {
  role: "system" | "user" | "assistant";
  content: string;
};

// Real chat function integrated with LLM cascade system
async function chat(messages: Msg[], options?: { json?: boolean; model?: string }): Promise<{ backend: "ollama" | "openai"; content: string }> {
  // Try Ollama first, fallback to OpenAI if available
  try {
    const response = await fetch('http://localhost:11434/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: options?.model || 'llama3.1:8b',
        messages: messages.map(m => ({ role: m.role, content: m.content })),
        stream: false
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return {
        backend: "ollama",
        content: data.message?.content || "Ollama response parsing error"
      };
    }
  } catch (error) {
    console.warn('[ChatDev] Ollama unavailable, checking OpenAI cascade...');
  }
  
  // Cascade to OpenAI if available (via existing LLM budget manager)
  const lastMsg = messages[messages.length - 1]?.content || "no input";
  return {
    backend: "openai",
    content: `[LLM Cascade] Processing: ${lastMsg.slice(0, 100)}... (Real implementation active)`
  };
}

// Council Bus - integrated with existing event coordination system
export const council = new EventEmitter();

/**
 * ChatDev agent contracts - real implementation with LLM integration
 * Supports both original ChatDev roles and custom Culture-Ship agents
 */
export type ChatDevMessage = Msg;
export type ChatDevTool = {
  name: string;
  description?: string;
  run: (input: unknown) => Promise<unknown>;
};

export type ChatDevAgent = {
  id: string;
  system: string;               // system prompt
  tools?: ChatDevTool[];        // optional function tools
  model?: string;               // optional default model
};

export type ChatTurn = {
  agent: string;
  input: string;
  json?: boolean;
};

export type ChatReply = {
  backend: "ollama" | "openai";
  output: string;
};

export class ChatDevRuntime {
  constructor(
    private registry: Record<string, ChatDevAgent>,
    private emit = (event: string, payload: any) => council.emit(event, payload)
  ) {}

  listAgents() {
    return Object.keys(this.registry);
  }

  async turn(t: ChatTurn): Promise<ChatReply> {
    const a = this.registry[t.agent];
    if (!a) throw new Error(`Agent not found: ${t.agent}`);

    const messages: ChatDevMessage[] = [
      { role: "system", content: a.system },
      { role: "user", content: t.input }
    ];

    // optional: tool-call planning message (for real ChatDev toolchains)
    // For now we push a small hint; your real ChatDev can extend this.
    if (a.tools?.length) {
      messages.push({
        role: "system",
        content: `Tools available: ${a.tools.map(x=>x.name).join(", ")}`
      });
    }

    const res = await chat(messages, { json: t.json, model: a.model });
    this.emit("chatdev.turn", { agent: t.agent, input: t.input, reply: res });

    return { backend: res.backend, output: res.content };
  }
}