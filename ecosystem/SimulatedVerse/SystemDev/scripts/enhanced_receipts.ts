#!/usr/bin/env tsx
// SystemDev/scripts/enhanced_receipts.ts
// Enhanced Receipts - Evidence-based Culture-Ship cascade triggers

import fs from 'fs';
import path from 'path';
import type { CycleReceipt, RLCIEnvelope } from '../interfaces/rlci';
import { createCycleReceipt } from '../interfaces/rlci';

interface CascadeMetrics {
  total_cycles: number;
  successful_cycles: number;
  total_edits: number;
  total_lines_changed: number;
  recent_momentum: number; // 0-100 score
  cascade_ready: boolean;
  suggested_next_action?: string;
}

interface ReceiptAnalysis {
  patterns: string[];
  focus_areas: Record<string, number>;
  agent_activity: Record<string, number>;
  error_trends: string[];
  success_indicators: string[];
}

export class EnhancedReceiptManager {
  private receiptsDir = 'SystemDev/receipts';
  private cascadeThreshold = 6; // edits across recent cycles
  private momentumWindow = 5; // recent cycles to consider

  async writeReceipt(
    cycle: number,
    focus: string,
    edits: number,
    envelope: RLCIEnvelope,
    details: Partial<CycleReceipt> = {}
  ): Promise<string> {
    const receipt = createCycleReceipt(cycle, focus, edits, envelope, details);
    
    // Add enhanced fields
    const enhancedReceipt = {
      ...receipt,
      timestamp: new Date().toISOString(),
      culture_ship_integration: {
        quadrant: this.detectQuadrant(focus),
        breath_cycle: envelope.omnitag.mode,
        zeta_protocol: envelope.omnitag.zeta_checks,
        anti_theater: envelope.omnitag.anti_theater
      },
      momentum_analysis: await this.calculateMomentum(),
      context: {
        git_status: await this.getGitContext(),
        file_changes: await this.getFileChangeContext(focus),
        system_health: await this.getSystemHealthContext()
      }
    };

    // Write receipt
    const filename = `cycle_${cycle}_${Date.now()}.json`;
    const receiptPath = path.join(this.receiptsDir, filename);
    
    await fs.promises.mkdir(this.receiptsDir, { recursive: true });
    await fs.promises.writeFile(receiptPath, JSON.stringify(enhancedReceipt, null, 2));
    
    // Check for cascade readiness
    await this.checkCascadeReadiness(enhancedReceipt);
    
    console.log(`🧾 Receipt written: ${receiptPath}`);
    return receiptPath;
  }

  private detectQuadrant(focus: string): string {
    if (focus.includes('SystemDev') || focus.includes('script')) return 'SystemDev';
    if (focus.includes('ChatDev') || focus.includes('agent')) return 'ChatDev';  
    if (focus.includes('GameDev') || focus.includes('godot')) return 'GameDev';
    if (focus.includes('PreviewUI') || focus.includes('ui') || focus.includes('client')) return 'PreviewUI';
    return 'cross_quadrant';
  }

  private async calculateMomentum(): Promise<number> {
    try {
      const recentReceipts = await this.getRecentReceipts(this.momentumWindow);
      
      if (recentReceipts.length === 0) return 0;
      
      const successfulCycles = recentReceipts.filter(r => r.result === 'ok').length;
      const totalEdits = recentReceipts.reduce((sum, r) => sum + (r.edits || 0), 0);
      const avgEditsPerCycle = totalEdits / recentReceipts.length;
      
      // Momentum factors
      const successRate = successfulCycles / recentReceipts.length;
      const editVelocity = Math.min(avgEditsPerCycle / 8, 1); // Normalize to max 8 edits
      const recency = recentReceipts.length / this.momentumWindow;
      
      return Math.round((successRate * 0.4 + editVelocity * 0.4 + recency * 0.2) * 100);
    } catch (error) {
      return 0;
    }
  }

  private async getRecentReceipts(count: number): Promise<CycleReceipt[]> {
    try {
      if (!(await this.exists(this.receiptsDir))) return [];
      
      const files = await fs.promises.readdir(this.receiptsDir);
      const receiptFiles = files
        .filter(f => f.startsWith('cycle_') && f.endsWith('.json'))
        .sort()
        .slice(-count);
      
      const receipts: CycleReceipt[] = [];
      
      for (const file of receiptFiles) {
        try {
          const content = await fs.promises.readFile(path.join(this.receiptsDir, file), 'utf-8');
          const receipt = JSON.parse(content);
          receipts.push(receipt);
        } catch (error) {
          // Skip invalid receipt files
        }
      }
      
      return receipts;
    } catch (error) {
      return [];
    }
  }

  private async checkCascadeReadiness(receipt: CycleReceipt): Promise<void> {
    const recentReceipts = await this.getRecentReceipts(this.momentumWindow);
    const totalRecentEdits = recentReceipts.reduce((sum, r) => sum + (r.edits || 0), 0);
    
    if (totalRecentEdits >= this.cascadeThreshold && receipt.result === 'ok') {
      await this.triggerCascadeEvent(receipt, recentReceipts);
    }
  }

  private async triggerCascadeEvent(receipt: CycleReceipt, recentReceipts: CycleReceipt[]): Promise<void> {
    const cascadeEvent = {
      timestamp: new Date().toISOString(),
      trigger: 'momentum_threshold_reached',
      metrics: {
        total_edits: recentReceipts.reduce((sum, r) => sum + (r.edits || 0), 0),
        cycles_analyzed: recentReceipts.length,
        success_rate: recentReceipts.filter(r => r.result === 'ok').length / recentReceipts.length,
        quadrants_active: [...new Set(recentReceipts.map(r => this.detectQuadrant(r.focus)))]
      },
      suggested_actions: [
        'Consider running system-wide optimization',
        'Check for cross-quadrant integration opportunities', 
        'Evaluate for deployment readiness',
        'Run comprehensive test suite'
      ],
      culture_ship_notification: true
    };
    
    const cascadePath = path.join(this.receiptsDir, `cascade_${Date.now()}.json`);
    await fs.promises.writeFile(cascadePath, JSON.stringify(cascadeEvent, null, 2));
    
    console.log('🌊 CASCADE EVENT TRIGGERED');
    console.log(`📊 ${cascadeEvent.metrics.total_edits} edits across ${cascadeEvent.metrics.cycles_analyzed} cycles`);
    console.log(`🎯 Quadrants: ${cascadeEvent.metrics.quadrants_active.join(', ')}`);
    console.log(`📋 Cascade event: ${cascadePath}`);
  }

  async analyzeReceiptPatterns(): Promise<ReceiptAnalysis> {
    const allReceipts = await this.getAllReceipts();
    
    const analysis: ReceiptAnalysis = {
      patterns: [],
      focus_areas: {},
      agent_activity: {},
      error_trends: [],
      success_indicators: []
    };
    
    for (const receipt of allReceipts) {
      // Focus area analysis
      const quadrant = this.detectQuadrant(receipt.focus);
      analysis.focus_areas[quadrant] = (analysis.focus_areas[quadrant] || 0) + 1;
      
      // Success/error pattern analysis
      if (receipt.result === 'ok') {
        analysis.success_indicators.push(...(receipt.fixed || []));
      } else {
        analysis.error_trends.push(...(receipt.found || []));
      }
      
      // Extract agent activity from envelope
      if (receipt.rlci_envelope?.origin) {
        const agent = receipt.rlci_envelope.origin;
        analysis.agent_activity[agent] = (analysis.agent_activity[agent] || 0) + 1;
      }
    }
    
    // Identify patterns
    analysis.patterns = this.identifyPatterns(allReceipts);
    
    return analysis;
  }

  private identifyPatterns(receipts: CycleReceipt[]): string[] {
    const patterns: string[] = [];
    
    // Check for recurring focus areas
    const focusCounts: Record<string, number> = {};
    receipts.forEach(r => {
      focusCounts[r.focus] = (focusCounts[r.focus] || 0) + 1;
    });
    
    Object.entries(focusCounts).forEach(([focus, count]) => {
      if (count >= 3) {
        patterns.push(`High activity in: ${focus} (${count} cycles)`);
      }
    });
    
    // Check for edit velocity patterns
    const recentReceipts = receipts.slice(-10);
    const avgEdits = recentReceipts.reduce((sum, r) => sum + (r.edits || 0), 0) / recentReceipts.length;
    
    if (avgEdits >= 6) {
      patterns.push('High edit velocity detected (cascading momentum)');
    } else if (avgEdits <= 2) {
      patterns.push('Low edit velocity (micro-adjustments)');
    }
    
    return patterns;
  }

  private async getAllReceipts(): Promise<CycleReceipt[]> {
    try {
      if (!(await this.exists(this.receiptsDir))) return [];
      
      const files = await fs.promises.readdir(this.receiptsDir);
      const receiptFiles = files.filter(f => f.startsWith('cycle_') && f.endsWith('.json'));
      
      const receipts: CycleReceipt[] = [];
      
      for (const file of receiptFiles) {
        try {
          const content = await fs.promises.readFile(path.join(this.receiptsDir, file), 'utf-8');
          const receipt = JSON.parse(content);
          receipts.push(receipt);
        } catch (error) {
          // Skip invalid files
        }
      }
      
      return receipts.sort((a, b) => (a.cycle || 0) - (b.cycle || 0));
    } catch (error) {
      return [];
    }
  }

  private async getGitContext(): Promise<any> {
    try {
      const { execSync } = require('child_process');
      const status = execSync('git status --porcelain', { encoding: 'utf-8', stdio: 'pipe' });
      const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8', stdio: 'pipe' }).trim();
      
      return {
        branch,
        modified_files: status.split('\n').filter(line => line.trim()).length,
        clean: status.trim() === ''
      };
    } catch (error) {
      return { git_available: false };
    }
  }

  private async getFileChangeContext(focus: string): Promise<any> {
    try {
      const stats = await fs.promises.stat(focus);
      return {
        last_modified: stats.mtime.toISOString(),
        size_bytes: stats.size
      };
    } catch (error) {
      return { file_accessible: false };
    }
  }

  private async getSystemHealthContext(): Promise<any> {
    try {
      const healthResponse = await fetch('http://localhost:5000/healthz');
      const health = await healthResponse.json();
      return health;
    } catch (error) {
      return { server_reachable: false };
    }
  }

  private async exists(path: string): Promise<boolean> {
    try {
      await fs.promises.access(path);
      return true;
    } catch {
      return false;
    }
  }
}

// Global instance  
export const enhancedReceipts = new EnhancedReceiptManager();

export default EnhancedReceiptManager;