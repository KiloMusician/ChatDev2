#!/usr/bin/env tsx
/**
 * Duplicate Content Scanner - SAGE-PILOT Foundation
 * Detects exact and similar files for consolidation
 */
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

interface DuplicateInfo {
  hash: string;
  paths: string[];
  size: number;
  type: 'exact' | 'similar';
  similarity?: number;
}

interface ScanOptions {
  mode: 'exact' | 'similar';
  threshold: number;
  limit: number;
  exclude: string[];
}

interface ScanReport {
  timestamp: string;
  mode: string;
  files_scanned: number;
  duplicates_found: number;
  bytes_redundant: number;
  groups: DuplicateInfo[];
  recommendations: string[];
}

function getFileHash(filePath: string): string {
  try {
    const content = fs.readFileSync(filePath);
    return crypto.createHash('sha256').update(content).digest('hex');
  } catch (error) {
    return '';
  }
}

function getFileContent(filePath: string): string {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch (error) {
    return '';
  }
}

function calculateSimilarity(content1: string, content2: string): number {
  // Simple line-based similarity calculation
  const lines1 = content1.split('\n');
  const lines2 = content2.split('\n');
  
  const maxLines = Math.max(lines1.length, lines2.length);
  if (maxLines === 0) return 1;
  
  let commonLines = 0;
  const set1 = new Set(lines1.map(line => line.trim()).filter(line => line.length > 0));
  const set2 = new Set(lines2.map(line => line.trim()).filter(line => line.length > 0));
  
  for (const line of set1) {
    if (set2.has(line)) commonLines++;
  }
  
  return commonLines / Math.max(set1.size, set2.size);
}

function walkFiles(dir: string, exclude: string[]): string[] {
  const files: string[] = [];
  
  function walk(currentDir: string) {
    try {
      const entries = fs.readdirSync(currentDir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(currentDir, entry.name);
        const relativePath = path.relative('.', fullPath);
        
        // Skip excluded patterns
        if (exclude.some(pattern => relativePath.includes(pattern))) continue;
        
        if (entry.isDirectory()) {
          walk(fullPath);
        } else if (entry.isFile()) {
          // Only scan text-like files for similarity
          const ext = path.extname(entry.name).toLowerCase();
          if (['.ts', '.js', '.tsx', '.jsx', '.py', '.md', '.txt', '.json', '.yml', '.yaml', '.css', '.scss', '.html'].includes(ext)) {
            files.push(relativePath);
          }
        }
      }
    } catch (error) {
      console.error(`Error walking ${currentDir}:`, error);
    }
  }
  
  walk(dir);
  return files;
}

function scanExactDuplicates(files: string[]): DuplicateInfo[] {
  const hashMap = new Map<string, string[]>();
  
  for (const file of files) {
    const hash = getFileHash(file);
    if (hash) {
      if (!hashMap.has(hash)) {
        hashMap.set(hash, []);
      }
      hashMap.get(hash)!.push(file);
    }
  }
  
  const duplicates: DuplicateInfo[] = [];
  
  for (const [hash, paths] of hashMap) {
    if (paths.length > 1) {
      const size = fs.statSync(paths[0]).size;
      duplicates.push({
        hash,
        paths,
        size,
        type: 'exact'
      });
    }
  }
  
  return duplicates.sort((a, b) => b.size - a.size);
}

function scanSimilarFiles(files: string[], threshold: number, limit: number): DuplicateInfo[] {
  const similar: DuplicateInfo[] = [];
  const processed = new Set<string>();
  
  for (let i = 0; i < files.length && similar.length < limit; i++) {
    const file1 = files[i];
    if (processed.has(file1)) continue;
    
    const content1 = getFileContent(file1);
    if (!content1 || content1.length < 100) continue; // Skip very short files
    
    const group: string[] = [file1];
    processed.add(file1);
    
    for (let j = i + 1; j < files.length; j++) {
      const file2 = files[j];
      if (processed.has(file2)) continue;
      
      const content2 = getFileContent(file2);
      if (!content2) continue;
      
      const similarity = calculateSimilarity(content1, content2);
      
      if (similarity >= threshold) {
        group.push(file2);
        processed.add(file2);
      }
    }
    
    if (group.length > 1) {
      const size = fs.statSync(file1).size;
      similar.push({
        hash: crypto.createHash('md5').update(group.join('|')).digest('hex'),
        paths: group,
        size,
        type: 'similar',
        similarity: threshold
      });
    }
  }
  
  return similar.sort((a, b) => b.paths.length - a.paths.length);
}

function generateRecommendations(duplicates: DuplicateInfo[]): string[] {
  const recs: string[] = [];
  
  if (duplicates.length === 0) {
    recs.push('No duplicates found - repository is clean');
    return recs;
  }
  
  const exactDupes = duplicates.filter(d => d.type === 'exact');
  const similarFiles = duplicates.filter(d => d.type === 'similar');
  
  if (exactDupes.length > 0) {
    recs.push(`Found ${exactDupes.length} exact duplicate groups - safe to consolidate`);
    
    const topExact = exactDupes.slice(0, 3);
    for (const dup of topExact) {
      const canonical = dup.paths.find(p => p.includes('GameDev/') || p.includes('src/')) || dup.paths[0];
      recs.push(`Exact: Keep ${canonical}, move others to attic/dup/`);
    }
  }
  
  if (similarFiles.length > 0) {
    recs.push(`Found ${similarFiles.length} similar file groups - review for deep-merge`);
    
    const topSimilar = similarFiles.slice(0, 2);
    for (const sim of topSimilar) {
      recs.push(`Similar: ${sim.paths.length} files, review: ${sim.paths.slice(0, 2).join(', ')}`);
    }
  }
  
  const totalRedundant = duplicates.reduce((sum, d) => sum + (d.size * (d.paths.length - 1)), 0);
  recs.push(`Potential space savings: ${Math.round(totalRedundant / 1024)} KB`);
  
  return recs;
}

function main() {
  const args = process.argv.slice(2);
  const options: ScanOptions = {
    mode: 'exact',
    threshold: 0.85,
    limit: 20,
    exclude: ['.git', 'node_modules', 'dist', 'build', '.next', '.cache']
  };
  
  // Parse command line arguments
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--mode' && args[i + 1]) {
      options.mode = args[i + 1] as 'exact' | 'similar';
      i++;
    } else if (arg === '--threshold' && args[i + 1]) {
      options.threshold = parseFloat(args[i + 1]);
      i++;
    } else if (arg === '--limit' && args[i + 1]) {
      options.limit = parseInt(args[i + 1]);
      i++;
    }
  }
  
  console.log(`🔍 SAGE-PILOT Duplicate Scan (${options.mode} mode)...`);
  
  const files = walkFiles('.', options.exclude);
  console.log(`📁 Scanning ${files.length} files...`);
  
  let duplicates: DuplicateInfo[];
  
  if (options.mode === 'exact') {
    duplicates = scanExactDuplicates(files);
  } else {
    duplicates = scanSimilarFiles(files, options.threshold, options.limit);
  }
  
  const recommendations = generateRecommendations(duplicates);
  
  const report: ScanReport = {
    timestamp: new Date().toISOString(),
    mode: options.mode,
    files_scanned: files.length,
    duplicates_found: duplicates.length,
    bytes_redundant: duplicates.reduce((sum, d) => sum + (d.size * (d.paths.length - 1)), 0),
    groups: duplicates,
    recommendations
  };
  
  // Ensure output directories exist
  fs.mkdirSync('SystemDev/reports', { recursive: true });
  fs.mkdirSync('SystemDev/receipts', { recursive: true });
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPath = `SystemDev/reports/duplicates_${options.mode}_${timestamp}.json`;
  const receiptPath = `SystemDev/receipts/duplicates_${options.mode}_${timestamp}.json`;
  
  // Write detailed report
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  // Write receipt
  const receipt = {
    stage: 'duplicate_scan',
    mode: options.mode,
    timestamp: report.timestamp,
    duplicates_found: report.duplicates_found,
    bytes_redundant: report.bytes_redundant,
    top_recommendation: recommendations[0] || 'No issues found',
    next_hint: duplicates.length > 0 ? 'Review recommendations in report' : 'Repository is clean'
  };
  
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(`✅ Scan complete: ${duplicates.length} duplicate groups found`);
  console.log(`📄 Report: ${reportPath}`);
  console.log(`📄 Receipt: ${receiptPath}`);
  
  if (recommendations.length > 0) {
    console.log(`💡 Recommendations:`);
    recommendations.forEach(rec => console.log(`   - ${rec}`));
  }
}

// Run main if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}