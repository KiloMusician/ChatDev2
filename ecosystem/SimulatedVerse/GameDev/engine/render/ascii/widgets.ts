// ASCII UI Widgets - Meters, tooltips, logs, mini-maps
// Bridges symbolic UI to literal text rendering

import type { RenderState } from '../../core/sim.js';

export interface ASCIIMeter {
  label: string;
  current: number;
  max: number;
  width: number;
  color: string;
}

export interface ASCIITooltip {
  x: number;
  y: number;
  text: string;
  width?: number;
}

export interface ASCIILog {
  messages: string[];
  maxLines: number;
  x: number;
  y: number;
  width: number;
}

export class ASCIIWidgets {
  // Draw progress bar/meter
  static drawMeter(meter: ASCIIMeter): string[] {
    const filled = Math.floor((meter.current / meter.max) * meter.width);
    const empty = meter.width - filled;
    
    const bar = '█'.repeat(filled) + '░'.repeat(empty);
    const text = `${meter.label}: [${bar}] ${Math.floor(meter.current)}/${meter.max}`;
    
    return [text];
  }

  // Draw bordered tooltip
  static drawTooltip(tooltip: ASCIITooltip): string[] {
    const lines = tooltip.text.split('\n');
    const width = tooltip.width || Math.max(...lines.map(l => l.length)) + 2;
    
    const result: string[] = [];
    
    // Top border
    result.push('┌' + '─'.repeat(width - 2) + '┐');
    
    // Content lines
    for (const line of lines) {
      const padding = ' '.repeat(Math.max(0, width - line.length - 2));
      result.push(`│${line}${padding}│`);
    }
    
    // Bottom border
    result.push('└' + '─'.repeat(width - 2) + '┘');
    
    return result;
  }

  // Draw scrolling log
  static drawLog(log: ASCIILog): string[] {
    const result: string[] = [];
    
    // Take last N messages
    const recent = log.messages.slice(-log.maxLines);
    
    for (const message of recent) {
      // Truncate if too long
      const truncated = message.length > log.width 
        ? message.substring(0, log.width - 3) + '...' 
        : message;
      result.push(truncated);
    }
    
    // Pad with empty lines if needed
    while (result.length < log.maxLines) {
      result.unshift(''); // Add empty lines at top
    }
    
    return result;
  }

  // Draw mini-map with player position
  static drawMiniMap(renderState: RenderState, mapSize: number = 12): string[] {
    const result: string[] = [];
    const scale = Math.max(1, Math.floor(64 / mapSize)); // Scale down from 64x64 world
    
    for (let y = 0; y < mapSize; y++) {
      let row = '';
      for (let x = 0; x < mapSize; x++) {
        // Sample world at this scaled position
        const worldX = x * scale;
        const worldY = y * scale;
        
        // Check for player
        const hasPlayer = renderState.sprites.some(s => 
          Math.floor(s.x / 16) === worldX && Math.floor(s.y / 16) === worldY && s.key === 'player'
        );
        
        if (hasPlayer) {
          row += '@';
        } else {
          // Sample terrain
          const gridX = Math.min(x, renderState.grid[0]?.length || 0);
          const gridY = Math.min(y, renderState.grid.length);
          const cell = renderState.grid[gridY]?.[gridX];
          row += cell?.char === '#' ? '#' : (cell?.char === '.' ? '·' : ' ');
        }
      }
      result.push(row);
    }
    
    return result;
  }

  // Draw status panel
  static drawStatusPanel(renderState: RenderState): string[] {
    const result: string[] = [];
    
    result.push('┌─ Status ─┐');
    result.push(`│ FPS: ${Math.floor(renderState.fps).toString().padStart(3)} │`);
    result.push(`│ Frame: ${renderState.frame.toString().padStart(4)} │`);
    
    // Resource summary
    for (const [name, resource] of Object.entries(renderState.hud.resources)) {
      if (typeof resource === 'object' && resource.amount !== undefined) {
        const amount = Math.floor(resource.amount).toString().padStart(4);
        const line = `│ ${name.substring(0, 4)}: ${amount} │`;
        result.push(line);
      }
    }
    
    result.push('└──────────┘');
    
    return result;
  }

  // Combine multiple widgets into layout
  static combineWidgets(widgets: Array<{lines: string[], x: number, y: number}>): string[] {
    const maxY = Math.max(...widgets.map(w => w.y + w.lines.length));
    const maxX = Math.max(...widgets.map(w => w.x + Math.max(...w.lines.map(l => l.length))));
    
    // Create canvas
    const canvas: string[][] = [];
    for (let y = 0; y <= maxY; y++) {
      const row: string[] = [];
      for (let x = 0; x <= maxX; x++) {
        row.push(' ');
      }
      canvas.push(row);
    }
    
    // Render widgets onto canvas
    for (const widget of widgets) {
      for (let lineIdx = 0; lineIdx < widget.lines.length; lineIdx++) {
        const line = widget.lines[lineIdx];
        const y = widget.y + lineIdx;
        
        for (let charIdx = 0; charIdx < line.length; charIdx++) {
          const x = widget.x + charIdx;
          if (y < canvas.length && x < canvas[y].length) {
            canvas[y][x] = line[charIdx];
          }
        }
      }
    }
    
    // Convert canvas back to strings
    return canvas.map(row => row.join(''));
  }

  // Draw hotkey help
  static drawHotkeys(): string[] {
    return [
      '┌─ Controls ─┐',
      '│ WASD: Move │',
      '│ Space: Act │',
      '│ F9: Render │',
      '│ P: Pause   │',
      '└────────────┘'
    ];
  }

  // Resource cost preview
  static drawCostPreview(costs: Record<string, number>, affordable: boolean): string[] {
    const result: string[] = [];
    
    result.push('┌─ Cost ─┐');
    for (const [resource, amount] of Object.entries(costs)) {
      const icon = affordable ? '✓' : '✗';
      const color = affordable ? '32' : '31'; // Green or red
      result.push(`│ ${icon} ${resource}: ${amount} │`);
    }
    result.push('└────────┘');
    
    return result;
  }
}
