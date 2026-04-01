import { apiRequest } from '@/lib/queryClient';

export interface Achievement {
  id: string;
  code: string;
  name: string;
  description: string;
  category: 'progression' | 'discovery' | 'social' | 'mastery' | 'time';
  icon?: string;
  points: number;
  requirement: {
    type: string;
    value: number;
    current?: number;
  };
  reward?: {
    resources?: Record<string, number>;
    unlocks?: string[];
  };
  hidden: boolean;
  unlocked?: boolean;
  unlockedAt?: Date;
  progress?: number;
}

class AchievementService {
  private achievements: Achievement[] = [];
  private listeners: ((achievement: Achievement) => void)[] = [];
  
  constructor() {
    this.initializeAchievements();
  }
  
  private initializeAchievements() {
    this.achievements = [
      // Progression Achievements
      {
        id: 'first-steps',
        code: 'FIRST_STEPS',
        name: 'First Steps',
        description: 'Gather your first 100 energy',
        category: 'progression',
        icon: '⚡',
        points: 10,
        requirement: { type: 'energy_total', value: 100 },
        hidden: false
      },
      {
        id: 'energy-baron',
        code: 'ENERGY_BARON',
        name: 'Energy Baron',
        description: 'Accumulate 10,000 energy',
        category: 'progression',
        icon: '⚡',
        points: 50,
        requirement: { type: 'energy_total', value: 10000 },
        hidden: false
      },
      {
        id: 'material-master',
        code: 'MATERIAL_MASTER',
        name: 'Material Master',
        description: 'Gather 5,000 materials',
        category: 'progression',
        icon: '🪨',
        points: 50,
        requirement: { type: 'materials_total', value: 5000 },
        hidden: false
      },
      {
        id: 'population-boom',
        code: 'POPULATION_BOOM',
        name: 'Population Boom',
        description: 'Reach 100 population',
        category: 'progression',
        icon: '👥',
        points: 100,
        requirement: { type: 'population', value: 100 },
        hidden: false
      },
      
      // Discovery Achievements
      {
        id: 'first-research',
        code: 'FIRST_RESEARCH',
        name: 'Scientific Method',
        description: 'Complete your first research',
        category: 'discovery',
        icon: '🔬',
        points: 20,
        requirement: { type: 'research_completed', value: 1 },
        hidden: false
      },
      {
        id: 'quantum-unlock',
        code: 'QUANTUM_UNLOCK',
        name: 'Quantum Breakthrough',
        description: 'Unlock quantum technology',
        category: 'discovery',
        icon: '⚛️',
        points: 100,
        requirement: { type: 'unlock_quantum', value: 1 },
        reward: { resources: { research: 500 } },
        hidden: false
      },
      {
        id: 'consciousness-awakening',
        code: 'CONSCIOUSNESS_AWAKENING',
        name: 'Consciousness Awakening',
        description: 'Reach 50% consciousness',
        category: 'discovery',
        icon: '🧠',
        points: 200,
        requirement: { type: 'consciousness', value: 50 },
        reward: { unlocks: ['advanced_ai'] },
        hidden: false
      },
      {
        id: 'transcendence',
        code: 'TRANSCENDENCE',
        name: 'Transcendence',
        description: 'Achieve 100% consciousness',
        category: 'discovery',
        icon: '🌟',
        points: 500,
        requirement: { type: 'consciousness', value: 100 },
        reward: { unlocks: ['culture_ship'] },
        hidden: true
      },
      
      // Social Achievements
      {
        id: 'first-multiplayer',
        code: 'FIRST_MULTIPLAYER',
        name: 'Connected',
        description: 'Join your first multiplayer game',
        category: 'social',
        icon: '🌐',
        points: 30,
        requirement: { type: 'multiplayer_joined', value: 1 },
        hidden: false
      },
      {
        id: 'cooperative-success',
        code: 'COOPERATIVE_SUCCESS',
        name: 'Teamwork',
        description: 'Complete a cooperative game',
        category: 'social',
        icon: '🤝',
        points: 50,
        requirement: { type: 'coop_completed', value: 1 },
        hidden: false
      },
      {
        id: 'chat-active',
        code: 'CHAT_ACTIVE',
        name: 'Communicator',
        description: 'Send 100 chat messages',
        category: 'social',
        icon: '💬',
        points: 20,
        requirement: { type: 'chat_messages', value: 100 },
        hidden: false
      },
      
      // Mastery Achievements
      {
        id: 'efficient-builder',
        code: 'EFFICIENT_BUILDER',
        name: 'Efficient Builder',
        description: 'Build 10 structures without waste',
        category: 'mastery',
        icon: '🏗️',
        points: 75,
        requirement: { type: 'efficient_builds', value: 10 },
        hidden: false
      },
      {
        id: 'speedrunner',
        code: 'SPEEDRUNNER',
        name: 'Speedrunner',
        description: 'Reach 30% consciousness in under 10 minutes',
        category: 'mastery',
        icon: '⏱️',
        points: 150,
        requirement: { type: 'speed_consciousness', value: 600 },
        hidden: true
      },
      {
        id: 'perfectionist',
        code: 'PERFECTIONIST',
        name: 'Perfectionist',
        description: 'Complete all research without failures',
        category: 'mastery',
        icon: '✨',
        points: 200,
        requirement: { type: 'perfect_research', value: 1 },
        hidden: true
      },
      
      // Time-based Achievements
      {
        id: 'daily-player',
        code: 'DAILY_PLAYER',
        name: 'Daily Dedication',
        description: 'Play for 7 consecutive days',
        category: 'time',
        icon: '📅',
        points: 50,
        requirement: { type: 'consecutive_days', value: 7 },
        hidden: false
      },
      {
        id: 'veteran',
        code: 'VETERAN',
        name: 'Veteran Commander',
        description: 'Play for 100 total hours',
        category: 'time',
        icon: '🎖️',
        points: 300,
        requirement: { type: 'play_hours', value: 100 },
        hidden: false
      }
    ];
  }
  
  async loadPlayerAchievements(playerId: string) {
    try {
      const response = await apiRequest(`/api/game/achievements/${playerId}`, {
        method: 'GET'
      }) as Response;
      
      if (response.ok) {
        const data = await response.json();
        // Merge with local achievements
        this.achievements = this.achievements.map(achievement => {
          const playerAchievement = data.find((pa: any) => pa.achievement.code === achievement.code);
          if (playerAchievement) {
            return {
              ...achievement,
              unlocked: true,
              unlockedAt: playerAchievement.unlockedAt,
              progress: playerAchievement.progress
            };
          }
          return achievement;
        });
      }
    } catch (error) {
      console.error('Failed to load achievements:', error);
    }
  }
  
  checkAchievement(type: string, value: number): Achievement | null {
    const achievement = this.achievements.find(
      a => !a.unlocked && a.requirement.type === type && value >= a.requirement.value
    );
    
    if (achievement) {
      this.unlockAchievement(achievement);
      return achievement;
    }
    
    return null;
  }
  
  checkProgress(gameState: any) {
    const checks = [
      { type: 'energy_total', value: gameState.totalEnergyGenerated || 0 },
      { type: 'materials_total', value: gameState.totalMaterialsGathered || 0 },
      { type: 'population', value: gameState.resources?.population || 0 },
      { type: 'consciousness', value: gameState.consciousness || 0 },
      { type: 'research_completed', value: gameState.researchCompleted?.length || 0 }
    ];
    
    const unlocked: Achievement[] = [];
    
    for (const check of checks) {
      const achievement = this.checkAchievement(check.type, check.value);
      if (achievement) {
        unlocked.push(achievement);
      }
    }
    
    return unlocked;
  }
  
  private unlockAchievement(achievement: Achievement) {
    achievement.unlocked = true;
    achievement.unlockedAt = new Date();
    achievement.progress = 100;
    
    // Notify listeners
    this.listeners.forEach(listener => listener(achievement));
    
    // Save to server
    this.saveAchievementUnlock(achievement);
  }
  
  private async saveAchievementUnlock(achievement: Achievement) {
    const playerId = localStorage.getItem('playerId') || 'default-player';
    
    try {
      await apiRequest('/api/game/achievement/unlock', {
        method: 'POST',
        body: JSON.stringify({
          playerId,
          achievementCode: achievement.code
        })
      });
    } catch (error) {
      console.error('Failed to save achievement unlock:', error);
    }
  }
  
  onAchievementUnlocked(listener: (achievement: Achievement) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
  
  getAchievements() {
    return this.achievements;
  }
  
  getAchievementsByCategory(category: Achievement['category']) {
    return this.achievements.filter(a => a.category === category);
  }
  
  getUnlockedCount() {
    return this.achievements.filter(a => a.unlocked).length;
  }
  
  getTotalPoints() {
    return this.achievements
      .filter(a => a.unlocked)
      .reduce((sum, a) => sum + a.points, 0);
  }
  
  getProgress() {
    const total = this.achievements.length;
    const unlocked = this.getUnlockedCount();
    return (unlocked / total) * 100;
  }
}

export const achievementService = new AchievementService();