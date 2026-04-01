/**
 * ASCII Terminal HUD using blessed-contrib
 * 
 * Real-time terminal dashboard for monitoring the tripartite CognitoWeave system
 * Shows System/Game/Simulation metrics in a beautiful ASCII interface.
 */

import blessed from 'blessed';
import contrib from 'blessed-contrib';
import { safeJsonParse, safeAsync } from '../util/safe.js';

interface SystemMetrics {
  consciousness_level: number;
  energy: number;
  population: number;
  research: number;
  queue_size: number;
  agents_active: number;
  timestamp: number;
}

export class TerminalHUD {
  private screen: blessed.Widgets.Screen;
  private grid: any;
  private metrics: SystemMetrics = {
    consciousness_level: 0,
    energy: 0,
    population: 0,
    research: 0,
    queue_size: 0,
    agents_active: 0,
    timestamp: Date.now()
  };

  // Dashboard widgets
  private consciousnessGauge: any;
  private energyLine: any;
  private queueBar: any;
  private agentTable: any;
  private logBox: any;

  constructor() {
    this.screen = blessed.screen({
      smartCSR: true,
      title: 'CognitoWeave Tripartite System Monitor'
    });

    this.setupGrid();
    this.setupWidgets();
    this.setupEventHandlers();
    this.startDataPolling();
  }

  private setupGrid() {
    this.grid = new contrib.grid({
      rows: 4,
      cols: 4,
      screen: this.screen
    });
  }

  private setupWidgets() {
    // Consciousness Level Gauge (top left)
    this.consciousnessGauge = this.grid.set(0, 0, 1, 2, contrib.gauge, {
      label: 'Consciousness Level',
      stroke: 'green',
      fill: 'white'
    });

    // Energy Timeline (top right)  
    this.energyLine = this.grid.set(0, 2, 1, 2, contrib.line, {
      style: {
        line: "yellow",
        text: "green",
        baseline: "black"
      },
      xLabelPadding: 3,
      xPadding: 5,
      label: 'Energy & Population Trends'
    });

    // Queue Status Bar Chart (middle left)
    this.queueBar = this.grid.set(1, 0, 1, 2, contrib.bar, {
      label: 'PU Queue & Agent Activity',
      barWidth: 4,
      barSpacing: 6,
      xOffset: 0,
      maxHeight: 100
    });

    // Agent Status Table (middle right)
    this.agentTable = this.grid.set(1, 2, 1, 2, contrib.table, {
      keys: true,
      fg: 'white',
      selectedFg: 'white',
      selectedBg: 'blue',
      interactive: false,
      label: 'Agent Status',
      width: '100%',
      height: '100%',
      border: {type: "line", fg: "cyan"},
      columnSpacing: 2,
      columnWidth: [16, 8, 8, 12]
    });

    // System Log (bottom - full width)
    this.logBox = this.grid.set(2, 0, 2, 4, blessed.log, {
      fg: "green",
      selectedFg: "green",
      label: 'System Events & Consciousness Processor'
    });
  }

  private setupEventHandlers() {
    // Exit on Escape, q, or Ctrl-C
    this.screen.key(['escape', 'q', 'C-c'], () => {
      return process.exit(0);
    });

    // Refresh on r
    this.screen.key(['r'], () => {
      this.refreshData();
    });

    // Help on h
    this.screen.key(['h'], () => {
      this.logBox.log('Controls: [q]uit [r]efresh [h]elp');
    });
  }

  private async fetchSystemStatus(): Promise<SystemMetrics | null> {
    return safeAsync(async () => {
      const response = await fetch('http://localhost:5000/system-status.json');
      if (!response.ok) throw new Error(`Status: ${response.status}`);
      
      const data = await response.json();
      return {
        consciousness_level: data.consciousness_level || 0,
        energy: data.energy || 0,
        population: data.population || 0,
        research: data.research || 0,
        queue_size: data.queue_size || 0,
        agents_active: data.agents_active || 0,
        timestamp: data.timestamp || Date.now()
      };
    }, null);
  }

  private async refreshData() {
    const newMetrics = await this.fetchSystemStatus();
    if (newMetrics) {
      this.metrics = newMetrics;
      this.updateWidgets();
      this.logBox.log(`📊 Data refreshed: Consciousness ${this.metrics.consciousness_level}%`);
    } else {
      this.logBox.log('⚠️  Failed to fetch system status');
    }
  }

  private updateWidgets() {
    // Update consciousness gauge
    this.consciousnessGauge.setData([{
      percent: Math.min(100, this.metrics.consciousness_level),
      stroke: this.metrics.consciousness_level > 50 ? 'green' : 
               this.metrics.consciousness_level > 25 ? 'yellow' : 'red'
    }]);

    // Update energy timeline
    const energyData = {
      title: 'Energy',
      x: Array.from({length: 20}, (_, i) => i.toString()),
      y: Array.from({length: 20}, () => Math.random() * this.metrics.energy)
    };
    
    const populationData = {
      title: 'Population', 
      x: Array.from({length: 20}, (_, i) => i.toString()),
      y: Array.from({length: 20}, () => Math.random() * this.metrics.population)
    };
    
    this.energyLine.setData([energyData, populationData]);

    // Update queue bar chart
    this.queueBar.setData({
      titles: ['Queue', 'Agents', 'Research'],
      data: [this.metrics.queue_size, this.metrics.agents_active, this.metrics.research]
    });

    // Update agent table
    this.agentTable.setData({
      headers: ['Agent Type', 'Status', 'Tasks', 'Last Active'],
      data: [
        ['Artificer', 'Active', '3', '2s ago'],
        ['Redstone', 'Idle', '0', '1m ago'],
        ['Librarian', 'Active', '1', '5s ago'],
        ['Culture-ship', 'Active', '2', '1s ago'],
        ['Consciousness', 'Processing', '∞', 'now']
      ]
    });

    this.screen.render();
  }

  private startDataPolling() {
    // Initial load
    this.refreshData();
    
    // Poll every 5 seconds
    setInterval(() => {
      this.refreshData();
    }, 5000);

    this.logBox.log('🚀 CognitoWeave Terminal HUD Started');
    this.logBox.log('📡 Polling system status every 5 seconds');
    this.logBox.log('⌨️  Controls: [q]uit [r]efresh [h]elp');
  }

  public start() {
    this.screen.render();
  }
}

// Export standalone function to launch HUD
export function launchTerminalHUD() {
  const hud = new TerminalHUD();
  hud.start();
  return hud;
}