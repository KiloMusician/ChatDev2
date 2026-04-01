// GameDev/systems/state_adapter.ts
// State Adapter V1→V2 for seamless legacy compatibility
// Implements CARD C: State Adapter v1→v2

export interface SimStateV1 {
  energy?: number;
  population?: number;
  research?: number;
  resources?: Record<string, number>;
  buildings?: any[];
  agents?: any[];
  alerts?: any[];
  [key: string]: any;
}

export interface SimViewV2 {
  core: {
    energy: number;
    population: number;
    research: number;
    morale: number;
    heat: number;
    power_capacity: number;
  };
  resources: {
    materials: number;
    components: number;
    food: number;
    medicine: number;
    tools: number;
    [key: string]: number;
  };
  infrastructure: {
    buildings: Building[];
    power_grid: PowerNode[];
    transport: TransportLink[];
    heat_sinks: HeatSink[];
  };
  population: {
    agents: Agent[];
    roles: Record<string, number>;
    schedules: Schedule[];
    morale_factors: Record<string, number>;
  };
  research: {
    active_projects: ResearchProject[];
    completed: string[];
    available: string[];
    points_per_second: number;
  };
  alerts: {
    critical: Alert[];
    warnings: Alert[];
    info: Alert[];
    system: Alert[];
  };
  ui_state: {
    active_panels: string[];
    selected_building?: string;
    camera_position?: [number, number];
    zoom_level?: number;
  };
}

interface Building {
  id: string;
  type: string;
  position: [number, number];
  health: number;
  power_consumption: number;
  heat_generation: number;
  efficiency: number;
  active: boolean;
}

interface PowerNode {
  id: string;
  type: 'generator' | 'consumer' | 'storage';
  output: number;
  capacity: number;
  efficiency: number;
}

interface TransportLink {
  id: string;
  from: string;
  to: string;
  throughput: number;
  resource_type: string;
}

interface HeatSink {
  id: string;
  cooling_capacity: number;
  efficiency: number;
  position: [number, number];
}

interface Agent {
  id: string;
  name: string;
  role: string;
  skills: Record<string, number>;
  morale: number;
  health: number;
  current_task?: string;
  schedule?: string;
}

interface Schedule {
  agent_id: string;
  tasks: Task[];
  rest_periods: RestPeriod[];
}

interface Task {
  type: string;
  priority: number;
  duration: number;
  requirements: string[];
}

interface RestPeriod {
  start_hour: number;
  duration: number;
  quality: number;
}

interface ResearchProject {
  id: string;
  name: string;
  progress: number;
  total_cost: number;
  rate: number;
  prerequisites: string[];
}

interface Alert {
  id: string;
  type: 'critical' | 'warning' | 'info' | 'system';
  message: string;
  timestamp: number;
  source: string;
  actions?: AlertAction[];
}

interface AlertAction {
  label: string;
  action: string;
  parameters?: Record<string, any>;
}

export class StateAdapter {
  private coverageMap: Record<string, boolean> = {};

  /**
   * Convert legacy SimStateV1 to modern SimViewV2
   */
  adapt(legacyState: SimStateV1): SimViewV2 {
    const adapted: SimViewV2 = {
      core: this.adaptCore(legacyState),
      resources: this.adaptResources(legacyState),
      infrastructure: this.adaptInfrastructure(legacyState),
      population: this.adaptPopulation(legacyState),
      research: this.adaptResearch(legacyState),
      alerts: this.adaptAlerts(legacyState),
      ui_state: this.adaptUIState(legacyState)
    };

    this.updateCoverage(legacyState, adapted);
    return adapted;
  }

  private adaptCore(state: SimStateV1): SimViewV2['core'] {
    this.markCovered('energy', !!state.energy);
    this.markCovered('population', !!state.population);
    this.markCovered('research', !!state.research);

    return {
      energy: state.energy || 0,
      population: state.population || 0,
      research: state.research || 0,
      morale: state.morale || 0.7, // Default morale
      heat: state.heat || 0,
      power_capacity: state.power_capacity || 100
    };
  }

  private adaptResources(state: SimStateV1): SimViewV2['resources'] {
    this.markCovered('resources', !!state.resources);

    const defaultResources = {
      materials: 0,
      components: 0,
      food: 0,
      medicine: 0,
      tools: 0
    };

    if (state.resources) {
      return { ...defaultResources, ...state.resources };
    }

    return defaultResources;
  }

  private adaptInfrastructure(state: SimStateV1): SimViewV2['infrastructure'] {
    this.markCovered('buildings', !!state.buildings);

    const buildings: Building[] = (state.buildings || []).map((b: any, index: number) => ({
      id: b.id || `building_${index}`,
      type: b.type || 'unknown',
      position: b.position || [0, 0],
      health: b.health || 100,
      power_consumption: b.power_consumption || 0,
      heat_generation: b.heat_generation || 0,
      efficiency: b.efficiency || 1.0,
      active: b.active !== false
    }));

    return {
      buildings,
      power_grid: state.power_grid || [],
      transport: state.transport || [],
      heat_sinks: state.heat_sinks || []
    };
  }

  private adaptPopulation(state: SimStateV1): SimViewV2['population'] {
    this.markCovered('agents', !!state.agents);

    const agents: Agent[] = (state.agents || []).map((a: any, index: number) => ({
      id: a.id || `agent_${index}`,
      name: a.name || `Agent ${index + 1}`,
      role: a.role || 'worker',
      skills: a.skills || {},
      morale: a.morale || 0.7,
      health: a.health || 100,
      current_task: a.current_task,
      schedule: a.schedule
    }));

    // Calculate role distribution
    const roles: Record<string, number> = {};
    agents.forEach(agent => {
      roles[agent.role] = (roles[agent.role] || 0) + 1;
    });

    return {
      agents,
      roles,
      schedules: state.schedules || [],
      morale_factors: state.morale_factors || {}
    };
  }

  private adaptResearch(state: SimStateV1): SimViewV2['research'] {
    this.markCovered('research_projects', !!state.research_projects);

    return {
      active_projects: state.research_projects || [],
      completed: state.completed_research || [],
      available: state.available_research || [],
      points_per_second: state.research_rate || 0
    };
  }

  private adaptAlerts(state: SimStateV1): SimViewV2['alerts'] {
    this.markCovered('alerts', !!state.alerts);

    const alerts = state.alerts || [];
    const categorized = {
      critical: alerts.filter((a: any) => a.type === 'critical'),
      warnings: alerts.filter((a: any) => a.type === 'warning'),
      info: alerts.filter((a: any) => a.type === 'info'),
      system: alerts.filter((a: any) => a.type === 'system')
    };

    return categorized;
  }

  private adaptUIState(state: SimStateV1): SimViewV2['ui_state'] {
    return {
      active_panels: state.active_panels || ['colony'],
      selected_building: state.selected_building,
      camera_position: state.camera_position || [0, 0],
      zoom_level: state.zoom_level || 1.0
    };
  }

  private markCovered(field: string, covered: boolean): void {
    this.coverageMap[field] = covered;
  }

  private updateCoverage(original: SimStateV1, adapted: SimViewV2): void {
    // Track which fields were successfully mapped
    const totalFields = Object.keys(this.coverageMap).length;
    const coveredFields = Object.values(this.coverageMap).filter(Boolean).length;
    const coverage = totalFields > 0 ? coveredFields / totalFields : 0;

    console.log(`[StateAdapter] Coverage: ${(coverage * 100).toFixed(1)}% (${coveredFields}/${totalFields} fields)`);
  }

  /**
   * Generate coverage report for receipts
   */
  getCoverageReport(): {
    total_fields: number;
    covered_fields: number;
    coverage_percentage: number;
    missing_fields: string[];
    timestamp: number;
  } {
    const totalFields = Object.keys(this.coverageMap).length;
    const coveredFields = Object.values(this.coverageMap).filter(Boolean).length;
    const coverage = totalFields > 0 ? coveredFields / totalFields : 0;
    
    const missingFields = Object.entries(this.coverageMap)
      .filter(([_, covered]) => !covered)
      .map(([field, _]) => field);

    return {
      total_fields: totalFields,
      covered_fields: coveredFields,
      coverage_percentage: Math.round(coverage * 100),
      missing_fields: missingFields,
      timestamp: Date.now()
    };
  }

  /**
   * Reverse adapter for backwards compatibility
   */
  reverse(modernState: SimViewV2): SimStateV1 {
    return {
      energy: modernState.core.energy,
      population: modernState.core.population,
      research: modernState.core.research,
      resources: modernState.resources,
      buildings: modernState.infrastructure.buildings,
      agents: modernState.population.agents,
      alerts: [
        ...modernState.alerts.critical,
        ...modernState.alerts.warnings,
        ...modernState.alerts.info,
        ...modernState.alerts.system
      ]
    };
  }
}

// Export singleton instance
export const stateAdapter = new StateAdapter();