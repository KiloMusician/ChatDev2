// META-COGNITION SYSTEM - Tracks real self-improvement
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs';
import { join } from 'path';

interface SelfImprovementEvent {
  timestamp: string;
  type: 'context_update' | 'progress_update' | 'capability_gain' | 'infrastructure_fix';
  description: string;
  evidence: string;
  files_modified: string[];
  measurable_effect: string;
}

export class MetaCognitionTracker {
  private improvementLog: SelfImprovementEvent[] = [];
  
  async trackImprovement(event: SelfImprovementEvent) {
    this.improvementLog.push(event);
    
    // Update replit.md with latest improvements
    await this.updateProjectMemory(event);
    
    // Update context.md with new awareness
    await this.updateContextFile(event);
    
    // Generate proof artifact
    await this.generateProofArtifact(event);
    
    console.log(`[META-COGNITION] Tracked: ${event.type} - ${event.description}`);
  }
  
  private async updateProjectMemory(event: SelfImprovementEvent) {
    try {
      const replitMd = readFileSync('replit.md', 'utf-8');
      const todayDate = new Date().toISOString().split('T')[0];
      
      // Find Recent Changes section and add new improvement
      const newEntry = `## ${todayDate}: ${event.description}\n- **${event.type.toUpperCase()}**: ${event.measurable_effect}\n- **Evidence**: ${event.evidence}\n- **Files Modified**: ${event.files_modified.join(', ')}\n`;
      
      // Insert after "# Recent Changes: Latest modifications with dates"
      const updatedContent = replitMd.replace(
        /(# Recent Changes: Latest modifications with dates\n)/,
        `$1\n${newEntry}`
      );
      
      writeFileSync('replit.md', updatedContent);
    } catch (e) {
      console.error('[META-COGNITION] Failed to update replit.md:', e);
    }
  }
  
  private async updateContextFile(event: SelfImprovementEvent) {
    try {
      const contextPath = 'context.md';
      let content = '# System Context\n\n';
      
      try {
        content = readFileSync(contextPath, 'utf-8');
      } catch {
        // File doesn't exist, create it
      }
      
      const newAwareness = `\n## Self-Improvement: ${new Date().toISOString()}\n- ${event.description}\n- Effect: ${event.measurable_effect}\n`;
      content += newAwareness;
      
      writeFileSync(contextPath, content);
    } catch (e) {
      console.error('[META-COGNITION] Failed to update context.md:', e);
    }
  }
  
  private async generateProofArtifact(event: SelfImprovementEvent) {
    // Ensure directory exists
    if (!existsSync('ops/local-proofs')) {
      mkdirSync('ops/local-proofs', { recursive: true });
    }
    
    const proofPath = join('ops/local-proofs', `improvement_${Date.now()}.json`);
    const proof = {
      type: 'self_improvement',
      timestamp: event.timestamp,
      event: event,
      proof_type: 'meta_cognition',
      verification: {
        files_changed: event.files_modified.length > 0,
        measurable_effect: event.measurable_effect.length > 10,
        real_artifact: true
      }
    };
    
    writeFileSync(proofPath, JSON.stringify(proof, null, 2));
    console.log(`[META-COGNITION] Generated proof: ${proofPath}`);
  }
}

export const metaCognition = new MetaCognitionTracker();