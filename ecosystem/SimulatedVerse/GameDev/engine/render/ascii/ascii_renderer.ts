// ASCII Renderer - Fast text-based rendering for terminals
// Bridges symbolic render operations to literal character output

import type { RenderState, Coord } from '../../core/sim.js';

export interface ASCIIStyle {
  char: string;
  color: string;
  bg?: string;
}

export interface ASCIIViewport {
  width: number;
  height: number;
  centerX: number;
  centerY: number;
  scale: number;
}

export class ASCIIRenderer {
  private canvas: ASCIIStyle[][];
  private viewport: ASCIIViewport;
  
  constructor(width: number = 80, height: number = 24) {
    this.viewport = {
      width,
      height,
      centerX: 0,
      centerY: 0,
      scale: 1
    };
    
    this.canvas = this.createCanvas(width, height);
    console.log(`[ASCII] Renderer initialized ${width}x${height}`);
  }

  private createCanvas(width: number, height: number): ASCIIStyle[][] {
    const canvas: ASCIIStyle[][] = [];
    for (let y = 0; y < height; y++) {
      const row: ASCIIStyle[] = [];
      for (let x = 0; x < width; x++) {
        row.push({ char: ' ', color: '#888', bg: '#000' });
      }
      canvas.push(row);
    }
    return canvas;
  }

  // Main render method
  render(renderState: RenderState): string {
    this.clearCanvas();
    
    // Update viewport from render state
    this.viewport.centerX = renderState.viewport.x;
    this.viewport.centerY = renderState.viewport.y;
    
    // Render grid tiles
    this.renderGrid(renderState.grid);
    
    // Render entities as characters
    this.renderEntities(renderState.sprites);
    
    // Render HUD
    this.renderHUD(renderState.hud);
    
    // Convert canvas to string
    return this.canvasToString();
  }

  private clearCanvas(): void {
    for (let y = 0; y < this.viewport.height; y++) {
      for (let x = 0; x < this.viewport.width; x++) {
        this.canvas[y][x] = { char: ' ', color: '#888', bg: '#000' };
      }
    }
  }

  private renderGrid(grid: RenderState['grid']): void {
    for (let y = 0; y < Math.min(grid.length, this.viewport.height - 3); y++) {
      for (let x = 0; x < Math.min(grid[y]?.length || 0, this.viewport.width); x++) {
        const cell = grid[y][x];
        if (cell && y < this.canvas.length && x < this.canvas[y].length) {
          this.canvas[y][x] = {
            char: cell.char,
            color: cell.color || '#888',
            bg: cell.bg || '#000'
          };
        }
      }
    }
  }

  private renderEntities(sprites: RenderState['sprites']): void {
    for (const sprite of sprites) {
      // Convert pixel coordinates to grid coordinates
      const gridX = Math.floor(sprite.x / 16);
      const gridY = Math.floor(sprite.y / 16);
      
      // Adjust for viewport
      const screenX = gridX - this.viewport.centerX + Math.floor(this.viewport.width / 2);
      const screenY = gridY - this.viewport.centerY + Math.floor(this.viewport.height / 2);
      
      if (screenX >= 0 && screenX < this.viewport.width && 
          screenY >= 0 && screenY < this.viewport.height - 3) {
        
        const char = this.spriteToChar(sprite.key);
        this.canvas[screenY][screenX] = {
          char,
          color: this.spriteToColor(sprite.key),
          bg: '#000'
        };
      }
    }
  }

  private renderHUD(hud: RenderState['hud']): void {
    const hudY = this.viewport.height - 3;
    
    // Resources bar
    let hudText = 'Resources: ';
    for (const [name, value] of Object.entries(hud.resources)) {
      if (typeof value === 'object' && value.amount !== undefined) {
        hudText += `${name}:${Math.floor(value.amount)} `;
      }
    }
    
    this.drawText(hudText, 0, hudY, '#0f0');
    
    // Messages
    if (hud.messages.length > 0) {
      const message = hud.messages[hud.messages.length - 1];
      this.drawText(message, 0, hudY + 1, '#ff0');
    }
    
    // Tooltips
    for (const tooltip of hud.tooltips) {
      this.drawText(`[${tooltip.text}]`, tooltip.x, tooltip.y, '#0ff');
    }
  }

  private drawText(text: string, x: number, y: number, color: string = '#888'): void {
    for (let i = 0; i < text.length && x + i < this.viewport.width; i++) {
      if (y >= 0 && y < this.viewport.height) {
        this.canvas[y][x + i] = {
          char: text[i],
          color,
          bg: '#000'
        };
      }
    }
  }

  private spriteToChar(spriteKey: string): string {
    const charMap: Record<string, string> = {
      'entity_default': '?',
      'player': '@',
      'enemy_basic': 'e',
      'enemy_fast': 'f',
      'enemy_tank': 'T',
      'tower_basic': '◊',
      'tower_rapid': '◈',
      'tower_heavy': '◆',
      'citizen': 'c',
      'building': '▢',
      'resource_node': '*',
      'tile_wall': '#',
      'tile_floor': '.',
      'tile_rough': '∴'
    };
    
    return charMap[spriteKey] || '?';
  }

  private spriteToColor(spriteKey: string): string {
    const colorMap: Record<string, string> = {
      'player': '#0f0',
      'enemy_basic': '#f00',
      'enemy_fast': '#f80',
      'enemy_tank': '#800',
      'tower_basic': '#00f',
      'tower_rapid': '#0ff',
      'tower_heavy': '#80f',
      'citizen': '#0f8',
      'building': '#888',
      'resource_node': '#ff0'
    };
    
    return colorMap[spriteKey] || '#888';
  }

  private canvasToString(): string {
    let output = '';
    for (let y = 0; y < this.viewport.height; y++) {
      for (let x = 0; x < this.viewport.width; x++) {
        const cell = this.canvas[y][x];
        // Simple output without ANSI colors for now
        output += cell.char;
      }
      output += '\n';
    }
    return output;
  }

  // Export with ANSI colors for terminals
  renderWithColors(renderState: RenderState): string {
    this.render(renderState); // Update canvas
    
    let output = '';
    for (let y = 0; y < this.viewport.height; y++) {
      for (let x = 0; x < this.viewport.width; x++) {
        const cell = this.canvas[y][x];
        const colorCode = this.htmlToAnsi(cell.color);
        const bgCode = this.htmlToBgAnsi(cell.bg || '#000');
        output += `${bgCode}${colorCode}${cell.char}`;
      }
      output += '\x1b[0m\n'; // Reset colors + newline
    }
    return output;
  }

  private htmlToAnsi(htmlColor: string): string {
    const colorMap: Record<string, string> = {
      '#000': '\x1b[30m', '#800': '\x1b[31m', '#080': '\x1b[32m', '#880': '\x1b[33m',
      '#008': '\x1b[34m', '#808': '\x1b[35m', '#088': '\x1b[36m', '#888': '\x1b[37m',
      '#f00': '\x1b[91m', '#0f0': '\x1b[92m', '#ff0': '\x1b[93m',
      '#00f': '\x1b[94m', '#f0f': '\x1b[95m', '#0ff': '\x1b[96m', '#fff': '\x1b[97m'
    };
    return colorMap[htmlColor] || '\x1b[37m';
  }

  private htmlToBgAnsi(htmlColor: string): string {
    const bgMap: Record<string, string> = {
      '#000': '\x1b[40m', '#800': '\x1b[41m', '#080': '\x1b[42m', '#880': '\x1b[43m',
      '#008': '\x1b[44m', '#808': '\x1b[45m', '#088': '\x1b[46m', '#888': '\x1b[47m'
    };
    return bgMap[htmlColor] || '\x1b[40m';
  }

  // Viewport control
  setCenter(x: number, y: number): void {
    this.viewport.centerX = x;
    this.viewport.centerY = y;
  }

  resize(width: number, height: number): void {
    this.viewport.width = width;
    this.viewport.height = height;
    this.canvas = this.createCanvas(width, height);
  }
}

export const asciiRenderer = new ASCIIRenderer();
