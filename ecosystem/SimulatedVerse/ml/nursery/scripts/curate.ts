#!/usr/bin/env tsx
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { z } from 'zod';

// **Data Schemas**
const EventRow = z.object({
  t: z.number(),
  kind: z.string(), 
  data: z.record(z.any()),
  redacted: z.boolean().default(false)
});

const ErrorRow = z.object({
  t: z.number(),
  error: z.string(),
  stack: z.string().optional(),
  context: z.record(z.any()).default({}),
  redacted: z.boolean().default(false)
});

const EditRow = z.object({
  t: z.number(),
  before: z.string(),
  after: z.string(), 
  file: z.string(),
  summary: z.string().optional(),
  redacted: z.boolean().default(false)
});

// **PII Redaction Patterns**
const PII_PATTERNS = [
  /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, // emails
  /\b[A-Za-z0-9]{20,}\b/g, // likely API keys
  /\/home\/[^\/\s]+/g, // home paths
  /\/Users\/[^\/\s]+/g, // user paths
  /\b(?:\d{1,3}\.){3}\d{1,3}\b/g // IP addresses
];

function redactPII(text: string): string {
  let result = text;
  for (const pattern of PII_PATTERNS) {
    result = result.replace(pattern, '[REDACTED]');
  }
  return result;
}

function loadJSONL<T>(path: string, schema: z.ZodType<T>): T[] {
  if (!existsSync(path)) return [];
  
  const lines = readFileSync(path, 'utf8').trim().split('\n').filter(Boolean);
  const results: T[] = [];
  
  for (const line of lines) {
    try {
      const parsed = JSON.parse(line);
      const validated = schema.parse(parsed);
      results.push(validated);
    } catch (error) {
      console.warn(`[CURATE] Skipped invalid line in ${path}:`, error);
    }
  }
  
  return results;
}

function saveJSONL<T>(path: string, data: T[]): void {
  const lines = data.map(item => JSON.stringify(item)).join('\n');
  writeFileSync(path, lines + '\n');
}

// **Stratified Sampling**
function stratifiedSplit<T extends { kind?: string }>(
  data: T[], 
  trainRatio = 0.7, 
  devRatio = 0.15
): { train: T[], dev: T[], test: T[] } {
  // Group by kind for stratification
  const byKind = new Map<string, T[]>();
  for (const item of data) {
    const kind = item.kind || 'unknown';
    if (!byKind.has(kind)) byKind.set(kind, []);
    byKind.get(kind)!.push(item);
  }
  
  const train: T[] = [];
  const dev: T[] = [];
  const test: T[] = [];
  
  for (const [kind, items] of byKind) {
    // Shuffle items
    const shuffled = [...items].sort(() => Math.random() - 0.5);
    
    const trainCount = Math.floor(shuffled.length * trainRatio);
    const devCount = Math.floor(shuffled.length * devRatio);
    
    train.push(...shuffled.slice(0, trainCount));
    dev.push(...shuffled.slice(trainCount, trainCount + devCount));
    test.push(...shuffled.slice(trainCount + devCount));
  }
  
  return { train, dev, test };
}

// **Main Curation Function**
export async function curate() {
  console.log('[CURATE] Starting dataset curation...');
  
  // Load raw data
  const events = loadJSONL('ml/nursery/datasets/events.jsonl', EventRow);
  const errors = loadJSONL('ml/nursery/datasets/errors.jsonl', ErrorRow);
  const edits = loadJSONL('ml/nursery/datasets/edits.jsonl', EditRow);
  
  console.log(`[CURATE] Loaded ${events.length} events, ${errors.length} errors, ${edits.length} edits`);
  
  // Redact PII
  const redactedEvents = events.map(e => ({
    ...e,
    data: Object.fromEntries(
      Object.entries(e.data).map(([k, v]) => [k, typeof v === 'string' ? redactPII(v) : v])
    ),
    redacted: true
  }));
  
  const redactedErrors = errors.map(e => ({
    ...e,
    error: redactPII(e.error),
    stack: e.stack ? redactPII(e.stack) : undefined,
    redacted: true
  }));
  
  const redactedEdits = edits.map(e => ({
    ...e,
    before: redactPII(e.before),
    after: redactPII(e.after),
    file: redactPII(e.file),
    redacted: true
  }));
  
  // Create splits
  const eventSplits = stratifiedSplit(redactedEvents);
  const errorSplits = stratifiedSplit(redactedErrors.map(e => ({ ...e, kind: 'error' })));
  const editSplits = stratifiedSplit(redactedEdits.map(e => ({ ...e, kind: 'edit' })));
  
  // Save splits
  saveJSONL('ml/nursery/datasets/train_events.jsonl', eventSplits.train);
  saveJSONL('ml/nursery/datasets/dev_events.jsonl', eventSplits.dev);
  saveJSONL('ml/nursery/datasets/test_events.jsonl', eventSplits.test);
  
  saveJSONL('ml/nursery/datasets/train_errors.jsonl', errorSplits.train);
  saveJSONL('ml/nursery/datasets/dev_errors.jsonl', errorSplits.dev);
  saveJSONL('ml/nursery/datasets/test_errors.jsonl', errorSplits.test);
  
  saveJSONL('ml/nursery/datasets/train_edits.jsonl', editSplits.train);
  saveJSONL('ml/nursery/datasets/dev_edits.jsonl', editSplits.dev);
  saveJSONL('ml/nursery/datasets/test_edits.jsonl', editSplits.test);
  
  console.log('[Msg⛛{CURATE}] Nursery curation operational');
  console.log(`[CURATE] Events: ${eventSplits.train.length}/${eventSplits.dev.length}/${eventSplits.test.length}`);
  console.log(`[CURATE] Errors: ${errorSplits.train.length}/${errorSplits.dev.length}/${errorSplits.test.length}`);
  console.log(`[CURATE] Edits: ${editSplits.train.length}/${editSplits.dev.length}/${editSplits.test.length}`);
}

// CLI usage
if (import.meta.url === `file://${process.argv[1]}`) {
  curate().catch(console.error);
}