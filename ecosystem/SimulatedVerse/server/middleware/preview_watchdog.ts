// server/middleware/preview_watchdog.ts
// Preview Error Trapping Middleware - CARD G implementation
// Traps unhandled rejections and logs to logger/preview.log with UI flag context

import { promises as fs } from 'node:fs';
import path from 'node:path';

interface ErrorContext {
  timestamp: number;
  error_type: 'unhandled_rejection' | 'uncaught_exception' | 'preview_crash';
  error_message: string;
  stack_trace?: string;
  ui_context?: {
    active_ui: string;
    milestone: string | null;
    url: string;
    user_agent?: string;
  };
  system_state?: {
    memory_usage: NodeJS.MemoryUsage;
    uptime: number;
    active_connections: number;
  };
}

class PreviewWatchdog {
  private logPath = 'logger/preview.log';
  private errorCount = 0;
  private lastErrorTime = 0;
  private councilBus: any = null;

  constructor() {
    this.setupErrorHandlers();
    this.ensureLogDirectory();
  }

  public setCouncilBus(bus: any): void {
    this.councilBus = bus;
  }

  private async ensureLogDirectory(): Promise<void> {
    try {
      await fs.mkdir(path.dirname(this.logPath), { recursive: true });
    } catch (error) {
      console.warn('[PreviewWatchdog] Could not create log directory:', error);
    }
  }

  private setupErrorHandlers(): void {
    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      this.handleError('unhandled_rejection', reason, {
        promise_location: promise.toString()
      });
    });

    // Handle uncaught exceptions (already exists in server but we'll supplement)
    process.on('uncaughtException', (error) => {
      this.handleError('uncaught_exception', error);
    });

    console.log('[PreviewWatchdog] Error handlers registered');
  }

  private async handleError(type: ErrorContext['error_type'], error: any, metadata?: any): Promise<void> {
    this.errorCount++;
    this.lastErrorTime = Date.now();

    const errorContext: ErrorContext = {
      timestamp: Date.now(),
      error_type: type,
      error_message: error?.message || String(error),
      stack_trace: error?.stack,
      ui_context: await this.getUIContext(),
      system_state: this.getSystemState()
    };

    if (metadata) {
      (errorContext as any).metadata = metadata;
    }

    // Log to file
    await this.logError(errorContext);

    // Alert Council Bus if available
    if (this.councilBus) {
      this.alertCouncilBus(errorContext);
    }

    // Post to ChatDev council if it's a critical error
    if (this.isCriticalError(errorContext)) {
      await this.postToCouncilWithRepro(errorContext);
    }

    console.error(`[PreviewWatchdog] ${type}: ${errorContext.error_message}`);
  }

  private async getUIContext(): Promise<ErrorContext['ui_context']> {
    try {
      // Try to read current UI flags
      const flagsResponse = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/SystemDev/guards/flags.json`, {
        signal: AbortSignal.timeout(1000)
      }).catch(() => null);

      let uiFlags = null;
      if (flagsResponse?.ok) {
        uiFlags = await flagsResponse.json();
      }

      return {
        active_ui: uiFlags?.active_ui || 'unknown',
        milestone: uiFlags?.milestones ? this.getHighestMilestone(uiFlags.milestones) : null,
        url: process.env.REPLIT_URL || `localhost:${(process.env.PORT || '5000').trim()}`,
        user_agent: 'server-side'
      };
    } catch (error) {
      return {
        active_ui: 'unknown',
        milestone: null,
        url: `localhost:${(process.env.PORT || '5000').trim()}`
      };
    }
  }

  private getHighestMilestone(milestones: Record<string, boolean>): string | null {
    const ordered = ['UI_M0_BOOT', 'UI_M1_PANELS', 'UI_M2_ADVISOR', 'UI_M3_HOLO', 'UI_M4_CHATDEV', 'UI_M5_COMPOSER'];
    
    for (let i = ordered.length - 1; i >= 0; i--) {
      const milestone = ordered[i];
      if (milestone && milestones[milestone]) {
        return milestone;
      }
    }
    
    return null;
  }

  private getSystemState(): ErrorContext['system_state'] {
    return {
      memory_usage: process.memoryUsage(),
      uptime: process.uptime(),
      active_connections: (process as any).getActiveResourcesInfo?.()?.length || 0
    };
  }

  private async logError(context: ErrorContext): Promise<void> {
    try {
      const logEntry = {
        ...context,
        log_level: 'ERROR',
        source: 'preview_watchdog'
      };

      const logLine = JSON.stringify(logEntry) + '\n';
      await fs.appendFile(this.logPath, logLine);
    } catch (error) {
      console.warn('[PreviewWatchdog] Could not write to log file:', error);
    }
  }

  private alertCouncilBus(context: ErrorContext): void {
    try {
      this.councilBus.publish('preview.error', {
        error_type: context.error_type,
        message: context.error_message,
        ui_context: context.ui_context,
        error_count: this.errorCount,
        timestamp: context.timestamp
      });
    } catch (error) {
      console.warn('[PreviewWatchdog] Could not alert Council Bus:', error);
    }
  }

  private isCriticalError(context: ErrorContext): boolean {
    // Define critical error conditions
    const criticalPatterns = [
      /cannot read property/i,
      /undefined is not a function/i,
      /module not found/i,
      /syntaxerror/i,
      /referenceerror/i
    ];

    const isCriticalPattern = criticalPatterns.some(pattern => 
      pattern.test(context.error_message)
    );

    const isHighFrequency = this.errorCount > 5 && 
      (Date.now() - this.lastErrorTime) < 30000; // 5 errors in 30 seconds

    return isCriticalPattern || isHighFrequency;
  }

  private async postToCouncilWithRepro(context: ErrorContext): Promise<void> {
    try {
      const reproData = {
        error_context: context,
        repro_steps: this.generateReproSteps(context),
        hotlinks: this.generateHotlinks(context),
        suggested_actions: this.generateSuggestedActions(context)
      };

      // Post to Council Bus for agent consumption
      if (this.councilBus) {
        this.councilBus.publish('preview.critical_error', {
          ...reproData,
          priority: 'high',
          requires_agent_intervention: true
        });
      }

      // Also save to receipts for persistence
      await fs.mkdir('SystemDev/receipts', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/preview_critical_error_${Date.now()}.json`,
        JSON.stringify(reproData, null, 2)
      );

      console.log('[PreviewWatchdog] Critical error reported to Council with repro data');
    } catch (error) {
      console.warn('[PreviewWatchdog] Could not post to Council:', error);
    }
  }

  private generateReproSteps(context: ErrorContext): string[] {
    const steps = [
      `Navigate to UI: ${context.ui_context?.active_ui || 'unknown'}`,
      `Current milestone: ${context.ui_context?.milestone || 'none'}`,
      `Error occurred at: ${new Date(context.timestamp).toISOString()}`
    ];

    if (context.error_type === 'unhandled_rejection') {
      steps.push('Triggered by: Promise rejection');
    } else if (context.error_type === 'uncaught_exception') {
      steps.push('Triggered by: Uncaught exception');
    }

    steps.push(`Error: ${context.error_message}`);

    return steps;
  }

  private generateHotlinks(context: ErrorContext): Record<string, string> {
    return {
      log_file: `/logger/preview.log`,
      ui_flags: `/SystemDev/guards/flags.json`,
      council_bus_health: `/api/council-bus/health`,
      preview_ui: `/?ui=${context.ui_context?.active_ui || 'legacy'}`,
      system_status: `/api/ai/status`
    };
  }

  private generateSuggestedActions(context: ErrorContext): string[] {
    const actions = [];

    if (context.error_message.includes('module')) {
      actions.push('Check build configuration and module resolution');
      actions.push('Run build audit script: npm run build:audit');
    }

    if (context.error_message.includes('undefined')) {
      actions.push('Check state adapter mappings');
      actions.push('Verify UI milestone unlocks');
    }

    if (context.ui_context?.active_ui === 'main') {
      actions.push('Try fallback to legacy UI: ?ui=legacy');
    }

    if (this.errorCount > 3) {
      actions.push('Consider system restart due to high error frequency');
    }

    actions.push('Check Council Bus events for related errors');
    actions.push('Review recent receipts for system changes');

    return actions;
  }

  /**
   * Express middleware factory for client-side error reporting
   */
  public createClientErrorHandler() {
    return (req: any, res: any, next: any) => {
      if (req.path === '/api/preview/error') {
        const { error, ui_context, user_agent } = req.body;
        
        this.handleError('preview_crash', error, {
          client_reported: true,
          ui_context,
          user_agent
        });

        res.json({ 
          success: true, 
          message: 'Error reported to watchdog',
          error_count: this.errorCount
        });
      } else {
        next();
      }
    };
  }

  /**
   * Get current watchdog status
   */
  public getStatus() {
    return {
      active: true,
      error_count: this.errorCount,
      last_error_time: this.lastErrorTime,
      log_path: this.logPath,
      council_bus_connected: !!this.councilBus
    };
  }
}

// Export singleton instance
export const previewWatchdog = new PreviewWatchdog();