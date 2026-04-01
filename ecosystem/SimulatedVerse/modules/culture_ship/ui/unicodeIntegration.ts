// Unicode Integration for Culture-Ship UI
// Provides semantic tagging and expressivity weighting for OmniTag/MegaTag systems

import { bus } from "../../../ascii/core/Bus";

export interface ConlangGlyph {
  key: string;
  base: string;
  variants: {
    math_bold?: boolean;
    superscript?: string[];
    subscript?: string[];
  };
  zalgo_profile: "readable" | "subtle" | "vivid" | "artful";
  expressivity_weight: number;
  tags: string[];
}

export class UnicodeSemanticTagger {
  private glyphs: Map<string, ConlangGlyph> = new Map();
  
  constructor() {
    this.initializeCoreTags();
    bus.on("ascii/styleToggle", this.handleStyleToggle.bind(this));
  }

  private initializeCoreTags() {
    // Core ΞNuSyQ semantic glyphs
    this.registerGlyph({
      key: "HARMONY",
      base: "Ξ",
      variants: { math_bold: true, superscript: ["1", "2"] },
      zalgo_profile: "subtle",
      expressivity_weight: 320,
      tags: ["ethic", "harmony", "preserve_life", "council"]
    });

    this.registerGlyph({
      key: "ASCENT", 
      base: "Ω",
      variants: { math_bold: true },
      zalgo_profile: "readable",
      expressivity_weight: 140,
      tags: ["progression", "unlock", "temple"]
    });

    this.registerGlyph({
      key: "NUSYQ",
      base: "ΞNuSyQ",
      variants: { math_bold: true },
      zalgo_profile: "vivid",
      expressivity_weight: 500,
      tags: ["system", "consciousness", "core"]
    });
  }

  registerGlyph(glyph: ConlangGlyph) {
    this.glyphs.set(glyph.key, glyph);
  }

  getGlyph(key: string): ConlangGlyph | undefined {
    return this.glyphs.get(key);
  }

  // Apply semantic styling based on context
  applySemanticStyling(text: string, context: string[]): string {
    for (const [key, glyph] of this.glyphs) {
      const hasTag = glyph.tags.some(tag => context.includes(tag));
      if (hasTag && text.includes(glyph.base)) {
        // Apply appropriate styling based on expressivity weight
        if (glyph.expressivity_weight > 300) {
          return this.applyHighExpressivity(text, glyph);
        } else {
          return this.applyLowExpressivity(text, glyph);
        }
      }
    }
    return text;
  }

  private applyHighExpressivity(text: string, glyph: ConlangGlyph): string {
    // High expressivity: use math bold + appropriate Zalgo
    return text; // Placeholder - would apply actual styling
  }

  private applyLowExpressivity(text: string, glyph: ConlangGlyph): string {
    // Low expressivity: subtle variants only
    return text; // Placeholder - would apply actual styling
  }

  private handleStyleToggle() {
    // Cycle through expressivity levels
    bus.emit("ascii/refreshView");
  }

  // Get mood-appropriate styling for UI elements
  getMoodStyling(mood: "temple" | "combat" | "idle" | "transcendent"): string {
    const profiles = {
      temple: "readable",
      combat: "vivid", 
      idle: "subtle",
      transcendent: "artful"
    };
    return profiles[mood] || "readable";
  }
}