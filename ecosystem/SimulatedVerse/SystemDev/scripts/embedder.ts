#!/usr/bin/env tsx
/**
 * Embeddings with cloud→local fallback — Culture-Ship semantic memory
 * Strategy: OpenAI embeddings → local fallback → hash fallback (keeps pipelines alive)
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import pino from "pino";

const logger = pino({ level: 'info' });

// Embedding configuration
const OPENAI_MODEL = process.env.OPENAI_EMBED ?? "text-embedding-3-small";
const CACHE_DIR = "SystemDev/cache/embeddings";
const MAX_TOKENS = 8000; // Conservative limit for embeddings

fs.mkdirSync(CACHE_DIR, { recursive: true });

export interface EmbeddingResult {
  vectors: number[][];
  method: "openai" | "local" | "hash";
  model: string;
  cached: boolean;
  timestamp: string;
}

/**
 * Multi-tier embedding strategy with graceful fallbacks
 */
export async function embed(texts: string[]): Promise<EmbeddingResult> {
  if (texts.length === 0) {
    return {
      vectors: [],
      method: "hash",
      model: "none",
      cached: false,
      timestamp: new Date().toISOString()
    };
  }

  // Check cache first
  const cacheKey = generateCacheKey(texts);
  const cached = await getCachedEmbedding(cacheKey);
  if (cached) {
    logger.info(`📚 Embeddings cache hit: ${texts.length} texts`);
    return cached;
  }

  // Tier 1: OpenAI embeddings (best quality)
  if (process.env.OPENAI_API_KEY && texts.every(t => estimateTokens(t) < MAX_TOKENS)) {
    try {
      const vectors = await getOpenAIEmbeddings(texts);
      const result: EmbeddingResult = {
        vectors,
        method: "openai",
        model: OPENAI_MODEL,
        cached: false,
        timestamp: new Date().toISOString()
      };
      
      await setCachedEmbedding(cacheKey, result);
      logger.info(`🤖 OpenAI embeddings: ${texts.length} texts, ${vectors[0]?.length || 0}D`);
      return result;
    } catch (error) {
      logger.warn("OpenAI embeddings failed, falling back:", error);
    }
  }

  // Tier 2: Local ONNX model (future enhancement)
  // TODO: Implement when onnxruntime-node is available
  // if (fs.existsSync("models/all-minilm-l6-v2.onnx")) { ... }

  // Tier 3: Hash-based fallback (keeps pipelines alive)
  logger.info(`🔢 Hash-based embeddings fallback: ${texts.length} texts`);
  const vectors = texts.map(text => hashToVector(text, 384)); // Standard embedding dimension
  
  const result: EmbeddingResult = {
    vectors,
    method: "hash", 
    model: "hash-384d",
    cached: false,
    timestamp: new Date().toISOString()
  };
  
  await setCachedEmbedding(cacheKey, result);
  return result;
}

/**
 * OpenAI embeddings with proper error handling
 */
async function getOpenAIEmbeddings(texts: string[]): Promise<number[][]> {
  // Dynamic import to handle missing openai package gracefully
  let OpenAI;
  try {
    const openaiModule = await import("openai");
    OpenAI = openaiModule.OpenAI;
  } catch {
    throw new Error("OpenAI package not available");
  }

  const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
  
  // Batch processing for large text arrays
  const batchSize = 100;
  const allVectors: number[][] = [];
  
  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    const response = await client.embeddings.create({ 
      model: OPENAI_MODEL, 
      input: batch 
    });
    
    const vectors = response.data.map(d => d.embedding);
    allVectors.push(...vectors);
  }
  
  return allVectors;
}

/**
 * Deterministic hash-based embeddings (fallback)
 */
function hashToVector(text: string, dimensions: number): number[] {
  const hash = crypto.createHash('sha256').update(text).digest();
  const vector: number[] = [];
  
  for (let i = 0; i < dimensions; i++) {
    const byteIndex = i % hash.length;
    const value = (hash[byteIndex] / 255) * 2 - 1; // Normalize to [-1, 1]
    vector.push(value);
  }
  
  // Normalize to unit vector
  const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
  return magnitude > 0 ? vector.map(val => val / magnitude) : vector;
}

/**
 * Token estimation for text
 */
function estimateTokens(text: string): number {
  // Rough approximation: 1 token ≈ 4 characters for English
  return Math.ceil(text.length / 4);
}

/**
 * Cache management
 */
function generateCacheKey(texts: string[]): string {
  const combined = texts.join('\n');
  return crypto.createHash('md5').update(combined).digest('hex');
}

async function getCachedEmbedding(key: string): Promise<EmbeddingResult | null> {
  try {
    const cachePath = path.join(CACHE_DIR, `${key}.json`);
    if (fs.existsSync(cachePath)) {
      const cached = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      
      // Check cache age (24 hour TTL)
      const age = Date.now() - new Date(cached.timestamp).getTime();
      if (age < 24 * 60 * 60 * 1000) {
        return { ...cached, cached: true };
      }
    }
  } catch (error) {
    logger.warn("Cache read failed:", error);
  }
  return null;
}

async function setCachedEmbedding(key: string, result: EmbeddingResult): Promise<void> {
  try {
    const cachePath = path.join(CACHE_DIR, `${key}.json`);
    fs.writeFileSync(cachePath, JSON.stringify(result, null, 2));
  } catch (error) {
    logger.warn("Cache write failed:", error);
  }
}

/**
 * Semantic search functionality
 */
export async function semanticSearch(query: string, documents: string[], topK: number = 5): Promise<Array<{text: string, score: number, index: number}>> {
  const queryEmbedding = await embed([query]);
  const docEmbeddings = await embed(documents);
  
  const results = documents.map((doc, index) => ({
    text: doc,
    score: cosineSimilarity(queryEmbedding.vectors[0], docEmbeddings.vectors[index]),
    index
  }));
  
  return results
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

/**
 * Cosine similarity calculation
 */
function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;
  
  const dotProduct = a.reduce((sum, val, i) => sum + val * b[i], 0);
  const magnitudeA = Math.sqrt(a.reduce((sum, val) => sum + val * val, 0));
  const magnitudeB = Math.sqrt(b.reduce((sum, val) => sum + val * val, 0));
  
  return magnitudeA && magnitudeB ? dotProduct / (magnitudeA * magnitudeB) : 0;
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
  const texts = process.argv.slice(2);
  if (texts.length === 0) {
    console.log("Usage: tsx embedder.ts <text1> [text2] ...");
    process.exit(1);
  }
  
  embed(texts).then(result => {
    console.log(JSON.stringify(result, null, 2));
  }).catch(console.error);
}