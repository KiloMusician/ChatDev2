import type { Request, Response } from "express";
import { spawn } from "node:child_process";
import path from "node:path";

const PY = "python3";
const ROOT = process.cwd();

export function mlRouter(app: any) {
  // Train on demand
  app.post("/api/ml/train", (_req: Request, res: Response) => {
    const proc = spawn(PY, ["ml/pipelines/pu_ranker.py"], { cwd: ROOT });
    let out = ""; let err = "";
    proc.stdout.on("data", d => out += d.toString());
    proc.stderr.on("data", d => err += d.toString());
    proc.on("close", code => {
      res.json({ code, out, err });
    });
  });

  // Rank a batch of PUs (cheap heuristics if model missing)
  app.post("/api/ml/rank", async (req: Request, res: Response) => {
    const items = Array.isArray(req.body) ? req.body : [];
    try {
      // Fast path: call a tiny Python scorer if model exists, else heuristic
      const modelPath = path.join(ROOT, "ml/models/pu_ranker.pkl");
      const fs = await import("node:fs");
      if (fs.existsSync(modelPath)) {
        const p = spawn(PY, ["-c", `
import sys, json
from joblib import load
from features import featurize_pu
m=load("ml/models/pu_ranker.pkl")
raw=json.load(sys.stdin)
X=[list(featurize_pu(x).values()) for x in raw]
try:
    p=m.predict_proba(X)[:,1].tolist()
except:
    p=m.decision_function(X).tolist()
out=[{"score": float(s)} for s in p]
print(json.dumps(out))
        `], { cwd: ROOT });
        let buf=""; let err="";
        p.stdout.on("data", d=>buf+=d.toString());
        p.stderr.on("data", d=>err+=d.toString());
        p.stdin.write(JSON.stringify(items));
        p.stdin.end();
        p.on("close", _ => {
          try {
            res.json(JSON.parse(buf||"[]"));
          } catch {
            res.status(500).json({ error: "Model prediction failed", stderr: err });
          }
        });
      } else {
        // Heuristic fallback
        const scored = items.map((it: any) => {
          const title = `${it.title||""} ${it.desc||""}`.toLowerCase();
          let s = 0.0;
          if (title.includes("test")) s+=0.2;
          if (title.includes("perf")||title.includes("optimiz")) s+=0.2;
          if (title.includes("doc")||title.includes("readme")) s+=0.1;
          if ((it.priority||"").toLowerCase()==="critical") s+=0.3;
          return { score: Math.min(1, Math.max(0, s)) };
        });
        res.json(scored);
      }
    } catch (e:any) {
      res.status(500).json({ error: e?.message||String(e) });
    }
  });

  // Get ML system status  
  app.get("/api/ml/status", async (_req: Request, res: Response) => {
    const fs = await import("node:fs");
    const modelExists = fs.existsSync(path.join(ROOT, "ml/models/pu_ranker.pkl"));
    const traceFiles = fs.existsSync(path.join(ROOT, "ml/data/traces")) ? 
      fs.readdirSync(path.join(ROOT, "ml/data/traces")).filter(f => f.endsWith('.jsonl')).length : 0;
    
    // Check Ollama orchestration status
    let ollamaStatus = "offline";
    try {
      const { OllamaCoherenceManager } = await import("../../system/llm/ollama-orchestration/ollama-startup.js");
      const manager = OllamaCoherenceManager.getInstance();
      const status = manager.getStatus();
      ollamaStatus = status.running ? "operational" : "offline";
    } catch (error) {
      console.warn('[ML-STATUS] Ollama check failed:', error);
    }
    
    res.json({
      model_trained: modelExists,
      trace_files: traceFiles,
      ollama: ollamaStatus,
      endpoints: ["/api/ml/train", "/api/ml/rank", "/api/ml/status", "/api/ml/ollama/status", "/api/ml/ollama/generate"],
      status: "operational"
    });
  });

  // **OLLAMA ORCHESTRATION ENDPOINTS** - Local LLM Integration
  app.get("/api/ml/ollama/status", async (_req: Request, res: Response) => {
    try {
      // Direct status check via Ollama API
      const versionResponse = await fetch('http://localhost:11434/api/version');
      const tagsResponse = await fetch('http://localhost:11434/api/tags');
      
      const running = versionResponse.ok;
      const version = running ? (await versionResponse.json()).version : 'unknown';
      const models = running && tagsResponse.ok ? (await tagsResponse.json()).models || [] : [];
      
      // Calculate coherence based on service health
      let coherence = 0.0;
      if (running) coherence += 0.5;
      if (models.length > 0) coherence += 0.3;
      if (models.length >= 2) coherence += 0.2;
      
      res.json({
        running,
        models: models.map((m: any) => m.name),
        version,
        coherence: Math.min(coherence, 1.0),
        last_check: new Date().toISOString(),
        model_count: models.length,
        endpoints: ["/api/ml/ollama/status", "/api/ml/ollama/generate", "/api/ml/ollama/models"],
        infrastructure_first: true,
        local_first: true
      });
    } catch (error) {
      res.json({ 
        running: false,
        models: [],
        version: 'unknown',
        coherence: 0.0,
        last_check: new Date().toISOString(),
        model_count: 0,
        error: "Ollama service not accessible",
        detail: error instanceof Error ? error.message : String(error),
        infrastructure_first: true
      });
    }
  });

  app.post("/api/ml/ollama/generate", async (req: Request, res: Response) => {
    try {
      const { prompt, model = "qwen2.5:7b", options = {} } = req.body;
      if (!prompt) {
        return res.status(400).json({ error: "Prompt required" });
      }
      
      // Direct Ollama API call for maximum reliability
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model,
          prompt,
          stream: false,
          options: {
            temperature: options.temperature || 0.5,
            ...options
          }
        })
      });
      
      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status}`);
      }
      
      const result = await response.json();
      
      res.json({ 
        ok: true, 
        response: result.response,
        model: result.model,
        tokens: result.eval_count,
        duration: result.total_duration,
        local_first: true,
        infrastructure_first: true
      });
    } catch (error) {
      res.status(500).json({ 
        ok: false,
        error: "Ollama generation failed",
        detail: error instanceof Error ? error.message : String(error)
      });
    }
  });

  app.get("/api/ml/ollama/models", async (_req: Request, res: Response) => {
    try {
      // Direct Ollama API call for model list
      const response = await fetch('http://localhost:11434/api/tags');
      
      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      res.json({
        available: data.models || [],
        total: data.models?.length || 0,
        base_url: "http://localhost:11434",
        local_first: true,
        infrastructure_first: true,
        endpoints: ["/api/ml/ollama/status", "/api/ml/ollama/generate", "/api/ml/ollama/models"]
      });
    } catch (error) {
      res.status(500).json({ 
        error: "Failed to get Ollama models",
        detail: error instanceof Error ? error.message : String(error),
        available: [],
        total: 0
      });
    }
  });
}