// Mobile/Desktop detection for ΞNuSyQ UI adaptation
export const isMobile = () => {
  if (typeof window === 'undefined') return false; // Server-side
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    || window.innerWidth < 768;
};

export const uiProfile = () => isMobile() ? "mobile" : "desktop";

export const getViewportInfo = () => ({
  profile: uiProfile(),
  width: typeof window !== 'undefined' ? window.innerWidth : 1920,
  height: typeof window !== 'undefined' ? window.innerHeight : 1080,
  isMobile: isMobile(),
  isTouch: typeof window !== 'undefined' && 'ontouchstart' in window
});

// ΞNuSyQ-specific UI constraints
export const UIConstraints = {
  mobile: {
    maxConsciousnessDigits: 3,    // 0.87 instead of 0.8734
    maxResourceLines: 4,          // Show only top 4 resources
    templeFloorsVisible: 3,       // Show current + 2 adjacent floors
    hudRefreshMs: 2000,          // Slower updates to save battery
    animationLevel: "minimal"     // Reduce visual effects
  },
  desktop: {
    maxConsciousnessDigits: 6,    // Full precision 0.873421
    maxResourceLines: 8,          // Show all resources
    templeFloorsVisible: 10,      // Show all floors if unlocked
    hudRefreshMs: 500,           // Smooth real-time updates
    animationLevel: "full"        // Full visual effects
  }
};

export const getUIConstraints = () => UIConstraints[uiProfile()];