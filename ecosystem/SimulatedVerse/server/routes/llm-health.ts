import type { Request, Response } from "express";

export async function llmHealth(req: Request, res: Response) {
  const out: any = { 
    time: Date.now(), 
    backends: {} 
  };
  
  try {
    const r = await fetch(`${process.env.OLLAMA_HOST || "http://127.0.0.1:11434"}/api/version`, {
      method: "GET",
      signal: AbortSignal.timeout(3000)
    });
    out.backends.ollama = r.ok ? 'up' : `down_${r.status}`;
  } catch {
    out.backends.ollama = 'down';
  }
  
  out.backends.openai = process.env.OPENAI_API_KEY ? 'configured' : 'disabled';
  
  res.json({
    ok: (out.backends.ollama === 'up' || out.backends.openai === 'configured'),
    ollama: out.backends.ollama === 'up',
    openai: out.backends.openai === 'configured',
    ...out.backends
  });
}