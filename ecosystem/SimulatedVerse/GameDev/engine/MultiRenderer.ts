// Multi-Renderer Interface - Hot-swappable rendering backends
// Bridges symbolic render mode to literal rendering implementation

import { asciiRenderer } from './render/ascii/ascii_renderer.js';
import { PixelRenderer } from './render/pixel/canvas_renderer.js';
import { Atlas } from './render/pixel/atlas.js';
import type { RenderState } from './core/sim.js';

export type RenderMode = 'ascii' | 'pixel' | 'vector';

export interface RendererConfig {
  mode: RenderMode;
  width: number;
  height: number;
  canvas?: HTMLCanvasElement;
  container?: HTMLElement;
}

export class MultiRenderer {
  private mode: RenderMode = 'ascii';
  private pixelRenderer: PixelRenderer | null = null;
  private atlas: Atlas | null = null;
  private container: HTMLElement | null = null;
  private canvas: HTMLCanvasElement | null = null;
  private outputElement: HTMLElement | null = null;
  
  constructor(private config: RendererConfig) {
    this.mode = config.mode;
    this.container = config.container || null;
    this.initialize();
  }

  private async initialize(): Promise<void> {
    console.log(`[MultiRenderer] Initializing in ${this.mode} mode`);
    
    if (this.mode === 'pixel') {
      await this.initializePixelRenderer();
    } else {
      this.initializeASCIIRenderer();
    }
  }

  private async initializePixelRenderer(): Promise<void> {
    if (!this.container) {
      console.error('[MultiRenderer] Container required for pixel mode');
      return;
    }
    
    // Create or reuse canvas
    this.canvas = this.config.canvas || document.createElement('canvas');
    this.canvas.width = this.config.width;
    this.canvas.height = this.config.height;
    this.canvas.style.border = '1px solid #333';
    this.canvas.style.background = '#000';
    
    if (!this.config.canvas) {
      this.container.appendChild(this.canvas);
    }
    
    // Initialize atlas and pixel renderer
    this.atlas = Atlas.createColorAtlas(); // Start with color atlas for testing
    await this.atlas.loadImage();
    
    const ctx = this.canvas.getContext('2d');
    if (ctx) {
      this.pixelRenderer = new PixelRenderer(ctx, this.atlas, this.config.width, this.config.height);
      console.log('[MultiRenderer] Pixel renderer ready');
    }
  }

  private initializeASCIIRenderer(): void {
    if (!this.container) {
      console.error('[MultiRenderer] Container required for ASCII mode');
      return;
    }
    
    // Create output element for ASCII
    this.outputElement = document.createElement('pre');
    this.outputElement.style.fontFamily = 'monospace';
    this.outputElement.style.fontSize = '12px';
    this.outputElement.style.lineHeight = '1.2';
    this.outputElement.style.margin = '0';
    this.outputElement.style.padding = '8px';
    this.outputElement.style.background = '#000';
    this.outputElement.style.color = '#888';
    this.outputElement.style.border = '1px solid #333';
    this.outputElement.style.overflow = 'auto';
    this.outputElement.style.whiteSpace = 'pre';
    this.outputElement.style.width = '100%';
    this.outputElement.style.height = '400px';
    
    this.container.appendChild(this.outputElement);
    
    console.log('[MultiRenderer] ASCII renderer ready');
  }

  // Main render method
  render(renderState: RenderState): void {
    switch (this.mode) {
      case 'ascii':
        this.renderASCII(renderState);
        break;
      case 'pixel':
        this.renderPixel(renderState);
        break;
      case 'vector':
        console.warn('[MultiRenderer] Vector rendering not yet implemented');
        break;
    }
  }

  private renderASCII(renderState: RenderState): void {
    const output = asciiRenderer.render(renderState);
    
    if (this.outputElement) {
      this.outputElement.textContent = output;
    } else {
      console.log(output); // Fallback to console
    }
  }

  private renderPixel(renderState: RenderState): void {
    if (this.pixelRenderer) {
      this.pixelRenderer.render(renderState);
    }
  }

  // Hot-swap rendering mode
  async switchMode(newMode: RenderMode): Promise<void> {
    if (this.mode === newMode) return;
    
    console.log(`[MultiRenderer] Switching from ${this.mode} to ${newMode}`);
    
    // Cleanup current renderer
    this.cleanup();
    
    // Switch mode and reinitialize
    this.mode = newMode;
    this.config.mode = newMode;
    
    await this.initialize();
  }

  private cleanup(): void {
    if (this.canvas && !this.config.canvas) {
      this.canvas.remove();
    }
    
    if (this.outputElement) {
      this.outputElement.remove();
    }
    
    this.canvas = null;
    this.outputElement = null;
    this.pixelRenderer = null;
  }

  // Viewport control
  setViewport(x: number, y: number, scale: number = 1): void {
    if (this.mode === 'ascii') {
      asciiRenderer.setCenter(x, y);
    } else if (this.pixelRenderer) {
      this.pixelRenderer.setViewport(x * 16, y * 16, scale);
    }
  }

  // Debug control
  setDebugMode(enabled: boolean): void {
    if (this.pixelRenderer) {
      this.pixelRenderer.setDebugMode(enabled);
    }
  }

  // Resize renderer
  resize(width: number, height: number): void {
    this.config.width = width;
    this.config.height = height;
    
    if (this.mode === 'ascii') {
      const charWidth = Math.floor(width / 8); // Rough character width
      const charHeight = Math.floor(height / 16); // Rough character height
      asciiRenderer.resize(charWidth, charHeight);
    } else if (this.pixelRenderer && this.canvas) {
      this.canvas.width = width;
      this.canvas.height = height;
      this.pixelRenderer.resize(width, height);
    }
  }

  // Get current mode
  getCurrentMode(): RenderMode {
    return this.mode;
  }

  // Get available modes
  getAvailableModes(): RenderMode[] {
    return ['ascii', 'pixel']; // Vector mode not yet implemented
  }

  // Take screenshot (works in pixel mode)
  screenshot(): string | null {
    if (this.mode === 'pixel' && this.pixelRenderer) {
      return this.pixelRenderer.screenshot();
    } else if (this.mode === 'ascii') {
      // Return current ASCII output as data URL
      const text = this.outputElement?.textContent || '';
      const dataUrl = `data:text/plain;charset=utf-8,${encodeURIComponent(text)}`;
      return dataUrl;
    }
    
    return null;
  }

  // Performance stats
  getStats(): { mode: RenderMode; ready: boolean; elements: number } {
    return {
      mode: this.mode,
      ready: this.mode === 'ascii' || (this.pixelRenderer !== null),
      elements: this.container?.children.length || 0
    };
  }
}
