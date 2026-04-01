// packages/yap/llmAdapter.ts
/**
 * Pluggable LLM adapter. By default, it's a no-op that returns `null`.
 * Wire your local LLM or API here and return a YapClassification[].
 */
import { YapLog, YapClassification, YapTag } from "./types";

export async function llmClassify(_log: YapLog): Promise<YapClassification[] | null> {
  const endpoint = process.env.YAP_LLM_ENDPOINT;
  const enabled = process.env.YAP_LLM_ENABLED !== "false";
  if (!enabled || !endpoint) return null;

  const provider = process.env.YAP_LLM_PROVIDER || "generic";
  const timeoutMs = Number(process.env.YAP_LLM_TIMEOUT_MS || 1200);

  if (typeof fetch !== "function") return null;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    if (provider === "ollama") {
      const model = process.env.YAP_LLM_MODEL || "qwen2.5-coder";
      const prompt = [
        "Classify this log into labels. Respond with JSON: {\"labels\":[\"label\"],\"reasons\":[\"...\"]}.",
        `level: ${_log.level}`,
        `source: ${_log.source}`,
        `message: ${_log.message}`
      ].join("\n");

      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ model, prompt, stream: false }),
        signal: controller.signal
      });
      if (!response.ok) return null;
      const data = await response.json();
      const raw = typeof data?.response === "string" ? data.response : JSON.stringify(data);
      const extracted = extractJson(raw);
      return normalizeLLMResponse(extracted);
    }

    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ log: _log }),
      signal: controller.signal
    });
    if (!response.ok) return null;
    const data = await response.json();
    return normalizeLLMResponse(data);
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function normalizeLLMResponse(data: any): YapClassification[] | null {
  if (!data) return null;

  if (Array.isArray(data)) {
    return data.map((item) => toClassification(item)).filter(Boolean) as YapClassification[];
  }

  if (Array.isArray(data.classes)) {
    return data.classes.map((item: any) => toClassification(item)).filter(Boolean) as YapClassification[];
  }

  if (Array.isArray(data.labels)) {
    return data.labels.map((label: string) => ({
      label,
      score: 0.5,
      tags: [] as YapTag[],
      reasons: Array.isArray(data.reasons) ? data.reasons : []
    }));
  }

  return null;
}

function toClassification(item: any): YapClassification | null {
  if (!item) return null;
  if (typeof item === "string") {
    return { label: item, score: 0.5, tags: [], reasons: [] };
  }
  if (typeof item.label === "string") {
    return {
      label: item.label,
      score: typeof item.score === "number" ? item.score : 0.5,
      tags: Array.isArray(item.tags) ? item.tags : [],
      reasons: Array.isArray(item.reasons) ? item.reasons : []
    };
  }
  return null;
}

function extractJson(text: string): any | null {
  const match = text.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
  if (!match) return null;
  try {
    return JSON.parse(match[0]);
  } catch {
    return null;
  }
}
