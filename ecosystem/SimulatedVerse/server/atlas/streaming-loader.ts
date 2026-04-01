/**
 * 🗂️ Atlas Streaming Loader - Prime Codex Interface
 * SAGE Enhanced: Streaming access to 150MB assets/unicode/atlas.json
 * ΞNuSyQ-prime directive: Efficient symbol queries without memory overload
 */

import * as fs from 'fs';
import * as path from 'path';

interface UnicodeSymbol {
  cp: number;        // Code point
  ch: string;        // Character
  plane: number;     // Unicode plane
  block: string;     // Unicode block name
  cat: string;       // Category
  bidi: string;      // Bidirectional class
  combining: number; // Combining class
}

interface AtlasStats {
  count: number;
  size_mb: number;
  loaded_timestamp: number;
  streaming_active: boolean;
}

export class AtlasStreamingLoader {
  private atlasPath: string;
  private stats: AtlasStats | null = null;
  private symbolCache = new Map<number, UnicodeSymbol>();
  private blockCache = new Map<string, UnicodeSymbol[]>();
  private maxCacheSize = 10000; // Limit memory usage

  constructor() {
    this.atlasPath = path.join(process.cwd(), 'assets', 'unicode', 'atlas.json');
  }

  /**
   * Initialize and get atlas statistics without loading full file
   */
  async getStats(): Promise<AtlasStats> {
    if (this.stats) return this.stats;

    try {
      const fileStats = await fs.promises.stat(this.atlasPath);
      
      // Read just the first part to get count
      const stream = fs.createReadStream(this.atlasPath, { 
        encoding: 'utf8', 
        start: 0, 
        end: 500 
      });
      
      let header = '';
      for await (const chunk of stream) {
        header += chunk;
      }
      
      // Extract count from header
      const countMatch = header.match(/"count":\s*(\d+)/);
      const countValue = countMatch?.[1];
      const count = countValue ? parseInt(countValue, 10) : 974596;
      
      this.stats = {
        count,
        size_mb: Math.round(fileStats.size / (1024 * 1024)),
        loaded_timestamp: Date.now(),
        streaming_active: true
      };
      
      console.log(`[ATLAS] Prime Codex loaded: ${count} symbols, ${this.stats.size_mb}MB`);
      return this.stats;
    } catch (error) {
      console.error('[ATLAS] Failed to get stats:', error);
      return {
        count: 0,
        size_mb: 0,
        loaded_timestamp: Date.now(),
        streaming_active: false
      };
    }
  }

  /**
   * Find symbols by code point range (efficient for specific lookups)
   */
  async findByCodePoint(codePoint: number): Promise<UnicodeSymbol | null> {
    // Check cache first
    if (this.symbolCache.has(codePoint)) {
      return this.symbolCache.get(codePoint) || null;
    }

    try {
      // Stream through file to find specific code point
      const stream = fs.createReadStream(this.atlasPath, { encoding: 'utf8' });
      let buffer = '';
      let inAtlasArray = false;
      
      for await (const chunk of stream) {
        buffer += chunk;
        
        // Process complete objects
        if (buffer.includes('"atlas":')) {
          inAtlasArray = true;
        }
        
        if (inAtlasArray) {
          const symbols = this.extractSymbolsFromBuffer(buffer, codePoint);
          for (const symbol of symbols) {
            if (symbol.cp === codePoint) {
              this.cacheSymbol(symbol);
              return symbol;
            }
          }
        }
        
        // Keep last part of buffer for next iteration
        const lastBrace = buffer.lastIndexOf('}');
        if (lastBrace > 0) {
          buffer = buffer.substring(lastBrace);
        }
      }
      
      return null;
    } catch (error) {
      console.error('[ATLAS] Code point search failed:', error);
      return null;
    }
  }

  /**
   * Find symbols by Unicode block (e.g., "Basic Latin", "Mathematical Operators")
   */
  async findByBlock(blockName: string): Promise<UnicodeSymbol[]> {
    // Check cache first
    if (this.blockCache.has(blockName)) {
      return this.blockCache.get(blockName) || [];
    }

    try {
      const symbols: UnicodeSymbol[] = [];
      const stream = fs.createReadStream(this.atlasPath, { encoding: 'utf8' });
      let buffer = '';
      let inAtlasArray = false;
      
      for await (const chunk of stream) {
        buffer += chunk;
        
        if (buffer.includes('"atlas":')) {
          inAtlasArray = true;
        }
        
        if (inAtlasArray) {
          const blockSymbols = this.extractSymbolsFromBuffer(buffer, null, blockName);
          symbols.push(...blockSymbols);
        }
        
        // Keep buffer manageable
        const lastBrace = buffer.lastIndexOf('}');
        if (lastBrace > 0) {
          buffer = buffer.substring(lastBrace);
        }
      }
      
      // Cache result (limit cache size)
      if (symbols.length < 1000) { // Don't cache huge blocks
        this.blockCache.set(blockName, symbols);
        this.cleanupCache();
      }
      
      console.log(`[ATLAS] Found ${symbols.length} symbols in block: ${blockName}`);
      return symbols;
    } catch (error) {
      console.error('[ATLAS] Block search failed:', error);
      return [];
    }
  }

  /**
   * Search symbols by category (e.g., "assigned", "control", "format")
   */
  async findByCategory(category: string, limit: number = 100): Promise<UnicodeSymbol[]> {
    try {
      const symbols: UnicodeSymbol[] = [];
      const stream = fs.createReadStream(this.atlasPath, { encoding: 'utf8' });
      let buffer = '';
      let inAtlasArray = false;
      
      for await (const chunk of stream) {
        buffer += chunk;
        
        if (buffer.includes('"atlas":')) {
          inAtlasArray = true;
        }
        
        if (inAtlasArray) {
          const categorySymbols = this.extractSymbolsFromBuffer(buffer, null, null, category);
          symbols.push(...categorySymbols);
          
          // Stop when limit reached
          if (symbols.length >= limit) {
            break;
          }
        }
        
        const lastBrace = buffer.lastIndexOf('}');
        if (lastBrace > 0) {
          buffer = buffer.substring(lastBrace);
        }
      }
      
      console.log(`[ATLAS] Found ${symbols.length} symbols in category: ${category}`);
      return symbols.slice(0, limit);
    } catch (error) {
      console.error('[ATLAS] Category search failed:', error);
      return [];
    }
  }

  /**
   * Get random symbols for exploration/discovery
   */
  async getRandomSymbols(count: number = 20): Promise<UnicodeSymbol[]> {
    try {
      const stats = await this.getStats();
      const symbols: UnicodeSymbol[] = [];
      
      // Generate random positions in file
      const fileSize = stats.size_mb * 1024 * 1024;
      const positions = Array.from({ length: count * 3 }, () => Math.floor(Math.random() * fileSize));
      
      for (const position of positions) {
        const stream = fs.createReadStream(this.atlasPath, { 
          encoding: 'utf8',
          start: position,
          end: position + 2000 // Read small chunk
        });
        
        let buffer = '';
        for await (const chunk of stream) {
          buffer += chunk;
        }
        
        const extractedSymbols = this.extractSymbolsFromBuffer(buffer);
        symbols.push(...extractedSymbols);
        
        if (symbols.length >= count) break;
      }
      
      return symbols.slice(0, count);
    } catch (error) {
      console.error('[ATLAS] Random symbol generation failed:', error);
      return [];
    }
  }

  /**
   * Extract symbols from JSON buffer with optional filters
   */
  private extractSymbolsFromBuffer(
    buffer: string, 
    targetCodePoint?: number | null,
    targetBlock?: string | null,
    targetCategory?: string | null
  ): UnicodeSymbol[] {
    const symbols: UnicodeSymbol[] = [];
    
    try {
      // Find complete JSON objects in buffer
      const objectRegex = /\{[^{}]*"cp":\s*\d+[^{}]*\}/g;
      const matches = buffer.match(objectRegex);
      
      if (matches) {
        for (const match of matches) {
          try {
            const symbol = JSON.parse(match) as UnicodeSymbol;
            
            // Apply filters
            if (targetCodePoint !== null && symbol.cp !== targetCodePoint) continue;
            if (targetBlock && symbol.block !== targetBlock) continue;
            if (targetCategory && symbol.cat !== targetCategory) continue;
            
            symbols.push(symbol);
          } catch {
            // Skip malformed JSON
            continue;
          }
        }
      }
    } catch (error) {
      // Skip buffer processing errors
    }
    
    return symbols;
  }

  /**
   * Cache management
   */
  private cacheSymbol(symbol: UnicodeSymbol): void {
    if (this.symbolCache.size >= this.maxCacheSize) {
      // Remove oldest entries
      const entries = Array.from(this.symbolCache.entries());
      const toRemove = entries.slice(0, Math.floor(this.maxCacheSize * 0.2));
      toRemove.forEach(([key]) => this.symbolCache.delete(key));
    }
    
    this.symbolCache.set(symbol.cp, symbol);
  }

  private cleanupCache(): void {
    if (this.blockCache.size > 20) {
      const entries = Array.from(this.blockCache.entries());
      const toRemove = entries.slice(0, 5);
      toRemove.forEach(([key]) => this.blockCache.delete(key));
    }
  }

  /**
   * Health check for streaming system
   */
  async healthCheck(): Promise<{ ok: boolean; stats: AtlasStats | null; cache_size: number }> {
    try {
      const stats = await this.getStats();
      return {
        ok: stats.streaming_active,
        stats,
        cache_size: this.symbolCache.size + this.blockCache.size
      };
    } catch (error) {
      return {
        ok: false,
        stats: null,
        cache_size: 0
      };
    }
  }
}

// Export singleton instance
export const atlasLoader = new AtlasStreamingLoader();
