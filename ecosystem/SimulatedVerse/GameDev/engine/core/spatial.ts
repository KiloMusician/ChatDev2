// Spatial Systems - Grid coordinates, FOV, chunking, noise generation
// Bridges symbolic space operations to literal world representation

import { campaignRNG, SeededRNG } from './rng.js';

export interface Coord {
  x: number;
  y: number;
  z?: number;
}

export interface Bounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Tile {
  coord: Coord;
  type: string;
  visible: boolean;
  explored: boolean;
  blocked: boolean;
  opaque: boolean;
  char?: string;
  sprite?: string;
  entities: string[]; // EntityIds occupying this tile
}

export interface Chunk {
  id: string;
  coord: Coord;
  size: number;
  tiles: Map<string, Tile>;
  generated: boolean;
  dirty: boolean;
}

export class SpatialGrid {
  private tiles = new Map<string, Tile>();
  private chunks = new Map<string, Chunk>();
  public entityPositions = new Map<string, Coord>();
  private chunkSize = 16;
  
  constructor(public width: number = 128, public height: number = 128) {
    console.log(`[Spatial] Grid initialized ${width}x${height}`);
  }

  // Coordinate utilities
  coordKey(x: number, y: number): string {
    return `${x},${y}`;
  }

  chunkKey(x: number, y: number): string {
    const chunkX = Math.floor(x / this.chunkSize);
    const chunkY = Math.floor(y / this.chunkSize);
    return `${chunkX},${chunkY}`;
  }

  // Get or create tile
  getTile(x: number, y: number): Tile {
    const key = this.coordKey(x, y);
    if (!this.tiles.has(key)) {
      this.tiles.set(key, {
        coord: { x, y },
        type: 'floor',
        visible: false,
        explored: false,
        blocked: false,
        opaque: false,
        entities: []
      });
    }
    return this.tiles.get(key)!;
  }

  // Set tile properties
  setTile(x: number, y: number, properties: Partial<Tile>): void {
    const tile = this.getTile(x, y);
    Object.assign(tile, properties);
    
    // Mark chunk as dirty
    const chunkId = this.chunkKey(x, y);
    const chunk = this.chunks.get(chunkId);
    if (chunk) {
      chunk.dirty = true;
    }
  }

  // Entity position tracking
  setEntityPosition(entityId: string, x: number, y: number): void {
    // Remove from old position
    const oldPos = this.entityPositions.get(entityId);
    if (oldPos) {
      const oldTile = this.getTile(oldPos.x, oldPos.y);
      oldTile.entities = oldTile.entities.filter(id => id !== entityId);
    }

    // Add to new position
    this.entityPositions.set(entityId, { x, y });
    const newTile = this.getTile(x, y);
    if (!newTile.entities.includes(entityId)) {
      newTile.entities.push(entityId);
    }
  }

  getEntityPosition(entityId: string): Coord | null {
    return this.entityPositions.get(entityId) || null;
  }

  // Field of View calculation using simple raycasting
  calculateFOV(centerX: number, centerY: number, radius: number): Set<string> {
    const visible = new Set<string>();
    
    for (let x = centerX - radius; x <= centerX + radius; x++) {
      for (let y = centerY - radius; y <= centerY + radius; y++) {
        const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
        if (distance <= radius && this.hasLineOfSight(centerX, centerY, x, y)) {
          visible.add(this.coordKey(x, y));
          const tile = this.getTile(x, y);
          tile.visible = true;
          tile.explored = true;
        }
      }
    }
    
    return visible;
  }

  private hasLineOfSight(x1: number, y1: number, x2: number, y2: number): boolean {
    // Simple Bresenham-style line-of-sight
    const dx = Math.abs(x2 - x1);
    const dy = Math.abs(y2 - y1);
    const sx = x1 < x2 ? 1 : -1;
    const sy = y1 < y2 ? 1 : -1;
    let err = dx - dy;
    
    let x = x1, y = y1;
    
    while (true) {
      const tile = this.getTile(x, y);
      if (tile.opaque && !(x === x1 && y === y1) && !(x === x2 && y === y2)) {
        return false; // Blocked by opaque tile
      }
      
      if (x === x2 && y === y2) break;
      
      const e2 = 2 * err;
      if (e2 > -dy) { err -= dy; x += sx; }
      if (e2 < dx) { err += dx; y += sy; }
    }
    
    return true;
  }

  // Distance calculations
  distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
  }

  manhattanDistance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.abs(x2 - x1) + Math.abs(y2 - y1);
  }

  // Get neighbors (4-directional)
  getNeighbors(x: number, y: number): Coord[] {
    return [
      { x: x - 1, y },
      { x: x + 1, y },
      { x, y: y - 1 },
      { x, y: y + 1 }
    ].filter(coord => 
      coord.x >= 0 && coord.x < this.width && 
      coord.y >= 0 && coord.y < this.height
    );
  }

  // Get entities at position
  getEntitiesAt(x: number, y: number): string[] {
    return this.getTile(x, y).entities;
  }

  // Find empty positions in area
  findEmptyPositions(bounds: Bounds, count: number = 1): Coord[] {
    const empty: Coord[] = [];
    
    for (let attempts = 0; attempts < count * 10 && empty.length < count; attempts++) {
      const x = bounds.x + campaignRNG.int(0, bounds.width - 1);
      const y = bounds.y + campaignRNG.int(0, bounds.height - 1);
      
      const tile = this.getTile(x, y);
      if (!tile.blocked && tile.entities.length === 0) {
        empty.push({ x, y });
      }
    }
    
    return empty;
  }

  // Chunking for large worlds
  getChunk(chunkX: number, chunkY: number): Chunk {
    const key = `${chunkX},${chunkY}`;
    if (!this.chunks.has(key)) {
      this.chunks.set(key, {
        id: key,
        coord: { x: chunkX, y: chunkY },
        size: this.chunkSize,
        tiles: new Map(),
        generated: false,
        dirty: false
      });
    }
    return this.chunks.get(key)!;
  }

  // Generate chunk procedurally
  generateChunk(chunkX: number, chunkY: number, biome: string = 'temperate'): void {
    const chunk = this.getChunk(chunkX, chunkY);
    if (chunk.generated) return;

    const rng = campaignRNG.branch(`chunk_${chunkX}_${chunkY}_${biome}`);
    
    // Generate tiles for this chunk
    for (let y = 0; y < this.chunkSize; y++) {
      for (let x = 0; x < this.chunkSize; x++) {
        const worldX = chunkX * this.chunkSize + x;
        const worldY = chunkY * this.chunkSize + y;
        
        // Simple noise-based terrain
        const noise = Math.sin(worldX * 0.1) * Math.cos(worldY * 0.1) + rng.random() * 0.3;
        
        let tileType = 'floor';
        let blocked = false;
        let opaque = false;
        
        if (noise > 0.5) {
          tileType = 'wall';
          blocked = true;
          opaque = true;
        } else if (noise > 0.2) {
          tileType = 'rough';
        }
        
        this.setTile(worldX, worldY, {
          type: tileType,
          blocked,
          opaque,
          char: tileType === 'wall' ? '#' : tileType === 'rough' ? '.' : ' ',
          sprite: `tile_${tileType}`
        });
      }
    }
    
    chunk.generated = true;
    console.log(`[Spatial] Generated chunk ${chunkX},${chunkY} (${biome})`);
  }

  // Clear visibility for next FOV calculation
  clearVisibility(): void {
    for (const tile of this.tiles.values()) {
      tile.visible = false;
    }
  }

  // Get render data for viewport
  getViewportTiles(centerX: number, centerY: number, width: number, height: number): Tile[] {
    const tiles: Tile[] = [];
    const startX = centerX - Math.floor(width / 2);
    const startY = centerY - Math.floor(height / 2);
    
    for (let y = startY; y < startY + height; y++) {
      for (let x = startX; x < startX + width; x++) {
        tiles.push(this.getTile(x, y));
      }
    }
    
    return tiles;
  }
}

// Simplex noise for terrain generation
export class SimplexNoise {
  private perm: number[];
  
  constructor(seed: number) {
    // Generate permutation table
    this.perm = [];
    const rng = new SeededRNG(seed);
    
    for (let i = 0; i < 256; i++) {
      this.perm[i] = i;
    }
    
    // Shuffle using seeded RNG
    for (let i = 255; i > 0; i--) {
      const j = rng.int(0, i);
      [this.perm[i], this.perm[j]] = [this.perm[j], this.perm[i]];
    }
    
    // Duplicate for overflow
    for (let i = 0; i < 256; i++) {
      this.perm[256 + i] = this.perm[i];
    }
  }

  noise2D(x: number, y: number): number {
    // Simplified 2D noise implementation
    const X = Math.floor(x) & 255;
    const Y = Math.floor(y) & 255;
    
    x -= Math.floor(x);
    y -= Math.floor(y);
    
    const fade = (t: number) => t * t * t * (t * (t * 6 - 15) + 10);
    const u = fade(x);
    const v = fade(y);
    
    const A = this.perm[X] + Y;
    const B = this.perm[X + 1] + Y;
    
    const lerp = (a: number, b: number, t: number) => a + t * (b - a);
    
    return lerp(
      lerp(this.grad(this.perm[A], x, y), this.grad(this.perm[B], x - 1, y), u),
      lerp(this.grad(this.perm[A + 1], x, y - 1), this.grad(this.perm[B + 1], x - 1, y - 1), u),
      v
    );
  }

  private grad(hash: number, x: number, y: number): number {
    const h = hash & 3;
    return ((h & 1) === 0 ? x : -x) + ((h & 2) === 0 ? y : -y);
  }

  // Octave noise for more complex terrain
  octaveNoise(x: number, y: number, octaves: number = 4, persistence: number = 0.5): number {
    let value = 0;
    let amplitude = 1;
    let frequency = 1;
    let maxValue = 0;
    
    for (let i = 0; i < octaves; i++) {
      value += this.noise2D(x * frequency, y * frequency) * amplitude;
      maxValue += amplitude;
      amplitude *= persistence;
      frequency *= 2;
    }
    
    return value / maxValue;
  }
}

export const spatialGrid = new SpatialGrid();
export const worldNoise = new SimplexNoise(campaignRNG.next());
