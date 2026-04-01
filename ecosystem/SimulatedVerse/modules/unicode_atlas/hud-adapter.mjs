// HUD Adapter: Unicode system integration for ASCII HUD and UI components
// Provides font detection, fallback handling, and dynamic styling

export class UnicodeHudAdapter {
  constructor() {
    this.fontSupport = new Map();
    this.fallbackEnabled = true;
  }

  // Test if a specific Unicode character is supported by current font
  testGlyphSupport(codePoint) {
    const char = String.fromCodePoint(codePoint);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.font = '16px monospace';
    
    const normalWidth = ctx.measureText('A').width;
    const testWidth = ctx.measureText(char).width;
    
    // If width is 0 or matches the fallback glyph width, not supported
    return testWidth > 0 && testWidth !== normalWidth;
  }

  // Get the best available variant for a character
  getBestVariant(char, variants) {
    for (const variant of variants) {
      if (this.testGlyphSupport(variant.codePointAt(0))) {
        return variant;
      }
    }
    return this.fallbackEnabled ? char : '';
  }

  // Apply safe styling with mobile/desktop awareness
  styleText(text, profile = 'readable', options = {}) {
    const isMobile = window.innerWidth < 800;
    const maxProfile = isMobile ? 'subtle' : profile;
    
    if (options.fallbackOnly) {
      return text; // Plain text fallback
    }

    // Use Zalgo with appropriate profile
    return this.applyZalgo(text, maxProfile);
  }

  // Bridge to Zalgo system
  applyZalgo(text, profile) {
    // This would import zalgoSafe when running in browser context
    // For now, return styled placeholder
    return text; // Will be enhanced with actual Zalgo implementation
  }

  // Generate accessibility mirror
  generateAriaLabel(styledText, plainText) {
    return {
      'aria-label': plainText,
      'title': `Styled text: ${plainText}`,
      'data-plain': plainText
    };
  }
}