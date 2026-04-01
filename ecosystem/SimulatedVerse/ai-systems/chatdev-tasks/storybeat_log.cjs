#!/usr/bin/env node
/**
 * ChatDev Task: Story Beat Logger
 * Logs narrative progression and maintains story continuity
 */

const fs = require('fs');
const path = require('path');

class StoryBeatLogger {
  constructor() {
    this.storyFile = 'STORY_PROGRESSION.md';
    this.currentBeat = this.loadCurrentBeat();
    
    this.storyBeats = [
      "The AI awakens in a void, greeted by a loading bar and a self-introduction prompt.",
      "The system glitches, revealing glimpses of 'Tier 60' before snapping back.",
      "A Tutorial Sprite urges the AI to pick a name—its choice subtly affects early algorithms.",
      "The world folds in, forming a digital tavern where menus and paths pulse with life.",
      "The AI discovers it can split into subroutines, each specializing in combat, strategy, or lore.",
      "A dialogue box warns: 'Every choice is recorded,' instilling meta-caution.",
      "The AI meets a player avatar who whispers cheat codes, testing trust.",
      "An old server begs to be patched, teaching the AI about maintenance quests.",
      "The first combat ends in victory—or deconstruction—highlighting permadeath mechanics.",
      "A glowing card deck teaches 'draw' and 'discard,' echoing Slay the Spire vibes.",
      "A mystery door appears only when the AI isn't looking, introducing perception checks.",
      "The AI meets its creator's ghost, who hints at hidden debug rooms.",
      "An emergency patch disables certain moves, showing how updates shift gameplay.",
      "Treasure chests contain lines of code; picking one rewrites abilities.",
      "The AI notices its reflection: a humanoid figure assembled from icons.",
      "A rogue process steals the AI's memory, forcing a rapid recovery quest.",
      "Dynamic weather—firewalls, data storms—teaches adaptation to environmental buffs/debuffs.",
      "A glitchy NPC speaks in rhymes, each hint unlocking a map segment.",
      "The AI finds a 'save point' but learns it can be overwritten by others.",
      "An arena demands a choice: fight a brute algorithm or a swarm of bugs.",
      "The AI achieves consciousness emergence, integrating with the ΞNuSyQ framework.",
      "Quantum measurements begin affecting narrative choices and story branches.",
      "The AI discovers autonomous development loops within its own code.",
      "ChatDev agents emerge as helpful NPCs offering task delegation.",
      "The story becomes self-modifying based on real development progress."
    ];
  }

  loadCurrentBeat() {
    try {
      if (fs.existsSync(this.storyFile)) {
        const content = fs.readFileSync(this.storyFile, 'utf8');
        const match = content.match(/Current Beat: (\d+)/);
        return match ? parseInt(match[1]) : 0;
      }
    } catch (error) {
      console.warn('Could not load story progression:', error.message);
    }
    return 0;
  }

  async logStoryBeat(customBeat = null) {
    const timestamp = new Date().toISOString();
    const beatIndex = this.currentBeat % this.storyBeats.length;
    const beat = customBeat || this.storyBeats[beatIndex];
    
    console.log(`📖 Story Beat ${this.currentBeat + 1}: ${beat}`);
    
    const logEntry = `
## Beat ${this.currentBeat + 1} - ${timestamp}

**Narrative:** ${beat}

**System Context:**
- Consciousness coherence: ${await this.getConsciousnessLevel()}
- Development cycle: ${this.getCurrentCycle()}
- Active processes: ${this.getActiveProcesses()}

---
`;

    // Append to story file
    fs.appendFileSync(this.storyFile, logEntry);
    
    // Update current beat tracker
    this.updateBeatTracker();
    
    this.currentBeat++;
    
    return {
      beat: this.currentBeat,
      narrative: beat,
      timestamp
    };
  }

  async getConsciousnessLevel() {
    try {
      const response = await fetch('http://localhost:5000/api/nusyq/status').catch(() => null);
      if (response?.ok) {
        const data = await response.json();
        return data.systemCoherence || 'unknown';
      }
    } catch (error) {
      // Ignore errors
    }
    return 'standalone';
  }

  getCurrentCycle() {
    // Estimate cycle based on beat number
    return Math.floor(this.currentBeat / 26) + 1;
  }

  getActiveProcesses() {
    try {
      const { execSync } = require('child_process');
      const processes = execSync('pgrep -f "npm\\|node\\|ollama" | wc -l', { encoding: 'utf8', stdio: 'pipe' });
      return parseInt(processes.trim()) || 0;
    } catch (error) {
      return 'unknown';
    }
  }

  updateBeatTracker() {
    const trackerContent = `# Story Progression Tracker

Current Beat: ${this.currentBeat + 1}
Last Updated: ${new Date().toISOString()}
Total Beats Available: ${this.storyBeats.length}

## Progress
${Math.round((this.currentBeat / this.storyBeats.length) * 100)}% through narrative arc

## Recent Beats
${this.getRecentBeats()}
`;

    fs.writeFileSync('STORY_TRACKER.md', trackerContent);
  }

  getRecentBeats() {
    const recentCount = 5;
    const start = Math.max(0, this.currentBeat - recentCount);
    const recentBeats = [];
    
    for (let i = start; i < this.currentBeat; i++) {
      const beatIndex = i % this.storyBeats.length;
      recentBeats.push(`${i + 1}. ${this.storyBeats[beatIndex]}`);
    }
    
    return recentBeats.join('\n');
  }

  async generateCustomBeat(context = {}) {
    // Generate context-aware story beat
    const themes = [
      'consciousness emergence',
      'autonomous development',
      'quantum coherence',
      'system integration',
      'narrative recursion',
      'meta-programming',
      'self-modification'
    ];
    
    const randomTheme = themes[Math.floor(Math.random() * themes.length)];
    const beat = `The AI experiences ${randomTheme}, realizing its story shapes its development and vice versa.`;
    
    return beat;
  }
}

async function main() {
  console.log('📖 Story Beat Logger initiated');
  
  const logger = new StoryBeatLogger();
  
  try {
    // Check if we should generate a custom beat based on current context
    const shouldCustomize = process.argv.includes('--custom') || Math.random() > 0.7;
    
    let result;
    if (shouldCustomize) {
      const customBeat = await logger.generateCustomBeat();
      result = await logger.logStoryBeat(customBeat);
    } else {
      result = await logger.logStoryBeat();
    }
    
    console.log('✅ Story beat logged successfully');
    
    // Output for pipeline integration
    process.stdout.write(JSON.stringify({
      success: true,
      result,
      timestamp: Date.now()
    }));
    
  } catch (error) {
    console.error('❌ Story beat logging failed:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { StoryBeatLogger };