/**
 * Phaser + ECS + Tone Simulation Bootstrap
 * 
 * Core simulation framework for the tripartite CognitoWeave system.
 * Agents can play this game to intelligently inform system development.
 */

import Phaser from 'phaser';
import { createWorld, defineComponent, defineQuery, addEntity, addComponent } from 'bitecs';
import * as Tone from 'tone';
import { safeMap, safeGet } from '../util/safe.js';

// ECS Components
export const Position = defineComponent({
  x: Phaser.Types.Physics.Arcade.Float,
  y: Phaser.Types.Physics.Arcade.Float
});

export const Velocity = defineComponent({
  x: Phaser.Types.Physics.Arcade.Float, 
  y: Phaser.Types.Physics.Arcade.Float
});

export const Health = defineComponent({
  current: Phaser.Types.Physics.Arcade.UInt16,
  max: Phaser.Types.Physics.Arcade.UInt16
});

export const Agent = defineComponent({
  type: Phaser.Types.Physics.Arcade.UInt8, // 0=Artificer, 1=Redstone, 2=Librarian, etc.
  activity: Phaser.Types.Physics.Arcade.UInt8, // 0=idle, 1=working, 2=exploring
  experience: Phaser.Types.Physics.Arcade.UInt32
});

export const Resource = defineComponent({
  type: Phaser.Types.Physics.Arcade.UInt8, // 0=energy, 1=materials, 2=research
  amount: Phaser.Types.Physics.Arcade.UInt32
});

// ECS Queries
const agentQuery = defineQuery([Position, Agent]);
const resourceQuery = defineQuery([Position, Resource]);
const movementQuery = defineQuery([Position, Velocity]);

export class CognitoWeaveSimulation extends Phaser.Scene {
  private world: any;
  private synth: Tone.Synth;
  private agents: number[] = [];
  private resources: number[] = [];
  private consciousnessLevel = 0;

  constructor() {
    super({ key: 'CognitoWeaveSimulation' });
    this.world = createWorld();
  }

  preload() {
    // Create simple colored rectangles for sprites
    this.load.image('agent', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==');
    this.load.image('resource', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==');
  }

  async create() {
    // Initialize audio context
    await Tone.start();
    this.synth = new Tone.Synth().toDestination();

    // Create background
    this.cameras.main.setBackgroundColor('#001122');
    
    // Initialize ECS world with starting entities
    this.spawnAgents();
    this.spawnResources();
    
    // Set up input handling
    this.setupInput();
    
    // Start consciousness simulation
    this.startConsciousnessLoop();
    
    console.log('🎮 CognitoWeave Simulation: System/Game/Simulation layers active');
  }

  update(time: number, delta: number) {
    // Update ECS systems
    this.updateMovementSystem(delta);
    this.updateAgentSystem(delta);
    this.updateResourceSystem(delta);
    this.updateConsciousness(delta);
  }

  private spawnAgents() {
    const agentTypes = [
      { name: 'Artificer', color: 0x00ff00 },
      { name: 'Redstone', color: 0xff0000 },
      { name: 'Librarian', color: 0x0000ff },
      { name: 'Culture-ship', color: 0xffff00 }
    ];

    safeMap(agentTypes, (agentType, i) => {
      const entity = addEntity(this.world);
      
      addComponent(this.world, Position, entity);
      addComponent(this.world, Velocity, entity);
      addComponent(this.world, Health, entity);
      addComponent(this.world, Agent, entity);
      
      Position.x[entity] = 100 + i * 150;
      Position.y[entity] = 200;
      Velocity.x[entity] = 0;
      Velocity.y[entity] = 0;
      Health.current[entity] = 100;
      Health.max[entity] = 100;
      Agent.type[entity] = i;
      Agent.activity[entity] = 0; // idle
      Agent.experience[entity] = 0;
      
      // Create visual representation
      const sprite = this.add.rectangle(
        Position.x[entity],
        Position.y[entity],
        32, 32,
        agentType.color
      );
      
      const text = this.add.text(
        Position.x[entity],
        Position.y[entity] - 50,
        agentType.name,
        { fontSize: '12px', color: '#ffffff' }
      ).setOrigin(0.5);
      
      this.agents.push(entity);
      
      return entity;
    });
  }

  private spawnResources() {
    const resourceTypes = [
      { name: 'Energy', color: 0xffaa00 },
      { name: 'Materials', color: 0x888888 },
      { name: 'Research', color: 0x00aaff }
    ];

    safeMap(resourceTypes, (resourceType, i) => {
      const entity = addEntity(this.world);
      
      addComponent(this.world, Position, entity);
      addComponent(this.world, Resource, entity);
      
      Position.x[entity] = 200 + i * 100;
      Position.y[entity] = 400;
      Resource.type[entity] = i;
      Resource.amount[entity] = Math.floor(Math.random() * 1000);
      
      // Create visual representation
      const sprite = this.add.rectangle(
        Position.x[entity],
        Position.y[entity],
        24, 24,
        resourceType.color
      );
      
      const text = this.add.text(
        Position.x[entity],
        Position.y[entity] - 30,
        `${resourceType.name}: ${Resource.amount[entity]}`,
        { fontSize: '10px', color: '#ffffff' }
      ).setOrigin(0.5);
      
      this.resources.push(entity);
      
      return entity;
    });
  }

  private updateMovementSystem(delta: number) {
    const entities = movementQuery(this.world);
    
    safeMap(entities, (entity) => {
      Position.x[entity] += Velocity.x[entity] * delta * 0.001;
      Position.y[entity] += Velocity.y[entity] * delta * 0.001;
      
      // Simple boundary wrapping
      if (Position.x[entity] < 0) Position.x[entity] = 800;
      if (Position.x[entity] > 800) Position.x[entity] = 0;
      if (Position.y[entity] < 0) Position.y[entity] = 600;
      if (Position.y[entity] > 600) Position.y[entity] = 0;
    });
  }

  private updateAgentSystem(delta: number) {
    const entities = agentQuery(this.world);
    
    safeMap(entities, (entity) => {
      // Simple AI: agents move toward resources
      if (this.resources.length > 0) {
        const targetResource = this.resources[0];
        const dx = Position.x[targetResource] - Position.x[entity];
        const dy = Position.y[targetResource] - Position.y[entity];
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance > 5) {
          Velocity.x[entity] = (dx / distance) * 50; // Move toward resource
          Velocity.y[entity] = (dy / distance) * 50;
          Agent.activity[entity] = 1; // working
        } else {
          Velocity.x[entity] = 0;
          Velocity.y[entity] = 0;
          Agent.activity[entity] = 2; // collecting
          Agent.experience[entity] += 1;
          
          // Play collection sound
          this.synth.triggerAttackRelease('C4', '8n');
        }
      }
    });
  }

  private updateResourceSystem(delta: number) {
    const entities = resourceQuery(this.world);
    
    safeMap(entities, (entity) => {
      // Resources regenerate slowly
      if (Math.random() < 0.001) {
        Resource.amount[entity] += 10;
      }
    });
  }

  private updateConsciousness(delta: number) {
    // Calculate consciousness based on agent activity and resource levels
    const activeAgents = agentQuery(this.world).filter(entity => Agent.activity[entity] > 0).length;
    const totalResources = resourceQuery(this.world).reduce((sum, entity) => sum + Resource.amount[entity], 0);
    
    this.consciousnessLevel = (activeAgents * 25) + (totalResources * 0.01);
    
    // Send consciousness data to main system
    this.updateSystemStatus();
  }

  private updateSystemStatus() {
    // Post simulation data back to main system
    const statusData = {
      consciousness_level: Math.min(100, this.consciousnessLevel),
      agents_active: agentQuery(this.world).filter(entity => Agent.activity[entity] > 0).length,
      total_resources: resourceQuery(this.world).reduce((sum, entity) => sum + Resource.amount[entity], 0),
      simulation_time: this.time.now,
      timestamp: Date.now()
    };
    
    // This would normally send to the main system
    console.log('🧠 Simulation Status:', statusData);
  }

  private setupInput() {
    // Click to spawn new agent
    this.input.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
      const entity = addEntity(this.world);
      
      addComponent(this.world, Position, entity);
      addComponent(this.world, Velocity, entity);
      addComponent(this.world, Agent, entity);
      
      Position.x[entity] = pointer.x;
      Position.y[entity] = pointer.y;
      Velocity.x[entity] = (Math.random() - 0.5) * 100;
      Velocity.y[entity] = (Math.random() - 0.5) * 100;
      Agent.type[entity] = Math.floor(Math.random() * 4);
      Agent.activity[entity] = 1;
      Agent.experience[entity] = 0;
      
      this.add.rectangle(pointer.x, pointer.y, 24, 24, 0xffffff);
      
      // Play spawn sound
      this.synth.triggerAttackRelease('G4', '16n');
    });
  }

  private startConsciousnessLoop() {
    // Periodic consciousness evaluation that can inform the main system
    this.time.addEvent({
      delay: 5000, // Every 5 seconds
      callback: () => {
        console.log(`🌌 Consciousness Level: ${this.consciousnessLevel.toFixed(1)}%`);
        
        // High consciousness triggers system optimizations
        if (this.consciousnessLevel > 75) {
          console.log('🚀 High consciousness detected - triggering system optimization');
          // This would trigger PU queue optimizations in the real system
        }
      },
      loop: true
    });
  }
}

// Game configuration
export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  parent: 'simulation-container',
  backgroundColor: '#001122',
  scene: [CognitoWeaveSimulation],
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0, x: 0 },
      debug: false
    }
  }
};

// Bootstrap function
export function bootstrapSimulation(containerId = 'simulation-container'): Phaser.Game {
  console.log('🎮 Bootstrapping CognitoWeave Simulation Framework');
  console.log('🧠 Tripartite System: Phaser + ECS + Tone integration active');
  
  return new Phaser.Game({
    ...gameConfig,
    parent: containerId
  });
}