import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';

interface CodeChunk {
  file: string;
  content: string;
  embedding?: number[];
  metadata: {
    size: number;
    type: string;
    lastModified: number;
  };
}

let codeIndex: CodeChunk[] = [];
const EMBED_MODEL = process.env.EMBED_MODEL || 'nomic-embed-text';

export async function indexRepository() {
  console.log('[RepoPilot] Building repository index...');
  
  const startTime = Date.now();
  codeIndex = [];
  
  // Define which files to index
  const indexPaths = [
    'apps',
    'shared',
    'clients',
    'server',
    'client/src',
    'package.json',
    'Makefile',
    'replit.md'
  ];
  
  // Collect all files
  for (const indexPath of indexPaths) {
    if (fs.existsSync(indexPath)) {
      await indexPath.includes('.') ? indexFile(indexPath) : indexDirectory(indexPath);
    }
  }
  
  console.log(`[RepoPilot] Indexed ${codeIndex.length} files in ${Date.now() - startTime}ms`);
}

async function indexDirectory(dirPath: string) {
  const files = fs.readdirSync(dirPath, { withFileTypes: true });
  
  for (const file of files) {
    const fullPath = path.join(dirPath, file.name);
    
    if (file.isDirectory()) {
      // Skip node_modules, .git, dist, etc.
      if (!['node_modules', '.git', 'dist', 'build', '.next'].includes(file.name)) {
        await indexDirectory(fullPath);
      }
    } else if (file.isFile()) {
      await indexFile(fullPath);
    }
  }
}

async function indexFile(filePath: string) {
  try {
    const ext = path.extname(filePath);
    
    // Only index relevant file types
    const relevantExtensions = ['.ts', '.tsx', '.js', '.jsx', '.json', '.md', '.yml', '.yaml', '.txt'];
    if (!relevantExtensions.includes(ext) && !filePath.includes('Makefile')) {
      return;
    }
    
    const stats = fs.statSync(filePath);
    
    // Skip very large files
    if (stats.size > 100000) { // 100KB limit
      console.log(`[RepoPilot] Skipping large file: ${filePath}`);
      return;
    }
    
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Split large files into chunks
    const chunks = splitIntoChunks(content, 2000); // 2KB chunks
    
    for (let i = 0; i < chunks.length; i++) {
      const chunk: CodeChunk = {
        file: chunks.length > 1 ? `${filePath}#chunk${i + 1}` : filePath,
        content: chunks[i],
        metadata: {
          size: chunks[i].length,
          type: ext || 'text',
          lastModified: stats.mtime.getTime()
        }
      };
      
      // Generate embedding (optional - can be expensive)
      if (process.env.ENABLE_EMBEDDINGS === 'true') {
        chunk.embedding = await generateEmbedding(chunks[i]);
      }
      
      codeIndex.push(chunk);
    }
  } catch (error) {
    console.error(`[RepoPilot] Error indexing ${filePath}:`, error);
  }
}

function splitIntoChunks(content: string, maxSize: number): string[] {
  if (content.length <= maxSize) {
    return [content];
  }
  
  const chunks: string[] = [];
  const lines = content.split('\n');
  let currentChunk = '';
  
  for (const line of lines) {
    if (currentChunk.length + line.length + 1 > maxSize && currentChunk.length > 0) {
      chunks.push(currentChunk.trim());
      currentChunk = line;
    } else {
      currentChunk += (currentChunk.length > 0 ? '\n' : '') + line;
    }
  }
  
  if (currentChunk.trim().length > 0) {
    chunks.push(currentChunk.trim());
  }
  
  return chunks;
}

async function generateEmbedding(text: string): Promise<number[]> {
  try {
    // Use Ollama to generate embeddings
    const result = spawnSync('ollama', ['embeddings', EMBED_MODEL], {
      input: text,
      encoding: 'utf8',
      timeout: 10000
    });
    
    if (result.status === 0) {
      const embedding = JSON.parse(result.stdout.trim());
      return embedding.embedding || [];
    }
  } catch (error) {
    console.error('[RepoPilot] Embedding error:', error);
  }
  
  return [];
}

export async function searchContext(query: string, limit: number = 5): Promise<CodeChunk[]> {
  if (codeIndex.length === 0) {
    console.log('[RepoPilot] Index empty, rebuilding...');
    await indexRepository();
  }
  
  // Simple keyword-based search (can be enhanced with embeddings)
  const queryWords = query.toLowerCase().split(/\s+/);
  
  const results = codeIndex
    .map(chunk => ({
      chunk,
      score: calculateRelevanceScore(chunk, queryWords)
    }))
    .filter(result => result.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(result => result.chunk);
  
  return results;
}

function calculateRelevanceScore(chunk: CodeChunk, queryWords: string[]): number {
  const content = chunk.content.toLowerCase();
  const filename = chunk.file.toLowerCase();
  
  let score = 0;
  
  for (const word of queryWords) {
    // Filename matches are weighted higher
    if (filename.includes(word)) {
      score += 10;
    }
    
    // Content matches
    const matches = (content.match(new RegExp(word, 'g')) || []).length;
    score += matches * 2;
    
    // Exact phrase matches get bonus
    if (content.includes(queryWords.join(' '))) {
      score += 20;
    }
  }
  
  // Boost for certain file types
  if (chunk.file.endsWith('.ts') || chunk.file.endsWith('.tsx')) {
    score *= 1.2;
  }
  
  if (chunk.file.includes('types') || chunk.file.includes('schema')) {
    score *= 1.1;
  }
  
  // Penalize very large chunks
  if (chunk.content.length > 5000) {
    score *= 0.8;
  }
  
  return score;
}

// Export for debugging
export function getIndexStats() {
  const stats = {
    totalChunks: codeIndex.length,
    totalSize: codeIndex.reduce((sum, chunk) => sum + chunk.metadata.size, 0),
    fileTypes: {} as Record<string, number>,
    lastIndexed: Math.max(...codeIndex.map(chunk => chunk.metadata.lastModified))
  };
  
  codeIndex.forEach(chunk => {
    const type = chunk.metadata.type;
    stats.fileTypes[type] = (stats.fileTypes[type] || 0) + 1;
  });
  
  return stats;
}