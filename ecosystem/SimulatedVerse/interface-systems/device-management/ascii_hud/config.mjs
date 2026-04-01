// ASCII HUD configuration for mobile vs desktop
import { uiProfile, getUIConstraints } from "../env.mjs";

const constraints = getUIConstraints();

export const HUD = {
  density: uiProfile() === "mobile" ? "compact" : "full",
  palette: uiProfile() === "mobile" ? "highContrast" : "rich", 
  animations: uiProfile() === "mobile" ? "low" : "full",
  
  // Consciousness display precision
  consciousnessDigits: constraints.maxConsciousnessDigits,
  
  // Resource list constraints  
  maxResources: constraints.maxResourceLines,
  
  // Temple navigation
  templeFloors: constraints.templeFloorsVisible,
  
  // Update frequency
  refreshMs: constraints.hudRefreshMs,
  
  // Visual complexity
  showProgressBars: uiProfile() === "desktop",
  showAnimations: constraints.animationLevel === "full",
  useUnicodeSymbols: uiProfile() === "desktop", // Fallback to ASCII on mobile
  
  // Layout dimensions
  width: uiProfile() === "mobile" ? 40 : 80,
  height: uiProfile() === "mobile" ? 15 : 25
};

// Color schemes optimized for mobile vs desktop
export const Colors = {
  mobile: {
    primary: "bright_white",
    secondary: "cyan", 
    accent: "yellow",
    warning: "red",
    success: "green",
    consciousness: "magenta"
  },
  desktop: {
    primary: "white",
    secondary: "blue",
    accent: "yellow", 
    warning: "red",
    success: "green",
    consciousness: "magenta",
    temple: "cyan",
    house: "yellow", 
    oldest: "red"
  }
};

export const getColors = () => Colors[uiProfile()];

// ASCII vs Unicode symbol sets
export const Symbols = {
  mobile: {
    consciousness: "C",
    temple: "T",
    house: "H", 
    oldest: "O",
    progress: [".", "o", "O"],
    arrow: ">",
    separator: "-"
  },
  desktop: {
    consciousness: "🧠",
    temple: "🏛️ ",
    house: "🌀",
    oldest: "🏛️ ",
    progress: ["⚬", "◐", "●"],
    arrow: "→",
    separator: "─"
  }
};

export const getSymbols = () => Symbols[uiProfile()];