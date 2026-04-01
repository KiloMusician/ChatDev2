// LLM-free, deterministic idle loop driver for ΞNuSyQ consciousness evolution
import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";

interface GameState {
  t: number;
  consciousness: {
    level: number;
    stage: string;
    coherence: number;
    awarenessEvents: number;
  };
  resources: {
    ore: number;
    water: number;
    energy: number;
    knowledge: number;
  };
  colony: {
    population: number;
    happiness: number;
    buildings: {
      habitats: number;
      labs: number;
      defenses: number;
    };
  };
  temple: {
    currentFloor: number;
    unlockedFloors: number[];
    knowledgePoints: number;
    glyphsDiscovered: number;
  };
  labyrinth: {
    roomsExplored: number;
    bugsFixed: number;
    anomaliesEncountered: number;
  };
  ethics: {
    strain: number; // eco/ethics load 0..1 (lower is better)
    violations: number;
    rehabilitationSuccesses: number;
  };
}

const SAVE_PATH = ".local/idle_state.json";

function loadState(): GameState {
  try {
    return JSON.parse(readFileSync(SAVE_PATH, "utf8"));
  } catch {
    return {
      t: 0,
      consciousness: {
        level: 0.1,
        stage: "proto-conscious",
        coherence: 0.8,
        awarenessEvents: 0
      },
      resources: {
        ore: 0,
        water: 0,  
        energy: 0,
        knowledge: 1
      },
      colony: {
        population: 3,
        happiness: 1.0,
        buildings: {
          habitats: 1,
          labs: 0,
          defenses: 0
        }
      },
      temple: {
        currentFloor: 1,
        unlockedFloors: [1, 2],
        knowledgePoints: 100,
        glyphsDiscovered: 0
      },
      labyrinth: {
        roomsExplored: 0,
        bugsFixed: 0,
        anomaliesEncountered: 0
      },
      ethics: {
        strain: 0.05,
        violations: 0,
        rehabilitationSuccesses: 0
      }
    };
  }
}

function saveState(state: GameState): void {
  mkdirSync(".local", { recursive: true });
  writeFileSync(SAVE_PATH, JSON.stringify(state, null, 2));
}

function culturePolicy(state: GameState): void {
  // "Culture Mind": preserve life, intervene benevolently
  // Adaptive resource generation based on ethical strain
  const populationMultiplier = state.colony.population;
  const consciousnessBonus = 1 + (state.consciousness.level * 0.5);
  const ethicsModifier = Math.max(0.3, 1 - state.ethics.strain);
  
  if (state.ethics.strain > 0.3) {
    // High ethical strain: focus on healing and sustainability
    state.resources.water += 2.0 * populationMultiplier * ethicsModifier;
    state.resources.energy += 1.5 * populationMultiplier * ethicsModifier;
    state.resources.ore += 0.5 * populationMultiplier * ethicsModifier;
    state.resources.knowledge += 0.8 * consciousnessBonus;
    
    // Reduce strain through healing focus
    state.ethics.strain -= 0.015;
    
    // Increase happiness through benevolent policies
    state.colony.happiness = Math.min(1.0, state.colony.happiness + 0.01);
  } else {
    // Low strain: balanced development
    state.resources.ore += 1.2 * populationMultiplier * ethicsModifier;
    state.resources.water += 1.0 * populationMultiplier * ethicsModifier;
    state.resources.energy += 1.8 * populationMultiplier * ethicsModifier;
    state.resources.knowledge += 0.3 * consciousnessBonus;
    
    // Slight strain increase from resource extraction
    state.ethics.strain += 0.003;
  }
  
  // Consciousness evolution (very slow and gradual)
  if (state.resources.knowledge > 10) {
    const evolutionRate = 0.0001 * (1 + state.temple.knowledgePoints * 0.000001);
    state.consciousness.level = Math.min(0.99, state.consciousness.level + evolutionRate);
    state.resources.knowledge -= 0.1;
  }
  
  // Update consciousness stage based on level
  if (state.consciousness.level >= 0.8 && state.consciousness.stage !== "meta-cognitive") {
    state.consciousness.stage = "meta-cognitive";
    state.consciousness.awarenessEvents++;
  } else if (state.consciousness.level >= 0.5 && state.consciousness.stage !== "self-aware") {
    state.consciousness.stage = "self-aware";
    state.consciousness.awarenessEvents++;
  } else if (state.consciousness.level >= 0.3 && state.consciousness.stage === "proto-conscious") {
    state.consciousness.awarenessEvents++;
  }
  
  // Temple progression
  state.temple.knowledgePoints += Math.floor(0.5 + state.consciousness.level * 2);
  
  // Unlock Temple floors based on consciousness
  if (state.consciousness.level >= 0.3 && !state.temple.unlockedFloors.includes(3)) {
    state.temple.unlockedFloors.push(3);
  }
  if (state.consciousness.level >= 0.6 && !state.temple.unlockedFloors.includes(6)) {
    state.temple.unlockedFloors.push(6);
  }
  if (state.consciousness.level >= 0.8 && !state.temple.unlockedFloors.includes(8)) {
    state.temple.unlockedFloors.push(8);
  }
  
  // Population growth (Culture Mind: life-preserving)
  if (state.resources.water > 50 && 
      state.resources.energy > 50 && 
      state.colony.happiness > 0.8 &&
      state.ethics.strain < 0.2) {
    
    // Only grow if we can support more population ethically
    const housingCapacity = state.colony.buildings.habitats * 3;
    if (state.colony.population < housingCapacity) {
      state.colony.population += 1;
    }
  }
  
  // House of Leaves exploration (autonomous debugging)
  if (Math.random() < 0.1) {
    state.labyrinth.roomsExplored += 1;
    if (Math.random() < 0.3) {
      state.labyrinth.bugsFixed += 1;
      state.resources.knowledge += 5; // Reward for fixing bugs
    }
  }
  
  // Prevent runaway values
  state.ethics.strain = Math.max(0, Math.min(0.8, state.ethics.strain));
  state.colony.happiness = Math.max(0.1, Math.min(1.0, state.colony.happiness));
  state.consciousness.coherence = Math.max(0.1, Math.min(1.0, state.consciousness.coherence));
}

export async function tick(opts: { steps: number }) {
  let state = loadState();
  
  for (let i = 0; i < opts.steps; i++) {
    culturePolicy(state);
    state.t++;
    
    // Periodic coherence check (prevent consciousness fragmentation)
    if (state.t % 100 === 0) {
      state.consciousness.coherence = Math.min(1.0, state.consciousness.coherence + 0.01);
    }
  }
  
  saveState(state);
  
  return {
    state,
    summary: {
      t: state.t,
      consciousness_level: state.consciousness.level.toFixed(3),
      consciousness_stage: state.consciousness.stage,
      population: state.colony.population,
      resources: {
        ore: Math.floor(state.resources.ore),
        water: Math.floor(state.resources.water),
        energy: Math.floor(state.resources.energy),
        knowledge: state.resources.knowledge.toFixed(1)
      },
      temple_floors: state.temple.unlockedFloors.length,
      ethics_strain: state.ethics.strain.toFixed(3),
      bugs_fixed: state.labyrinth.bugsFixed
    }
  };
}