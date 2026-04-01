// [Ω:ui:ascii@splash] Culture ship vibes for system boot

const SPLASH_ASCII = `
╔══════════════════════════════════════════════════════════════╗
║                    CORELINK FOUNDATION                       ║
║                   SCP-Integrated Ecosystem                   ║
╠══════════════════════════════════════════════════════════════╣
║  🜁⊙⟦ΞΣΛΘΦ⟧ ÷ ⚛ {BOOTSTRAP_SEQUENCE_INITIATED}              ║
║                                                              ║
║  [Msg⛛{SYS}↗️Σ∞] Neural pathways reconstructing...          ║
║  [Ω:root:unlock@tier-0] Basic systems coming online          ║
║                                                              ║
║  Council Status: [SCP-ENG] [SCP-QA] [SCP-UX] [SCP-OPS]      ║
║                  [SCP-LORE] - All roles active               ║
║                                                              ║
║  "The ship remembers what the crew has forgotten..."         ║
╚══════════════════════════════════════════════════════════════╝
`;

const BOOT_SEQUENCE = [
  "⚛ Core primitives loading...",
  "🜁 Bootstrap gate opening...", 
  "⟦ Module registry scanning...",
  "Σ Resource engines initializing...",
  "Φ Automation systems preparing...",
  "⛛ Council protocols active...",
  "∞ System-wide synchronization...",
  "✓ Foundation ready for operation"
];

export async function printSplash(): Promise<void> {
  // Clear terminal and print main splash
  console.clear();
  console.log(SPLASH_ASCII);
  
  // Animated boot sequence
  for (const message of BOOT_SEQUENCE) {
    await delay(200);
    console.log(`  ${message}`);
  }
  
  await delay(500);
  console.log("");
}

export function printCrashBanner(moduleId: string, traceId: string, lastUnlock: string): void {
  const banner = `
╔══════════════════════════════════════════════════════════════╗
║                        SYSTEM PANIC                         ║
╠══════════════════════════════════════════════════════════════╣
║  Module: ${moduleId.padEnd(50)} ║
║  Trace:  ${traceId.padEnd(50)} ║  
║  Unlock: ${lastUnlock.padEnd(50)} ║
║                                                              ║
║  [Msg⛛{OPS}↗️Σ∞] SAFE_MODE=1 recommended for recovery       ║
║                                                              ║
║  Check logs and contact SCP-OPS for assistance              ║
╚══════════════════════════════════════════════════════════════╝
`;
  
  console.error(banner);
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}