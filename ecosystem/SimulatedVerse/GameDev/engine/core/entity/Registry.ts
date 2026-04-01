// ECS Registry - Lightweight Entity Component System
// Bridges symbolic entity operations to literal component management

export type EntityId = string;
export type ComponentType = string;

export interface Component {
  type: ComponentType;
  data: any;
}

export interface Entity {
  id: EntityId;
  components: Map<ComponentType, any>;
  created: number;
  active: boolean;
}

// Component definitions
export interface Position { x: number; y: number; z?: number; }
export interface Position { x: number; y: number; z?: number; }
export interface Health { current: number; max: number; }
export interface Inventory { items: Array<{id: string, quantity: number}>; capacity: number; }
export interface AIState { state: string; target?: EntityId; data?: any; }
export interface Buildable { cost: Record<string, number>; build_time: number; progress?: number; }
export interface Projectile { target: EntityId; damage: number; speed: number; effects?: string[]; }
export interface Tower { range: number; damage: number; fire_rate: number; last_shot: number; }
export interface Enemy { path: Position[]; path_index: number; reward: number; }
export interface Citizen { job: string; skill_level: number; happiness: number; }

export class Registry {
  private entities = new Map<EntityId, Entity>();
  private componentIndex = new Map<ComponentType, Set<EntityId>>();
  private nextEntityId = 1;

  constructor() {
    console.log('[Registry] ECS registry initialized');
  }

  // Create new entity
  createEntity(kind: string = 'generic', initialComponents: Record<ComponentType, any> = {}): EntityId {
    const entityId = `${kind}_${this.nextEntityId++}`;
    
    const entity: Entity = {
      id: entityId,
      components: new Map(),
      created: Date.now(),
      active: true
    };

    this.entities.set(entityId, entity);

    // Add initial components
    for (const [componentType, data] of Object.entries(initialComponents)) {
      this.addComponent(entityId, componentType, data);
    }

    console.log(`[Registry] Created entity ${entityId} with ${entity.components.size} components`);
    return entityId;
  }

  // Add component to entity
  addComponent(entityId: EntityId, componentType: ComponentType, data: any): boolean {
    const entity = this.entities.get(entityId);
    if (!entity || !entity.active) return false;

    entity.components.set(componentType, data);
    
    // Update component index
    if (!this.componentIndex.has(componentType)) {
      this.componentIndex.set(componentType, new Set());
    }
    this.componentIndex.get(componentType)!.add(entityId);

    return true;
  }

  // Get component from entity
  getComponent<T = any>(entityId: EntityId, componentType: ComponentType): T | null {
    const entity = this.entities.get(entityId);
    if (!entity || !entity.active) return null;

    return entity.components.get(componentType) || null;
  }

  // Remove component from entity
  removeComponent(entityId: EntityId, componentType: ComponentType): boolean {
    const entity = this.entities.get(entityId);
    if (!entity) return false;

    const removed = entity.components.delete(componentType);
    if (removed) {
      this.componentIndex.get(componentType)?.delete(entityId);
    }

    return removed;
  }

  // Get single entity by ID
  getEntity(entityId: EntityId): Entity | null {
    return this.entities.get(entityId) || null;
  }

  // Get all entities
  getAllEntities(): Entity[] {
    return Array.from(this.entities.values()).filter(e => e.active);
  }

  // Query entities with specific components
  query(withComponents: ComponentType[]): EntityId[] {
    if (withComponents.length === 0) return [];

    // Start with entities that have the first component
    let candidates = this.componentIndex.get(withComponents[0]);
    if (!candidates) return [];

    // Filter by remaining components
    for (let i = 1; i < withComponents.length; i++) {
      const componentEntities = this.componentIndex.get(withComponents[i]);
      if (!componentEntities) return [];
      
      candidates = new Set([...candidates].filter(id => componentEntities.has(id)));
    }

    // Filter out inactive entities
    return Array.from(candidates).filter(id => {
      const entity = this.entities.get(id);
      return entity && entity.active;
    });
  }

  // Get all entities of a specific kind
  getEntitiesByKind(kind: string): EntityId[] {
    return Array.from(this.entities.keys())
      .filter(id => id.startsWith(`${kind}_`))
      .filter(id => this.entities.get(id)?.active);
  }

  // Destroy entity
  destroyEntity(entityId: EntityId): boolean {
    const entity = this.entities.get(entityId);
    if (!entity) return false;

    entity.active = false;

    // Remove from component indices
    for (const componentType of entity.components.keys()) {
      this.componentIndex.get(componentType)?.delete(entityId);
    }

    // Keep entity for potential resurrection, but mark inactive
    console.log(`[Registry] Destroyed entity ${entityId}`);
    return true;
  }

  // Utility: Create common game entities
  createTower(position: Position, towerType = 'basic'): EntityId {
    const towerData = this.getTowerDefaults(towerType);
    
    return this.createEntity('tower', {
      'Position': position,
      'Tower': towerData,
      'Health': { current: 100, max: 100 }
    });
  }

  createEnemy(path: Position[], enemyType = 'basic'): EntityId {
    const enemyData = this.getEnemyDefaults(enemyType);
    
    return this.createEntity('enemy', {
      'Position': path[0],
      'Health': enemyData.health,
      'Enemy': { path, path_index: 0, reward: enemyData.reward }
    });
  }

  createCitizen(position: Position, job = 'unemployed'): EntityId {
    return this.createEntity('citizen', {
      'Position': position,
      'Health': { current: 100, max: 100 },
      'AIState': { state: 'idle' },
      'Citizen': { job, skill_level: 1, happiness: 50 }
    });
  }

  // Get registry statistics
  getStats(): any {
    const stats = {
      total_entities: this.entities.size,
      active_entities: Array.from(this.entities.values()).filter(e => e.active).length,
      component_types: this.componentIndex.size,
      recent_events: this.eventHistory.slice(-10).map(e => ({ type: e.type, timestamp: e.timestamp }))
    };

    // Count entities by type
    const entityCounts = {};
    for (const entity of this.entities.values()) {
      if (entity.active) {
        const kind = entity.id.split('_')[0];
        entityCounts[kind] = (entityCounts[kind] || 0) + 1;
      }
    }
    stats['entity_counts'] = entityCounts;

    // Count by component type
    const componentCounts = {};
    for (const [componentType, entities] of this.componentIndex.entries()) {
      componentCounts[componentType] = entities.size;
    }
    stats['component_counts'] = componentCounts;

    return stats;
  }

  // Save/Load entity snapshot
  async saveSnapshot(filename: string): Promise<boolean> {
    try {
      const snapshot = {
        timestamp: Date.now(),
        entities: Array.from(this.entities.values()).map(entity => ({
          id: entity.id,
          components: Object.fromEntries(entity.components),
          created: entity.created,
          active: entity.active
        })),
        next_entity_id: this.nextEntityId
      };

      await fs.mkdir('GameDev/content/snapshots', { recursive: true });
      await fs.writeFile(filename, JSON.stringify(snapshot, null, 2));
      
      console.log(`[Registry] Saved snapshot: ${filename} (${this.entities.size} entities)`);
      return true;
    } catch (error) {
      console.error('[Registry] Save failed:', error);
      return false;
    }
  }

  async loadSnapshot(filename: string): Promise<boolean> {
    try {
      const content = await fs.readFile(filename, 'utf8');
      const snapshot = JSON.parse(content);

      // Clear current state
      this.entities.clear();
      this.componentIndex.clear();
      this.nextEntityId = snapshot.next_entity_id || 1;

      // Restore entities
      for (const entityData of snapshot.entities) {
        const entity: Entity = {
          id: entityData.id,
          components: new Map(Object.entries(entityData.components)),
          created: entityData.created,
          active: entityData.active
        };

        this.entities.set(entity.id, entity);

        // Rebuild component index
        for (const componentType of entity.components.keys()) {
          if (!this.componentIndex.has(componentType)) {
            this.componentIndex.set(componentType, new Set());
          }
          this.componentIndex.get(componentType)!.add(entity.id);
        }
      }

      console.log(`[Registry] Loaded snapshot: ${filename} (${this.entities.size} entities)`);
      return true;
    } catch (error) {
      console.error('[Registry] Load failed:', error);
      return false;
    }
  }

  private getTowerDefaults(type: string): Tower {
    const defaults = {
      'basic': { range: 100, damage: 25, fire_rate: 1.0, last_shot: 0 },
      'rapid': { range: 80, damage: 15, fire_rate: 2.0, last_shot: 0 },
      'heavy': { range: 120, damage: 50, fire_rate: 0.5, last_shot: 0 }
    };
    return defaults[type] || defaults['basic'];
  }

  private getEnemyDefaults(type: string): any {
    const defaults = {
      'basic': { health: { current: 100, max: 100 }, reward: 10 },
      'fast': { health: { current: 50, max: 50 }, reward: 15 },
      'tank': { health: { current: 200, max: 200 }, reward: 25 }
    };
    return defaults[type] || defaults['basic'];
  }
}

export const registry = new Registry();