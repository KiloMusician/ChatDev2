// Intelligent System Manager - Contextual Theater Control
// Infrastructure-First: Preserve value, eliminate blocking

import { systemControls, shouldActivateSystem } from './flexible-system-controls.js';

export class IntelligentSystemManager {
  private activeSystems = new Set<string>();
  private systemMetrics = new Map<string, { 
    startTime: number, 
    lastActivity: number, 
    userValue: number 
  }>();

  // Context-aware activation
  activateIfNeeded(systemName: keyof typeof systemControls, context: {
    userRequested?: boolean;
    serverUptime?: number;
    currentLoad?: number;
  }) {
    const control = systemControls[systemName];
    
    // Always honor user requests
    if (context.userRequested) {
      return this.activateSystem(systemName);
    }
    
    // Intelligent defaults based on context
    if (control.mode === 'contextual') {
      if (systemName === 'culture_guardian' && context.serverUptime && context.serverUptime > 300) {
        return this.activateSystem(systemName);
      }
    }
    
    return false;
  }

  // Graceful activation with monitoring
  activateSystem(systemName: string) {
    if (this.activeSystems.has(systemName)) return true;
    
    this.activeSystems.add(systemName);
    this.systemMetrics.set(systemName, {
      startTime: Date.now(),
      lastActivity: Date.now(),
      userValue: 0
    });
    
    console.log(`[INTELLIGENT-MGR] ✅ Activated ${systemName} with monitoring`);
    return true;
  }

  // Automatic deactivation if system becomes problematic
  monitorAndDeactivate() {
    for (const [systemName, metrics] of this.systemMetrics) {
      const runtime = Date.now() - metrics.startTime;
      const inactivity = Date.now() - metrics.lastActivity;
      
      // Deactivate if running too long without user value
      if (runtime > 300000 && metrics.userValue === 0) { // 5 minutes
        console.log(`[INTELLIGENT-MGR] 🚫 Auto-deactivating ${systemName} - no user value`);
        this.deactivateSystem(systemName);
      }
      
      // Deactivate if inactive too long
      if (inactivity > 120000) { // 2 minutes
        console.log(`[INTELLIGENT-MGR] 🚫 Auto-deactivating ${systemName} - inactive`);
        this.deactivateSystem(systemName);
      }
    }
  }

  deactivateSystem(systemName: string) {
    this.activeSystems.delete(systemName);
    this.systemMetrics.delete(systemName);
  }

  // Report user-facing value
  recordUserValue(systemName: string, value: number) {
    const metrics = this.systemMetrics.get(systemName);
    if (metrics) {
      metrics.userValue += value;
      metrics.lastActivity = Date.now();
    }
  }
}

export const intelligentManager = new IntelligentSystemManager();