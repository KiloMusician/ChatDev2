// REAL FILE OPERATIONS - Extract actual useful work from OfflineOperations
// No theater - just functional file system operations

import { promises as fs } from 'fs';
import path from 'path';

export class RealFileOps {
  
  // Actually useful: Clean up receipt files
  static async cleanupOldReceipts(): Promise<{ removed: number; errors: number }> {
    let removed = 0;
    let errors = 0;
    
    try {
      const receiptsDir = 'receipts';
      if (!(await fs.access(receiptsDir).then(() => true).catch(() => false))) {
        return { removed, errors };
      }
      
      const files = await fs.readdir(receiptsDir);
      const oldFiles = files.filter(f => f.endsWith('.receipt') && f.includes('2024'));
      
      for (const file of oldFiles) {
        try {
          await fs.unlink(path.join(receiptsDir, file));
          removed++;
        } catch (error) {
          errors++;
          if (errors <= 3) {
            console.warn('[RealFileOps] Failed to remove receipt:', file, error);
          }
        }
      }
      
      return { removed, errors };
    } catch (error) {
      console.warn('[RealFileOps] Receipt cleanup failed:', error);
      return { removed: 0, errors: 1 };
    }
  }
  
  // Actually useful: Get repo stats
  static async getRepoStats() {
    try {
      const server_files = await fs.readdir('server', { recursive: true });
      const ts_files = server_files.filter(f => f.toString().endsWith('.ts'));
      
      return {
        total_files: server_files.length,
        ts_files: ts_files.length,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.warn('[RealFileOps] Failed to collect repo stats:', error);
      return { total_files: 0, ts_files: 0, timestamp: new Date().toISOString() };
    }
  }
  
  // Actually useful: Find duplicate files by size
  static async findDuplicateFiles(): Promise<string[]> {
    const sizemap = new Map<number, string[]>();
    const duplicates: string[] = [];
    let statErrors = 0;
    
    try {
      const files = await fs.readdir('.', { recursive: true });
      
      for (const file of files) {
        try {
          const stat = await fs.stat(file.toString());
          if (stat.isFile()) {
            const size = stat.size;
            if (!sizemap.has(size)) sizemap.set(size, []);
            sizemap.get(size)!.push(file.toString());
          }
        } catch (error) {
          statErrors += 1;
          if (statErrors <= 3) {
            console.warn('[RealFileOps] Skipped file during duplicate scan due to read error:', file, error);
          }
        }
      }

      if (statErrors > 0) {
        console.warn(`[RealFileOps] Skipped ${statErrors} files during duplicate scan due to read errors`);
      }
      
      // Find actual duplicates (same size)
      for (const [size, fileList] of sizemap) {
        if (fileList.length > 1 && size > 1024) { // Only report files > 1KB
          duplicates.push(...fileList);
        }
      }
      
      return duplicates;
    } catch (error) {
      console.warn('[RealFileOps] Duplicate scan failed:', error);
      return [];
    }
  }
}
