// Sprite Atlas - Pack and manage pixel sprites
// Bridges symbolic sprite references to literal texture coordinates

export interface AtlasRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  originX?: number;
  originY?: number;
}

export interface AtlasManifest {
  image_path: string;
  tile_size: number;
  regions: Record<string, AtlasRegion>;
  metadata: {
    created: string;
    generator: string;
    version: string;
  };
}

export class Atlas {
  private regions = new Map<string, AtlasRegion>();
  private image: HTMLImageElement | null = null;
  private tileSize: number;
  private loaded: boolean = false;
  
  constructor(private manifest: AtlasManifest) {
    this.tileSize = manifest.tile_size;
    this.loadRegions();
    console.log(`[Atlas] Initialized with ${Object.keys(manifest.regions).length} sprites`);
  }

  private loadRegions(): void {
    for (const [key, region] of Object.entries(this.manifest.regions)) {
      this.regions.set(key, region);
    }
  }

  async loadImage(): Promise<boolean> {
    try {
      this.image = new Image();
      
      return new Promise((resolve) => {
        this.image!.onload = () => {
          this.loaded = true;
          console.log(`[Atlas] Loaded image: ${this.manifest.image_path}`);
          resolve(true);
        };
        
        this.image!.onerror = () => {
          console.error(`[Atlas] Failed to load: ${this.manifest.image_path}`);
          resolve(false);
        };
        
        this.image!.src = this.manifest.image_path;
      });
    } catch (error) {
      console.error('[Atlas] Load error:', error);
      return false;
    }
  }

  getRegion(spriteKey: string): AtlasRegion | null {
    return this.regions.get(spriteKey) || null;
  }

  hasSprite(spriteKey: string): boolean {
    return this.regions.has(spriteKey);
  }

  getImage(): HTMLImageElement | null {
    return this.loaded ? this.image : null;
  }

  isLoaded(): boolean {
    return this.loaded;
  }

  getTileSize(): number {
    return this.tileSize;
  }

  // Create manifest from grid of tiles
  static createGridManifest(
    imagePath: string, 
    tileSize: number, 
    gridWidth: number,
    spriteNames: string[]
  ): AtlasManifest {
    const regions: Record<string, AtlasRegion> = {};
    
    for (let i = 0; i < spriteNames.length; i++) {
      const name = spriteNames[i];
      const gridX = i % gridWidth;
      const gridY = Math.floor(i / gridWidth);
      
      regions[name] = {
        x: gridX * tileSize,
        y: gridY * tileSize,
        width: tileSize,
        height: tileSize
      };
    }
    
    return {
      image_path: imagePath,
      tile_size: tileSize,
      regions,
      metadata: {
        created: new Date().toISOString(),
        generator: 'GridAtlas',
        version: '1.0.0'
      }
    };
  }

  // Create simple atlas for testing
  static createTestAtlas(): Atlas {
    const manifest: AtlasManifest = {
      image_path: '/game-assets/test_tiles.png',
      tile_size: 16,
      regions: {
        'tile_floor': { x: 0, y: 0, width: 16, height: 16 },
        'tile_wall': { x: 16, y: 0, width: 16, height: 16 },
        'tile_rough': { x: 32, y: 0, width: 16, height: 16 },
        'player': { x: 0, y: 16, width: 16, height: 16 },
        'enemy_basic': { x: 16, y: 16, width: 16, height: 16 },
        'enemy_fast': { x: 32, y: 16, width: 16, height: 16 },
        'enemy_tank': { x: 48, y: 16, width: 16, height: 16 },
        'tower_basic': { x: 0, y: 32, width: 16, height: 16 },
        'tower_rapid': { x: 16, y: 32, width: 16, height: 16 },
        'tower_heavy': { x: 32, y: 32, width: 16, height: 16 },
        'citizen': { x: 0, y: 48, width: 16, height: 16 },
        'building': { x: 16, y: 48, width: 16, height: 16 },
        'resource_node': { x: 32, y: 48, width: 16, height: 16 }
      },
      metadata: {
        created: new Date().toISOString(),
        generator: 'TestAtlas',
        version: '1.0.0'
      }
    };
    
    return new Atlas(manifest);
  }

  // Generate colored squares for testing (without image)
  static createColorAtlas(): Atlas {
    const manifest: AtlasManifest = {
      image_path: 'data:color', // Special marker for color mode
      tile_size: 16,
      regions: {
        'tile_floor': { x: 0, y: 0, width: 16, height: 16 },
        'tile_wall': { x: 1, y: 0, width: 16, height: 16 },
        'tile_rough': { x: 2, y: 0, width: 16, height: 16 },
        'player': { x: 0, y: 1, width: 16, height: 16 },
        'enemy_basic': { x: 1, y: 1, width: 16, height: 16 },
        'tower_basic': { x: 0, y: 2, width: 16, height: 16 }
      },
      metadata: {
        created: new Date().toISOString(),
        generator: 'ColorAtlas',
        version: '1.0.0'
      }
    };
    
    return new Atlas(manifest);
  }
}
