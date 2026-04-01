# Card Ω-5 — Semantic Memory MVP

**Goal**: Embed receipts & docs for smarter agent recall and context injection

**Priority**: MEDIUM - Enhanced agent intelligence and institutional memory

## Steps (≤8 edits)

- [ ] **1. Receipt Embedding**: Process all SystemDev/receipts/*.json for semantic search
- [ ] **2. Documentation Indexing**: Embed knowledge base, Rosetta docs, README files
- [ ] **3. Vector Storage**: Store embeddings with metadata for fast retrieval  
- [ ] **4. Semantic Search API**: Provide queryEmbeds(query) for agent context injection
- [ ] **5. Navigator Integration**: Connect semantic memory to Navigator decision-making
- [ ] **6. Council Context**: Inject relevant historical context into Council Breaths
- [ ] **7. Culture Memory**: Store Culture-Ship events and progression patterns
- [ ] **8. Performance Optimization**: Ensure mobile-friendly search and caching

## Memory Sources

```bash
# Embed existing receipts
tsx SystemDev/scripts/embedder.ts "$(cat SystemDev/receipts/*.json | jq -r '.details | tostring')"

# Process knowledge base
find . -name "*.md" -not -path "*/node_modules/*" | head -20

# Embed recent system events  
curl -s http://localhost:5000/api/ops/status | jq -r '.details'
```

## Vector Storage Implementation

```typescript
// SystemDev/scripts/memory.store.ts
import { embed } from "./embedder.js";
import fs from "node:fs";

interface MemoryDocument {
  id: string;
  content: string;
  vector: number[];
  metadata: {
    type: "receipt" | "doc" | "event";
    timestamp: string;
    breath?: string;
    quadrant?: string;
  };
}

class SemanticMemory {
  private documents: MemoryDocument[] = [];
  
  async ingest(content: string, metadata: any): Promise<string> {
    const result = await embed([content]);
    const doc: MemoryDocument = {
      id: generateId(),
      content,
      vector: result.vectors[0],
      metadata: { timestamp: new Date().toISOString(), ...metadata }
    };
    this.documents.push(doc);
    return doc.id;
  }
  
  async search(query: string, topK = 5): Promise<MemoryDocument[]> {
    const queryResult = await embed([query]);
    const queryVector = queryResult.vectors[0];
    
    return this.documents
      .map(doc => ({
        ...doc,
        similarity: cosineSimilarity(queryVector, doc.vector)
      }))
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, topK);
  }
}
```

## Agent Integration

```typescript
// Navigator context injection
async function enhanceNavigatorContext(currentState: any) {
  const memory = new SemanticMemory();
  
  // Search for relevant historical context
  const context = await memory.search(`
    Navigator decision making ${currentState.mode} 
    ${currentState.quadrant_focus.join(' ')} breath
  `);
  
  return {
    ...currentState,
    historical_context: context.map(doc => ({
      content: doc.content.slice(0, 200),
      relevance: doc.similarity,
      timestamp: doc.metadata.timestamp
    }))
  };
}
```

## Council Memory Integration

```typescript
// Enhance Council Breaths with relevant context
async function injectCouncilMemory(breath: string, state: any) {
  const relevantMemory = await semanticMemory.search(`
    ${breath} breath completion success patterns
    receipt details artifacts
  `, 3);
  
  return {
    ...state,
    memory_context: relevantMemory
  };
}
```

## Performance Optimization

```typescript
// Mobile-friendly caching and batching
class MobileOptimizedMemory {
  private cache = new Map<string, any>();
  private batchSize = 10; // Samsung S23 memory constraints
  
  async batchEmbed(texts: string[]): Promise<number[][]> {
    const results: number[][] = [];
    for (let i = 0; i < texts.length; i += this.batchSize) {
      const batch = texts.slice(i, i + this.batchSize);
      const batchResult = await embed(batch);
      results.push(...batchResult.vectors);
    }
    return results;
  }
}
```

## Success Criteria

✅ All SystemDev/receipts/ embedded and searchable  
✅ Knowledge base documents indexed with metadata  
✅ Semantic search returns relevant context for agent queries  
✅ Navigator decisions enhanced with historical context  
✅ Council Breaths inject relevant memory patterns  
✅ Mobile performance acceptable (≤2s search response)  
✅ Memory persistence survives system restarts

## Receipt Pattern

```json
{
  "breath": "semantic_memory_mvp",
  "ok": true,
  "details": {
    "documents_embedded": 156,
    "receipts_indexed": 47,
    "knowledge_docs_processed": 23,
    "search_latency_ms": 420,
    "navigator_integration": true,
    "council_context_injection": true
  },
  "ts": "ISO_TIMESTAMP",
  "edit_count": 6
}
```

## Commands

```bash
# Initialize semantic memory
tsx SystemDev/scripts/memory.store.ts init

# Test search functionality
tsx SystemDev/scripts/memory.store.ts search "Council graph execution success"

# Embed recent receipts
find SystemDev/receipts/ -name "*.json" -mtime -7 | xargs tsx SystemDev/scripts/memory.store.ts ingest

# Performance test
time tsx SystemDev/scripts/memory.store.ts search "Culture-Ship consciousness calculation"
```