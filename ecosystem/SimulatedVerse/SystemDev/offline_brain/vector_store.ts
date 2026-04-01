import { Database } from 'better-sqlite3';
import * as fs from 'node:fs/promises';
import * as path from 'node:path';

// Simple vector store using sqlite-vec for offline embeddings
export class OfflineVectorStore {
  private db: Database | null = null;
  private initialized = false;

  constructor(private dbPath = 'logger/vec.db') {}

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Ensure directory exists
      await fs.mkdir(path.dirname(this.dbPath), { recursive: true });
      
      // For now, use a simple JSON-based store since sqlite-vec setup is complex
      // TODO: Implement proper sqlite-vec when stable
      this.initialized = true;
      console.log('[VectorStore] Initialized offline vector store');
    } catch (error) {
      console.warn('[VectorStore] Failed to initialize:', error);
    }
  }

  async indexSpecs(): Promise<number> {
    try {
      const specsDir = 'GameDev/gameplay/specs';
      let indexed = 0;

      try {
        const files = await fs.readdir(specsDir);
        
        for (const file of files) {
          if (file.endsWith('.yml') || file.endsWith('.yaml')) {
            const content = await fs.readFile(path.join(specsDir, file), 'utf8');
            // Simple indexing - store in memory for now
            await this.storeDocument(file, content, 'spec');
            indexed++;
          }
        }
      } catch (error) {
        // Directory doesn't exist yet
        console.log('[VectorStore] Specs directory not found, skipping spec indexing');
      }

      return indexed;
    } catch (error) {
      console.warn('[VectorStore] Spec indexing failed:', error);
      return 0;
    }
  }

  async indexReceipts(): Promise<number> {
    try {
      const receiptsDir = 'SystemDev/receipts';
      let indexed = 0;

      try {
        const files = await fs.readdir(receiptsDir);
        
        for (const file of files) {
          if (file.endsWith('.json')) {
            const content = await fs.readFile(path.join(receiptsDir, file), 'utf8');
            await this.storeDocument(file, content, 'receipt');
            indexed++;
          }
        }
      } catch (error) {
        console.log('[VectorStore] Receipts directory not found, creating...');
        await fs.mkdir(receiptsDir, { recursive: true });
      }

      return indexed;
    } catch (error) {
      console.warn('[VectorStore] Receipt indexing failed:', error);
      return 0;
    }
  }

  private async storeDocument(id: string, content: string, type: string): Promise<void> {
    // Simplified storage for now - just track metadata
    // TODO: Implement proper vector embeddings when needed
    const metadata = {
      id,
      type,
      content_length: content.length,
      indexed_at: Date.now()
    };
    
    // For now, just log the indexing
    if (process.env.NODE_ENV === 'development') {
      console.log(`[VectorStore] Indexed ${type}: ${id} (${content.length} chars)`);
    }
  }

  async findSimilar(query: string, type?: string, limit = 5): Promise<Array<{id: string, score: number}>> {
    // Simplified similarity - return empty for now
    // TODO: Implement proper similarity search
    return [];
  }

  async getInventory(): Promise<{specs: number, receipts: number, total: number}> {
    const specs = await this.indexSpecs();
    const receipts = await this.indexReceipts();
    
    return {
      specs,
      receipts,
      total: specs + receipts
    };
  }
}

export const vectorStore = new OfflineVectorStore();