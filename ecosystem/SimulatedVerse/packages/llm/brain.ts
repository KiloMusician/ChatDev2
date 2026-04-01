// packages/llm/brain.ts
import { speak, shout } from "../comms/speak";
import fetch from "node-fetch";
import { chat, type Msg } from "./cascade";

// Use the new LLM cascade instead of direct calls
export async function llmAskViaCascade(prompt: string, opts: LLMOpts = {}): Promise<string> {
  try {
    const messages: Msg[] = [{ role: 'user', content: prompt }];
    const result = await chat(messages, { model: opts.model, json: opts.json });
    console.log(`🧠 LLM Cascade (${result.backend}): Generated ${result.content.length} chars`);
    return result.content;
  } catch (error: any) {
    shout("brain", "LLM Cascade failed", `All backends down: ${error.message}`);
    return `CRITICAL: LLM spine unavailable - ${prompt.slice(0, 80)}...`;
  }
}

export type LLMOpts = { model?: string; temperature?: number; json?: boolean };
export async function llmAsk(prompt: string, opts: LLMOpts = {}): Promise<string> {
  const host = process.env.OLLAMA_HOST || "http://127.0.0.1:11434";
  const model = opts.model || "llama3";
  try {
    // Health
    const h = await fetch(`${host}/api/tags`, { method:"GET" });
    if (!h.ok) throw new Error(`ollama tags ${h.status}`);

    // Generate
    const r = await fetch(`${host}/api/generate`, {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ model, prompt, stream: false })
    });
    if (!r.ok) throw new Error(`ollama gen ${r.status}`);
    const data = await r.json() as any;
    return data.response as string;
  } catch (e:any) {
    shout("brain","Ollama unavailable","Switching to LLM cascade.", { error:String(e) });
    // Use the new LLM cascade system
    return await llmAskViaCascade(prompt, opts);
  }
}