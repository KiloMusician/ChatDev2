/**
 * Core type definitions for the KPulse/Culture-Ship system
 */

export interface KPulseState {
  tier: number;
  timestamp: number;
  resources: Resources;
  buildings: { [key: string]: Building };
  colonists: { [key: string]: Colonist };
  research: Research;
  narrative: Narrative;
  hash: string;
  checkpoints: any[];
}

export interface Resources {
  metal: number;
  power: number;
  food: number;
  knowledge: number;
  exotic: number;
}

export interface Building {
  id: string;
  type: string;
  level: number;
  efficiency: number;
  active: boolean;
  position?: { x: number; y: number };
}

export interface Colonist {
  id: string;
  name: string;
  traits: string[];
  mood: number;
  skills: { [skill: string]: number };
  task: string | null;
  relationships: { [colonistId: string]: number };
  voiceProfile: VoiceProfile;
  memoryBank: Memory[];
}

export interface VoiceProfile {
  tone: string;
  verbosity: number;
  quirks: string[];
}

export interface Memory {
  event: string;
  timestamp: number;
  emotionalWeight: number;
  tags: string[];
}

export interface Research {
  active: string | null;
  progress: number;
  completed: Set<string>;
  available: Set<string>;
  tree: ResearchNode[];
}

export interface ResearchNode {
  id: string;
  name: string;
  dependencies: string[];
  tier: number;
}

export interface Narrative {
  activeArcs: NarrativeArc[];
  recentEvents: StoryEvent[];
  storytellerMood: string;
  intensity: number;
  lastNarration: number;
  dialogueHistory: DialogueEntry[];
}

export interface NarrativeArc {
  id: string;
  type: string;
  phase: number;
  participants: string[];
  tension: number;
  outcomes: string[];
}

export interface StoryEvent {
  id: string;
  type: string;
  timestamp: number;
  participants: string[];
  description: string;
  impact: { [key: string]: number };
}

export interface DialogueEntry {
  speaker: string;
  message: string;
  timestamp: number;
  context: string;
}

export interface Directive {
  id: string;
  type: string;
  tier: number;
  status: 'pending' | 'active' | 'completed' | 'archived';
  priority: number;
  content: any;
  timestamp: number;
}

// Event bus types
export interface BusEvent {
  type: string;
  [key: string]: any;
}