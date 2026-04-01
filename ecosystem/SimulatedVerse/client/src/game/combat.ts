import { StructureManager } from "./structures";
import { EnemyManager } from "./enemies";
import { receipt } from "./receipts";

export class CombatSystem {
  constructor(
    private structureManager: StructureManager,
    private enemyManager: EnemyManager
  ) {}

  tick(deltaTime: number) {
    const now = Date.now();
    
    // Process turret attacks
    const turrets = this.structureManager.getByType("turret");
    
    for (const turret of turrets) {
      if (turret.health <= 0) continue;
      
      // Check cooldown
      if (now - turret.lastFired < turret.cooldown) continue;
      
      // Find enemies in range
      const enemiesInRange = this.enemyManager.getInRange(
        turret.position.x,
        turret.position.y,
        turret.range
      );
      
      if (enemiesInRange.length === 0) continue;
      
      // Target closest enemy
      const target = this.findClosestEnemy(turret.position, enemiesInRange);
      if (!target) continue;
      
      // Fire at target
      const killed = this.enemyManager.damage(target.id, turret.damage);
      turret.lastFired = now;
      
      receipt("combat:turret_fire", {
        turretId: turret.id,
        targetId: target.id,
        damage: turret.damage,
        killed,
        turretPosition: turret.position,
        targetPosition: target.position,
        range: turret.range,
      });
    }
  }

  private findClosestEnemy(position: {x: number, y: number}, enemies: any[]): any | null {
    if (enemies.length === 0) return null;
    
    let closest = enemies[0];
    let closestDistance = this.calculateDistance(position, closest.position);
    
    for (let i = 1; i < enemies.length; i++) {
      const distance = this.calculateDistance(position, enemies[i].position);
      if (distance < closestDistance) {
        closest = enemies[i];
        closestDistance = distance;
      }
    }
    
    return closest;
  }

  private calculateDistance(pos1: {x: number, y: number}, pos2: {x: number, y: number}): number {
    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  // Area of effect damage
  dealAreaDamage(centerX: number, centerY: number, radius: number, damage: number) {
    const enemiesInArea = this.enemyManager.getInRange(centerX, centerY, radius);
    const structuresInArea = this.structureManager.getInRange(centerX, centerY, radius);
    
    let enemiesKilled = 0;
    let structuresDestroyed = 0;
    
    // Damage enemies
    for (const enemy of enemiesInArea) {
      const killed = this.enemyManager.damage(enemy.id, damage);
      if (killed) enemiesKilled++;
    }
    
    // Damage structures
    for (const structure of structuresInArea) {
      const destroyed = this.structureManager.damage(structure.id, damage);
      if (destroyed) structuresDestroyed++;
    }
    
    receipt("combat:area_damage", {
      center: { x: centerX, y: centerY },
      radius,
      damage,
      enemiesHit: enemiesInArea.length,
      enemiesKilled,
      structuresHit: structuresInArea.length,
      structuresDestroyed,
    });
    
    return {
      enemiesHit: enemiesInArea.length,
      enemiesKilled,
      structuresHit: structuresInArea.length,
      structuresDestroyed,
    };
  }

  // Calculate total defense power
  getDefensePower(): number {
    const turrets = this.structureManager.getByType("turret");
    return turrets.reduce((total, turret) => {
      if (turret.health <= 0) return total;
      return total + turret.damage * (turret.level * 0.2 + 0.8);
    }, 0);
  }

  // Calculate total threat level
  getThreatLevel(): number {
    const enemies = this.enemyManager.getAll();
    return enemies.reduce((total, enemy) => {
      return total + (enemy.health / enemy.maxHealth) * enemy.damage;
    }, 0);
  }

  // Get combat statistics
  getCombatStats() {
    const defensePower = this.getDefensePower();
    const threatLevel = this.getThreatLevel();
    const turretCount = this.structureManager.getByType("turret").length;
    const enemyCount = this.enemyManager.getAll().length;
    
    return {
      defensePower,
      threatLevel,
      defenseAdvantage: threatLevel > 0 ? defensePower / threatLevel : 1,
      turretCount,
      enemyCount,
      activeTurrets: this.structureManager.getByType("turret").filter(t => t.health > 0).length,
    };
  }
}