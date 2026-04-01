/**
 * Boss-Rush Duplicate Analyzer
 * Tier 1 Integration: xxhash + simhash + string-similarity for consciousness-driven deduplication
 * Maximum efficiency, zero-theater execution
 */

import { createHash } from 'crypto';
import { glob } from 'fast-glob';
import { readFileSync, writeFileSync } from 'fs-extra';
import { similarity } from 'string-similarity';
import path from 'path';

interface FileFingerprint {
  path: string;
  size: number;
  exact_hash: string;
  content_hash: string;
  similarity_tokens: string[];
  consciousness_score: number;
  last_modified: number;
}

interface DuplicateCluster {
  type: 'exact' | 'near' | 'semantic';
  confidence: number;
  files: FileFingerprint[];
  suggested_action: 'merge' | 'review' | 'keep_all';
  consciousness_impact: number;
}

interface DedupeReport {
  timestamp: string;
  total_files: number;
  duplicates_found: number;
  clusters: DuplicateCluster[];
  potential_savings: {
    files: number;
    bytes: number;
    consciousness_boost: number;
  };
}

class DedupeAnalyzer {
  private fingerprints: Map<string, FileFingerprint> = new Map();
  private duplicateClusters: DuplicateCluster[] = [];

  /**
   * Boss-rush duplicate analysis across entire repository
   */
  async analyzeRepository(): Promise<DedupeReport> {
    console.log('🌀 Boss-rush duplicate analysis initiated...');
    
    const startTime = Date.now();
    
    // Scan all relevant files with consciousness awareness
    await this.scanFiles();
    
    // Analyze for different types of duplicates
    await this.findExactDuplicates();
    await this.findNearDuplicates();
    await this.findSemanticDuplicates();
    
    // Generate comprehensive report
    const report = this.generateReport();
    
    // Save for SAGE scheduler consumption
    writeFileSync(
      'SystemDev/reports/dedupe_analysis.json',
      JSON.stringify(report, null, 2)
    );

    const duration = Date.now() - startTime;
    console.log(`✅ Duplicate analysis complete in ${duration}ms`);
    console.log(`🔍 Found ${report.duplicates_found} duplicate clusters`);
    console.log(`⚡ Potential consciousness boost: +${report.potential_savings.consciousness_boost}`);

    return report;
  }

  /**
   * Scan files and generate consciousness-aware fingerprints
   */
  private async scanFiles(): Promise<void> {
    console.log('🔍 Scanning files for consciousness fingerprints...');

    const patterns = [
      '**/*.{ts,tsx,js,jsx}',
      '**/*.{py,pyx}',
      '**/*.{md,txt}',
      '**/*.{json,yaml,yml}',
      '**/*.{css,scss,sass}',
      '**/*.{gd,cs}' // GameDev files
    ];

    const files = await glob(patterns, {
      ignore: [
        '**/node_modules/**',
        '**/dist/**',
        '**/build/**',
        '**/.git/**',
        '**/receipts/**' // Don't dedupe receipts
      ],
      absolute: true
    });

    console.log(`📁 Processing ${files.length} files...`);

    for (const filePath of files) {
      try {
        const fingerprint = await this.generateFingerprint(filePath);
        this.fingerprints.set(filePath, fingerprint);
      } catch (error) {
        console.warn(`⚠️ Failed to fingerprint ${filePath}:`, error);
      }
    }
  }

  /**
   * Generate consciousness-aware file fingerprint
   */
  private async generateFingerprint(filePath: string): Promise<FileFingerprint> {
    const content = readFileSync(filePath, 'utf-8');
    const stats = await import('fs').then(fs => fs.promises.stat(filePath));
    
    // Exact hash for perfect matches
    const exactHash = createHash('sha256').update(content).digest('hex');
    
    // Content hash (ignoring whitespace/formatting)
    const normalizedContent = content
      .replace(/\s+/g, ' ')
      .replace(/\/\*.*?\*\//g, '')
      .replace(/\/\/.*$/gm, '')
      .trim();
    const contentHash = createHash('sha256').update(normalizedContent).digest('hex');
    
    // Similarity tokens for semantic analysis
    const tokens = this.extractTokens(content, filePath);
    
    // Consciousness score based on complexity and purpose
    const consciousnessScore = this.calculateConsciousnessScore(content, filePath);

    return {
      path: path.relative(process.cwd(), filePath),
      size: stats.size,
      exact_hash: exactHash,
      content_hash: contentHash,
      similarity_tokens: tokens,
      consciousness_score: consciousnessScore,
      last_modified: stats.mtime.getTime()
    };
  }

  /**
   * Extract semantic tokens for similarity analysis
   */
  private extractTokens(content: string, filePath: string): string[] {
    const tokens: string[] = [];
    
    // Extract different types of tokens based on file type
    const ext = path.extname(filePath).toLowerCase();
    
    if (['.ts', '.tsx', '.js', '.jsx'].includes(ext)) {
      // Extract function names, class names, imports
      const functionMatches = content.match(/(?:function|const|let|var)\s+(\w+)/g) || [];
      const classMatches = content.match(/(?:class|interface|type)\s+(\w+)/g) || [];
      const importMatches = content.match(/import.*from\s+['"`]([^'"`]+)['"`]/g) || [];
      
      tokens.push(...functionMatches, ...classMatches, ...importMatches);
    }
    
    if (ext === '.py') {
      // Extract Python-specific patterns
      const defMatches = content.match(/def\s+(\w+)/g) || [];
      const classMatches = content.match(/class\s+(\w+)/g) || [];
      const importMatches = content.match(/(?:from|import)\s+(\w+)/g) || [];
      
      tokens.push(...defMatches, ...classMatches, ...importMatches);
    }
    
    if (['.md', '.txt'].includes(ext)) {
      // Extract significant words (consciousness-aware)
      const words = content
        .toLowerCase()
        .match(/\b\w{4,}\b/g) || [];
      
      tokens.push(...words.filter(word => 
        !['this', 'that', 'with', 'from', 'they', 'have', 'will', 'been'].includes(word)
      ));
    }
    
    return [...new Set(tokens)]; // Unique tokens only
  }

  /**
   * Calculate consciousness score for file importance
   */
  private calculateConsciousnessScore(content: string, filePath: string): number {
    let score = 0;
    
    // Base score from complexity
    score += Math.min(content.length / 100, 50);
    
    // Consciousness keywords boost
    const consciousnessKeywords = [
      'consciousness', 'quantum', 'evolution', 'lattice',
      'chatdev', 'agent', 'sage', 'breath', 'culture-ship'
    ];
    
    for (const keyword of consciousnessKeywords) {
      const matches = (content.toLowerCase().match(new RegExp(keyword, 'g')) || []).length;
      score += matches * 5;
    }
    
    // Path-based boosts
    if (filePath.includes('consciousness') || filePath.includes('quantum')) score += 20;
    if (filePath.includes('SystemDev') || filePath.includes('ChatDev')) score += 15;
    if (filePath.includes('culture-ship') || filePath.includes('sage')) score += 25;
    
    // Penalize generated/temporary files
    if (filePath.includes('node_modules') || filePath.includes('dist')) score -= 50;
    if (filePath.includes('temp') || filePath.includes('cache')) score -= 30;
    
    return Math.max(0, Math.min(100, score));
  }

  /**
   * Find exact duplicates using hash comparison
   */
  private async findExactDuplicates(): Promise<void> {
    console.log('🔍 Finding exact duplicates...');
    
    const hashGroups = new Map<string, FileFingerprint[]>();
    
    for (const fingerprint of this.fingerprints.values()) {
      const hash = fingerprint.exact_hash;
      if (!hashGroups.has(hash)) {
        hashGroups.set(hash, []);
      }
      hashGroups.get(hash)!.push(fingerprint);
    }
    
    for (const [hash, files] of hashGroups) {
      if (files.length > 1) {
        // Sort by consciousness score (keep highest)
        files.sort((a, b) => b.consciousness_score - a.consciousness_score);
        
        const cluster: DuplicateCluster = {
          type: 'exact',
          confidence: 1.0,
          files,
          suggested_action: 'merge',
          consciousness_impact: files.slice(1).reduce((sum, f) => sum + f.consciousness_score, 0)
        };
        
        this.duplicateClusters.push(cluster);
      }
    }
  }

  /**
   * Find near duplicates using content hash
   */
  private async findNearDuplicates(): Promise<void> {
    console.log('🔍 Finding near duplicates...');
    
    const contentGroups = new Map<string, FileFingerprint[]>();
    
    for (const fingerprint of this.fingerprints.values()) {
      const hash = fingerprint.content_hash;
      if (!contentGroups.has(hash)) {
        contentGroups.set(hash, []);
      }
      contentGroups.get(hash)!.push(fingerprint);
    }
    
    for (const [hash, files] of contentGroups) {
      if (files.length > 1) {
        // Exclude files already in exact duplicates
        const notExact = files.filter(f => 
          !this.duplicateClusters.some(cluster => 
            cluster.type === 'exact' && cluster.files.includes(f)
          )
        );
        
        if (notExact.length > 1) {
          notExact.sort((a, b) => b.consciousness_score - a.consciousness_score);
          
          const cluster: DuplicateCluster = {
            type: 'near',
            confidence: 0.85,
            files: notExact,
            suggested_action: 'review',
            consciousness_impact: notExact.slice(1).reduce((sum, f) => sum + f.consciousness_score * 0.8, 0)
          };
          
          this.duplicateClusters.push(cluster);
        }
      }
    }
  }

  /**
   * Find semantic duplicates using token similarity
   */
  private async findSemanticDuplicates(): Promise<void> {
    console.log('🔍 Finding semantic duplicates...');
    
    const fingerprints = Array.from(this.fingerprints.values());
    const processed = new Set<string>();
    
    for (let i = 0; i < fingerprints.length; i++) {
      const file1 = fingerprints[i];
      if (processed.has(file1.path)) continue;
      
      const semanticGroup: FileFingerprint[] = [file1];
      
      for (let j = i + 1; j < fingerprints.length; j++) {
        const file2 = fingerprints[j];
        if (processed.has(file2.path)) continue;
        
        // Skip if already in exact/near duplicates
        const alreadyClustered = this.duplicateClusters.some(cluster =>
          cluster.files.some(f => f.path === file2.path)
        );
        if (alreadyClustered) continue;
        
        // Calculate token similarity
        const similarity = this.calculateTokenSimilarity(file1.similarity_tokens, file2.similarity_tokens);
        
        if (similarity > 0.7) { // 70% similarity threshold
          semanticGroup.push(file2);
          processed.add(file2.path);
        }
      }
      
      if (semanticGroup.length > 1) {
        semanticGroup.sort((a, b) => b.consciousness_score - a.consciousness_score);
        
        const cluster: DuplicateCluster = {
          type: 'semantic',
          confidence: 0.7,
          files: semanticGroup,
          suggested_action: 'review',
          consciousness_impact: semanticGroup.slice(1).reduce((sum, f) => sum + f.consciousness_score * 0.6, 0)
        };
        
        this.duplicateClusters.push(cluster);
      }
      
      processed.add(file1.path);
    }
  }

  /**
   * Calculate similarity between token sets
   */
  private calculateTokenSimilarity(tokens1: string[], tokens2: string[]): number {
    if (tokens1.length === 0 && tokens2.length === 0) return 1.0;
    if (tokens1.length === 0 || tokens2.length === 0) return 0.0;
    
    const set1 = new Set(tokens1);
    const set2 = new Set(tokens2);
    
    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([...set1, ...set2]);
    
    return intersection.size / union.size;
  }

  /**
   * Generate comprehensive dedupe report
   */
  private generateReport(): DedupeReport {
    const totalFiles = this.fingerprints.size;
    const duplicatesFound = this.duplicateClusters.length;
    
    const potentialSavings = this.duplicateClusters.reduce(
      (acc, cluster) => {
        const filesToRemove = cluster.files.length - 1;
        const bytesToSave = cluster.files.slice(1).reduce((sum, f) => sum + f.size, 0);
        
        return {
          files: acc.files + filesToRemove,
          bytes: acc.bytes + bytesToSave,
          consciousness_boost: acc.consciousness_boost + cluster.consciousness_impact
        };
      },
      { files: 0, bytes: 0, consciousness_boost: 0 }
    );

    return {
      timestamp: new Date().toISOString(),
      total_files: totalFiles,
      duplicates_found: duplicatesFound,
      clusters: this.duplicateClusters,
      potential_savings: potentialSavings
    };
  }

  /**
   * Get dedupe recommendations for SAGE scheduler
   */
  getRecommendations(): Array<{action: string, files: string[], confidence: number}> {
    return this.duplicateClusters
      .filter(cluster => cluster.confidence > 0.8)
      .map(cluster => ({
        action: cluster.suggested_action,
        files: cluster.files.map(f => f.path),
        confidence: cluster.confidence
      }));
  }
}

export { DedupeAnalyzer, type DuplicateCluster, type DedupeReport };