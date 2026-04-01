// Tower Manager - Literal tower placement and targeting system
// Bridges symbolic tower_breath to actual tower logic with DPS calculations

import { registry } from '../core/entity/Registry.js';
import { eventHub } from '../core/events/EventHub.js';

export interface TowerSlot {
  id: string;
  position: { x: number, y: number };
  occupied: boolean;
  tower_id?: string;
  valid: boolean;
}

export interface TowerStats {
  damage: number;
  range: number;
  fire_rate: number; // shots per second
  cost: number;
  dps: number; // calculated damage per second
  upgrade_cost: number;
  level: number;
}

export class TowerManager {
  private towerSlots: Map<string, TowerSlot> = new Map();
  private activeTowers: Map<string, string> = new Map(); // slot_id -> entity_id
  private towerTypes = new Map<string, TowerStats>();

  constructor() {
    this.initializeTowerSlots();
    this.initializeTowerTypes();
    this.startTowerTick();
    
    console.log('[TowerManager] Tower placement and targeting system initialized');
  }

  private initializeTowerSlots(): void {
    // Create tower slots for 2-lane setup
    const slots = [
      { id: 'slot_1', x: 150, y: 80 },   // Covers lane 1
      { id: 'slot_2', x: 350, y: 150 },  // Covers both lanes
      { id: 'slot_3', x: 550, y: 220 },  // Covers lane 2
      { id: 'slot_4', x: 250, y: 80 },   // Additional coverage
      { id: 'slot_5', x: 450, y: 220 },  // Additional coverage
    ];

    for (const slot of slots) {
      this.towerSlots.set(slot.id, {
        id: slot.id,
        position: { x: slot.x, y: slot.y },
        occupied: false,
        valid: true
      });
    }
  }

  private initializeTowerTypes(): void {
    const types = [
      {
        id: 'basic',
        damage: 25,
        range: 100,
        fire_rate: 1.0,
        cost: 50,
        level: 1
      },
      {
        id: 'rapid',
        damage: 15,
        range: 80, 
        fire_rate: 2.5,
        cost: 75,
        level: 1
      },
      {
        id: 'heavy',
        damage: 60,
        range: 120,
        fire_rate: 0.6,
        cost: 100,
        level: 1
      }
    ];

    for (const type of types) {
      this.towerTypes.set(type.id, {
        ...type,
        dps: type.damage * type.fire_rate,
        upgrade_cost: type.cost * 2
      });
    }
  }

  // Place tower in specific slot
  placeTower(slotId: string, towerType = 'basic'): boolean {
    const slot = this.towerSlots.get(slotId);
    const towerStats = this.towerTypes.get(towerType);
    
    if (!slot || !towerStats || slot.occupied || !slot.valid) {
      return false;
    }

    // Create tower entity
    const towerId = registry.createEntity('tower', {
      'Position': slot.position,
      'Tower': {
        type: towerType,
        damage: towerStats.damage,
        range: towerStats.range,
        fire_rate: towerStats.fire_rate,
        last_shot: 0,
        level: 1,
        kills: 0,
        total_damage: 0
      },
      'Health': { current: 100, max: 100 },
      'Renderable': { sprite: this.getTowerSprite(towerType) }
    });

    // Update slot
    slot.occupied = true;
    slot.tower_id = towerId;
    this.activeTowers.set(slotId, towerId);

    eventHub.publish('tower_placed', {
      slot_id: slotId,
      tower_id: towerId,
      tower_type: towerType,
      position: slot.position,
      stats: towerStats
    }, 'tower_manager');

    console.log(`[TowerManager] Placed ${towerType} tower in ${slotId} at (${slot.position.x}, ${slot.position.y})`);
    return true;
  }

  // Upgrade existing tower
  upgradeTower(slotId: string): boolean {
    const slot = this.towerSlots.get(slotId);
    if (!slot || !slot.occupied || !slot.tower_id) return false;

    const towerComponent = registry.getComponent(slot.tower_id, 'Tower');
    if (!towerComponent) return false;

    // Calculate upgrade cost
    const upgradeCost = Math.floor(towerComponent.level * 50 * 1.5);
    
    // Check if can afford (would integrate with ResourceLedger)
    // For now, assume affordable

    // Apply upgrade
    towerComponent.level++;
    towerComponent.damage = Math.floor(towerComponent.damage * 1.25);
    towerComponent.range = Math.floor(towerComponent.range * 1.1);
    towerComponent.fire_rate = Math.floor(towerComponent.fire_rate * 1.1 * 100) / 100;

    eventHub.publish('tower_upgraded', {
      slot_id: slotId,
      tower_id: slot.tower_id,
      new_level: towerComponent.level,
      new_stats: { 
        damage: towerComponent.damage, 
        range: towerComponent.range,
        fire_rate: towerComponent.fire_rate 
      }
    }, 'tower_manager');

    console.log(`[TowerManager] Upgraded tower in ${slotId} to level ${towerComponent.level}`);
    return true;
  }

  // Remove tower (sell)
  removeTower(slotId: string): boolean {
    const slot = this.towerSlots.get(slotId);
    if (!slot || !slot.occupied || !slot.tower_id) return false;

    // Remove entity
    registry.destroyEntity(slot.tower_id);

    // Update slot
    slot.occupied = false;
    slot.tower_id = undefined;
    this.activeTowers.delete(slotId);

    console.log(`[TowerManager] Removed tower from ${slotId}`);
    return true;
  }

  private startTowerTick(): void {
    import('../core/time/TickBus.js').then(({ tickBus }) => {
      tickBus.subscribe('combat', (deltaTime) => {
        this.tickTowers(deltaTime);
      });
    }).catch(() => {
      setInterval(() => this.tickTowers(1.0/30), 33); // 30 FPS fallback
    });
  }

  private tickTowers(deltaTime: number): void {
    const now = performance.now();
    
    // Get all tower entities
    const towers = registry.query(['Tower', 'Position']);
    const enemies = registry.query(['Enemy', 'Position', 'Health']);

    for (const towerId of towers) {
      const towerComponent = registry.getComponent(towerId, 'Tower');
      const towerPosition = registry.getComponent(towerId, 'Position');
      
      if (!towerComponent || !towerPosition) continue;

      // Check if ready to fire
      const timeSinceLastShot = (now - towerComponent.last_shot) / 1000;
      if (timeSinceLastShot < (1.0 / towerComponent.fire_rate)) {
        continue; // Still cooling down
      }

      // Find target
      const target = this.findTarget(towerPosition, towerComponent.range, enemies);
      if (target) {
        this.fireTower(towerId, target, towerComponent);
        towerComponent.last_shot = now;
      }
    }
  }

  private findTarget(towerPos: any, range: number, enemies: string[]): string | null {
    let closestEnemy: string | null = null;
    let closestDistance = Infinity;

    for (const enemyId of enemies) {
      const enemyPos = registry.getComponent(enemyId, 'Position');
      const enemyHealth = registry.getComponent(enemyId, 'Health');
      
      if (!enemyPos || !enemyHealth || enemyHealth.current <= 0) continue;

      const distance = Math.sqrt(
        Math.pow(enemyPos.x - towerPos.x, 2) + 
        Math.pow(enemyPos.y - towerPos.y, 2)
      );

      if (distance <= range && distance < closestDistance) {
        closestDistance = distance;
        closestEnemy = enemyId;
      }
    }

    return closestEnemy;
  }

  private fireTower(towerId: string, targetId: string, towerComponent: any): void {
    const enemyHealth = registry.getComponent(targetId, 'Health');
    if (!enemyHealth) return;

    // Apply damage
    enemyHealth.current -= towerComponent.damage;
    towerComponent.total_damage += towerComponent.damage;

    eventHub.publish('tower_fired', {
      tower_id: towerId,
      target_id: targetId,
      damage: towerComponent.damage
    }, 'tower_manager');

    // Check if enemy died
    if (enemyHealth.current <= 0) {
      const enemyComponent = registry.getComponent(targetId, 'Enemy');
      
      towerComponent.kills++;
      
      eventHub.publish('enemy_killed', {
        enemy_id: targetId,
        killed_by: towerId,
        reward: enemyComponent?.reward || 0
      }, 'tower_manager');

      registry.destroyEntity(targetId);
    }
  }

  private getTowerSprite(towerType: string): string {
    const sprites = {
      'basic': '🗼',
      'rapid': '⚡',
      'heavy': '🎯'
    };
    return sprites[towerType] || '🗼';
  }

  // Get tower slots for UI
  getTowerSlots(): Array<TowerSlot & {tower_stats?: TowerStats}> {
    return Array.from(this.towerSlots.values()).map(slot => {
      const result = { ...slot };
      
      if (slot.occupied && slot.tower_id) {
        const towerComponent = registry.getComponent(slot.tower_id, 'Tower');
        if (towerComponent) {
          result.tower_stats = {
            damage: towerComponent.damage,
            range: towerComponent.range,
            fire_rate: towerComponent.fire_rate,
            cost: 0, // Not relevant for placed towers
            dps: towerComponent.damage * towerComponent.fire_rate,
            upgrade_cost: Math.floor(towerComponent.level * 50 * 1.5),
            level: towerComponent.level
          };
        }
      }
      
      return result;
    });
  }

  getTowerTypes(): Map<string, TowerStats> {
    return new Map(this.towerTypes);
  }

  // Msg⛛ command interface
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Tower:Place' && parts.length >= 2) {
      const slotId = parts[1];
      const towerType = parts[2] || 'basic';
      return this.placeTower(slotId, towerType);
    } else if (parts[0] === 'Tower:Upgrade' && parts.length === 2) {
      return this.upgradeTower(parts[1]);
    }
    
    return false;
  }
}

export const towerManager = new TowerManager();