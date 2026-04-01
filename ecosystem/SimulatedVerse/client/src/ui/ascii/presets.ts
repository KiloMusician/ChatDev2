// ui/ascii/presets.ts
import { AsciiEngine, type Layer } from './engine';
import { Starfield, WaveTunnel, LatticeGrid, ParticleBurst } from './shaders';

export type SceneConfig = {
  name: string;
  layers: Layer[];
  hint?: string;
};

export const SCENES: SceneConfig[] = [
  {
    name: 'Hologram Starfield',
    hint: 'Jarvis idle. Pointer modulates parallax; sceneEnergy boosts.',
    layers: [
      { shader: new Starfield(), init: { speed: 0.55, density: 140 } }
    ]
  },
  {
    name: 'Wave Tunnel',
    hint: 'Responds to tunnelFreq + pointer. Great for travel sequences.',
    layers: [
      { shader: new WaveTunnel(), init: { speed: 1.0 } }
    ]
  },
  {
    name: 'Neo Lattice',
    hint: 'Diagnostics grid. Lattice cell size responds to pointer/state.',
    layers: [
      { shader: new LatticeGrid() }
    ]
  },
  {
    name: 'Particle Burst',
    hint: 'Celebration / craft complete / rare drop reveal.',
    layers: [
      { shader: new ParticleBurst(), init: { density: 220 } }
    ]
  }
];

export function loadScene(engine: AsciiEngine, scene: SceneConfig) {
  engine.clearLayers();
  for (const L of scene.layers) engine.addLayer(L);
}