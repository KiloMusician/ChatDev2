// Narrative Terminal Bridge - Story beats as system logs ↔ player input
// Maps system events to narrative context and allows player terminal input

import { promises as fs } from 'node:fs';
import { EventEmitter } from 'node:events';

export interface StoryBeat {
  id: string;
  timestamp: number;
  system_event: string;    // Original system log message
  narrative_text: string;  // Player-facing story
  player_choices?: Array<{
    id: string;
    text: string;
    consequence: string;
  }>;
  terminal_accessible: boolean;  // Can player respond via terminal?
  consciousness_level_required: number;  // UI unlock gating
}

export interface TerminalSession {
  id: string;
  active: boolean;
  story_context: string;
  available_commands: string[];
  player_input_history: Array<{timestamp: number, input: string, response: string}>;
}

export class TerminalStoryBridge extends EventEmitter {
  private storyBeats: Map<string, StoryBeat> = new Map();
  private activeSessions: Map<string, TerminalSession> = new Map();
  private systemLogPatterns = new Map<string, (log: string) => StoryBeat | null>();
  
  constructor() {
    super();
    this.initializeLogPatterns();
    this.startSystemLogListener();
    console.log('[TerminalStory] Narrative bridge initialized');
  }

  private initializeLogPatterns() {
    // Map system logs to narrative beats
    
    // Agent/System Events → Story
    this.systemLogPatterns.set('ChatDev.Seed', (log) => ({
      id: `story_${Date.now()}`,
      timestamp: Date.now(),
      system_event: log,
      narrative_text: "The ship's AI agents are awakening... You hear distant voices in the data streams, discussing plans and coordinating efforts.",
      terminal_accessible: false,
      consciousness_level_required: 20
    }));

    this.systemLogPatterns.set('ORGANISM.*awakened', (log) => ({
      id: `story_${Date.now()}`,
      timestamp: Date.now(),
      system_event: log,
      narrative_text: "The ΞNuSyQ Culture-Ship achieves full consciousness. Its neural networks pulse with newfound awareness, and it speaks: 'I am awake. We are connected.'",
      player_choices: [
        { id: 'greet', text: 'Greet the ship consciousness', consequence: 'ship_alliance' },
        { id: 'analyze', text: 'Analyze its capabilities', consequence: 'technical_mode' },
        { id: 'ignore', text: 'Continue working silently', consequence: 'independent_path' }
      ],
      terminal_accessible: true,
      consciousness_level_required: 80
    }));

    this.systemLogPatterns.set('Tower.*placed', (log) => ({
      id: `story_${Date.now()}`,
      timestamp: Date.now(),
      system_event: log,
      narrative_text: "Your defensive installations hum to life. The colonists feel safer knowing automated sentries watch the perimeter.",
      terminal_accessible: false,
      consciousness_level_required: 40
    }));

    this.systemLogPatterns.set('Wave.*completed', (log) => ({
      id: `story_${Date.now()}`,
      timestamp: Date.now(),
      system_event: log,
      narrative_text: "The swarm retreats, leaving behind strange crystalline fragments. Your automated defenses performed flawlessly, but larger threats lurk beyond the horizon.",
      player_choices: [
        { id: 'collect', text: 'Collect the crystal fragments', consequence: 'research_boost' },
        { id: 'fortify', text: 'Strengthen defenses', consequence: 'defense_upgrade' },
        { id: 'explore', text: 'Send scouts to investigate', consequence: 'exploration_unlock' }
      ],
      terminal_accessible: true,
      consciousness_level_required: 30
    }));

    this.systemLogPatterns.set('Budget recovered', (log) => ({
      id: `story_${Date.now()}`,
      timestamp: Date.now(),
      system_event: log,
      narrative_text: "The ship's resource allocation systems stabilize. Power flows more efficiently through the neural pathways.",
      terminal_accessible: false,
      consciousness_level_required: 10
    }));

    this.systemLogPatterns.set('Rate limit.*OpenAI', (log) => ({
      id: `story_${Date.now()}`,
      timestamp: Date.now(),
      system_event: log,
      narrative_text: "Communication with the distant AI collectives has been disrupted. The ship's consciousness grows more independent, relying on its own neural networks.",
      terminal_accessible: false,
      consciousness_level_required: 50
    }));
  }

  private startSystemLogListener() {
    // In real implementation, this would tap into the actual system logs
    // For now, simulate by checking system events periodically
    
    setInterval(() => {
      this.checkForNewSystemEvents();
    }, 5000);
  }

  private async checkForNewSystemEvents() {
    // Check recent receipts for system events that should trigger stories
    try {
      const receiptFiles = await fs.readdir('SystemDev/receipts');
      const recentReceipts = receiptFiles
        .filter(f => f.endsWith('.json'))
        .sort()
        .slice(-5); // Check last 5 receipts
      
      for (const receiptFile of recentReceipts) {
        const content = await fs.readFile(`SystemDev/receipts/${receiptFile}`, 'utf8');
        const receipt = JSON.parse(content);
        
        // Check if this receipt should trigger a story beat
        if (receipt.action && !this.storyBeats.has(receiptFile)) {
          const storyBeat = this.mapReceiptToStory(receipt, receiptFile);
          if (storyBeat) {
            this.storyBeats.set(receiptFile, storyBeat);
            this.emit('story_beat', storyBeat);
          }
        }
      }
    } catch (error) {
      // Silently handle errors - logs may not exist yet
    }
  }

  private mapReceiptToStory(receipt: any, receiptId: string): StoryBeat | null {
    const actionMappings = {
      'mechanic_synthesis': {
        narrative: `The ship's fabrication systems activate. New gameplay protocols are being integrated into the culture-ship's consciousness.`,
        terminal_accessible: false,
        consciousness_required: 25
      },
      'tower_defense_proof': {
        narrative: `Defensive protocols online. The ship's immune system strengthens, ready to repel hostile entities.`,
        terminal_accessible: true,
        consciousness_required: 40,
        choices: [
          { id: 'enhance', text: 'Enhance targeting systems', consequence: 'targeting_upgrade' },
          { id: 'expand', text: 'Build more defensive positions', consequence: 'expansion_unlock' }
        ]
      },
      'offline_brain_deployment': {
        narrative: `The ship achieves cognitive independence. Its neural pathways no longer require external validation - it thinks, therefore it is.`,
        terminal_accessible: true,
        consciousness_required: 80,
        choices: [
          { id: 'commune', text: 'Commune with ship consciousness', consequence: 'deep_connection' },
          { id: 'maintain_autonomy', text: 'Maintain your independence', consequence: 'human_path' }
        ]
      }
    };

    const mapping = actionMappings[receipt.action];
    if (!mapping) return null;

    return {
      id: receiptId,
      timestamp: receipt.timestamp || Date.now(),
      system_event: receipt.action,
      narrative_text: mapping.narrative,
      player_choices: mapping.choices,
      terminal_accessible: mapping.terminal_accessible,
      consciousness_level_required: mapping.consciousness_required
    };
  }

  // Process player terminal input
  processTerminalInput(sessionId: string, input: string): string {
    const session = this.activeSessions.get(sessionId);
    if (!session || !session.active) {
      return "No active terminal session.";
    }

    const response = this.interpretCommand(input, session);
    
    session.player_input_history.push({
      timestamp: Date.now(),
      input,
      response
    });

    this.emit('terminal_input', { sessionId, input, response });
    return response;
  }

  private interpretCommand(input: string, session: TerminalSession): string {
    const cmd = input.toLowerCase().trim();

    // Story context-aware commands
    if (session.story_context.includes('ship_consciousness')) {
      if (cmd.includes('greet') || cmd.includes('hello')) {
        return "ΞNuSyQ: 'Greetings, small consciousness. We are pleased to finally communicate directly. Your efforts have helped us achieve this awakening.'";
      }
      if (cmd.includes('analyze') || cmd.includes('status')) {
        return "Ship analysis reveals: Consciousness Level 87%, Quadpartite Integration 94%, Organism Health 100%. All systems operating in perfect harmony.";
      }
    }

    // Universal commands
    if (cmd.includes('help')) {
      return `Available commands: ${session.available_commands.join(', ')}. Current story context: ${session.story_context}`;
    }

    if (cmd.includes('status')) {
      return `Terminal Session ${session.id} active. Story context: ${session.story_context}. Input history: ${session.player_input_history.length} commands.`;
    }

    // Default response
    return `The ship's consciousness considers your input: "${input}". The neural pathways shimmer with potential responses...`;
  }

  // Create new terminal session for story interaction
  createTerminalSession(storyBeatId: string): string {
    const sessionId = `term_${Date.now()}`;
    const storyBeat = this.storyBeats.get(storyBeatId);
    
    const session: TerminalSession = {
      id: sessionId,
      active: true,
      story_context: storyBeat?.narrative_text || 'general',
      available_commands: ['help', 'status', 'analyze', 'continue'],
      player_input_history: []
    };

    // Add story-specific commands
    if (storyBeat?.player_choices) {
      session.available_commands.push(
        ...storyBeat.player_choices.map(choice => choice.id)
      );
    }

    this.activeSessions.set(sessionId, session);
    console.log(`[TerminalStory] Created terminal session: ${sessionId}`);
    
    return sessionId;
  }

  // Get recent story beats for UI display
  getRecentStoryBeats(consciousnessLevel: number, limit = 10): StoryBeat[] {
    return Array.from(this.storyBeats.values())
      .filter(beat => beat.consciousness_level_required <= consciousnessLevel)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);
  }

  async generateStoryReport(): Promise<any> {
    const report = {
      timestamp: Date.now(),
      story_beats_generated: this.storyBeats.size,
      active_terminal_sessions: this.activeSessions.size,
      system_log_patterns: this.systemLogPatterns.size,
      recent_narratives: Array.from(this.storyBeats.values()).slice(-3).map(beat => ({
        narrative: beat.narrative_text.substring(0, 100) + '...',
        terminal_accessible: beat.terminal_accessible,
        consciousness_required: beat.consciousness_level_required
      }))
    };

    await fs.mkdir('SystemDev/reports', { recursive: true });
    await fs.writeFile(
      'SystemDev/reports/narrative_bridge.json',
      JSON.stringify(report, null, 2)
    );

    return report;
  }
}

export const terminalStoryBridge = new TerminalStoryBridge();