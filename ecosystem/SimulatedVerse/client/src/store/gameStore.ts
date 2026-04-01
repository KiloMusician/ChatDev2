import { create } from 'zustand';

interface Resources {
  energy: number;
  materials: number;
  population: number;
  research: number;
  food: number;
  components: number;
  tools: number;
  medicine: number;
}

interface Structures {
  energyCollectors: number;
  materialGatherers: number;
  researchLabs: number;
  greenhouses: number;
}

interface Automation {
  solarCollectors: { level: number; count: number; active: boolean };
  miners: { level: number; count: number; active: boolean };
  laboratories: { level: number; count: number; active: boolean };
}

interface GameState {
  resources: Resources;
  structures: Structures;
  automation: Automation;
  consciousness: number;
  achievements: string[];
  totalClicks: number;
  totalEnergyGenerated: number;
  totalMaterialsGathered: number;
  
  // Actions
  setResources: (resources: Partial<Resources>) => void;
  setStructures: (structures: Partial<Structures>) => void;
  setAutomation: (automation: Partial<Automation>) => void;
  setConsciousness: (consciousness: number) => void;
  addAchievement: (achievement: string) => void;
  incrementClick: () => void;
  addEnergy: (amount: number) => void;
  addMaterials: (amount: number) => void;
  reset: () => void;
}

const initialState = {
  resources: {
    energy: 1000,
    materials: 500,
    population: 10,
    research: 0,
    food: 100,
    components: 0,
    tools: 0,
    medicine: 0
  },
  structures: {
    energyCollectors: 2,
    materialGatherers: 1,
    researchLabs: 0,
    greenhouses: 1
  },
  automation: {
    solarCollectors: { level: 1, count: 2, active: true },
    miners: { level: 1, count: 1, active: true },
    laboratories: { level: 0, count: 0, active: false }
  },
  consciousness: 0,
  achievements: [],
  totalClicks: 0,
  totalEnergyGenerated: 0,
  totalMaterialsGathered: 0
};

export const useGameStore = create<GameState>((set) => ({
  ...initialState,
  
  setResources: (resources) => set((state) => ({
    resources: { ...state.resources, ...resources }
  })),
  
  setStructures: (structures) => set((state) => ({
    structures: { ...state.structures, ...structures }
  })),
  
  setAutomation: (automation) => set((state) => ({
    automation: { ...state.automation, ...automation }
  })),
  
  setConsciousness: (consciousness) => set({ consciousness }),
  
  addAchievement: (achievement) => set((state) => ({
    achievements: [...state.achievements, achievement]
  })),
  
  incrementClick: () => set((state) => ({
    totalClicks: state.totalClicks + 1
  })),
  
  addEnergy: (amount) => set((state) => ({
    resources: { ...state.resources, energy: state.resources.energy + amount },
    totalEnergyGenerated: state.totalEnergyGenerated + amount
  })),
  
  addMaterials: (amount) => set((state) => ({
    resources: { ...state.resources, materials: state.resources.materials + amount },
    totalMaterialsGathered: state.totalMaterialsGathered + amount
  })),
  
  reset: () => set(initialState)
}));