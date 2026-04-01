#!/usr/bin/env tsx
// UI Desync Audit - Find mechanics with proofs but no UI routes, and routes with no proofs
// Anti-theater enforcement: buttons only appear when mechanics are proven

import { promises as fs } from 'node:fs';
import * as path from 'node:path';
import { glob } from 'glob';

interface DesyncAuditResult {
  timestamp: number;
  mechanics_with_proofs: string[];
  routes_in_ui: string[];
  missing_routes: Array<{
    mechanic_id: string;
    last_proof: number;
    spec_path?: string;
  }>;
  orphaned_routes: Array<{
    route_path: string;
    no_proof_since: number;
  }>;
  stale_proofs: Array<{
    mechanic_id: string;
    proof_age_hours: number;
    should_hide: boolean;
  }>;
  ui_desync_count: number;
  recommendations: string[];
}

export class UIDesyncAuditor {
  constructor() {}

  async auditDesync(): Promise<DesyncAuditResult> {
    const result: DesyncAuditResult = {
      timestamp: Date.now(),
      mechanics_with_proofs: [],
      routes_in_ui: [],
      missing_routes: [],
      orphaned_routes: [],
      stale_proofs: [],
      ui_desync_count: 0,
      recommendations: []
    };

    // 1. Find all mechanics that have recent proofs
    result.mechanics_with_proofs = await this.findMechanicsWithProofs();
    
    // 2. Find all routes currently in the UI
    result.routes_in_ui = await this.findUIRoutes();
    
    // 3. Find mechanics with proofs but no routes
    result.missing_routes = await this.findMissingRoutes(
      result.mechanics_with_proofs, 
      result.routes_in_ui
    );
    
    // 4. Find routes without recent proofs
    result.orphaned_routes = await this.findOrphanedRoutes(
      result.routes_in_ui,
      result.mechanics_with_proofs
    );
    
    // 5. Find stale proofs that should hide UI
    result.stale_proofs = await this.findStaleProofs();
    
    // 6. Calculate desync count and recommendations
    result.ui_desync_count = result.missing_routes.length + result.orphaned_routes.length;
    result.recommendations = this.generateRecommendations(result);

    return result;
  }

  private async findMechanicsWithProofs(): Promise<string[]> {
    const mechanics = [];
    
    try {
      // Check receipts for proof entries
      const receiptFiles = await glob('SystemDev/receipts/*proof*.json');
      const recentProofs = new Set<string>();
      const twentyFourHoursAgo = Date.now() - (24 * 60 * 60 * 1000);
      
      for (const receiptFile of receiptFiles) {
        try {
          const content = await fs.readFile(receiptFile, 'utf8');
          const receipt = JSON.parse(content);
          
          // Check if proof is recent
          if (receipt.timestamp > twentyFourHoursAgo) {
            if (receipt.mechanic_id) {
              recentProofs.add(receipt.mechanic_id);
            }
          }
        } catch (e) {
          // Skip invalid receipt files
        }
      }
      
      mechanics.push(...Array.from(recentProofs));
      
      // Also check for spec files (these are potential mechanics)
      const specFiles = await glob('GameDev/gameplay/specs/*.yml');
      for (const specFile of specFiles) {
        const mechanicId = path.basename(specFile, '.yml');
        if (!mechanics.includes(mechanicId)) {
          // Check if this spec has been synthesized recently
          const synthesisReceipts = await glob(`SystemDev/receipts/synthesis_${mechanicId}_*.json`);
          if (synthesisReceipts.length > 0) {
            mechanics.push(mechanicId);
          }
        }
      }
      
    } catch (error) {
      console.warn('[DesyncAudit] Error finding mechanics with proofs:', error);
    }
    
    return mechanics;
  }

  private async findUIRoutes(): Promise<string[]> {
    const routes = [];
    
    try {
      // Check PreviewUI routes
      const routeFiles = await glob('PreviewUI/web/pages/*Page.tsx');
      for (const routeFile of routeFiles) {
        const routeName = path.basename(routeFile, 'Page.tsx').toLowerCase();
        routes.push(routeName);
      }
      
      // Check React Router definitions if they exist
      const appFiles = await glob('PreviewUI/web/**/App.tsx');
      for (const appFile of appFiles) {
        try {
          const content = await fs.readFile(appFile, 'utf8');
          const routeMatches = content.match(/path=["']([^"']+)["']/g) || [];
          for (const match of routeMatches) {
            const path = match.match(/path=["']([^"']+)["']/)?.[1];
            if (path && path.includes('game')) {
              routes.push(path.replace('/game/', '').replace('/', ''));
            }
          }
        } catch (e) {
          // Skip files we can't read
        }
      }
      
      // Check for route registrations in the pattern library
      try {
        const patternFile = 'GameDev/patterns/index.ts';
        const content = await fs.readFile(patternFile, 'utf8');
        const routeMatches = content.match(/route:\s*['"`]([^'"`]+)['"`]/g) || [];
        for (const match of routeMatches) {
          const route = match.match(/route:\s*['"`]([^'"`]+)['"`]/)?.[1];
          if (route) {
            routes.push(route.replace('/game/', '').replace('/', ''));
          }
        }
      } catch (e) {
        // Pattern file doesn't exist yet
      }
      
    } catch (error) {
      console.warn('[DesyncAudit] Error finding UI routes:', error);
    }
    
    return [...new Set(routes)]; // Remove duplicates
  }

  private async findMissingRoutes(
    mechanicsWithProofs: string[], 
    routesInUI: string[]
  ): Promise<DesyncAuditResult['missing_routes']> {
    const missing = [];
    
    for (const mechanicId of mechanicsWithProofs) {
      // Check if this mechanic has a corresponding route
      const hasRoute = routesInUI.some(route => 
        route.includes(mechanicId.replace(/_/g, '-')) ||
        route.includes(mechanicId.replace(/_/g, '')) ||
        mechanicId.includes(route.replace(/-/g, '_'))
      );
      
      if (!hasRoute) {
        // Find the last proof time
        const proofFiles = await glob(`SystemDev/receipts/*${mechanicId}*.json`);
        let lastProof = 0;
        
        for (const proofFile of proofFiles) {
          try {
            const content = await fs.readFile(proofFile, 'utf8');
            const receipt = JSON.parse(content);
            if (receipt.timestamp > lastProof) {
              lastProof = receipt.timestamp;
            }
          } catch (e) {
            // Skip invalid files
          }
        }
        
        missing.push({
          mechanic_id: mechanicId,
          last_proof: lastProof,
          spec_path: `GameDev/gameplay/specs/${mechanicId}.yml`
        });
      }
    }
    
    return missing;
  }

  private async findOrphanedRoutes(
    routesInUI: string[],
    mechanicsWithProofs: string[]
  ): Promise<DesyncAuditResult['orphaned_routes']> {
    const orphaned = [];
    
    for (const route of routesInUI) {
      // Check if this route has a corresponding proven mechanic
      const hasMechanic = mechanicsWithProofs.some(mechanic => 
        mechanic.includes(route.replace(/-/g, '_')) ||
        route.includes(mechanic.replace(/_/g, '-'))
      );
      
      if (!hasMechanic) {
        orphaned.push({
          route_path: route,
          no_proof_since: Date.now() - (7 * 24 * 60 * 60 * 1000) // 7 days ago as default
        });
      }
    }
    
    return orphaned;
  }

  private async findStaleProofs(): Promise<DesyncAuditResult['stale_proofs']> {
    const stale = [];
    const staleThresholdHours = 48; // 48 hours
    
    try {
      const receiptFiles = await glob('SystemDev/receipts/*proof*.json');
      
      for (const receiptFile of receiptFiles) {
        try {
          const content = await fs.readFile(receiptFile, 'utf8');
          const receipt = JSON.parse(content);
          
          if (receipt.mechanic_id && receipt.timestamp) {
            const ageMs = Date.now() - receipt.timestamp;
            const ageHours = ageMs / (60 * 60 * 1000);
            
            if (ageHours > staleThresholdHours) {
              stale.push({
                mechanic_id: receipt.mechanic_id,
                proof_age_hours: Math.round(ageHours * 10) / 10,
                should_hide: ageHours > 72 // Hide after 72 hours
              });
            }
          }
        } catch (e) {
          // Skip invalid receipts
        }
      }
    } catch (error) {
      console.warn('[DesyncAudit] Error finding stale proofs:', error);
    }
    
    return stale;
  }

  private generateRecommendations(result: DesyncAuditResult): string[] {
    const recommendations = [];
    
    if (result.missing_routes.length > 0) {
      recommendations.push(
        `Wire ${result.missing_routes.length} missing routes: ${
          result.missing_routes.map(m => m.mechanic_id).join(', ')
        }`
      );
    }
    
    if (result.orphaned_routes.length > 0) {
      recommendations.push(
        `Hide ${result.orphaned_routes.length} orphaned routes: ${
          result.orphaned_routes.map(r => r.route_path).join(', ')
        }`
      );
    }
    
    if (result.stale_proofs.length > 0) {
      const shouldHide = result.stale_proofs.filter(p => p.should_hide);
      if (shouldHide.length > 0) {
        recommendations.push(
          `Hide ${shouldHide.length} stale mechanics: ${
            shouldHide.map(p => p.mechanic_id).join(', ')
          }`
        );
      }
    }
    
    if (result.ui_desync_count === 0) {
      recommendations.push('✅ UI is in sync with proven mechanics');
    } else {
      recommendations.push(`Priority: Fix ${result.ui_desync_count} UI desync issues`);
    }
    
    return recommendations;
  }
}

async function main() {
  console.log('[UIDesyncAudit] Starting UI desync audit...');
  
  const auditor = new UIDesyncAuditor();
  const result = await auditor.auditDesync();
  
  // Save detailed report
  await fs.mkdir('SystemDev/reports', { recursive: true });
  const reportPath = `SystemDev/reports/ui_desync_${Date.now()}.json`;
  await fs.writeFile(reportPath, JSON.stringify(result, null, 2));
  
  // Print summary
  console.log(`\\n[UIDesyncAudit] Audit Complete`);
  console.log(`Mechanics with proofs: ${result.mechanics_with_proofs.length}`);
  console.log(`Routes in UI: ${result.routes_in_ui.length}`);
  console.log(`Missing routes: ${result.missing_routes.length}`);
  console.log(`Orphaned routes: ${result.orphaned_routes.length}`);
  console.log(`Stale proofs: ${result.stale_proofs.length}`);
  console.log(`UI Desync Count: ${result.ui_desync_count}`);
  
  console.log(`\\nRecommendations:`);
  result.recommendations.forEach(rec => console.log(`  - ${rec}`));
  
  console.log(`\\nReport saved: ${reportPath}`);
  
  // Save receipt
  const receipt = {
    action: 'ui_desync_audit',
    timestamp: Date.now(),
    status: result.ui_desync_count === 0 ? 'synchronized' : 'desynchronized',
    mechanics_proven: result.mechanics_with_proofs.length,
    routes_available: result.routes_in_ui.length,
    desync_issues: result.ui_desync_count,
    missing_routes: result.missing_routes.length,
    orphaned_routes: result.orphaned_routes.length,
    recommendations: result.recommendations.length
  };
  
  await fs.mkdir('SystemDev/receipts', { recursive: true });
  await fs.writeFile(
    `SystemDev/receipts/ui_desync_audit_${Date.now()}.json`,
    JSON.stringify(receipt, null, 2)
  );
  
  return result;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { UIDesyncAuditor };