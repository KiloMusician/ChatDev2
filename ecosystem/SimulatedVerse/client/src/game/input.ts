import { world, make } from "./ecs";
import { receipt } from "./receipts";
import { getGameManagers } from "./game";

export class InputHandler {
  private playerEntity: string | null = null;

  constructor() {
    // Find the player entity (the one with @ glyph)
    for (const [entity, actor] of world.act) {
      if (actor.glyph === "@") {
        this.playerEntity = entity;
        break;
      }
    }
  }

  handleKeyPress(key: string) {
    if (!this.playerEntity) return;

    const pos = world.pos.get(this.playerEntity);
    if (!pos) return;

    let newX = pos.x;
    let newY = pos.y;
    let moved = false;

    // Arrow keys and WASD movement
    switch (key.toLowerCase()) {
      case "arrowup":
      case "w":
        newY = Math.max(0, pos.y - 1);
        moved = true;
        break;
      case "arrowdown":
      case "s":
        newY = Math.min(23, pos.y + 1);
        moved = true;
        break;
      case "arrowleft":
      case "a":
        newX = Math.max(0, pos.x - 1);
        moved = true;
        break;
      case "arrowright":
      case "d":
        newX = Math.min(59, pos.x + 1);
        moved = true;
        break;
      case " ":
      case "enter":
        // Spawn a new resource at player location
        make.resource("energy", 5, pos.x, pos.y);
        receipt("player:spawn_resource", { x: pos.x, y: pos.y, amount: 5 });
        break;
      case "b":
        // Build a structure (generator for now)
        const managers = getGameManagers();
        if (managers.structureManager) {
          const structure = managers.structureManager.place("generator", pos.x, pos.y);
          if (structure) {
            receipt("player:build_structure", { 
              type: "generator", 
              position: { x: pos.x, y: pos.y },
              id: structure.id 
            });
          }
        }
        break;
      case "t":
        // Build a turret
        const managersT = getGameManagers();
        if (managersT.structureManager) {
          const turret = managersT.structureManager.place("turret", pos.x, pos.y);
          if (turret) {
            receipt("player:build_turret", { 
              position: { x: pos.x, y: pos.y },
              id: turret.id 
            });
          }
        }
        break;
      case "n":
        // Start next wave - changed from "w" to avoid collision with movement
        const managersW = getGameManagers();
        if (managersW.waveManager) {
          const started = managersW.waveManager.startNextWave();
          if (started) {
            receipt("player:start_wave", { 
              wave: managersW.waveManager.getCurrentWave() 
            });
          }
        }
        break;
      case "q":
        // Quick save (if save system is available) - changed from "s" to avoid duplication
        receipt("player:save_request", { position: { x: pos.x, y: pos.y } });
        break;
    }

    if (moved && (newX !== pos.x || newY !== pos.y)) {
      world.pos.set(this.playerEntity, { x: newX, y: newY });
      receipt("player:move", { from: { x: pos.x, y: pos.y }, to: { x: newX, y: newY } });
    }
  }
}