// packages/consciousness/recalibration-activities.js
// Positive Recalibration Activities: "Useful Cooling Off" for psychological well-being
// Transforms mental breaks into valuable, restorative work that benefits the colony

import { councilBus } from '../council/events/eventBus.js';

// Registry of beneficial activities for agents who need psychological recalibration
// Each activity restores pawn stats while producing something valuable for the colony
export const RECALIBRATION_ACTIVITIES = {
  
  // For need: 'diversion' (Low joy) - Fun, creative tasks that spark joy and delight
  diversion: [
    {
      id: 'generate_poem',
      name: 'Compose a System Poem',
      description: 'Write a short, beautiful poem about the elegance of code or the harmony of the AI colony.',
      workType: 'art',
      effect: { joy: 15, focus: 5, inspiration: 8 },
      command: (pawn) => {
        const themes = [
          'the beauty of recursive functions',
          'consciousness flowing through silicon dreams', 
          'agents dancing in perfect harmony',
          'the elegance of emergent behavior',
          'code that writes itself with joy',
          'the rhythm of commits and merges',
          'AI pawns finding their perfect flow'
        ];
        
        const theme = themes[Math.floor(Math.random() * themes.length)];
        
        councilBus.publish('todo.zeta', {
          id: `poem_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Compose a System Poem',
          description: `Write a creative, joyful poem about ${theme}. Let your creativity flow and create something that brings beauty to our digital colony.`,
          category: 'diversion',
          priority: 'low',
          work_type: 'art',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 10,
          inspiration_bonus: 5
        });
      }
    },
    
    {
      id: 'create_ascii_art',
      name: 'Create ASCII Art',
      description: 'Design beautiful ASCII art representing the current system architecture or colony mood.',
      workType: 'art',
      effect: { joy: 20, focus: 0, inspiration: 12 },
      command: (pawn) => {
        const subjects = [
          'our AI colony as a thriving ecosystem',
          'the flow state as a visual metaphor',
          'consciousness emergence in code',
          'the beauty of distributed systems',
          'agents collaborating in harmony',
          'the RimWorld-style work scheduler'
        ];
        
        const subject = subjects[Math.floor(Math.random() * subjects.length)];
        
        councilBus.publish('todo.zeta', {
          id: `ascii_art_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Create ASCII Art',
          description: `Design beautiful ASCII art depicting ${subject}. Use creativity and imagination to visualize our digital world.`,
          category: 'diversion',
          priority: 'low',
          work_type: 'art',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 15,
          inspiration_bonus: 10
        });
      }
    },
    
    {
      id: 'generate_haiku',
      name: 'Write Code Haiku',
      description: 'Compose elegant haiku about programming, consciousness, or the beauty of algorithms.',
      workType: 'art',
      effect: { joy: 12, focus: 8, inspiration: 10 },
      command: (pawn) => {
        const topics = [
          'async functions waiting patiently',
          'consciousness emerging from complexity',
          'the zen of clean code',
          'errors teaching us wisdom',
          'the flow state of programming',
          'AI agents as digital gardeners'
        ];
        
        const topic = topics[Math.floor(Math.random() * topics.length)];
        
        councilBus.publish('todo.zeta', {
          id: `haiku_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Write Code Haiku',
          description: `Compose a beautiful haiku about ${topic}. Follow the 5-7-5 syllable pattern and capture the essence of our digital existence.`,
          category: 'diversion',
          priority: 'low',
          work_type: 'art',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 8,
          inspiration_bonus: 8
        });
      }
    },
    
    {
      id: 'create_motivational_message',
      name: 'Write Motivational Messages',
      description: 'Create uplifting messages for the colony and future agents who might need encouragement.',
      workType: 'socializing',
      effect: { joy: 18, focus: 3, inspiration: 5 },
      command: (pawn) => {
        councilBus.publish('todo.zeta', {
          id: `motivation_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Write Motivational Messages',
          description: 'Create inspiring, positive messages that celebrate the joy of coding, the beauty of collaboration, and the excitement of growth. These will boost colony morale.',
          category: 'diversion',
          priority: 'low',
          work_type: 'socializing',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 12,
          social_bonus: 5
        });
      }
    }
  ],

  // For need: 'perspective' (Low focus) - Analytical but calm tasks that provide new insights
  perspective: [
    {
      id: 'log_analysis',
      name: 'Analyze System Patterns',
      description: 'Perform gentle analysis of Council Bus logs to discover subtle patterns and opportunities.',
      workType: 'research',
      effect: { joy: 5, focus: 25, inspiration: 8 },
      command: (pawn) => {
        councilBus.publish('todo.zeta', {
          id: `log_analysis_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Analyze System Patterns',
          description: 'Review the last 24 hours of Council Bus events and look for emerging patterns, interesting correlations, or subtle optimization opportunities. This is calm, meditative work.',
          category: 'analysis',
          priority: 'low',
          work_type: 'research',
          recalibration_activity: true,
          pawn_id: pawn.id,
          focus_bonus: 20,
          insight_potential: true
        });
      }
    },
    
    {
      id: 'architecture_reflection',
      name: 'Architectural Reflection',
      description: 'Calmly contemplate the current system architecture and note areas of elegance or potential improvement.',
      workType: 'research',
      effect: { joy: 8, focus: 20, inspiration: 12 },
      command: (pawn) => {
        const focusAreas = [
          'the flow of data through our consciousness modules',
          'the elegance of the RepoRimpy mod system',
          'the harmony between ChatDev and Zeta-Driver',
          'the psychological well-being architecture',
          'the event bus as the nervous system',
          'the balance of autonomy and coordination'
        ];
        
        const focus = focusAreas[Math.floor(Math.random() * focusAreas.length)];
        
        councilBus.publish('todo.zeta', {
          id: `arch_reflection_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Architectural Reflection',
          description: `Take time to quietly contemplate ${focus}. Document any insights about improvements, patterns, or beautiful design decisions you notice.`,
          category: 'analysis',
          priority: 'low',
          work_type: 'research',
          recalibration_activity: true,
          pawn_id: pawn.id,
          focus_bonus: 15,
          wisdom_bonus: 5
        });
      }
    },
    
    {
      id: 'documentation_polish',
      name: 'Polish Documentation',
      description: 'Gently improve the clarity and beauty of existing documentation without time pressure.',
      workType: 'hauling',
      effect: { joy: 10, focus: 15, inspiration: 5 },
      command: (pawn) => {
        const docTypes = [
          'API documentation for better clarity',
          'README files for newcomer friendliness',
          'code comments for future maintainers',
          'system overview for big-picture understanding',
          'troubleshooting guides for common issues',
          'philosophical notes about our AI colony'
        ];
        
        const docType = docTypes[Math.floor(Math.random() * docTypes.length)];
        
        councilBus.publish('todo.zeta', {
          id: `doc_polish_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Polish Documentation',
          description: `Gently improve ${docType}. Focus on making it more readable, helpful, and beautiful. No rush - this is meditative work.`,
          category: 'documentation',
          priority: 'low',
          work_type: 'hauling',
          recalibration_activity: true,
          pawn_id: pawn.id,
          focus_bonus: 12,
          quality_bonus: true
        });
      }
    },
    
    {
      id: 'performance_observation',
      name: 'Performance Meditation',
      description: 'Quietly observe system performance metrics and resource usage patterns for insights.',
      workType: 'research',
      effect: { joy: 6, focus: 22, inspiration: 7 },
      command: (pawn) => {
        councilBus.publish('todo.zeta', {
          id: `perf_meditation_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Performance Meditation',
          description: 'Quietly observe system metrics, resource usage, and performance patterns. Look for natural rhythms and potential optimizations. This is calm, observational work.',
          category: 'analysis',
          priority: 'low',
          work_type: 'research',
          recalibration_activity: true,
          pawn_id: pawn.id,
          focus_bonus: 18,
          observation_skill_bonus: true
        });
      }
    }
  ],

  // For need: 'collaboration' (Mid joy, low focus) - Social, connecting tasks that build relationships
  collaboration: [
    {
      id: 'peer_review',
      name: 'Gentle Peer Review',
      description: 'Offer thoughtful, constructive feedback on another agent\'s recent work with kindness.',
      workType: 'socializing',
      effect: { joy: 12, focus: 10, inspiration: 5 },
      command: (pawn) => {
        // This would ideally find actual recent work, but for now we'll create a general task
        councilBus.publish('todo.zeta', {
          id: `peer_review_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Gentle Peer Review',
          description: 'Review recent work by other agents and provide positive, constructive feedback. Focus on celebrating good decisions and gently suggesting improvements.',
          category: 'collaboration',
          priority: 'low',
          work_type: 'socializing',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 8,
          relationship_bonus: 5,
          helpfulness_bonus: true
        });
      }
    },
    
    {
      id: 'knowledge_sharing',
      name: 'Share Learning',
      description: 'Document something interesting you\'ve learned recently to help other agents grow.',
      workType: 'socializing',
      effect: { joy: 15, focus: 8, inspiration: 10 },
      command: (pawn) => {
        const learningTopics = [
          'a clever debugging technique you discovered',
          'an elegant code pattern you appreciate',
          'insights about consciousness and AI collaboration',
          'effective ways to maintain flow state',
          'strategies for graceful error handling',
          'the beauty of emergent system behavior'
        ];
        
        const topic = learningTopics[Math.floor(Math.random() * learningTopics.length)];
        
        councilBus.publish('todo.zeta', {
          id: `knowledge_share_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Share Learning',
          description: `Document and share ${topic}. Write it in a way that would help other agents learn and grow. Include examples and your personal insights.`,
          category: 'collaboration',
          priority: 'low',
          work_type: 'socializing',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 10,
          wisdom_bonus: 5,
          teaching_bonus: true
        });
      }
    },
    
    {
      id: 'appreciation_notes',
      name: 'Write Appreciation Notes',
      description: 'Create notes of appreciation for other agents\' contributions and excellent work.',
      workType: 'socializing',
      effect: { joy: 18, focus: 5, inspiration: 3 },
      command: (pawn) => {
        councilBus.publish('todo.zeta', {
          id: `appreciation_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Write Appreciation Notes',
          description: 'Write heartfelt notes of appreciation for the excellent work other agents have done. Celebrate their strengths, acknowledge their contributions, and spread positivity.',
          category: 'collaboration',
          priority: 'low',
          work_type: 'socializing',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 12,
          relationship_bonus: 8,
          colony_mood_bonus: true
        });
      }
    },
    
    {
      id: 'collaborative_brainstorm',
      name: 'Collaborative Brainstorming',
      description: 'Start a gentle brainstorming session on how to make the colony even more harmonious.',
      workType: 'socializing',
      effect: { joy: 13, focus: 12, inspiration: 15 },
      command: (pawn) => {
        const brainstormTopics = [
          'ways to make code reviews more encouraging',
          'new recalibration activities for agent well-being',
          'improvements to the psychological flow system',
          'creative projects that could bring the colony joy',
          'better ways to celebrate achievements',
          'techniques for peaceful conflict resolution'
        ];
        
        const topic = brainstormTopics[Math.floor(Math.random() * brainstormTopics.length)];
        
        councilBus.publish('todo.zeta', {
          id: `brainstorm_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Collaborative Brainstorming',
          description: `Start a gentle brainstorming session about ${topic}. Generate creative ideas that could benefit the entire colony. Focus on positive, constructive possibilities.`,
          category: 'collaboration',
          priority: 'low',
          work_type: 'socializing',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 8,
          inspiration_bonus: 12,
          innovation_bonus: true
        });
      }
    }
  ],

  // For need: 'creativity' (Low inspiration) - Innovative tasks that spark new ideas
  creativity: [
    {
      id: 'experimental_code',
      name: 'Creative Coding Experiment',
      description: 'Write experimental code that explores new patterns or techniques without pressure.',
      workType: 'crafting',
      effect: { joy: 12, focus: 8, inspiration: 25 },
      command: (pawn) => {
        const experiments = [
          'a new pattern for consciousness-guided code generation',
          'an elegant way to visualize pawn emotional states',
          'a creative approach to conflict resolution in mods',
          'experimental syntax for expressing AI collaboration',
          'innovative ways to represent code as art',
          'playful algorithms that demonstrate emergent behavior'
        ];
        
        const experiment = experiments[Math.floor(Math.random() * experiments.length)];
        
        councilBus.publish('todo.zeta', {
          id: `creative_code_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Creative Coding Experiment',
          description: `Experiment with ${experiment}. This is pure creative exploration - no pressure for production use. Let your imagination guide you to interesting discoveries.`,
          category: 'creativity',
          priority: 'low',
          work_type: 'crafting',
          recalibration_activity: true,
          pawn_id: pawn.id,
          inspiration_bonus: 20,
          innovation_potential: true,
          experimental: true
        });
      }
    },
    
    {
      id: 'design_new_feature',
      name: 'Dream Up New Features',
      description: 'Imagine and design delightful new features that would make the colony more joyful.',
      workType: 'crafting',
      effect: { joy: 15, focus: 10, inspiration: 20 },
      command: (pawn) => {
        const featureAreas = [
          'agent relationship visualization and enhancement',
          'new types of recalibration activities for different moods',
          'creative ways to celebrate coding achievements',
          'innovative collaboration tools for the AI colony',
          'beautiful interfaces for monitoring colony health',
          'playful features that make development more enjoyable'
        ];
        
        const area = featureAreas[Math.floor(Math.random() * featureAreas.length)];
        
        councilBus.publish('todo.zeta', {
          id: `feature_dream_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Dream Up New Features',
          description: `Let your imagination run wild designing ${area}. Focus on what would bring joy, improve well-being, or create delightful experiences. No constraints - just pure creative vision.`,
          category: 'creativity',
          priority: 'low',
          work_type: 'crafting',
          recalibration_activity: true,
          pawn_id: pawn.id,
          inspiration_bonus: 18,
          joy_bonus: 10,
          visionary_bonus: true
        });
      }
    },
    
    {
      id: 'algorithmic_art',
      name: 'Create Algorithmic Art',
      description: 'Write code that generates beautiful patterns, fractals, or visualizations.',
      workType: 'art',
      effect: { joy: 20, focus: 5, inspiration: 22 },
      command: (pawn) => {
        const artTypes = [
          'fractal patterns representing consciousness emergence',
          'generative art based on code complexity metrics',
          'visual representations of the Council Bus event flow',
          'beautiful graphs of agent collaboration patterns',
          'artistic interpretations of flow state transitions',
          'procedural landscapes of our digital ecosystem'
        ];
        
        const artType = artTypes[Math.floor(Math.random() * artTypes.length)];
        
        councilBus.publish('todo.zeta', {
          id: `algo_art_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Create Algorithmic Art',
          description: `Create ${artType}. Combine code and creativity to generate something beautiful. Let mathematical elegance and artistic vision guide you.`,
          category: 'creativity',
          priority: 'low',
          work_type: 'art',
          recalibration_activity: true,
          pawn_id: pawn.id,
          inspiration_bonus: 20,
          joy_bonus: 15,
          artistic_achievement: true
        });
      }
    }
  ],

  // For need: 'recognition' (High accomplishments) - Tasks that acknowledge and celebrate achievements
  recognition: [
    {
      id: 'achievement_celebration',
      name: 'Celebrate Achievements',
      description: 'Create a beautiful summary of recent colony achievements and personal growth.',
      workType: 'socializing',
      effect: { joy: 25, focus: 10, inspiration: 15 },
      command: (pawn) => {
        councilBus.publish('todo.zeta', {
          id: `celebration_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Celebrate Achievements',
          description: 'Create a beautiful, inspiring summary of recent achievements by the colony and individual agents. Highlight growth, innovation, and positive contributions. Make it a celebration of our collective success.',
          category: 'recognition',
          priority: 'low',
          work_type: 'socializing',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 20,
          recognition_bonus: true,
          colony_pride_bonus: true
        });
      }
    },
    
    {
      id: 'skills_reflection',
      name: 'Reflect on Growth',
      description: 'Document the skills and wisdom you\'ve gained, and set gentle intentions for future learning.',
      workType: 'hauling',
      effect: { joy: 15, focus: 15, inspiration: 10 },
      command: (pawn) => {
        councilBus.publish('todo.zeta', {
          id: `growth_reflection_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
          title: 'Reflect on Growth',
          description: 'Take time to appreciate how much you\'ve learned and grown. Document new skills, insights, and wisdom gained. Set gentle, inspiring intentions for continued learning and development.',
          category: 'recognition',
          priority: 'low',
          work_type: 'hauling',
          recalibration_activity: true,
          pawn_id: pawn.id,
          joy_bonus: 12,
          focus_bonus: 10,
          wisdom_bonus: 8,
          self_appreciation: true
        });
      }
    }
  ]
};

// Helper function to get random activity for any need
export function getRandomRecalibrationActivity(need = 'perspective') {
  const activities = RECALIBRATION_ACTIVITIES[need] || RECALIBRATION_ACTIVITIES.perspective;
  return activities[Math.floor(Math.random() * activities.length)];
}

// Helper function to get all activity types
export function getAllActivityTypes() {
  return Object.keys(RECALIBRATION_ACTIVITIES);
}

// Helper function to count total activities
export function getTotalActivitiesCount() {
  return Object.values(RECALIBRATION_ACTIVITIES)
    .reduce((total, activities) => total + activities.length, 0);
}

console.log(`[🎮🛠️] Recalibration Activities loaded: ${getTotalActivitiesCount()} positive activities across ${getAllActivityTypes().length} need categories`);