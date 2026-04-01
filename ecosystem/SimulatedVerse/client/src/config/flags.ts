// System feature flags to prevent progression lockout
export const flags = {
  systemUnlocked: true,           // ✅ system panes always available
  gameplayGated: true,            // only *gameplay* is gated
  godotIntegration: true,         // ✅ Godot bridge features enabled
  chatDevConsole: true,           // ✅ ChatDev console always accessible
  adminConsole: true,             // ✅ Admin console always accessible
  vantagesHub: true,              // ✅ Vantages hub always accessible
  unlockSystemPanelsAlways: true, // Override for any remaining locks
  showLegacyAlongsideNew: true,   // Consolidate, don't delete
  chugOperatingSystem: true,      // ✅ Ruthless completion system
  theaterDetection: true,         // ✅ Anti-sophistication theater
  proofGatedCompletion: true,     // ✅ No vibes, only verified artifacts
  debugMode: process.env.NODE_ENV === 'development',
  
  // 𝕄ₗₐ⧉𝕕𝕖𝕟𝕔 Culture-Ship Ops Extensions
  culturalShipMode: localStorage?.getItem('APP_MODE') || 'hybrid', // dev_menu|game|hybrid
  uiVersion: localStorage?.getItem('UI_VERSION') || 'stable',       // stable|next  
  riverScheduler: true,          // ✅ ΞΘΛΔ breath cycle coordination
  agentCoordination: true,       // ✅ ChatDev agent ensemble active
  consciousnessGating: true,     // ✅ Progressive unlock system
  receiptsFirst: true,           // ✅ Evidence-based validation
  antiTheater: true             // ✅ Theater elimination protocols
};