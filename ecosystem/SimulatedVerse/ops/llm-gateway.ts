#!/usr/bin/env tsx
/**
 * ΞNuSyQ LLM Gateway - Minimal cascade implementation
 * Prefers Ollama → OpenAI fallback → Structured heuristic
 */
import express from "express";
import cors from "cors";
import { writeFileSync } from "node:fs";

const app = express();
app.use(cors());
app.use(express.json());

type LLMRequest = {
  messages: Array<{role: string; content: string}>;
  model?: string;
  json?: boolean;
  max_tokens?: number;
};

type LLMResponse = {
  backend: "ollama" | "openai" | "heuristic";
  content: string;
  tokens?: number;
  error?: string;
};

async function tryOllama(req: LLMRequest): Promise<LLMResponse | null> {
  try {
    // OLLAMA OFFLINE PROTECTION: Quick timeout for unresponsive service
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 1000);
    
    const model = req.model || "qwen2.5:7b-instruct";
    const response = await fetch("http://127.0.0.1:11434/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model,
        messages: req.messages,
        stream: false,
        options: { num_predict: req.max_tokens || 1024 }
      })
    });
    
    if (!response.ok) return null;
    const data = await response.json();
    return {
      backend: "ollama",
      content: data.message?.content || "",
      tokens: data.eval_count || 0
    };
  } catch {
    return null;
  }
}

async function tryLMStudio(req: LLMRequest): Promise<LLMResponse | null> {
  const host = process.env.LM_STUDIO_HOST || "http://localhost:1234";
  try {
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 1500);
    const response = await fetch(`${host}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: req.model || "local-model",
        messages: req.messages,
        max_tokens: req.max_tokens || 1024,
        stream: false,
        ...(req.json ? { response_format: { type: "json_object" } } : {})
      }),
      signal: controller.signal
    });
    if (!response.ok) return null;
    const data = await response.json();
    return {
      backend: "ollama", // compatible shape, re-uses "ollama" type as local-LLM
      content: data.choices?.[0]?.message?.content || "",
      tokens: data.usage?.total_tokens || 0
    };
  } catch {
    return null;
  }
}

async function tryOpenAI(req: LLMRequest): Promise<LLMResponse | null> {
  const key = process.env.OPENAI_API_KEY;
  if (!key) return null;
  
  try {
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${key}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: req.messages,
        max_tokens: req.max_tokens || 1024,
        ...(req.json ? { response_format: { type: "json_object" } } : {})
      })
    });
    
    if (!response.ok) return null;
    const data = await response.json();
    return {
      backend: "openai",
      content: data.choices?.[0]?.message?.content || "",
      tokens: data.usage?.total_tokens || 0
    };
  } catch {
    return null;
  }
}

function heuristicResponse(req: LLMRequest): LLMResponse {
  const lastMsg = req.messages[req.messages.length - 1]?.content || "";
  
  // Simple pattern matching for common requests
  if (/health|status|check/i.test(lastMsg)) {
    return {
      backend: "heuristic",
      content: JSON.stringify({ status: "operational", fallback: true })
    };
  }
  
  if (/task|todo|plan/i.test(lastMsg)) {
    return {
      backend: "heuristic", 
      content: JSON.stringify({ 
        task: "analyze_system",
        priority: "medium",
        next_step: "check_errors"
      })
    };
  }
  
  return {
    backend: "heuristic",
    content: "System operational. LLM cascade degraded - using fallback heuristics."
  };
}

app.post("/llm/chat", async (req, res) => {
  const timestamp = Date.now();
  const request: LLMRequest = req.body;
  
  // Try cascade: Ollama → LM Studio → OpenAI → Heuristic
  let response = await tryOllama(request) ||
                await tryLMStudio(request) ||
                await tryOpenAI(request) ||
                heuristicResponse(request);
  
  // Write receipt
  const receipt = {
    timestamp,
    backend: response.backend,
    tokens: response.tokens || 0,
    ok: !response.error
  };
  writeFileSync("reports/llm_health.json", JSON.stringify(receipt, null, 2));
  
  res.json(response);
});

app.get("/llm/health", async (req, res) => {
  const ollamaOk = await tryOllama({messages: [{role:"user", content:"test"}]});
  const openaiOk = process.env.OPENAI_API_KEY ? await tryOpenAI({messages: [{role:"user", content:"test"}]}) : null;
  
  const lmStudioOk = await tryLMStudio({messages: [{role:"user", content:"test"}]});
  const health = {
    ollama: !!ollamaOk,
    lm_studio: !!lmStudioOk,
    openai: !!openaiOk,
    gateway_up: true,
    timestamp: Date.now()
  };
  
  writeFileSync("reports/llm_health.json", JSON.stringify(health, null, 2));
  res.json(health);
});

const PORT = process.env.LLM_GATEWAY_PORT || 4455;
app.listen(PORT, () => {
  console.log(`[LLM Gateway] Listening on :${PORT}`);
});