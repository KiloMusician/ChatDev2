// Roguelike Genre Module - Dungeon generation and exploration
// Bridges procedural content to literal dungeon layouts

import { campaignRNG } from '../../engine/core/rng.js';
import type { Coord } from '../../engine/core/spatial.js';
import { registry } from '../../engine/core/entity/Registry.js';

export interface Room {
  x: number;
  y: number;
  width: number;
  height: number;
  type: 'room' | 'corridor' | 'chamber';
  connections: Coord[];
  features?: string[];
}

export interface DungeonLevel {
  width: number;
  height: number;
  rooms: Room[];
  tiles: string[][];
  stairsUp?: Coord;
  stairsDown?: Coord;
  depth: number;
}

export class DungeonGenerator {
  private rng: any;
  
  constructor(seed?: string) {
    this.rng = campaignRNG; // Use global campaign RNG for consistency
    console.log('[Dungeon] Generator initialized with campaign seed');
  }

  // Generate a complete dungeon level
  generateLevel(width: number = 64, height: number = 64, depth: number = 1): DungeonLevel {
    console.log(`[Dungeon] Generating level ${depth} (${width}x${height})`);
    
    const level: DungeonLevel = {
      width,
      height,
      rooms: [],
      tiles: this.createEmptyGrid(width, height),
      depth
    };
    
    // Generate rooms using BSP algorithm
    this.generateRooms(level);
    
    // Connect rooms with corridors
    this.connectRooms(level);
    
    // Add stairs
    this.addStairs(level);
    
    // Populate with entities
    this.populateLevel(level);
    
    return level;
  }

  private createEmptyGrid(width: number, height: number): string[][] {
    const grid: string[][] = [];
    for (let y = 0; y < height; y++) {
      const row: string[] = [];
      for (let x = 0; x < width; x++) {
        row.push('#'); // Start with walls
      }
      grid.push(row);
    }
    return grid;
  }

  private generateRooms(level: DungeonLevel): void {
    const roomCount = 6 + this.rng.nextInt(8);
    const attempts = roomCount * 10;
    
    for (let i = 0; i < attempts && level.rooms.length < roomCount; i++) {
      const room = this.generateRoom(level);
      
      if (room && !this.roomOverlaps(room, level.rooms)) {
        level.rooms.push(room);
        this.carveRoom(room, level.tiles);
      }
    }
    
    console.log(`[Dungeon] Created ${level.rooms.length} rooms`);
  }

  private generateRoom(level: DungeonLevel): Room | null {
    const minSize = 4;
    const maxSize = 12;
    
    const width = minSize + this.rng.nextInt(maxSize - minSize);
    const height = minSize + this.rng.nextInt(maxSize - minSize);
    
    const x = 2 + this.rng.nextInt(level.width - width - 4);
    const y = 2 + this.rng.nextInt(level.height - height - 4);
    
    return {
      x, y, width, height,
      type: 'room',
      connections: []
    };
  }

  private roomOverlaps(room: Room, existingRooms: Room[]): boolean {
    for (const existing of existingRooms) {
      if (room.x < existing.x + existing.width + 2 &&
          room.x + room.width + 2 > existing.x &&
          room.y < existing.y + existing.height + 2 &&
          room.y + room.height + 2 > existing.y) {
        return true;
      }
    }
    return false;
  }

  private carveRoom(room: Room, tiles: string[][]): void {
    for (let y = room.y; y < room.y + room.height; y++) {
      for (let x = room.x; x < room.x + room.width; x++) {
        if (y >= 0 && y < tiles.length && x >= 0 && x < tiles[y].length) {
          tiles[y][x] = '.';
        }
      }
    }
  }

  private connectRooms(level: DungeonLevel): void {
    // Connect each room to nearest room
    for (let i = 0; i < level.rooms.length; i++) {
      const room = level.rooms[i];
      let nearest = null;
      let nearestDist = Infinity;
      
      for (let j = 0; j < level.rooms.length; j++) {
        if (i === j) continue;
        
        const other = level.rooms[j];
        const dist = this.roomDistance(room, other);
        
        if (dist < nearestDist) {
          nearest = other;
          nearestDist = dist;
        }
      }
      
      if (nearest) {
        this.carveCorridorBetween(room, nearest, level.tiles);
        room.connections.push({ x: nearest.x + Math.floor(nearest.width / 2), y: nearest.y + Math.floor(nearest.height / 2) });
      }
    }
  }

  private roomDistance(room1: Room, room2: Room): number {
    const cx1 = room1.x + Math.floor(room1.width / 2);
    const cy1 = room1.y + Math.floor(room1.height / 2);
    const cx2 = room2.x + Math.floor(room2.width / 2);
    const cy2 = room2.y + Math.floor(room2.height / 2);
    
    return Math.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2);
  }

  private carveCorridorBetween(room1: Room, room2: Room, tiles: string[][]): void {
    const start = {
      x: room1.x + Math.floor(room1.width / 2),
      y: room1.y + Math.floor(room1.height / 2)
    };
    const end = {
      x: room2.x + Math.floor(room2.width / 2),
      y: room2.y + Math.floor(room2.height / 2)
    };
    
    // L-shaped corridor
    let current = { ...start };
    
    // Horizontal first
    const dx = end.x > start.x ? 1 : -1;
    while (current.x !== end.x) {
      if (current.y >= 0 && current.y < tiles.length && 
          current.x >= 0 && current.x < tiles[current.y].length) {
        tiles[current.y][current.x] = '.';
      }
      current.x += dx;
    }
    
    // Then vertical
    const dy = end.y > current.y ? 1 : -1;
    while (current.y !== end.y) {
      if (current.y >= 0 && current.y < tiles.length && 
          current.x >= 0 && current.x < tiles[current.y].length) {
        tiles[current.y][current.x] = '.';
      }
      current.y += dy;
    }
    
    // Mark final position
    if (end.y >= 0 && end.y < tiles.length && 
        end.x >= 0 && end.x < tiles[end.y].length) {
      tiles[end.y][end.x] = '.';
    }
  }

  private addStairs(level: DungeonLevel): void {
    if (level.rooms.length === 0) return;
    
    // Stairs up in first room
    const firstRoom = level.rooms[0];
    level.stairsUp = {
      x: firstRoom.x + Math.floor(firstRoom.width / 2),
      y: firstRoom.y + Math.floor(firstRoom.height / 2)
    };
    
    // Stairs down in last room
    const lastRoom = level.rooms[level.rooms.length - 1];
    level.stairsDown = {
      x: lastRoom.x + Math.floor(lastRoom.width / 2),
      y: lastRoom.y + Math.floor(lastRoom.height / 2)
    };
  }

  private populateLevel(level: DungeonLevel): void {
    // Place player in first room
    if (level.rooms.length > 0 && level.stairsUp) {
      registry.createEntity('player', {
        'Position': { x: level.stairsUp.x * 16, y: level.stairsUp.y * 16 },
        'Health': { current: 100, max: 100 },
        'Inventory': { items: [], capacity: 20 }
      });
    }
    
    // Populate rooms with entities
    for (let i = 1; i < level.rooms.length; i++) {
      const room = level.rooms[i];
      
      // Random enemies
      const enemyCount = 1 + this.rng.nextInt(3);
      for (let j = 0; j < enemyCount; j++) {
        const x = room.x + 1 + this.rng.nextInt(room.width - 2);
        const y = room.y + 1 + this.rng.nextInt(room.height - 2);
        
        registry.createEntity('enemy', {
          'Position': { x: x * 16, y: y * 16 },
          'Health': { current: 50, max: 50 },
          'AIState': { state: 'patrol' }
        });
      }
      
      // Random loot
      if (this.rng.nextFloat() < 0.6) {
        const x = room.x + 1 + this.rng.nextInt(room.width - 2);
        const y = room.y + 1 + this.rng.nextInt(room.height - 2);
        
        registry.createEntity('treasure', {
          'Position': { x: x * 16, y: y * 16 },
          'Inventory': { 
            items: [{ id: 'gold', quantity: 10 + this.rng.nextInt(20) }], 
            capacity: 1 
          }
        });
      }
    }
  }

  // Convert dungeon to grid format for rendering
  levelToGrid(level: DungeonLevel): any[][] {
    const grid: any[][] = [];
    
    for (let y = 0; y < level.height; y++) {
      const row: any[] = [];
      for (let x = 0; x < level.width; x++) {
        const char = level.tiles[y]?.[x] || '#';
        row.push({
          char,
          color: char === '#' ? '#888' : '#444',
          bg: '#000'
        });
      }
      grid.push(row);
    }
    
    // Mark stairs
    if (level.stairsUp) {
      const up = level.stairsUp;
      if (up.y < grid.length && up.x < grid[up.y].length) {
        grid[up.y][up.x] = { char: '<', color: '#0ff', bg: '#000' };
      }
    }
    
    if (level.stairsDown) {
      const down = level.stairsDown;
      if (down.y < grid.length && down.x < grid[down.y].length) {
        grid[down.y][down.x] = { char: '>', color: '#f80', bg: '#000' };
      }
    }
    
    return grid;
  }

  // Get room at coordinates
  getRoomAt(level: DungeonLevel, x: number, y: number): Room | null {
    for (const room of level.rooms) {
      if (x >= room.x && x < room.x + room.width &&
          y >= room.y && y < room.y + room.height) {
        return room;
      }
    }
    return null;
  }
}

export const dungeonGenerator = new DungeonGenerator();
