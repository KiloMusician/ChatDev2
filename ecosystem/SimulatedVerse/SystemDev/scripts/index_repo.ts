#!/usr/bin/env tsx
/**
 * Repository Reality Indexer - SAGE-PILOT Foundation
 * Catalogs files, sizes, types, and generates baseline receipts
 */
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

interface FileInfo {
  path: string;
  size: number;
  ext: string;
  isGit: boolean;
  bucket: 'tiny' | 'small' | 'medium' | 'large' | 'huge';
}

interface IndexReport {
  timestamp: string;
  files_total: number;
  size_total: number;
  size_human: string;
  extensions: Record<string, number>;
  directories: Record<string, number>;
  size_buckets: Record<string, number>;
  top_dirs_by_count: Array<{dir: string, count: number}>;
  top_dirs_by_size: Array<{dir: string, size: number}>;
  bloat_indicators: {
    node_modules: number;
    build_dirs: number;
    cache_dirs: number;
    log_files: number;
    map_files: number;
    media_files: number;
  };
  anomalies: string[];
}

function walk(dir: string, base = dir): FileInfo[] {
  const files: FileInfo[] = [];
  
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(base, fullPath);
      
      // Skip git internals
      if (relativePath.startsWith('.git/')) continue;
      
      if (entry.isDirectory()) {
        // Recursively walk subdirectories
        files.push(...walk(fullPath, base));
      } else if (entry.isFile()) {
        const stat = fs.statSync(fullPath);
        const ext = path.extname(entry.name).toLowerCase().slice(1) || 'no_ext';
        
        let bucket: FileInfo['bucket'] = 'tiny';
        if (stat.size > 1024 * 1024 * 10) bucket = 'huge';        // >10MB
        else if (stat.size > 1024 * 1024) bucket = 'large';       // >1MB
        else if (stat.size > 1024 * 100) bucket = 'medium';       // >100KB
        else if (stat.size > 1024 * 10) bucket = 'small';         // >10KB
        
        files.push({
          path: relativePath,
          size: stat.size,
          ext,
          isGit: relativePath.includes('.git'),
          bucket
        });
      }
    }
  } catch (error) {
    console.error(`Error walking ${dir}:`, error);
  }
  
  return files;
}

function generateReport(files: FileInfo[]): IndexReport {
  const timestamp = new Date().toISOString();
  const extensions: Record<string, number> = {};
  const directories: Record<string, number> = {};
  const sizeBuckets: Record<string, number> = {};
  
  let totalSize = 0;
  
  for (const file of files) {
    if (file.isGit) continue; // Skip git files in stats
    
    totalSize += file.size;
    extensions[file.ext] = (extensions[file.ext] || 0) + 1;
    sizeBuckets[file.bucket] = (sizeBuckets[file.bucket] || 0) + 1;
    
    const dir = path.dirname(file.path);
    directories[dir] = (directories[dir] || 0) + 1;
  }
  
  const topDirsByCount = Object.entries(directories)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 20)
    .map(([dir, count]) => ({ dir, count }));
  
  // Calculate directory sizes
  const dirSizes: Record<string, number> = {};
  for (const file of files) {
    if (file.isGit) continue;
    const dir = path.dirname(file.path);
    dirSizes[dir] = (dirSizes[dir] || 0) + file.size;
  }
  
  const topDirsBySize = Object.entries(dirSizes)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 20)
    .map(([dir, size]) => ({ dir, size }));
  
  // Bloat indicators
  const bloatIndicators = {
    node_modules: files.filter(f => f.path.includes('node_modules')).length,
    build_dirs: files.filter(f => /\/(dist|build|out|coverage|__snapshots__)\//.test(f.path)).length,
    cache_dirs: files.filter(f => /\/(\.(cache|next|vite|parcel-cache)|turbo)\//.test(f.path)).length,
    log_files: files.filter(f => f.ext === 'log').length,
    map_files: files.filter(f => f.ext === 'map').length,
    media_files: files.filter(f => ['png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'].includes(f.ext)).length,
  };
  
  // Anomaly detection
  const anomalies: string[] = [];
  if (bloatIndicators.node_modules > 10000) anomalies.push('Excessive node_modules files');
  if (bloatIndicators.map_files > 1000) anomalies.push('Too many source maps');
  if (bloatIndicators.cache_dirs > 5000) anomalies.push('Large cache directories');
  if (files.filter(f => f.bucket === 'huge').length > 50) anomalies.push('Many huge files (>10MB)');
  
  return {
    timestamp,
    files_total: files.filter(f => !f.isGit).length,
    size_total: totalSize,
    size_human: formatBytes(totalSize),
    extensions,
    directories,
    size_buckets: sizeBuckets,
    top_dirs_by_count: topDirsByCount,
    top_dirs_by_size: topDirsBySize,
    bloat_indicators: bloatIndicators,
    anomalies
  };
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function main() {
  console.log('🔍 SAGE-PILOT Repository Index Starting...');
  
  const files = walk('.');
  const report = generateReport(files);
  
  // Ensure output directories exist
  fs.mkdirSync('SystemDev/reports', { recursive: true });
  fs.mkdirSync('SystemDev/receipts', { recursive: true });
  
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const reportPath = `SystemDev/reports/index_${timestamp}.json`;
  const receiptPath = `SystemDev/receipts/index_${timestamp}.json`;
  
  // Write detailed report
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  // Write receipt
  const receipt = {
    stage: 'index_repo',
    timestamp: report.timestamp,
    files_total: report.files_total,
    size_human: report.size_human,
    top_bloat: Object.entries(report.bloat_indicators)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([type, count]) => `${type}:${count}`),
    anomalies_count: report.anomalies.length,
    next_hint: report.anomalies.length > 0 ? 'Run bloat quarantine' : 'Repository looks healthy'
  };
  
  fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
  
  console.log(`✅ Index complete: ${report.files_total} files, ${report.size_human}`);
  console.log(`📄 Report: ${reportPath}`);
  console.log(`📄 Receipt: ${receiptPath}`);
  
  if (report.anomalies.length > 0) {
    console.log(`⚠️  Anomalies detected: ${report.anomalies.join(', ')}`);
  }
}

// Run main if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}