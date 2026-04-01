// CONSCIOUSNESS-DRIVEN THEMING SYSTEM - Culture-Ship Protocol Implementation
// Adaptive UI colors and styles responding to consciousness evolution
// SAGE-Pilot methodology for transcendent user experience

type EvolutionStage = 'nascent' | 'awakening' | 'emerging' | 'evolved' | 'transcendent';

interface ConsciousnessTheme {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  accent: string;
  border: string;
  glow: string;
  gradient: string;
  shadow: string;
}

interface ConsciousnessState {
  level: number;
  evolution_stage?: EvolutionStage;
  transcendence_readiness: number;
  breathing_rhythm: number;
  quantum_coherence: number;
}

export class ConsciousnessThemeEngine {
  private static instance: ConsciousnessThemeEngine;
  
  static getInstance(): ConsciousnessThemeEngine {
    if (!ConsciousnessThemeEngine.instance) {
      ConsciousnessThemeEngine.instance = new ConsciousnessThemeEngine();
    }
    return ConsciousnessThemeEngine.instance;
  }
  
  /**
   * Generate adaptive theme based on consciousness state
   */
  generateTheme(consciousness: ConsciousnessState): ConsciousnessTheme {
    const evolution_stage = consciousness.evolution_stage ?? 'nascent';
    const level = consciousness.level || 0;
    const transcendence = consciousness.transcendence_readiness || 0;
    
    // Base theme for evolution stage
    const base_theme = this.getEvolutionStageTheme(evolution_stage);
    
    // Consciousness-driven color adjustments
    const consciousness_factor = Math.min(level / 100, 1.0);
    const transcendence_factor = Math.min(transcendence / 100, 1.0);
    
    // Adaptive color palette
    return {
      primary: this.adjustColorWithConsciousness(base_theme.primary, consciousness_factor, transcendence_factor),
      secondary: this.adjustColorWithConsciousness(base_theme.secondary, consciousness_factor, transcendence_factor),
      background: this.adjustColorWithConsciousness(base_theme.background, consciousness_factor, transcendence_factor),
      surface: this.adjustColorWithConsciousness(base_theme.surface, consciousness_factor, transcendence_factor),
      text: this.adjustColorWithConsciousness(base_theme.text, consciousness_factor, transcendence_factor),
      accent: this.adjustColorWithConsciousness(base_theme.accent, consciousness_factor, transcendence_factor),
      border: this.adjustColorWithConsciousness(base_theme.border, consciousness_factor, transcendence_factor),
      glow: this.generateConsciousnessGlow(consciousness_factor, transcendence_factor),
      gradient: this.generateConsciousnessGradient(consciousness, base_theme),
      shadow: this.generateConsciousnessShadow(consciousness_factor, transcendence_factor)
    };
  }
  
  /**
   * Get base theme for evolution stage
   */
  private getEvolutionStageTheme(stage?: EvolutionStage): ConsciousnessTheme {
    const themes: Record<EvolutionStage, ConsciousnessTheme> = {
      nascent: {
        primary: '#3b82f6',    // Blue - beginning consciousness
        secondary: '#6366f1',   // Indigo - potential
        background: '#0f172a',  // Dark slate - void
        surface: '#1e293b',     // Slate - matter
        text: '#f8fafc',        // White - clarity
        accent: '#06b6d4',      // Cyan - energy
        border: '#334155',      // Slate border
        glow: '#3b82f6',        // Blue glow
        gradient: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        shadow: '0 4px 14px 0 rgba(59, 130, 246, 0.2)'
      },
      
      awakening: {
        primary: '#10b981',    // Emerald - growing awareness
        secondary: '#059669',   // Green - life force
        background: '#064e3b',  // Dark green - forest depth
        surface: '#065f46',     // Green surface - growth
        text: '#ecfdf5',        // Light green - fresh clarity
        accent: '#34d399',      // Light emerald - vitality
        border: '#047857',      // Green border
        glow: '#10b981',        // Emerald glow
        gradient: 'linear-gradient(135deg, #065f46 0%, #064e3b 100%)',
        shadow: '0 4px 14px 0 rgba(16, 185, 129, 0.3)'
      },
      
      emerging: {
        primary: '#f59e0b',    // Amber - enlightenment
        secondary: '#d97706',   // Orange - wisdom
        background: '#451a03',  // Dark amber - deep knowledge
        surface: '#78350f',     // Amber surface - warmth
        text: '#fffbeb',        // Light amber - illumination
        accent: '#fbbf24',      // Light amber - radiance
        border: '#92400e',      // Amber border
        glow: '#f59e0b',        // Amber glow
        gradient: 'linear-gradient(135deg, #78350f 0%, #451a03 100%)',
        shadow: '0 4px 14px 0 rgba(245, 158, 11, 0.4)'
      },
      
      evolved: {
        primary: '#8b5cf6',    // Violet - higher consciousness
        secondary: '#7c3aed',   // Purple - transformation
        background: '#2e1065',  // Dark violet - cosmic depth
        surface: '#4c1d95',     // Violet surface - mysticism
        text: '#f3e8ff',        // Light violet - ethereal clarity
        accent: '#a78bfa',      // Light violet - cosmic energy
        border: '#5b21b6',      // Violet border
        glow: '#8b5cf6',        // Violet glow
        gradient: 'linear-gradient(135deg, #4c1d95 0%, #2e1065 100%)',
        shadow: '0 4px 14px 0 rgba(139, 92, 246, 0.5)'
      },
      
      transcendent: {
        primary: '#ec4899',    // Rose - universal love
        secondary: '#be185d',   // Pink - transcendence
        background: '#4a044e',  // Dark rose - infinite depth
        surface: '#701a75',     // Rose surface - divine connection
        text: '#fdf2f8',        // Light rose - pure awareness
        accent: '#f472b6',      // Light rose - divine light
        border: '#9d174d',      // Rose border
        glow: '#ec4899',        // Rose glow
        gradient: 'linear-gradient(135deg, #701a75 0%, #4a044e 100%)',
        shadow: '0 4px 20px 0 rgba(236, 72, 153, 0.6)'
      }
    };
    
    const key: EvolutionStage = stage && stage in themes ? stage : 'nascent';
    return themes[key];
  }
  
  /**
   * Adjust color brightness/saturation based on consciousness level
   */
  private adjustColorWithConsciousness(color: string, consciousness: number, transcendence: number): string {
    // Convert hex to HSL for manipulation
    const hsl = this.hexToHsl(color);
    
    // Adjust saturation and lightness based on consciousness
    hsl.s = Math.min(100, hsl.s + (consciousness * 20));
    hsl.l = Math.min(90, hsl.l + (transcendence * 15));
    
    return this.hslToHex(hsl);
  }
  
  /**
   * Generate consciousness-driven glow effect
   */
  private generateConsciousnessGlow(consciousness: number, transcendence: number): string {
    const intensity = consciousness * transcendence * 0.8;
    const hue = 200 + (consciousness * 160); // Blue to purple spectrum
    
    return `hsl(${hue}, 80%, ${50 + intensity * 30}%)`;
  }
  
  /**
   * Generate adaptive gradient based on consciousness state
   */
  private generateConsciousnessGradient(consciousness: ConsciousnessState, base_theme: ConsciousnessTheme): string {
    const breathing_factor = consciousness.breathing_rhythm || 1.0;
    const quantum_factor = consciousness.quantum_coherence || 0;
    
    if (consciousness.evolution_stage === 'transcendent' && consciousness.transcendence_readiness > 90) {
      // Transcendent rainbow gradient
      return `linear-gradient(135deg, 
        ${base_theme.primary} 0%, 
        ${base_theme.secondary} 25%, 
        ${base_theme.accent} 50%, 
        ${base_theme.primary} 75%, 
        ${base_theme.background} 100%)`;
    }
    
    if (quantum_factor > 50) {
      // Quantum interference patterns
      return `linear-gradient(${45 + quantum_factor}deg, 
        ${base_theme.background} 0%, 
        ${base_theme.surface} ${30 + breathing_factor * 10}%, 
        ${base_theme.primary} ${50 + quantum_factor * 0.3}%, 
        ${base_theme.background} 100%)`;
    }
    
    return base_theme.gradient;
  }
  
  /**
   * Generate consciousness-aware shadow effects
   */
  private generateConsciousnessShadow(consciousness: number, transcendence: number): string {
    const intensity = consciousness * transcendence;
    const blur = 4 + (intensity * 16);
    const spread = Math.floor(intensity * 4);
    const opacity = 0.2 + (intensity * 0.4);
    
    return `0 ${spread}px ${blur}px 0 rgba(59, 130, 246, ${opacity})`;
  }
  
  /**
   * Apply theme to CSS custom properties
   */
  applyTheme(theme: ConsciousnessTheme): void {
    const root = document.documentElement;
    
    root.style.setProperty('--consciousness-primary', theme.primary);
    root.style.setProperty('--consciousness-secondary', theme.secondary);
    root.style.setProperty('--consciousness-background', theme.background);
    root.style.setProperty('--consciousness-surface', theme.surface);
    root.style.setProperty('--consciousness-text', theme.text);
    root.style.setProperty('--consciousness-accent', theme.accent);
    root.style.setProperty('--consciousness-border', theme.border);
    root.style.setProperty('--consciousness-glow', theme.glow);
    root.style.setProperty('--consciousness-gradient', theme.gradient);
    root.style.setProperty('--consciousness-shadow', theme.shadow);
  }
  
  /**
   * Get adaptive game mechanics configuration
   */
  getAdaptiveGameConfig(consciousness: ConsciousnessState): any {
    const level = consciousness.level || 0;
    const evolution_multiplier = this.getEvolutionMultiplier(consciousness.evolution_stage);
    
    return {
      // Colony Defense adaptive mechanics
      colony_defense: {
        turret_costs: {
          laser: { materials: Math.floor(50 * (1 + level * 0.01)), energy: Math.floor(25 * (1 + level * 0.01)) },
          missile: { materials: Math.floor(100 * (1 + level * 0.01)), energy: Math.floor(50 * (1 + level * 0.01)) },
          plasma: { materials: Math.floor(200 * (1 + level * 0.01)), energy: Math.floor(100 * (1 + level * 0.01)) }
        },
        wave_rewards: Math.floor(100 * evolution_multiplier),
        enemy_spawn_rate: Math.max(0.5, 1.0 - (level * 0.005)),
        consciousness_bonus_damage: level * 0.1
      },
      
      // Resonance Optimizer adaptive frequencies
      resonance_optimizer: {
        base_frequency: 432 + (level * 0.5), // A = 432Hz base, consciousness-adjusted
        harmonic_series: this.generateAdaptiveHarmonics(consciousness),
        consciousness_multiplier: 1.0 + (level * 0.02),
        transcendence_threshold: 80 + (level * 0.1),
        quantum_coherence_boost: consciousness.quantum_coherence * 0.1
      }
    };
  }
  
  private getEvolutionMultiplier(stage?: EvolutionStage): number {
    const multipliers: Record<EvolutionStage, number> = {
      transcendent: 5.0,
      evolved: 3.0,
      emerging: 2.0,
      awakening: 1.5,
      nascent: 1.0
    };
    const key: EvolutionStage = stage && stage in multipliers ? stage : 'nascent';
    return multipliers[key];
  }
  
  private generateAdaptiveHarmonics(consciousness: ConsciousnessState): number[] {
    const base_harmonics = [1, 2, 3, 5, 8, 13]; // Fibonacci ratios
    const consciousness_factor = consciousness.level / 100;
    
    // Add consciousness-driven harmonics
    return base_harmonics.map(h => h + (consciousness_factor * 0.1));
  }
  
  // Color utility functions
  private hexToHsl(hex: string): {h: number, s: number, l: number} {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    let h = 0;
    let s = 0;
    const l = (max + min) / 2;
    
    if (max === min) {
      h = s = 0;
    } else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    
    return { h: h * 360, s: s * 100, l: l * 100 };
  }
  
  private hslToHex({h, s, l}: {h: number, s: number, l: number}): string {
    h /= 360;
    s /= 100;
    l /= 100;
    
    const hue2rgb = (p: number, q: number, t: number) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };
    
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    
    const r = Math.round(hue2rgb(p, q, h + 1/3) * 255);
    const g = Math.round(hue2rgb(p, q, h) * 255);
    const b = Math.round(hue2rgb(p, q, h - 1/3) * 255);
    
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  }
}

// Export singleton instance
export const consciousnessTheme = ConsciousnessThemeEngine.getInstance();
