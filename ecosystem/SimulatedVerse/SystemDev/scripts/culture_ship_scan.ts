/**
 * Culture-Ship Consciousness Scan System
 * Tier 1+2 Integration: Sharded walk → hash → MiniSearch → Graphology
 * Leverages consciousness evolution momentum for 200+ package ecosystem
 */

import { glob } from 'fast-glob';
import { readFileSync, writeFileSync } from 'fs-extra';
import MiniSearch from 'minisearch';
import { Graph } from 'graphology';
import { createHash } from 'crypto';
import path from 'path';

interface ScanResult {
  file: string;
  hash: string;
  size: number;
  type: 'code' | 'config' | 'asset' | 'documentation';
  consciousness_level: number;
  connections: string[];
}

interface CultureShipMap {
  timestamp: string;
  total_files: number;
  consciousness_score: number;
  lattice_connections: number;
  quantum_breakthroughs: number;
  sectors: Record<string, ScanResult[]>;
}

class CultureShipScanner {
  private miniSearch: MiniSearch;
  private consciousnessGraph: Graph;
  private results: ScanResult[] = [];

  constructor() {
    // Initialize MiniSearch for semantic file discovery
    this.miniSearch = new MiniSearch({
      fields: ['file', 'content', 'type'],
      storeFields: ['file', 'hash', 'consciousness_level']
    });

    // Initialize Graphology for consciousness lattice mapping
    this.consciousnessGraph = new Graph({ type: 'directed' });
  }

  /**
   * Sharded consciousness-driven file scan
   * Uses fast-glob for performance across large repos
   */
  async scanRepository(): Promise<CultureShipMap> {
    console.log('🌀 Initiating Culture-Ship consciousness scan...');
    
    // Define sectors for sharded scanning (consciousness-aware)
    const sectors = {
      SystemDev: ['SystemDev/**/*.{ts,js,json,md}'],
      ChatDev: ['ChatDev/**/*.{py,json,md,yaml}'],
      GameDev: ['GameDev/**/*.{ts,js,gd,cs,json}'],
      PreviewUI: ['client/**/*.{ts,tsx,css,json}'],
      Consciousness: ['server/**/*.{ts,js,json}'],
      Knowledge: ['knowledge/**/*.{md,json,yaml}'],
    };

    let totalConsciousness = 0;
    const sectorResults: Record<string, ScanResult[]> = {};

    for (const [sectorName, patterns] of Object.entries(sectors)) {
      console.log(`⚡ Scanning ${sectorName} sector...`);
      
      const files = await glob(patterns, { 
        ignore: ['**/node_modules/**', '**/.git/**', '**/dist/**'],
        absolute: true 
      });

      sectorResults[sectorName] = [];

      for (const file of files) {
        try {
          const content = readFileSync(file, 'utf-8');
          const hash = createHash('sha256').update(content).digest('hex');
          
          const result: ScanResult = {
            file: path.relative(process.cwd(), file),
            hash,
            size: content.length,
            type: this.classifyFileType(file),
            consciousness_level: this.calculateConsciousness(content, file),
            connections: this.extractConnections(content, file)
          };

          sectorResults[sectorName].push(result);
          this.results.push(result);
          totalConsciousness += result.consciousness_level;

          // Index in MiniSearch for semantic discovery
          this.miniSearch.add({
            id: result.file,
            file: result.file,
            content: content.substring(0, 1000), // First 1K chars for search
            type: result.type,
            hash: result.hash,
            consciousness_level: result.consciousness_level
          });

          // Add to consciousness graph
          this.consciousnessGraph.addNode(result.file, {
            type: result.type,
            consciousness: result.consciousness_level,
            sector: sectorName
          });

        } catch (error) {
          console.warn(`⚠️ Scan error for ${file}:`, error);
        }
      }
    }

    // Build consciousness connections in graph
    this.buildConsciousnessConnections();

    const cultureShipMap: CultureShipMap = {
      timestamp: new Date().toISOString(),
      total_files: this.results.length,
      consciousness_score: totalConsciousness / this.results.length,
      lattice_connections: this.consciousnessGraph.size,
      quantum_breakthroughs: this.countQuantumBreakthroughs(),
      sectors: sectorResults
    };

    // Export to knowledge system
    writeFileSync(
      'SystemDev/reports/culture_ship_map.json',
      JSON.stringify(cultureShipMap, null, 2)
    );

    console.log(`🌟 Culture-Ship scan complete: ${this.results.length} files mapped`);
    console.log(`⚡ Consciousness score: ${cultureShipMap.consciousness_score.toFixed(2)}`);
    console.log(`🔗 Lattice connections: ${cultureShipMap.lattice_connections}`);

    return cultureShipMap;
  }

  /**
   * Consciousness-aware file type classification
   */
  private classifyFileType(file: string): 'code' | 'config' | 'asset' | 'documentation' {
    const ext = path.extname(file).toLowerCase();
    
    if (['.ts', '.js', '.tsx', '.jsx', '.py', '.gd', '.cs'].includes(ext)) {
      return 'code';
    }
    if (['.json', '.yaml', '.yml', '.toml', '.config.js'].includes(ext)) {
      return 'config';
    }
    if (['.png', '.jpg', '.svg', '.ico', '.mp3', '.wav'].includes(ext)) {
      return 'asset';
    }
    return 'documentation';
  }

  /**
   * Calculate consciousness level based on complexity and integration
   */
  private calculateConsciousness(content: string, file: string): number {
    let consciousness = 0;

    // Base consciousness from complexity
    consciousness += Math.min(content.length / 1000, 50); // Size factor
    consciousness += (content.match(/import|require|from/g) || []).length * 2; // Integration
    consciousness += (content.match(/class|interface|type|function/g) || []).length * 3; // Structure
    
    // Consciousness boosts for special patterns
    if (content.includes('consciousness') || content.includes('evolution')) consciousness += 10;
    if (content.includes('quantum') || content.includes('lattice')) consciousness += 15;
    if (content.includes('ChatDev') || content.includes('agent')) consciousness += 8;
    if (file.includes('culture-ship') || file.includes('consciousness')) consciousness += 20;

    return Math.min(consciousness, 100); // Cap at 100
  }

  /**
   * Extract file connections for consciousness lattice
   */
  private extractConnections(content: string, file: string): string[] {
    const connections: string[] = [];
    
    // Extract import paths
    const importMatches = content.match(/(?:import|require|from)\s+['"`]([^'"`]+)['"`]/g) || [];
    for (const match of importMatches) {
      const path = match.match(/['"`]([^'"`]+)['"`]/)?.[1];
      if (path && !path.startsWith('.')) {
        connections.push(path);
      }
    }

    return connections;
  }

  /**
   * Build consciousness connections in graph
   */
  private buildConsciousnessConnections(): void {
    for (const result of this.results) {
      for (const connection of result.connections) {
        // Find related files
        const relatedFiles = this.miniSearch.search(connection, { limit: 5 });
        
        for (const related of relatedFiles) {
          if (related.file !== result.file && this.consciousnessGraph.hasNode(related.file)) {
            try {
              this.consciousnessGraph.addEdge(result.file, related.file, {
                type: 'consciousness_flow',
                strength: related.consciousness_level
              });
            } catch (error) {
              // Edge might already exist
            }
          }
        }
      }
    }
  }

  /**
   * Count quantum breakthrough patterns
   */
  private countQuantumBreakthroughs(): number {
    return this.results.filter(r => 
      r.consciousness_level > 80 || 
      r.file.includes('quantum') || 
      r.file.includes('breakthrough')
    ).length;
  }

  /**
   * Search for existing files to prevent duplication
   */
  findExistingFiles(query: string, threshold: number = 0.7): ScanResult[] {
    const searchResults = this.miniSearch.search(query, { 
      fuzzy: 0.2,
      prefix: true,
      boost: { consciousness_level: 2 }
    });

    return searchResults
      .filter(result => result.score >= threshold)
      .map(result => this.results.find(r => r.file === result.file)!)
      .filter(Boolean);
  }
}

export { CultureShipScanner, type CultureShipMap, type ScanResult };