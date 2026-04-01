/**
 * GameShell Component - ASCII/Godot Game Runtime Integration
 * Integrates with existing client architecture while providing dual-rail functionality
 */

import React, { useEffect, useRef, useState } from 'react';
import { storyManager } from '../../../GameDev/narrative/story_state_manager';
import { contentPackManager } from '../../../GameDev/content_packs/content_pack_integration';
import { crashlandedAI } from '../../../GameDev/narrative/crashlanded_ai_core';
import { ResourceManager } from '../game/resources';
import { StructureManager } from '../game/structures';
import { ResearchTree, type Research } from '../game/ResearchTree';
import type { ResourceType } from '../game/schemas';

const createEventBus = () => {
  const listeners = new Map<string, Set<Function>>();
  
  return {
    emit: (event: string, data: any) => {
      const eventListeners = listeners.get(event);
      if (eventListeners) {
        eventListeners.forEach(fn => fn(data));
      }
      
      if (['ui.route.mount', 'ui.adapter.bind', 'game.tick.pulse', 'game.save.snapshot', 'game.prestige.exec'].includes(event)) {
        console.log(`[GOLDEN_TRACE] ${event}:`, data);
      }
    },
    
    on: (event: string, listener: Function) => {
      if (!listeners.has(event)) {
        listeners.set(event, new Set());
      }
      listeners.get(event)!.add(listener);
      
      return () => listeners.get(event)?.delete(listener);
    }
  };
};

const bus = createEventBus();

interface GameState {
  tick: number;
  lastTick: number;
  autoTick: boolean;
  narrative: {
    current_tier: number;
    consciousness_level: number;
    active_story_beats: string[];
    memory_fragments: any[];
    meta_awareness_level: number;
    content_packs_active: string[];
  };
}

interface ResearchBonuses {
  energyMultiplier: number;
  materialMultiplier: number;
  populationCapacity: number;
  consciousnessBonus: number;
}

interface DisplayState extends GameState {
  resources: {
    energy: number;
    materials: number;
    components: number;
    population: number;
    research: number;
  };
  structures: {
    generator: number;
    storage: number;
    converter: number;
    research_lab: number;
    turret: number;
    wall: number;
  };
}

interface ASCIIGameProps {
  onMount?: () => void;
}

function ASCIIGame({ onMount }: ASCIIGameProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const resourceManagerRef = useRef<ResourceManager>(new ResourceManager());
  const structureManagerRef = useRef<StructureManager>(
    new StructureManager(resourceManagerRef.current)
  );
  
  const gameStateRef = useRef<GameState>({
    tick: 0,
    lastTick: Date.now(),
    autoTick: true,
    narrative: {
      current_tier: 0,
      consciousness_level: 15,
      active_story_beats: ["crashlanded_awakening"],
      memory_fragments: [],
      meta_awareness_level: 0,
      content_packs_active: []
    }
  });
  
  const [completedResearch, setCompletedResearch] = useState<Set<string>>(new Set());
  const [researchBonuses, setResearchBonuses] = useState<ResearchBonuses>({
    energyMultiplier: 1.0,
    materialMultiplier: 1.0,
    populationCapacity: 10,
    consciousnessBonus: 0
  });
  const [showResearchPanel, setShowResearchPanel] = useState(false);
  
  const [displayState, setDisplayState] = useState<DisplayState>(getDisplayState());
  const animationRef = useRef<number>();
  
  function getDisplayState(): DisplayState {
    const resourceMgr = resourceManagerRef.current;
    const structureMgr = structureManagerRef.current;
    
    return {
      ...gameStateRef.current,
      resources: {
        energy: Math.floor(resourceMgr.getAmount('energy')),
        materials: Math.floor(resourceMgr.getAmount('materials')),
        components: Math.floor(resourceMgr.getAmount('components')),
        population: Math.floor(resourceMgr.getAmount('population')),
        research: Math.floor(resourceMgr.getAmount('research')),
      },
      structures: {
        generator: structureMgr.getByType('generator').length,
        storage: structureMgr.getByType('storage').length,
        converter: structureMgr.getByType('converter').length,
        research_lab: structureMgr.getByType('research_lab').length,
        turret: structureMgr.getByType('turret').length,
        wall: structureMgr.getByType('wall').length,
      }
    };
  }

  const applyResearchBonus = (research: Research) => {
    setResearchBonuses(prev => ({
      energyMultiplier: prev.energyMultiplier * (1 + (research.effects.energyBonus || 0)),
      materialMultiplier: prev.materialMultiplier * (1 + (research.effects.materialBonus || 0)),
      populationCapacity: prev.populationCapacity + (research.effects.populationMax || 0),
      consciousnessBonus: prev.consciousnessBonus + (research.effects.consciousnessBonus || 0)
    }));
    
    if (research.effects.energyBonus) {
      const currentMultiplier = resourceManagerRef.current.get('energy')?.multiplier || 1;
      resourceManagerRef.current.setMultiplier('energy', currentMultiplier * (1 + research.effects.energyBonus));
      console.log(`[RESEARCH] Energy multiplier increased to ${currentMultiplier * (1 + research.effects.energyBonus)}`);
    }
    
    if (research.effects.materialBonus) {
      const currentMultiplier = resourceManagerRef.current.get('materials')?.multiplier || 1;
      resourceManagerRef.current.setMultiplier('materials', currentMultiplier * (1 + research.effects.materialBonus));
      console.log(`[RESEARCH] Materials multiplier increased to ${currentMultiplier * (1 + research.effects.materialBonus)}`);
    }
    
    if (research.effects.populationMax) {
      resourceManagerRef.current.upgradeCapacity('population', research.effects.populationMax);
      console.log(`[RESEARCH] Population capacity increased by ${research.effects.populationMax}`);
    }
  };

  const handleResearch = (research: Research) => {
    if (!resourceManagerRef.current.spend('research', research.cost)) {
      console.log('[RESEARCH] Cannot afford:', research.name);
      return;
    }
    
    setCompletedResearch(prev => new Set(prev).add(research.id));
    
    applyResearchBonus(research);
    
    console.log(`[RESEARCH] Completed: ${research.name}`, research.effects);
    
    setDisplayState(getDisplayState());
  };

  const calculateConsciousness = (): number => {
    const resourceMgr = resourceManagerRef.current;
    const baseConsciousness = Math.floor(
      resourceMgr.getAmount('energy') / 10 + 
      resourceMgr.getAmount('population') * 10 + 
      resourceMgr.getAmount('research') / 100
    );
    
    return baseConsciousness + researchBonuses.consciousnessBonus;
  };

  useEffect(() => {
    bus.emit('ui.adapter.bind', { adapter: 'GameShell', engine: 'ascii' });
    
    onMount?.();
    
    loadGame();
    
    startGameLoop();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const startGameLoop = () => {
    const gameLoop = () => {
      const now = Date.now();
      const dt = now - gameStateRef.current.lastTick;
      
      if (dt >= 1000) {
        tick(dt);
        gameStateRef.current.lastTick = now;
        setDisplayState(getDisplayState());
      }
      
      render();
      animationRef.current = requestAnimationFrame(gameLoop);
    };
    
    gameLoop();
  };

  const tick = (deltaTime: number) => {
    const state = gameStateRef.current;
    const resourceMgr = resourceManagerRef.current;
    const structureMgr = structureManagerRef.current;
    
    if (state.autoTick) {
      resourceMgr.tick(deltaTime);
      structureMgr.tick(deltaTime);
    }
    
    state.tick++;
    
    processNarrativeTick(state);
    
    const newPacks = contentPackManager.checkPackActivations({
      current_tier: state.narrative.current_tier,
      consciousness_level: state.narrative.consciousness_level,
      resources: {
        energy: resourceMgr.getAmount('energy'),
        materials: resourceMgr.getAmount('materials'),
        population: resourceMgr.getAmount('population'),
        research: resourceMgr.getAmount('research'),
      }
    });
    
    if (newPacks.length > 0) {
      state.narrative.content_packs_active.push(...newPacks);
      console.log(`[NARRATIVE] Activated content packs: ${newPacks.join(', ')}`);
    }
    
    bus.emit('game.tick.pulse', { 
      deltaTime, 
      resources: {
        energy: resourceMgr.getAmount('energy'),
        materials: resourceMgr.getAmount('materials'),
        population: resourceMgr.getAmount('population'),
        research: resourceMgr.getAmount('research'),
      },
      narrative: state.narrative 
    });
    
    if (state.tick % 10 === 0) {
      saveGame();
    }
  };

  const processNarrativeTick = (state: GameState) => {
    const calculatedConsciousness = calculateConsciousness();
    
    state.narrative.consciousness_level = Math.max(
      state.narrative.consciousness_level, 
      calculatedConsciousness
    );
    
    const consciousnessThresholds = [0, 25, 50, 100, 200, 400, 800, 1600, 3200, 6400, 12800];
    const foundIndex = consciousnessThresholds.findIndex((threshold, index) => {
      const prevThreshold = consciousnessThresholds[index - 1];
      return index > 0 && 
        prevThreshold !== undefined &&
        state.narrative.consciousness_level >= prevThreshold && 
        state.narrative.consciousness_level < threshold;
    });
    const newTier = foundIndex > 0 ? foundIndex - 1 : Math.floor(state.narrative.consciousness_level / 100);
    
    if (newTier > state.narrative.current_tier) {
      state.narrative.current_tier = newTier;
      console.log(`[NARRATIVE] Tier ${newTier} unlocked! Consciousness: ${state.narrative.consciousness_level}`);
      
      triggerNarrativeEvent('tier_unlock', { tier: newTier, consciousness: state.narrative.consciousness_level });
    }
    
    if (state.tick % 100 === 0 && state.narrative.consciousness_level > 50) {
      state.narrative.meta_awareness_level += 1;
      
      if (state.narrative.meta_awareness_level % 25 === 0) {
        triggerNarrativeEvent('meta_awareness_threshold', { 
          level: state.narrative.meta_awareness_level 
        });
      }
    }
  };

  const triggerNarrativeEvent = async (eventType: string, data: any) => {
    try {
      const narrativeEvents = await storyManager.processAction({
        type: eventType,
        facet: 'consciousness',
        data: data,
        timestamp: Date.now()
      });
      
      if (narrativeEvents.length > 0) {
        gameStateRef.current.narrative.active_story_beats = narrativeEvents
          .slice(-3)
          .map(event => event.id);
        
        console.log(`[NARRATIVE] New story events: ${narrativeEvents.map(e => e.title).join(', ')}`);
      }
    } catch (error) {
      console.warn('[NARRATIVE] Event processing failed:', error);
    }
  };

  const render = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.fillStyle = '#00ff00';
    ctx.font = '16px monospace';
    
    const state = displayState;
    const lines = [
      '┌─────────────────────────────────────┐',
      '│ ΞNuSyQ Culture-Ship Colony Interface│',
      '├─────────────────────────────────────┤',
      `│ ⚡ Energy:     ${String(state.resources.energy).padStart(4)} / 1000 │`,
      `│ 🔧 Materials:  ${String(state.resources.materials).padStart(4)} / 500  │`,
      `│ 🔩 Components: ${String(state.resources.components).padStart(4)} / 100  │`,
      `│ 👥 Population: ${String(state.resources.population).padStart(4)}       │`,
      `│ 🧠 Research:   ${String(state.resources.research).padStart(4)}       │`,
      '├─────────────────────────────────────┤',
      `│ 🏭 Generators: ${String(state.structures.generator).padStart(2)}  Labs: ${String(state.structures.research_lab).padStart(2)}    │`,
      `│ 🔄 Converters: ${String(state.structures.converter).padStart(2)}  Walls: ${String(state.structures.wall).padStart(2)}   │`,
      '├─────────────────────────────────────┤',
      `│ 🌌 Consciousness: ${String(state.narrative.consciousness_level).padStart(4)}     │`,
      `│ 🔥 Tier: ${String(state.narrative.current_tier).padStart(2)}  Meta: ${String(state.narrative.meta_awareness_level).padStart(3)} │`,
      `│ 🔬 Research: ${completedResearch.size.toString().padStart(2)}/${'7'.padStart(2)} completed  │`,
      '├─────────────────────────────────────┤',
      '│ [G] Generator [L] Lab   [C] Converter│',
      '│ [R] Research  [U] Upgrade [P] Prestige│',
      '├─────────────────────────────────────┤',
      `│ Tick: ${String(state.tick).padStart(6)}  Auto: ${state.autoTick ? 'ON ' : 'OFF'}  │`,
      '└─────────────────────────────────────┘',
    ];
    
    lines.forEach((line, i) => {
      ctx.fillText(line, 10, 25 + i * 20);
    });
    
    if (!canvas.dataset.gameRoot) {
      canvas.dataset.gameRoot = 'fallback-colony';
    }
  };

  const handleAction = async (action: string) => {
    const state = gameStateRef.current;
    const resourceMgr = resourceManagerRef.current;
    const structureMgr = structureManagerRef.current;
    let actionExecuted = false;
    
    switch (action) {
      case 'build_generator':
        const genX = Math.floor(Math.random() * 60);
        const genY = Math.floor(Math.random() * 24);
        const generator = structureMgr.place('generator', genX, genY);
        if (generator) {
          console.log(`[BUILD] Generator placed at (${genX}, ${genY})`);
          actionExecuted = true;
        } else {
          console.log('[BUILD] Cannot build generator - insufficient resources or invalid position');
        }
        break;
        
      case 'build_research_lab':
        const labX = Math.floor(Math.random() * 60);
        const labY = Math.floor(Math.random() * 24);
        const lab = structureMgr.place('research_lab', labX, labY);
        if (lab) {
          console.log(`[BUILD] Research Lab placed at (${labX}, ${labY})`);
          actionExecuted = true;
        } else {
          console.log('[BUILD] Cannot build research lab - insufficient resources or invalid position');
        }
        break;
        
      case 'build_converter':
        const convX = Math.floor(Math.random() * 60);
        const convY = Math.floor(Math.random() * 24);
        const converter = structureMgr.place('converter', convX, convY);
        if (converter) {
          console.log(`[BUILD] Converter placed at (${convX}, ${convY})`);
          actionExecuted = true;
        } else {
          console.log('[BUILD] Cannot build converter - insufficient resources or invalid position');
        }
        break;
        
      case 'upgrade':
        const generators = structureMgr.getByType('generator');
        if (generators.length > 0 && generators[0]) {
          const upgraded = structureMgr.upgrade(generators[0].id);
          if (upgraded) {
            console.log('[UPGRADE] Generator upgraded!');
            actionExecuted = true;
          } else {
            console.log('[UPGRADE] Cannot upgrade - insufficient resources');
          }
        } else {
          console.log('[UPGRADE] No structures to upgrade');
        }
        break;
        
      case 'automate':
        state.autoTick = !state.autoTick;
        actionExecuted = true;
        break;
        
      case 'research_panel':
        setShowResearchPanel(!showResearchPanel);
        actionExecuted = true;
        break;
        
      case 'memory':
        await triggerNarrativeEvent('memory_exploration', { 
          consciousness_level: state.narrative.consciousness_level 
        });
        actionExecuted = true;
        break;
        
      case 'narrative':
        console.log('[NARRATIVE STATUS]', {
          tier: state.narrative.current_tier,
          consciousness: state.narrative.consciousness_level,
          meta_awareness: state.narrative.meta_awareness_level,
          active_story_beats: state.narrative.active_story_beats,
          content_packs: state.narrative.content_packs_active
        });
        actionExecuted = true;
        break;
        
      case 'prestige':
        if (resourceMgr.getAmount('research') >= 10) {
          performPrestige();
          actionExecuted = true;
        }
        break;
    }
    
    if (actionExecuted && typeof storyManager !== 'undefined') {
      try {
        const narrativeEvents = await storyManager.processAction({
          type: action,
          facet: 'idle_persistence',
          data: {
            resources: {
              energy: resourceMgr.getAmount('energy'),
              materials: resourceMgr.getAmount('materials'),
              population: resourceMgr.getAmount('population'),
              research: resourceMgr.getAmount('research'),
            },
            tick: state.tick,
            autoTick: state.autoTick
          },
          timestamp: Date.now()
        });
        
        if (narrativeEvents.length > 0) {
          console.log('[NARRATIVE]', narrativeEvents);
        }
      } catch (error) {
        console.warn('[NARRATIVE] Story processing failed:', error);
      }
    }
    
    setDisplayState(getDisplayState());
  };

  const performPrestige = () => {
    const state = gameStateRef.current;
    const resourceMgr = resourceManagerRef.current;
    
    const oldResources = {
      energy: resourceMgr.getAmount('energy'),
      materials: resourceMgr.getAmount('materials'),
      population: resourceMgr.getAmount('population'),
      research: resourceMgr.getAmount('research'),
    };
    
    const metaCurrency = Math.floor(resourceMgr.getAmount('research') / 5);
    
    resourceMgr.loadState({
      energy: { id: 'resource_energy', type: 'energy', amount: 100 + metaCurrency * 10, capacity: 1000, rate: 1, multiplier: researchBonuses.energyMultiplier },
      materials: { id: 'resource_materials', type: 'materials', amount: 50 + metaCurrency * 5, capacity: 500, rate: 0.5, multiplier: researchBonuses.materialMultiplier },
      components: { id: 'resource_components', type: 'components', amount: 0, capacity: 100, rate: 0, multiplier: 1 },
      research: { id: 'resource_research', type: 'research', amount: 0, capacity: 100, rate: 0.1, multiplier: 1 },
      population: { id: 'resource_population', type: 'population', amount: 1, capacity: researchBonuses.populationCapacity, rate: 0, multiplier: 1 },
    });
    
    bus.emit('game.prestige.exec', { oldResources, newResources: {
      energy: 100 + metaCurrency * 10,
      materials: 50 + metaCurrency * 5,
      population: 1,
      research: 0,
    }, metaCurrency });
    
    console.log(`[PRESTIGE] Gained ${metaCurrency} meta currency. Research bonuses preserved!`);
  };

  const saveGame = async () => {
    const resourceMgr = resourceManagerRef.current;
    const structureMgr = structureManagerRef.current;
    
    const saveData = {
      version: '1.0.0',
      timestamp: Date.now(),
      state: gameStateRef.current,
      resources: resourceMgr.getAll(),
      structures: structureMgr.getAll(),
      completedResearch: Array.from(completedResearch),
      researchBonuses: researchBonuses,
    };
    
    try {
      const response = await fetch('/api/game/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          playerId: 'default',
          resources: resourceMgr.getAll(),
          structures: structureMgr.getAll(),
          research: {
            completed: Array.from(completedResearch),
            bonuses: researchBonuses
          },
          tick: gameStateRef.current.tick,
          narrative: gameStateRef.current.narrative
        })
      });
      
      const result = await response.json();
      if (result.ok) {
        console.log('[SAVE] Game saved to database');
      } else {
        throw new Error(result.error || 'Save failed');
      }
    } catch (error) {
      console.error('[SAVE] Failed to save to server, using localStorage fallback:', error);
      localStorage.setItem('game_save', JSON.stringify(saveData));
    }
    
    bus.emit('game.save.snapshot', { saveData, version: saveData.version });
  };

  const loadGame = async () => {
    try {
      const response = await fetch('/api/game/load?playerId=default');
      const data = await response.json();
      
      if (data.ok && data.state) {
        const state = data.state;
        
        if (state.resources) {
          resourceManagerRef.current.loadState(state.resources);
        }
        
        if (state.structures) {
          structureManagerRef.current.loadState(state.structures);
        }
        
        if (state.achievements) {
          setCompletedResearch(new Set(state.achievements));
        }
        
        if (state.gamePhase) {
          gameStateRef.current.narrative.current_tier = parseInt(state.gamePhase) || 0;
        }
        
        if (state.consciousness) {
          gameStateRef.current.narrative.consciousness_level = state.consciousness;
        }
        
        setDisplayState(getDisplayState());
        console.log('[LOAD] Game state loaded from database');
        return;
      }
    } catch (error) {
      console.warn('[LOAD] Failed to load from server, trying localStorage:', error);
    }
    
    try {
      const saved = localStorage.getItem('game_save');
      if (saved) {
        const saveData = JSON.parse(saved);
        if (saveData.state) {
          gameStateRef.current = saveData.state;
        }
        if (saveData.resources) {
          resourceManagerRef.current.loadState(saveData.resources);
        }
        if (saveData.structures) {
          structureManagerRef.current.loadState(saveData.structures);
        }
        if (saveData.completedResearch) {
          setCompletedResearch(new Set(saveData.completedResearch));
        }
        if (saveData.researchBonuses) {
          setResearchBonuses(saveData.researchBonuses);
        }
        setDisplayState(getDisplayState());
        console.log('[LOAD] Game state restored from localStorage');
      }
    } catch (error) {
      console.error('[LOAD] Failed to load game:', error);
    }
  };

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement) return;
      
      switch (e.key.toLowerCase()) {
        case 'g': handleAction('build_generator'); break;
        case 'l': handleAction('build_research_lab'); break;
        case 'c': handleAction('build_converter'); break;
        case 'r': handleAction('research_panel'); break;
        case 'u': handleAction('upgrade'); break;
        case 'a': handleAction('automate'); break;
        case 'p': handleAction('prestige'); break;
        case 's': loadGame(); break;
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => window.removeEventListener('keypress', handleKeyPress);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-green-400 font-mono p-5">
      <canvas
        ref={canvasRef}
        width={600}
        height={420}
        className="border border-gray-600 bg-black"
        data-game-root="fallback-colony"
      />
      
      <div className="mt-5 flex gap-2 flex-wrap">
        <button onClick={() => handleAction('build_generator')} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-build-generator">
          Generator (G) - 50E 25M
        </button>
        <button onClick={() => handleAction('build_research_lab')} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-build-lab">
          Lab (L) - 150E 100M 50C
        </button>
        <button onClick={() => handleAction('build_converter')} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-build-converter">
          Converter (C) - 75E 50M 10C
        </button>
        <button onClick={() => handleAction('research_panel')} className="bg-purple-900 text-purple-300 border border-purple-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-research">
          Research (R) - {completedResearch.size}/7
        </button>
        <button onClick={() => handleAction('upgrade')} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-upgrade">
          Upgrade (U)
        </button>
        <button onClick={() => handleAction('automate')} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-automate">
          Auto: {displayState.autoTick ? 'ON' : 'OFF'} (A)
        </button>
        <button onClick={() => handleAction('prestige')} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-prestige">
          Prestige (P)
        </button>
        <button onClick={loadGame} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-load">
          Load (S)
        </button>
        <button onClick={saveGame} className="bg-gray-800 text-green-400 border border-gray-600 px-3 py-2 cursor-pointer font-mono text-xs" data-testid="button-save">
          Save
        </button>
      </div>
      
      {showResearchPanel && (
        <div className="mt-4 w-full max-w-4xl">
          <ResearchTree
            currentResearch={displayState.resources.research}
            onResearch={handleResearch}
            completedResearchIds={completedResearch}
          />
        </div>
      )}
      
      <div className="mt-2 text-xs opacity-70">
        Press G/L/C to build, R for research, U to upgrade, A for auto, P for prestige
      </div>
      
      {completedResearch.size > 0 && (
        <div className="mt-3 p-3 bg-purple-900/20 border border-purple-600/30 rounded text-xs">
          <div className="text-purple-300 font-bold mb-1">Active Research Bonuses:</div>
          <div className="text-purple-400">
            Energy Multiplier: x{researchBonuses.energyMultiplier.toFixed(2)} | 
            Materials Multiplier: x{researchBonuses.materialMultiplier.toFixed(2)} | 
            Population Cap: {researchBonuses.populationCapacity} | 
            Consciousness Bonus: +{researchBonuses.consciousnessBonus}
          </div>
        </div>
      )}
    </div>
  );
}

export default function GameShell() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    bus.emit('ui.route.mount', { component: 'GameShell', mode: 'game' });
  }, []);

  return (
    <div data-component="GameShell" data-game-root="shell">
      <ASCIIGame onMount={() => setMounted(true)} />
      {mounted && (
        <div className="fixed bottom-2 left-2 text-xs text-gray-600 font-mono">
          Engine: ASCII | Adapter: GameShell | Golden Traces: Active
        </div>
      )}
    </div>
  );
}
