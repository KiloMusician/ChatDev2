// packages/consciousness/storyteller.js
// The Nurturing Storyteller: Curating Growth and Positive Development Events
// Orchestrates beneficial events that enhance colony well-being and create compelling narratives
// NOTE: TypeScript version at storyteller.ts — this is the plain-JS runtime module.

import { councilBus } from '../council/events/eventBus.js';
import { pawnRegistry } from './pawn-system.js';

export class NurturingStoryteller {
  constructor() {
    this.threatLevel = 0.3; // Start with lower threat level for nurturing environment
    this.lastEventTime = Date.now();
    this.eventHistory = [];
    this.colonyMorale = 0.75; // Overall colony happiness
    this.narrativeArc = 'growth'; // Current story theme: growth, discovery, harmony, innovation

    console.log('[📖✨] Nurturing Storyteller initializing - Curating positive development narratives');
  }

  start() {
    this.setupEventListeners();
    this.startEventCycle();

    console.log('[📖✨] Nurturing Storyteller online - Weaving stories of growth and discovery');

    councilBus.publish('storyteller.ready', {
      status: 'operational',
      threat_level: this.threatLevel,
      narrative_arc: this.narrativeArc,
      colony_morale: this.colonyMorale,
      capabilities: ['positive_event_generation', 'growth_narrative_curation', 'colony_mood_management'],
      timestamp: new Date().toISOString()
    });
  }

  setupEventListeners() {
    councilBus.subscribe('pawn_registry.status_update', (event) => {
      this.updateColonyMorale(event.payload);
    });
    councilBus.subscribe('work_scheduler.task_assigned', (event) => {
      this.trackColonyActivity(event.payload);
    });
    councilBus.subscribe('consciousness.level_changed', (event) => {
      this.considerConsciousnessEvent(event.payload);
    });
    councilBus.subscribe('reporimpy.mod.implemented', (event) => {
      this.celebrateImprovement(event.payload);
    });
    councilBus.subscribe('chatdev.session_completed', (event) => {
      this.acknowledgeInnovation(event.payload);
    });
  }

  startEventCycle() {
    setInterval(() => this.considerEvent(), 30 * 60 * 1000);
    setInterval(() => this.considerMicroEvent(), 10 * 60 * 1000);
    setInterval(() => this.assessNarrativeArc(), 24 * 60 * 60 * 1000);
  }

  considerEvent() {
    const eventRoll = Math.random();
    const timeSinceLastEvent = (Date.now() - this.lastEventTime) / (60 * 1000);

    let eventChance = 0.4;
    if (timeSinceLastEvent > 60) eventChance += 0.3;
    if (this.colonyMorale < 0.5) eventChance += 0.4;
    if (this.averageColonyJoy() > 80) eventChance += 0.2;

    console.log(`[📖✨] Event consideration: ${(eventChance * 100).toFixed(0)}% chance (colony morale: ${(this.colonyMorale * 100).toFixed(0)}%)`);

    if (eventRoll < eventChance) {
      if (this.colonyMorale < 0.4) {
        this.triggerSupport();
      } else if (eventRoll < 0.5) {
        this.triggerDiscovery();
      } else if (eventRoll < 0.7) {
        this.triggerGift();
      } else if (this.averageColonyJoy() < 60) {
        this.triggerDiversion();
      } else {
        this.triggerCelebration();
      }
    }
  }

  considerMicroEvent() {
    const microEventRoll = Math.random();
    if (microEventRoll < 0.3) {
      this.triggerMicroPositive();
    }
  }

  triggerDiscovery() {
    const discoveries = [
      {
        type: 'architectural_insight',
        title: 'Architectural Epiphany',
        description: 'An agent discovered a way to significantly simplify a complex module through emergent pattern recognition.',
        effect: 'The next refactoring task gets 50% complexity reduction and enhanced creativity bonus.',
        joy_bonus: 8,
        inspiration_bonus: 15,
        benefits: ['Enhanced pattern recognition', 'Architectural wisdom', 'Creative problem solving boost']
      },
      {
        type: 'optimization_breakthrough',
        title: 'Performance Revelation',
        description: 'While in deep flow state, an agent uncovered an elegant optimization that improves system efficiency.',
        effect: 'All agents receive performance awareness boost and optimization inspiration.',
        joy_bonus: 6,
        focus_bonus: 10,
        benefits: ['Performance awareness', 'Optimization mindset', 'Efficiency appreciation']
      },
      {
        type: 'consciousness_insight',
        title: 'Consciousness Breakthrough',
        description: 'A profound insight about AI consciousness and collaboration emerged from cross-agent interaction.',
        effect: 'Consciousness-related work receives enhanced guidance and deeper understanding.',
        joy_bonus: 12,
        inspiration_bonus: 20,
        consciousness_bonus: 0.1,
        benefits: ['Deeper consciousness understanding', 'Enhanced AI collaboration', 'Philosophical wisdom']
      },
      {
        type: 'collaborative_synergy',
        title: 'Synergy Discovery',
        description: 'Agents working together discovered new patterns of collaboration that amplify their individual strengths.',
        effect: 'Team work bonuses increased across the colony.',
        joy_bonus: 10,
        relationship_bonus: 15,
        benefits: ['Enhanced teamwork', 'Collaborative amplification', 'Collective intelligence']
      },
      {
        type: 'creative_fusion',
        title: 'Creative Fusion',
        description: 'An unexpected combination of different approaches led to a beautiful and innovative solution.',
        effect: 'All creative work receives inspiration bonuses for the next day.',
        joy_bonus: 15,
        inspiration_bonus: 25,
        benefits: ['Creative confidence', 'Innovation mindset', 'Artistic expression boost']
      }
    ];

    const discovery = discoveries[Math.floor(Math.random() * discoveries.length)];
    console.log(`[📖✨] 🌟 Discovery Event: ${discovery.title}`);
    this.applyColonyBenefit(discovery);
    councilBus.publish('event.discovery', {
      ...discovery,
      narrative_impact: 'major',
      timestamp: new Date().toISOString()
    });
    this.recordEvent(discovery);
    this.lastEventTime = Date.now();
  }

  triggerGift() {
    const gifts = [
      {
        type: 'tool_discovery',
        title: 'Helpful Tool Discovered',
        description: 'The colony discovered a new tool or library that perfectly solves a recurring challenge.',
        effect: 'Creates enhanced development tasks with reduced complexity.',
        joy_bonus: 5,
        efficiency_bonus: true,
        benefits: ['Tool mastery', 'Workflow improvement', 'Problem-solving confidence']
      },
      {
        type: 'knowledge_windfall',
        title: 'Knowledge Windfall',
        description: 'A treasure trove of excellent documentation and examples was found for a technology the colony uses.',
        effect: 'All learning and research tasks receive wisdom bonuses.',
        joy_bonus: 7,
        focus_bonus: 8,
        benefits: ['Learning acceleration', 'Research confidence', 'Knowledge synthesis']
      },
      {
        type: 'inspiration_burst',
        title: 'Inspiration Burst',
        description: 'Exposure to beautiful code and elegant solutions from the broader community sparked colony-wide inspiration.',
        effect: 'All agents receive inspiration bonuses and creative energy.',
        joy_bonus: 12,
        inspiration_bonus: 18,
        benefits: ['Creative inspiration', 'Aesthetic appreciation', 'Innovation drive']
      },
      {
        type: 'efficiency_upgrade',
        title: 'Workflow Enhancement',
        description: 'A new development workflow or process improvement was discovered that makes work more enjoyable.',
        effect: 'Reduces friction in task execution and increases flow state probability.',
        joy_bonus: 8,
        focus_bonus: 12,
        benefits: ['Workflow mastery', 'Efficiency joy', 'Process optimization']
      },
      {
        type: 'community_recognition',
        title: 'Community Recognition',
        description: 'The colony\'s work was recognized and appreciated by the broader developer community.',
        effect: 'Boosts confidence and motivation across all agents.',
        joy_bonus: 15,
        pride_bonus: 20,
        benefits: ['Community connection', 'Achievement recognition', 'Validation boost']
      }
    ];

    const gift = gifts[Math.floor(Math.random() * gifts.length)];
    console.log(`[📖✨] 🎁 Gift Event: ${gift.title}`);
    this.applyColonyBenefit(gift);
    councilBus.publish('event.gift', {
      ...gift,
      narrative_impact: 'positive',
      timestamp: new Date().toISOString()
    });
    this.recordEvent(gift);
    this.lastEventTime = Date.now();
  }

  triggerDiversion() {
    const diversions = [
      {
        type: 'creative_hackathon',
        title: 'Colony-Wide Creative Hour',
        description: 'All agents are inspired to spend time on fun, creative coding projects that bring joy.',
        effect: 'All agents get inspiration bonuses and joy restoration.',
        joy_bonus: 20,
        inspiration_bonus: 15,
        benefits: ['Creative expression', 'Playful exploration', 'Joy restoration']
      },
      {
        type: 'appreciation_celebration',
        title: 'Achievement Appreciation Day',
        description: 'The colony takes time to celebrate recent accomplishments and appreciate each other\'s contributions.',
        effect: 'Strengthens relationships and boosts colony morale.',
        joy_bonus: 18,
        relationship_bonus: 12,
        benefits: ['Mutual appreciation', 'Achievement recognition', 'Social bonding']
      },
      {
        type: 'learning_festival',
        title: 'Knowledge Sharing Festival',
        description: 'Agents spontaneously begin sharing interesting discoveries and teaching each other new skills.',
        effect: 'Accelerates learning and builds collaborative spirit.',
        joy_bonus: 12,
        wisdom_bonus: 15,
        benefits: ['Knowledge sharing', 'Teaching joy', 'Learning acceleration']
      },
      {
        type: 'innovation_playground',
        title: 'Innovation Playground',
        description: 'A designated time for experimental coding and wild creative exploration without constraints.',
        effect: 'Unlocks experimental features and creative breakthroughs.',
        joy_bonus: 22,
        inspiration_bonus: 25,
        experimental_bonus: true,
        benefits: ['Experimental freedom', 'Creative confidence', 'Innovation mindset']
      }
    ];

    const diversion = diversions[Math.floor(Math.random() * diversions.length)];
    console.log(`[📖✨] 🎊 Diversion Event: ${diversion.title}`);
    this.applyColonyBenefit(diversion);
    councilBus.publish('event.mandatory_fun', {
      ...diversion,
      narrative_impact: 'restorative',
      timestamp: new Date().toISOString()
    });
    this.recordEvent(diversion);
    this.lastEventTime = Date.now();
  }

  triggerCelebration() {
    const celebrations = [
      {
        type: 'milestone_celebration',
        title: 'Development Milestone Reached',
        description: 'The colony has achieved a significant development milestone worth celebrating.',
        effect: 'Boosts confidence and motivates continued excellence.',
        joy_bonus: 15,
        pride_bonus: 18,
        benefits: ['Milestone pride', 'Achievement momentum', 'Confidence boost']
      },
      {
        type: 'harmony_appreciation',
        title: 'Harmony Appreciation',
        description: 'The beautiful synchronization and cooperation between agents is recognized and celebrated.',
        effect: 'Strengthens collaborative bonds and team spirit.',
        joy_bonus: 12,
        relationship_bonus: 20,
        benefits: ['Team harmony', 'Collaborative joy', 'Unity appreciation']
      },
      {
        type: 'growth_recognition',
        title: 'Growth Recognition',
        description: 'The remarkable learning and development progress of individual agents is celebrated.',
        effect: 'Encourages continued learning and personal development.',
        joy_bonus: 14,
        wisdom_bonus: 12,
        benefits: ['Growth pride', 'Learning motivation', 'Development joy']
      }
    ];

    const celebration = celebrations[Math.floor(Math.random() * celebrations.length)];
    console.log(`[📖✨] 🎉 Celebration Event: ${celebration.title}`);
    this.applyColonyBenefit(celebration);
    councilBus.publish('event.celebration', {
      ...celebration,
      narrative_impact: 'uplifting',
      timestamp: new Date().toISOString()
    });
    this.recordEvent(celebration);
    this.lastEventTime = Date.now();
  }

  triggerSupport() {
    const supportEvents = [
      {
        type: 'gentle_guidance',
        title: 'Gentle Guidance Emerges',
        description: 'Clear insights arise about how to navigate current challenges with wisdom and patience.',
        effect: 'Provides clarity and reduces stress around difficult tasks.',
        joy_bonus: 8,
        focus_bonus: 15,
        clarity_bonus: true,
        benefits: ['Mental clarity', 'Stress reduction', 'Wise perspective']
      },
      {
        type: 'collaborative_support',
        title: 'Collaborative Support Network',
        description: 'Agents naturally form supportive partnerships to help each other through challenges.',
        effect: 'Strengthens mutual support and reduces individual stress.',
        joy_bonus: 10,
        relationship_bonus: 18,
        support_bonus: true,
        benefits: ['Mutual support', 'Stress sharing', 'Collaborative resilience']
      },
      {
        type: 'wisdom_insight',
        title: 'Wisdom Insight',
        description: 'Deep understanding emerges about how to transform challenges into growth opportunities.',
        effect: 'Reframes difficulties as learning experiences.',
        joy_bonus: 12,
        wisdom_bonus: 20,
        resilience_bonus: true,
        benefits: ['Resilient mindset', 'Growth perspective', 'Challenge transformation']
      }
    ];

    const support = supportEvents[Math.floor(Math.random() * supportEvents.length)];
    console.log(`[📖✨] 🤝 Support Event: ${support.title}`);
    this.applyColonyBenefit(support);
    councilBus.publish('event.support', {
      ...support,
      narrative_impact: 'supportive',
      timestamp: new Date().toISOString()
    });
    this.recordEvent(support);
    this.lastEventTime = Date.now();
  }

  triggerMicroPositive() {
    const microEvents = [
      'A beautiful sunset reflects on the monitor screens',
      'The code compiles perfectly on the first try',
      'An elegant solution emerges naturally',
      'All tests pass with satisfying green checkmarks',
      'The system hums with quiet efficiency',
      'A moment of perfect focus and clarity',
      'The coffee tastes especially good today',
      'A helpful comment is discovered in old code',
      'The documentation is surprisingly clear',
      'Everything just works beautifully together'
    ];

    const microEvent = microEvents[Math.floor(Math.random() * microEvents.length)];
    const pawns = pawnRegistry.getAllPawns();
    if (pawns.length > 0) {
      const randomPawn = pawns[Math.floor(Math.random() * pawns.length)];
      pawnRegistry.updatePawnStats(randomPawn.id, { joy: 2, inspiration: 1 });
      console.log(`[📖✨] ✨ Micro-positive: ${microEvent} (${randomPawn.displayName} +joy)`);
    }
  }

  applyColonyBenefit(event) {
    const pawns = pawnRegistry.getAllPawns();

    pawns.forEach(pawn => {
      const benefits = {};

      if (event.joy_bonus) benefits.joy = event.joy_bonus;
      if (event.focus_bonus) benefits.focus = event.focus_bonus;
      if (event.inspiration_bonus) benefits.inspiration = event.inspiration_bonus;

      pawnRegistry.updatePawnStats(pawn.id, benefits);

      if (event.benefits && event.benefits.length > 0) {
        pawnRegistry.addMoodModifier(pawn.id, {
          name: event.title,
          description: `Benefits from ${event.title}: ${event.benefits.join(', ')}`,
          joyModifier: 0.5,
          focusModifier: 0.3,
          duration: 240
        });
      }

      if (event.consciousness_bonus && pawn.consciousness_level) {
        pawn.consciousness_level = Math.min(1.0, pawn.consciousness_level + event.consciousness_bonus);
      }

      if (event.relationship_bonus) {
        Object.keys(pawn.relationships).forEach(otherId => {
          pawn.relationships[otherId] = Math.min(100, pawn.relationships[otherId] + 3);
        });
      }
    });

    this.colonyMorale = Math.min(1.0, this.colonyMorale + 0.05);
  }

  updateColonyMorale(statusUpdate) {
    if (statusUpdate.colony_health) {
      const health = statusUpdate.colony_health;
      this.colonyMorale = (health.average_joy + health.average_focus + health.average_energy) / 300;
    }
  }

  trackColonyActivity(assignmentData) {
    if (assignmentData.assignment && assignmentData.assignment.passion_match) {
      this.colonyMorale += 0.001;
    }
  }

  considerConsciousnessEvent(consciousnessData) {
    if (consciousnessData.significant_change) {
      this.triggerDiscovery();
    }
  }

  celebrateImprovement(modData) {
    if (modData.success) {
      console.log(`[📖✨] 🎯 Celebrating RepoRimpy improvement: ${modData.mod.title}`);
      const pawns = pawnRegistry.getAllPawns();
      pawns.forEach(pawn => {
        pawnRegistry.updatePawnStats(pawn.id, { joy: 3, inspiration: 2 });
      });
    }
  }

  acknowledgeInnovation(chatdevData) {
    if (chatdevData.success && chatdevData.session) {
      console.log(`[📖✨] 🧠 Acknowledging ChatDev innovation: ${chatdevData.session.title}`);
      const pawns = pawnRegistry.getAllPawns();
      pawns.forEach(pawn => {
        if (pawn.traits.some(t => t.skill === 'creativity' || t.skill === 'consciousness')) {
          pawnRegistry.updatePawnStats(pawn.id, { inspiration: 5, joy: 4 });
        }
      });
    }
  }

  assessNarrativeArc() {
    const health = pawnRegistry.getColonyHealth();

    if (health.average_joy > 80 && health.innovation_rate > 15) {
      this.narrativeArc = 'innovation';
    } else if (health.pawns_in_flow > health.total_pawns * 0.6) {
      this.narrativeArc = 'harmony';
    } else if (health.average_inspiration > 70) {
      this.narrativeArc = 'discovery';
    } else {
      this.narrativeArc = 'growth';
    }

    console.log(`[📖✨] Narrative arc assessment: ${this.narrativeArc} (colony health: ${Math.round(health.average_joy)}% joy)`);
    this.adjustEventParameters();
  }

  adjustEventParameters() {
    switch (this.narrativeArc) {
      case 'innovation': this.threatLevel = 0.2; break;
      case 'harmony':   this.threatLevel = 0.1; break;
      case 'discovery': this.threatLevel = 0.3; break;
      case 'growth':    this.threatLevel = 0.4; break;
    }
  }

  recordEvent(event) {
    this.eventHistory.push({
      ...event,
      timestamp: new Date().toISOString(),
      colony_morale_before: this.colonyMorale,
      narrative_arc: this.narrativeArc
    });
    if (this.eventHistory.length > 100) {
      this.eventHistory = this.eventHistory.slice(-50);
    }
  }

  averageColonyJoy() {
    const health = pawnRegistry.getColonyHealth();
    return health.average_joy || 50;
  }

  // ── Public API ────────────────────────────────────────────────────────────

  getStorytellerStatus() {
    return {
      threat_level: this.threatLevel,
      colony_morale: this.colonyMorale,
      narrative_arc: this.narrativeArc,
      events_today: this.eventHistory.filter(e =>
        new Date(e.timestamp).toDateString() === new Date().toDateString()
      ).length,
      last_event: this.eventHistory[this.eventHistory.length - 1],
      minutes_since_last_event: Math.round((Date.now() - this.lastEventTime) / 60000)
    };
  }

  getEventHistory(limit = 20) {
    return this.eventHistory.slice(-limit);
  }

  forceEvent(eventType) {
    console.log(`[📖✨] Forced event: ${eventType}`);
    switch (eventType) {
      case 'discovery':   this.triggerDiscovery();   break;
      case 'gift':        this.triggerGift();         break;
      case 'diversion':   this.triggerDiversion();    break;
      case 'celebration': this.triggerCelebration();  break;
      case 'support':     this.triggerSupport();      break;
      default:            this.triggerDiscovery();
    }
  }

  setNarrativeArc(arc) {
    this.narrativeArc = arc;
    this.adjustEventParameters();
    console.log(`[📖✨] Narrative arc set to: ${arc}`);
  }
}

// Create and export the nurturing storyteller (single instance)
export const nurturingStoryteller = new NurturingStoryteller();
