// Canvas Pixel Renderer - Hardware accelerated sprite rendering
// Bridges symbolic render operations to literal Canvas2D drawing

import type { RenderState } from '../../core/sim.js';
import { Atlas, type AtlasRegion } from './atlas.js';
import { ASCIIWidgets } from '../ascii/widgets.js';

export interface PixelViewport {
  x: number;
  y: number;
  width: number;
  height: number;
  scale: number;
  smooth: boolean;
}

export class PixelRenderer {
  private ctx: CanvasRenderingContext2D;
  private atlas: Atlas;
  private viewport: PixelViewport;
  private debugMode: boolean = false;
  private colorMap = new Map<string, string>();
  
  constructor(
    ctx: CanvasRenderingContext2D, 
    atlas: Atlas, 
    width: number = 800, 
    height: number = 600
  ) {
    this.ctx = ctx;
    this.atlas = atlas;
    
    this.viewport = {
      x: 0,
      y: 0,
      width,
      height,
      scale: 1,
      smooth: false
    };
    
    this.initializeColorMap();
    this.setupCanvas();
    
    console.log(`[PixelRenderer] Initialized ${width}x${height}`);
  }

  private initializeColorMap(): void {
    // Map sprite keys to colors for fallback rendering
    this.colorMap.set('tile_floor', '#444');
    this.colorMap.set('tile_wall', '#888');
    this.colorMap.set('tile_rough', '#666');
    this.colorMap.set('player', '#0f0');
    this.colorMap.set('enemy_basic', '#f00');
    this.colorMap.set('enemy_fast', '#f80');
    this.colorMap.set('enemy_tank', '#800');
    this.colorMap.set('tower_basic', '#00f');
    this.colorMap.set('tower_rapid', '#0ff');
    this.colorMap.set('tower_heavy', '#80f');
    this.colorMap.set('citizen', '#0f8');
    this.colorMap.set('building', '#888');
    this.colorMap.set('resource_node', '#ff0');
  }

  private setupCanvas(): void {
    // Configure canvas for pixel art
    this.ctx.imageSmoothingEnabled = this.viewport.smooth;
    this.ctx.textAlign = 'left';
    this.ctx.textBaseline = 'top';
  }

  // Main render method
  render(renderState: RenderState): void {
    this.clearCanvas();
    
    // Update viewport
    this.viewport.x = renderState.viewport.x * 16; // Convert grid to pixels
    this.viewport.y = renderState.viewport.y * 16;
    
    // Render background tiles
    this.renderTiles(renderState);
    
    // Render entities/sprites
    this.renderSprites(renderState.sprites);
    
    // Render HUD overlay
    this.renderHUD(renderState.hud);
    
    // Debug overlay
    if (this.debugMode) {
      this.renderDebugInfo(renderState);
    }
  }

  private clearCanvas(): void {
    this.ctx.fillStyle = '#000';
    this.ctx.fillRect(0, 0, this.viewport.width, this.viewport.height);
  }

  private renderTiles(renderState: RenderState): void {
    const tileSize = this.atlas.getTileSize();
    const { grid } = renderState;
    
    for (let y = 0; y < grid.length; y++) {
      for (let x = 0; x < (grid[y]?.length || 0); x++) {
        const cell = grid[y][x];
        if (!cell || cell.char === ' ') continue;
        
        const screenX = x * tileSize - this.viewport.x;
        const screenY = y * tileSize - this.viewport.y;
        
        // Only render visible tiles
        if (screenX >= -tileSize && screenX < this.viewport.width && 
            screenY >= -tileSize && screenY < this.viewport.height) {
          
          // Try to get sprite from atlas, fallback to colored square
          const spriteKey = this.charToSpriteKey(cell.char);
          const region = this.atlas.getRegion(spriteKey);
          
          if (region && this.atlas.isLoaded()) {
            this.drawSprite(spriteKey, screenX, screenY);
          } else {
            this.drawColoredSquare(spriteKey, screenX, screenY, tileSize);
          }
        }
      }
    }
  }

  private renderSprites(sprites: RenderState['sprites']): void {
    for (const sprite of sprites) {
      const screenX = sprite.x - this.viewport.x;
      const screenY = sprite.y - this.viewport.y;
      
      // Only render visible sprites
      if (screenX >= -32 && screenX < this.viewport.width && 
          screenY >= -32 && screenY < this.viewport.height) {
        
        this.ctx.save();
        
        // Apply transformations
        if (sprite.scale && sprite.scale !== 1) {
          this.ctx.scale(sprite.scale, sprite.scale);
        }
        
        if (sprite.rotation) {
          this.ctx.translate(screenX + 8, screenY + 8);
          this.ctx.rotate(sprite.rotation);
          this.ctx.translate(-8, -8);
        }
        
        // Draw sprite
        const region = this.atlas.getRegion(sprite.key);
        if (region && this.atlas.isLoaded()) {
          this.drawSprite(sprite.key, screenX, screenY);
        } else {
          this.drawColoredSquare(sprite.key, screenX, screenY, this.atlas.getTileSize());
        }
        
        this.ctx.restore();
      }
    }
  }

  private drawSprite(spriteKey: string, x: number, y: number): void {
    const region = this.atlas.getRegion(spriteKey);
    const image = this.atlas.getImage();
    
    if (!region || !image) return;
    
    this.ctx.drawImage(
      image,
      region.x, region.y, region.width, region.height,
      x, y, region.width * this.viewport.scale, region.height * this.viewport.scale
    );
  }

  private drawColoredSquare(spriteKey: string, x: number, y: number, size: number): void {
    const color = this.colorMap.get(spriteKey) || '#888';
    this.ctx.fillStyle = color;
    this.ctx.fillRect(x, y, size * this.viewport.scale, size * this.viewport.scale);
    
    // Add border for definition
    this.ctx.strokeStyle = '#000';
    this.ctx.lineWidth = 1;
    this.ctx.strokeRect(x, y, size * this.viewport.scale, size * this.viewport.scale);
  }

  private charToSpriteKey(char: string): string {
    const charMap: Record<string, string> = {
      '#': 'tile_wall',
      '.': 'tile_floor',
      '∴': 'tile_rough',
      '@': 'player',
      'e': 'enemy_basic',
      'f': 'enemy_fast',
      'T': 'enemy_tank',
      '◊': 'tower_basic',
      '◈': 'tower_rapid',
      '◆': 'tower_heavy',
      'c': 'citizen',
      '▢': 'building',
      '*': 'resource_node'
    };
    
    return charMap[char] || 'tile_floor';
  }

  private renderHUD(hud: RenderState['hud']): void {
    const hudY = this.viewport.height - 80;
    
    // Semi-transparent background
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    this.ctx.fillRect(0, hudY, this.viewport.width, 80);
    
    // Resource display
    this.ctx.fillStyle = '#0f0';
    this.ctx.font = '16px monospace';
    
    let x = 10;
    for (const [name, resource] of Object.entries(hud.resources)) {
      if (typeof resource === 'object' && resource.amount !== undefined) {
        const text = `${name}: ${Math.floor(resource.amount)}`;
        this.ctx.fillText(text, x, hudY + 10);
        x += this.ctx.measureText(text).width + 20;
      }
    }
    
    // Messages
    if (hud.messages.length > 0) {
      this.ctx.fillStyle = '#ff0';
      const message = hud.messages[hud.messages.length - 1];
      this.ctx.fillText(message, 10, hudY + 35);
    }
    
    // Tooltips
    for (const tooltip of hud.tooltips) {
      this.drawTooltip(tooltip.text, tooltip.x, tooltip.y);
    }
  }

  private drawTooltip(text: string, x: number, y: number): void {
    const padding = 8;
    const lines = text.split('\n');
    const lineHeight = 14;
    const maxWidth = Math.max(...lines.map(l => this.ctx.measureText(l).width));
    
    const tooltipWidth = maxWidth + padding * 2;
    const tooltipHeight = lines.length * lineHeight + padding * 2;
    
    // Background
    this.ctx.fillStyle = 'rgba(0, 0, 0, 0.9)';
    this.ctx.fillRect(x, y, tooltipWidth, tooltipHeight);
    
    // Border
    this.ctx.strokeStyle = '#888';
    this.ctx.lineWidth = 1;
    this.ctx.strokeRect(x, y, tooltipWidth, tooltipHeight);
    
    // Text
    this.ctx.fillStyle = '#fff';
    this.ctx.font = '12px monospace';
    
    for (let i = 0; i < lines.length; i++) {
      this.ctx.fillText(lines[i], x + padding, y + padding + i * lineHeight);
    }
  }

  private renderDebugInfo(renderState: RenderState): void {
    this.ctx.fillStyle = 'rgba(255, 255, 0, 0.8)';
    this.ctx.font = '12px monospace';
    
    const debugLines = [
      `FPS: ${Math.floor(renderState.fps)}`,
      `Frame: ${renderState.frame}`,
      `Sprites: ${renderState.sprites.length}`,
      `Viewport: ${this.viewport.x},${this.viewport.y}`,
      `Scale: ${this.viewport.scale.toFixed(1)}x`
    ];
    
    for (let i = 0; i < debugLines.length; i++) {
      this.ctx.fillText(debugLines[i], 10, 10 + i * 15);
    }
  }

  // Public API
  setViewport(x: number, y: number, scale: number = 1): void {
    this.viewport.x = x;
    this.viewport.y = y;
    this.viewport.scale = scale;
  }

  setDebugMode(enabled: boolean): void {
    this.debugMode = enabled;
  }

  resize(width: number, height: number): void {
    this.viewport.width = width;
    this.viewport.height = height;
    this.ctx.canvas.width = width;
    this.ctx.canvas.height = height;
    this.setupCanvas();
  }

  // Take screenshot for testing
  screenshot(): string {
    return this.ctx.canvas.toDataURL('image/png');
  }
}
