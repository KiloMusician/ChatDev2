// server/routes/agent_hooks.ts
// Agent Hooks for UI Milestones - CARD H implementation
// Exposes UI Milestones channel on Council Bus and triggers agent responses

import express from 'express';
import { promises as fs } from 'node:fs';

interface MilestoneEvent {
  milestone: string;
  unlocked: boolean;
  timestamp: number;
  trigger_source: string;
  context?: any;
}

interface PlaybookSuggestion {
  id: string;
  title: string;
  description: string;
  actions: PlaybookAction[];
  priority: 'low' | 'medium' | 'high';
  estimated_time: number;
  prerequisites?: string[];
}

interface PlaybookAction {
  type: 'enable_feature' | 'show_tutorial' | 'unlock_content' | 'config_change';
  target: string;
  parameters?: Record<string, any>;
  description: string;
}

class UIMilestoneAgent {
  private councilBus: any = null;
  private milestoneHistory: MilestoneEvent[] = [];
  private playbooks: Map<string, PlaybookSuggestion[]> = new Map();

  constructor() {
    this.loadPlaybooks();
  }

  public setCouncilBus(bus: any): void {
    this.councilBus = bus;
    this.setupEventListeners();
    console.log('[UIMilestoneAgent] Connected to Council Bus');
  }

  private setupEventListeners(): void {
    if (!this.councilBus) return;

    // Listen for milestone unlock events
    this.councilBus.on('ui.milestone.unlock', (data: MilestoneEvent) => {
      this.handleMilestoneUnlock(data);
    });

    // Listen for research completions that might trigger milestones
    this.councilBus.on('research.complete', (data: any) => {
      this.handleResearchComplete(data);
    });

    // Listen for building constructions that might unlock milestones
    this.councilBus.on('building.constructed', (data: any) => {
      this.handleBuildingConstructed(data);
    });

    console.log('[UIMilestoneAgent] Event listeners registered');
  }

  private async loadPlaybooks(): Promise<void> {
    const playbookMappings = {
      'UI_M1_PANELS': this.getPanelsMilestonePlaybooks(),
      'UI_M2_ADVISOR': this.getAdvisorMilestonePlaybooks(), 
      'UI_M3_HOLO': this.getHoloMilestonePlaybooks(),
      'UI_M4_CHATDEV': this.getChatDevMilestonePlaybooks(),
      'UI_M5_COMPOSER': this.getComposerMilestonePlaybooks()
    };

    for (const [milestone, playbooks] of Object.entries(playbookMappings)) {
      this.playbooks.set(milestone, playbooks);
    }

    console.log('[UIMilestoneAgent] Playbooks loaded for all milestones');
  }

  private async handleMilestoneUnlock(event: MilestoneEvent): Promise<void> {
    this.milestoneHistory.push(event);
    
    console.log(`[UIMilestoneAgent] Milestone unlocked: ${event.milestone}`);

    // Get relevant playbooks for this milestone
    const playbooks = this.playbooks.get(event.milestone) || [];
    
    if (playbooks.length > 0) {
      // Post playbook suggestions to Council Bus
      for (const playbook of playbooks) {
        await this.postPlaybookSuggestion(event.milestone, playbook);
      }
    }

    // Update UI flags to reflect the unlock
    await this.updateUIFlags(event.milestone, true);

    // Emit follow-up events for dependent systems
    await this.emitFollowUpEvents(event);

    // Save receipt
    await this.saveReceipt('milestone_unlock', { event, playbooks_posted: playbooks.length });
  }

  private async handleResearchComplete(data: any): Promise<void> {
    const { research_id, effects } = data;

    // Check if this research unlocks any milestones
    const milestoneMap = {
      'cognitics.nanofab_online': 'UI_M1_PANELS',
      'cognitics.agent_core': 'UI_M2_ADVISOR',
      'cognitics.holo_weave': 'UI_M3_HOLO',
      'cognitics.symbiosis': 'UI_M4_CHATDEV',
      'cognitics.culture_ship_singularity': 'UI_M5_COMPOSER'
    };

    const milestone = milestoneMap[research_id as keyof typeof milestoneMap];
    if (milestone) {
      const event: MilestoneEvent = {
        milestone,
        unlocked: true,
        timestamp: Date.now(),
        trigger_source: 'research_completion',
        context: { research_id, effects }
      };

      await this.handleMilestoneUnlock(event);
    }
  }

  private async handleBuildingConstructed(data: any): Promise<void> {
    const { building_type, effects } = data;

    // Some buildings might unlock milestones directly
    if (building_type === 'nanofab_unit' && effects?.includes('UI_M1_PANELS')) {
      const event: MilestoneEvent = {
        milestone: 'UI_M1_PANELS',
        unlocked: true,
        timestamp: Date.now(),
        trigger_source: 'building_construction',
        context: { building_type, effects }
      };

      await this.handleMilestoneUnlock(event);
    }
  }

  private async postPlaybookSuggestion(milestone: string, playbook: PlaybookSuggestion): Promise<void> {
    if (!this.councilBus) return;

    const suggestion = {
      ...playbook,
      source_milestone: milestone,
      posted_at: Date.now(),
      agent: 'ui_milestone_agent'
    };

    // Post to Navigator agent for task planning
    this.councilBus.publish('navigator.playbook_suggestion', suggestion);

    // Also post general announcement
    this.councilBus.publish('ui.milestone.playbook_available', {
      milestone,
      playbook_id: playbook.id,
      title: playbook.title,
      priority: playbook.priority
    });

    console.log(`[UIMilestoneAgent] Posted playbook: ${playbook.title}`);
  }

  private async updateUIFlags(milestone: string, unlocked: boolean): Promise<void> {
    try {
      const flagsPath = 'SystemDev/guards/flags.json';
      const flags = JSON.parse(await fs.readFile(flagsPath, 'utf8'));
      
      flags.milestones[milestone] = unlocked;
      flags.updated = new Date().toISOString();
      
      await fs.writeFile(flagsPath, JSON.stringify(flags, null, 2));
      
      console.log(`[UIMilestoneAgent] Updated flags: ${milestone} = ${unlocked}`);
    } catch (error) {
      console.warn('[UIMilestoneAgent] Could not update UI flags:', error);
    }
  }

  private async emitFollowUpEvents(event: MilestoneEvent): Promise<void> {
    if (!this.councilBus) return;

    // Emit specific events based on milestone
    switch (event.milestone) {
      case 'UI_M1_PANELS':
        this.councilBus.publish('ui.evolution.panels_unlocked', {
          features: ['tooltips_plus', 'batch_buy', 'cost_breakdown'],
          timestamp: Date.now()
        });
        break;

      case 'UI_M2_ADVISOR':
        this.councilBus.publish('ui.evolution.advisor_unlocked', {
          features: ['macro_recorder', 'smart_alerts', 'inspector_overlays'],
          timestamp: Date.now()
        });
        break;

      case 'UI_M3_HOLO':
        this.councilBus.publish('ui.evolution.holo_unlocked', {
          features: ['spatial_ui', 'heatmaps', 'flow_visualization'],
          timestamp: Date.now()
        });
        break;
    }
  }

  private async saveReceipt(action: string, data: any): Promise<void> {
    try {
      await fs.mkdir('SystemDev/receipts', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/ui_milestone_${action}_${Date.now()}.json`,
        JSON.stringify({
          action,
          timestamp: Date.now(),
          agent: 'ui_milestone_agent',
          ...data
        }, null, 2)
      );
    } catch (error) {
      console.warn('[UIMilestoneAgent] Could not save receipt:', error);
    }
  }

  // Playbook definitions for each milestone

  private getPanelsMilestonePlaybooks(): PlaybookSuggestion[] {
    return [
      {
        id: 'enable_ghost_planner',
        title: 'Enable Ghost Planner across all panel types',
        description: 'Now that panelized UI is available, enable blueprint mode for buildings and systems',
        priority: 'high',
        estimated_time: 300,
        actions: [
          {
            type: 'enable_feature',
            target: 'ghost_planner',
            description: 'Enable ghost building placement with preview'
          },
          {
            type: 'show_tutorial',
            target: 'ghost_planner_tutorial',
            description: 'Show tutorial on blueprint mode usage'
          }
        ]
      },
      {
        id: 'unlock_qol_pack_1',
        title: 'Unlock Tier 1 QoL Features',
        description: 'Enable tooltips+, batch buy, and cost breakdown features',
        priority: 'medium',
        estimated_time: 180,
        actions: [
          {
            type: 'enable_feature',
            target: 'tooltips_plus',
            description: 'Enable enhanced tooltips with cost details'
          },
          {
            type: 'enable_feature',
            target: 'batch_buy',
            description: 'Enable quantity selectors for bulk purchases'
          },
          {
            type: 'enable_feature',
            target: 'cost_breakdown',
            description: 'Enable detailed cost analysis displays'
          }
        ]
      }
    ];
  }

  private getAdvisorMilestonePlaybooks(): PlaybookSuggestion[] {
    return [
      {
        id: 'setup_automation_advisor',
        title: 'Configure Automation Advisor',
        description: 'Set up intelligent automation suggestions and macro recording',
        priority: 'high',
        estimated_time: 600,
        actions: [
          {
            type: 'enable_feature',
            target: 'macro_recorder',
            description: 'Enable action sequence recording and playback'
          },
          {
            type: 'enable_feature',
            target: 'smart_alerts',
            description: 'Enable context-aware alert system'
          },
          {
            type: 'config_change',
            target: 'advisor_sensitivity',
            parameters: { level: 'medium' },
            description: 'Configure advisor suggestion frequency'
          }
        ]
      }
    ];
  }

  private getHoloMilestonePlaybooks(): PlaybookSuggestion[] {
    return [
      {
        id: 'activate_spatial_overlays',
        title: 'Activate Spatial UI Overlays',
        description: 'Enable 3D visualizations and holographic interface elements',
        priority: 'high',
        estimated_time: 900,
        actions: [
          {
            type: 'enable_feature',
            target: 'spatial_ui',
            description: 'Enable 3D colony visualization'
          },
          {
            type: 'enable_feature',
            target: 'flow_visualization',
            description: 'Enable resource flow arrows and heat maps'
          }
        ]
      }
    ];
  }

  private getChatDevMilestonePlaybooks(): PlaybookSuggestion[] {
    return [
      {
        id: 'integrate_conversational_workbench',
        title: 'Integrate Conversational Workbench',
        description: 'Connect ChatDev copilot panels to live game state',
        priority: 'high',
        estimated_time: 1200,
        actions: [
          {
            type: 'enable_feature',
            target: 'conversational_ui',
            description: 'Enable natural language commands'
          },
          {
            type: 'config_change',
            target: 'chatdev_integration',
            parameters: { mode: 'live_state' },
            description: 'Connect ChatDev to real-time game state'
          }
        ]
      }
    ];
  }

  private getComposerMilestonePlaybooks(): PlaybookSuggestion[] {
    return [
      {
        id: 'unlock_scenario_authoring',
        title: 'Unlock Scenario Authoring Tools',
        description: 'Enable full scenario composer and workshop integration',
        priority: 'medium',
        estimated_time: 1800,
        actions: [
          {
            type: 'enable_feature',
            target: 'scenario_composer',
            description: 'Enable scenario creation and editing tools'
          },
          {
            type: 'enable_feature',
            target: 'workshop_integration',
            description: 'Enable sharing and loading community scenarios'
          }
        ]
      }
    ];
  }

  public getStatus() {
    return {
      active: true,
      council_bus_connected: !!this.councilBus,
      milestone_history_count: this.milestoneHistory.length,
      playbooks_loaded: this.playbooks.size,
      last_milestone: this.milestoneHistory[this.milestoneHistory.length - 1]?.milestone
    };
  }
}

// Export singleton instance
export const uiMilestoneAgent = new UIMilestoneAgent();

// Express router for HTTP endpoints
const router = express.Router();

router.get('/milestones/status', (req, res) => {
  res.json(uiMilestoneAgent.getStatus());
});

router.post('/milestones/trigger', (req, res) => {
  const { milestone, source } = req.body;
  
  if (!milestone) {
    return res.status(400).json({ error: 'milestone is required' });
  }

  const event: MilestoneEvent = {
    milestone,
    unlocked: true,
    timestamp: Date.now(),
    trigger_source: source || 'manual_trigger'
  };

  uiMilestoneAgent['handleMilestoneUnlock'](event);
  
  res.json({
    success: true,
    message: `Milestone ${milestone} triggered`,
    timestamp: event.timestamp
  });
});

export default router;