#!/usr/bin/env tsx
import { createServer } from "node:http";

const OLLAMA = process.env.OLLAMA_HOST || "http://127.0.0.1:11434";
const OPENAI_KEY = process.env.OPENAI_API_KEY;

type ChatReq = {
  model?: string;
  messages: Array<{role: "system" | "user" | "assistant", content: string}>;
  json?: boolean;
};

async function tryOllama(req: ChatReq) {
  const body = {
    model: req.model || "qwen2.5:7b-instruct",
    messages: req.messages,
    stream: false,
    format: req.json ? "json" : undefined
  };
  const r = await fetch(`${OLLAMA}/api/chat`, {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "content-type": "application/json" },
    signal: AbortSignal.timeout(30000)
  });
  if (!r.ok) throw new Error("ollama-not-ok");
  const j = await r.json() as any;
  const content = j?.message?.content ?? "";
  return { backend: "ollama", content };
}

async function tryOpenAI(req: ChatReq) {
  if (!OPENAI_KEY) throw new Error("openai-missing");
  const body = {
    model: process.env.OPENAI_MODEL || "gpt-4o-mini",
    messages: req.messages,
    response_format: req.json ? { type: "json_object" } : undefined
  };
  const r = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "content-type": "application/json",
      "authorization": `Bearer ${OPENAI_KEY}`
    },
    signal: AbortSignal.timeout(30000)
  });
  if (!r.ok) throw new Error("openai-not-ok");
  const j = await r.json() as any;
  const content = j?.choices?.[0]?.message?.content ?? "";
  return { backend: "openai", content };
}

createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/llm/chat") {
    try {
      const chunks: Buffer[] = [];
      for await (const c of req) chunks.push(c as Buffer);
      const payload = JSON.parse(Buffer.concat(chunks).toString()) as ChatReq;

      // Try Ollama first, then OpenAI fallback
      let result;
      try {
        result = await tryOllama(payload);
      } catch (e1) {
        console.warn("[gateway] ollama failed:", (e1 as Error).message);
        try {
          result = await tryOpenAI(payload);
        } catch (e2) {
          console.error("[gateway] both failed:", (e2 as Error).message);
          throw new Error("all-backends-failed");
        }
      }

      res.writeHead(200, {"content-type": "application/json"})
         .end(JSON.stringify(result));
    } catch (e) {
      res.writeHead(500, {"content-type": "application/json"})
         .end(JSON.stringify({ error: (e as Error).message }));
    }
    return;
  }

  if (req.method === "GET" && req.url === "/llm/health") {
    let status: any = { ollama: false, openai: !!OPENAI_KEY };
    try {
      const r = await fetch(`${OLLAMA}/api/version`, {
        method: "GET",
        signal: AbortSignal.timeout(3000)
      });
      status.ollama = r.ok;
    } catch {}
    res.writeHead(200, {"content-type": "application/json"})
       .end(JSON.stringify(status));
    return;
  }

  res.writeHead(404).end();
}).listen(process.env.LLM_GATEWAY_PORT || 4455, () => {
  console.log(`[llm-gateway] listening on :${process.env.LLM_GATEWAY_PORT || 4455}`);
});