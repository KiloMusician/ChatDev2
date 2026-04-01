/**
 * Convergence Validation Script
 * Final validation of UI↔Game convergence and golden traces
 */

import fs from "fs/promises";

interface ValidationResult {
  timestamp: number;
  world_online: boolean;
  golden_traces_complete: boolean;
  ui_toggle_functional: boolean;
  ascii_game_working: boolean;
  adapter_detected: boolean;
  critical_issues: string[];
  validation_summary: string;
}

async function validateUIToggle(): Promise<boolean> {
  try {
    // Test both routes exist and return different content
    const gameResponse = await fetch('http://localhost:5000/game');
    const devResponse = await fetch('http://localhost:5000/dev');
    
    if (!gameResponse.ok || !devResponse.ok) {
      return false;
    }
    
    const gameContent = await gameResponse.text();
    const devContent = await devResponse.text();
    
    // Check for distinctive markers
    const hasGameMarkers = gameContent.includes('GameShell') || gameContent.includes('game-root');
    const hasDevMarkers = devContent.includes('DevMenu') || devContent.includes('Golden Traces');
    
    return hasGameMarkers && hasDevMarkers;
  } catch (error) {
    console.error('[VALIDATION] UI toggle test failed:', error);
    return false;
  }
}

async function validateGoldenTraces(): Promise<{ complete: boolean; count: number }> {
  try {
    const telemetryPath = "SystemDev/reports/telemetry_summary.json";
    const content = await fs.readFile(telemetryPath, 'utf-8');
    const telemetry = JSON.parse(content);
    
    return {
      complete: telemetry.convergence_complete || false,
      count: telemetry.golden_traces_count || 0,
    };
  } catch (error) {
    return { complete: false, count: 0 };
  }
}

async function validateASCIIGame(): Promise<boolean> {
  try {
    // Check if ASCII game endpoint responds
    const response = await fetch('http://localhost:5000/game');
    if (!response.ok) return false;
    
    const content = await response.text();
    
    // Look for ASCII game markers
    return content.includes('data-game-root') || 
           content.includes('ASCII') || 
           content.includes('canvas') ||
           content.includes('GameShell');
  } catch (error) {
    return false;
  }
}

async function validateAdapterPresence(): Promise<boolean> {
  try {
    // Check for adapter files
    const adapterPaths = [
      "client/src/components/GameShell.tsx",
      "PreviewUI/web/adapters/GameShell.tsx",
    ];
    
    for (const path of adapterPaths) {
      try {
        const content = await fs.readFile(path, 'utf-8');
        if (content.includes('GameShell') && content.includes('adapter')) {
          return true;
        }
      } catch (error) {
        // File doesn't exist, continue
      }
    }
    
    return false;
  } catch (error) {
    return false;
  }
}

export async function runValidation(): Promise<ValidationResult> {
  console.log("[VALIDATION] Running final convergence validation...");
  
  const criticalIssues: string[] = [];
  
  // Test UI toggle
  const uiToggleFunctional = await validateUIToggle();
  if (!uiToggleFunctional) {
    criticalIssues.push("UI toggle between /game and /dev routes not functional");
  }
  
  // Test golden traces
  const goldenTraces = await validateGoldenTraces();
  if (!goldenTraces.complete) {
    criticalIssues.push(`Golden traces incomplete: ${goldenTraces.count}/5 captured`);
  }
  
  // Test ASCII game
  const asciiGameWorking = await validateASCIIGame();
  if (!asciiGameWorking) {
    criticalIssues.push("ASCII game not accessible or missing game markers");
  }
  
  // Test adapter presence
  const adapterDetected = await validateAdapterPresence();
  if (!adapterDetected) {
    criticalIssues.push("GameShell adapter not detected in expected locations");
  }
  
  // Determine world online status
  const worldOnline = uiToggleFunctional && 
                     goldenTraces.complete && 
                     asciiGameWorking && 
                     adapterDetected &&
                     criticalIssues.length === 0;
  
  const result: ValidationResult = {
    timestamp: Date.now(),
    world_online: worldOnline,
    golden_traces_complete: goldenTraces.complete,
    ui_toggle_functional: uiToggleFunctional,
    ascii_game_working: asciiGameWorking,
    adapter_detected: adapterDetected,
    critical_issues: criticalIssues,
    validation_summary: worldOnline 
      ? "🌌 WORLD ONLINE - All convergence criteria met"
      : `❌ Convergence incomplete - ${criticalIssues.length} critical issues`,
  };
  
  // Save validation results
  await fs.mkdir("SystemDev/receipts", { recursive: true });
  await fs.writeFile(
    `SystemDev/receipts/convergence_validation_${Date.now()}.json`,
    JSON.stringify(result, null, 2)
  );
  
  // Update final status
  await fs.mkdir("SystemDev/reports", { recursive: true });
  await fs.writeFile(
    "SystemDev/reports/final_convergence_status.json",
    JSON.stringify(result, null, 2)
  );
  
  return result;
}

export async function generateFinalReport(): Promise<void> {
  const validation = await runValidation();
  
  console.log(`\n[VALIDATION] ══════════════════════════════════════════`);
  console.log(`[VALIDATION] 🌌 FINAL CONVERGENCE VALIDATION REPORT`);
  console.log(`[VALIDATION] ══════════════════════════════════════════`);
  console.log(`[VALIDATION] World Online: ${validation.world_online ? '✅ YES' : '❌ NO'}`);
  console.log(`[VALIDATION] UI Toggle: ${validation.ui_toggle_functional ? '✅' : '❌'}`);
  console.log(`[VALIDATION] Golden Traces: ${validation.golden_traces_complete ? '✅' : '❌'}`);
  console.log(`[VALIDATION] ASCII Game: ${validation.ascii_game_working ? '✅' : '❌'}`);
  console.log(`[VALIDATION] Adapter: ${validation.adapter_detected ? '✅' : '❌'}`);
  
  if (validation.critical_issues.length > 0) {
    console.log(`\n[VALIDATION] Critical Issues:`);
    validation.critical_issues.forEach(issue => 
      console.log(`[VALIDATION]   ❌ ${issue}`)
    );
  }
  
  console.log(`\n[VALIDATION] ${validation.validation_summary}`);
  console.log(`[VALIDATION] Report saved: SystemDev/reports/final_convergence_status.json`);
  
  if (validation.world_online) {
    console.log(`\n[VALIDATION] 🎉 SUCCESS: UI↔Game convergence achieved!`);
    console.log(`[VALIDATION] 🚀 Ready for next phase: vertical slice expansion`);
  } else {
    console.log(`\n[VALIDATION] ⚠️  Additional work needed for full convergence`);
  }
}

// CLI interface for ES modules
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  generateFinalReport().catch(console.error);
}