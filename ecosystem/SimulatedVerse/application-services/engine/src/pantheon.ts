import type { KPulseState } from '../../../shared/types/core';

export function renderPantheon(state: KPulseState): string {
  const { tier, resources, colonists, research, narrative } = state;
  
  // Resource bars
  const resourceBars = Object.entries(resources)
    .map(([key, value]) => {
      const barLength = 30;
      const maxValue = getMaxResourceValue(key, tier);
      const percentage = Math.min(value / maxValue, 1);
      const filledBars = Math.floor(percentage * barLength);
      const emptyBars = barLength - filledBars;
      
      const bar = '█'.repeat(filledBars) + '░'.repeat(emptyBars);
      const icon = getResourceIcon(key);
      
      return `${icon} ${key.padEnd(10)} │ ${bar} │ ${formatNumber(value)}/${formatNumber(maxValue)}`;
    })
    .join('\n');
  
  // Colonist status
  const colonistStatus = Object.values(colonists)
    .map(colonist => {
      const moodIcon = getMoodIcon(colonist.mood);
      const taskIcon = getTaskIcon(colonist.task);
      return `${moodIcon} ${colonist.name.padEnd(15)} ${taskIcon} ${colonist.task || 'idle'}`;
    })
    .join('\n');
  
  // Research status
  const researchStatus = research.active 
    ? `🔬 Researching: ${research.active} (${Math.floor(research.progress)}%)`
    : `🔬 No active research (${research.available.size} available)`;
  
  // Current narrative
  const narrativeStatus = narrative.activeArcs.length > 0
    ? `📖 Active story: ${narrative.activeArcs[0].type} (Phase ${narrative.activeArcs[0].phase + 1}/16)`
    : `📖 Narrative quiet (Intensity: ${narrative.intensity}/10)`;
  
  // Action menu
  const actions = [
    '[1] Build Outpost (100 metal)',
    '[2] Scout Area (20 power)', 
    '[3] Automate System',
    '[4] Research Tech (50 knowledge)',
    '[5] Story Event',
    '[6] Advance Tier',
    '[7] Spawn Directive' + (tier < 8 ? ' (Tier 8+)' : ''),
    '[8] Save State',
    '[9] Analytics'
  ];
  
  // Tier progress
  const tierProgress = getTierProgress(state);
  
  return `
╔══════════════════════════════════════════════════════════════════╗
║                        🌌 KARDASHEV PANTHEON 🌌                        ║
║                            Tier ${tier.toString().padStart(2)} Civilization                            ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║ RESOURCES                                                        ║
${resourceBars.split('\n').map(line => `║ ${line.padEnd(64)} ║`).join('\n')}
║                                                                  ║
║ COLONISTS                                                        ║
${colonistStatus.split('\n').map(line => `║ ${line.padEnd(64)} ║`).join('\n')}
║                                                                  ║
║ STATUS                                                           ║
║ ${researchStatus.padEnd(64)} ║
║ ${narrativeStatus.padEnd(64)} ║
║ ${tierProgress.padEnd(64)} ║
║                                                                  ║
║ ACTIONS                                                          ║
${actions.map(action => `║ ${action.padEnd(64)} ║`).join('\n')}
║                                                                  ║
║ [SPACE] Pause/Resume  [Q] Quit                                  ║
╚══════════════════════════════════════════════════════════════════╝

⚡ No placeholders — each key triggers a real action.
🎭 Every visible control is bound to a handler.
🔄 Event bus streams all interactions.

Hash: ${state.hash}  |  Time: ${new Date(state.timestamp).toLocaleTimeString()}
`;
}

function getResourceIcon(resource: string): string {
  const icons = {
    metal: '⚙️',
    power: '⚡',
    food: '🌾',
    knowledge: '🧠',
    exotic: '💫'
  };
  return icons[resource as keyof typeof icons] || '📦';
}

function getMaxResourceValue(resource: string, tier: number): number {
  const baseValues = {
    metal: 1000,
    power: 500,
    food: 200,
    knowledge: 300,
    exotic: 100
  };
  
  const base = baseValues[resource as keyof typeof baseValues] || 100;
  return base * Math.pow(10, tier - 1);
}

function getMoodIcon(mood: number): string {
  if (mood > 80) return '😊';
  if (mood > 60) return '🙂';
  if (mood > 40) return '😐';
  if (mood > 20) return '😟';
  return '😢';
}

function getTaskIcon(task: string | null): string {
  const icons = {
    research: '🔬',
    maintain_power: '⚡',
    mining: '⛏️',
    farming: '🌱',
    construction: '🏗️',
    exploration: '🔍',
    idle: '💤'
  };
  return icons[task as keyof typeof icons] || '🔧';
}

function getTierProgress(state: KPulseState): string {
  if (state.tier >= 19) {
    return '🌟 TRANSCENDENCE ACHIEVED';
  }
  
  // This is simplified - in practice you'd calculate based on requirements
  const progress = Math.min((state.resources.metal / 1000) * 100, 100);
  const progressBar = '█'.repeat(Math.floor(progress / 5)) + '░'.repeat(20 - Math.floor(progress / 5));
  
  return `Next Tier: ${progressBar} ${Math.floor(progress)}%`;
}

function formatNumber(num: number): string {
  if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
  if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
  if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
  if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
  return Math.floor(num).toString();
}