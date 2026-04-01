/**
 * ΞΘΛΔ_ui_route - UI Route Entanglement Detection
 * Raven breath for detecting route drift, entry collisions, adapter gaps
 */

import fs from "fs/promises";
import path from "path";
import glob from "fast-glob";

interface RouteEntry {
  path: string;
  type: "mount" | "fallback" | "static" | "api";
  priority: number;
  source: string;
  component?: string;
  adapter?: string;
}

interface UIEntanglement {
  routes: RouteEntry[];
  conflicts: Array<{
    route: string;
    conflicts: RouteEntry[];
    priority_winner: RouteEntry;
  }>;
  missing_adapters: string[];
  legacy_mounts: string[];
  game_shell_status: "missing" | "present_not_mounted" | "mounted" | "active";
  dev_menu_status: "missing" | "present_not_mounted" | "mounted" | "active";
  entry_precedence: {
    winner: string;
    all_entries: string[];
    server_config: any;
  };
}

export async function analyzeUIRoutes(): Promise<UIEntanglement> {
  const result: UIEntanglement = {
    routes: [],
    conflicts: [],
    missing_adapters: [],
    legacy_mounts: [],
    game_shell_status: "missing",
    dev_menu_status: "missing",
    entry_precedence: {
      winner: "unknown",
      all_entries: [],
      server_config: null,
    },
  };

  // Scan PreviewUI routes
  const previewFiles = await glob([
    "PreviewUI/**/*.{ts,tsx,js,jsx}",
    "client/src/**/*.{ts,tsx,js,jsx}",
    "dist/**/*.html",
  ]);

  // Analyze server routes
  const serverFiles = await glob([
    "server/**/*.{ts,js}",
    "SystemDev/scripts/patches/preview_launcher.ts",
  ]);

  // Extract route definitions
  for (const file of previewFiles) {
    try {
      const content = await fs.readFile(file, "utf-8");
      await extractRoutesFromFile(file, content, result);
    } catch (error) {
      // Silent fail for missing files
    }
  }

  for (const file of serverFiles) {
    try {
      const content = await fs.readFile(file, "utf-8");
      await extractServerRoutesFromFile(file, content, result);
    } catch (error) {
      // Silent fail for missing files
    }
  }

  // Detect conflicts and precedence
  analyzeConflicts(result);
  await analyzeAdapterStatus(result);
  await analyzeComponentStatus(result);

  return result;
}

async function extractRoutesFromFile(filePath: string, content: string, result: UIEntanglement) {
  // Look for Route components
  const routeMatches = content.match(/<Route[^>]*path=["']([^"']+)["'][^>]*component=\{?([^}>\s]+)\}?/g);
  if (routeMatches) {
    for (const match of routeMatches) {
      const pathMatch = match.match(/path=["']([^"']+)["']/);
      const componentMatch = match.match(/component=\{?([^}>\s]+)\}?/);
      
      if (pathMatch) {
        result.routes.push({
          path: pathMatch[1],
          type: "mount",
          priority: 50,
          source: filePath,
          component: componentMatch?.[1] || "unknown",
        });
      }
    }
  }

  // Look for Router switches
  const switchMatches = content.match(/Switch[^>]*>([\s\S]*?)<\/Switch>/g);
  if (switchMatches) {
    for (const switchContent of switchMatches) {
      // Extract routes within switches
      await extractRoutesFromFile(filePath + ":switch", switchContent, result);
    }
  }

  // Look for mode toggles
  if (content.includes("PLAY_MODE") || content.includes("GameShell") || content.includes("DevMenu")) {
    const hasGameShell = content.includes("GameShell");
    const hasDevMenu = content.includes("DevMenu");
    
    if (hasGameShell) {
      result.game_shell_status = content.includes("mode === 'game'") ? "mounted" : "present_not_mounted";
    }
    
    if (hasDevMenu) {
      result.dev_menu_status = content.includes("mode === 'dev_menu'") || content.includes("DevMenu") ? "mounted" : "present_not_mounted";
    }
  }
}

async function extractServerRoutesFromFile(filePath: string, content: string, result: UIEntanglement) {
  // Look for Express routes
  const routeMatches = content.match(/app\.(get|post|put|delete)\(["']([^"']+)["']/g);
  if (routeMatches) {
    for (const match of routeMatches) {
      const pathMatch = match.match(/["']([^"']+)["']/);
      if (pathMatch) {
        result.routes.push({
          path: pathMatch[1],
          type: "api",
          priority: 80,
          source: filePath,
        });
      }
    }
  }

  // Look for static serving
  const staticMatches = content.match(/app\.use\(["']([^"']*?)["'],?\s*express\.static/g);
  if (staticMatches) {
    for (const match of staticMatches) {
      const pathMatch = match.match(/["']([^"']*?)["']/);
      if (pathMatch) {
        result.routes.push({
          path: pathMatch[1] || "/",
          type: "static",
          priority: 10,
          source: filePath,
        });
      }
    }
  }

  // Look for SPA fallbacks
  if (content.includes("sendFile") && (content.includes("index.html") || content.includes("fallback"))) {
    const fallbackMatches = content.match(/app\.get\(["']([^"']+)["'][^}]*sendFile/g);
    if (fallbackMatches) {
      for (const match of fallbackMatches) {
        const pathMatch = match.match(/["']([^"']+)["']/);
        if (pathMatch) {
          result.routes.push({
            path: pathMatch[1],
            type: "fallback",
            priority: 5,
            source: filePath,
          });
        }
      }
    }
  }
}

function analyzeConflicts(result: UIEntanglement) {
  const routeGroups = new Map<string, RouteEntry[]>();
  
  // Group routes by path
  for (const route of result.routes) {
    const normalizedPath = route.path.replace(/\/+$/, '') || '/';
    if (!routeGroups.has(normalizedPath)) {
      routeGroups.set(normalizedPath, []);
    }
    routeGroups.get(normalizedPath)!.push(route);
  }

  // Find conflicts (multiple routes for same path)
  for (const [routePath, routes] of routeGroups) {
    if (routes.length > 1) {
      // Sort by priority (higher priority wins)
      const sortedRoutes = [...routes].sort((a, b) => b.priority - a.priority);
      
      result.conflicts.push({
        route: routePath,
        conflicts: routes,
        priority_winner: sortedRoutes[0],
      });
    }
  }

  // Determine entry precedence
  const rootRoutes = routeGroups.get('/') || [];
  if (rootRoutes.length > 0) {
    const winner = rootRoutes.sort((a, b) => b.priority - a.priority)[0];
    result.entry_precedence = {
      winner: winner.source,
      all_entries: rootRoutes.map(r => r.source),
      server_config: winner,
    };
  }
}

async function analyzeAdapterStatus(result: UIEntanglement) {
  // Check for GameShell adapter
  const adapterPaths = [
    "PreviewUI/web/adapters/game_shell_adapter.ts",
    "PreviewUI/web/adapters/GameShell.tsx",
    "client/src/adapters/GameShell.tsx",
    "GameDev/ui/adapters/GameShell.tsx",
  ];

  for (const adapterPath of adapterPaths) {
    try {
      const content = await fs.readFile(adapterPath, "utf-8");
      if (content.includes("GameShell") || content.includes("mountASCII") || content.includes("game_shell_adapter")) {
        // Adapter exists
        break;
      }
    } catch (error) {
      result.missing_adapters.push(adapterPath);
    }
  }
}

async function analyzeComponentStatus(result: UIEntanglement) {
  // Look for legacy components that might be mounting instead of game
  const legacyPatterns = [
    "DevMenuOld",
    "LegacyUI", 
    "DebugShell",
    "TestInterface",
  ];

  const componentFiles = await glob([
    "PreviewUI/**/*.{ts,tsx}",
    "client/src/**/*.{ts,tsx}",
  ]);

  for (const file of componentFiles) {
    try {
      const content = await fs.readFile(file, "utf-8");
      for (const pattern of legacyPatterns) {
        if (content.includes(pattern)) {
          result.legacy_mounts.push(`${file}: ${pattern}`);
        }
      }
    } catch (error) {
      // Silent fail
    }
  }
}

export async function generateUIRouteReport(): Promise<void> {
  const analysis = await analyzeUIRoutes();
  
  const receipt = {
    timestamp: Date.now(),
    operation: "ui_route_analysis",
    breath: "ΞΘΛΔ_ui_route",
    agent: "raven",
    analysis,
    recommendations: generateRecommendations(analysis),
    golden_trace_readiness: assessGoldenTraceReadiness(analysis),
  };

  // Ensure reports directory exists
  await fs.mkdir("SystemDev/reports", { recursive: true });
  
  // Write main report
  await fs.writeFile(
    "SystemDev/reports/ui_entanglement.json",
    JSON.stringify(analysis, null, 2)
  );

  // Write receipt
  await fs.mkdir("SystemDev/receipts", { recursive: true });
  await fs.writeFile(
    `SystemDev/receipts/ui_route_analysis_${Date.now()}.json`,
    JSON.stringify(receipt, null, 2)
  );

  console.log(`[RAVEN:ΞΘΛΔ_ui_route] Analysis complete → SystemDev/reports/ui_entanglement.json`);
}

function generateRecommendations(analysis: UIEntanglement): string[] {
  const recommendations: string[] = [];

  if (analysis.conflicts.length > 0) {
    recommendations.push(`Route conflicts detected: ${analysis.conflicts.length} paths have multiple handlers`);
  }

  if (analysis.game_shell_status === "missing") {
    recommendations.push("GameShell component missing - synthesize adapter via Librarian");
  } else if (analysis.game_shell_status === "present_not_mounted") {
    recommendations.push("GameShell exists but not mounted - add mode toggle");
  }

  if (analysis.missing_adapters.length > 0) {
    recommendations.push(`Missing adapters: ${analysis.missing_adapters.length} adapter paths not found`);
  }

  if (analysis.legacy_mounts.length > 0) {
    recommendations.push(`Legacy components detected: ${analysis.legacy_mounts.length} - may shadow game interface`);
  }

  return recommendations;
}

function assessGoldenTraceReadiness(analysis: UIEntanglement): any {
  return {
    ui_route_mount_ready: analysis.game_shell_status === "mounted" || analysis.game_shell_status === "active",
    route_conflicts_resolved: analysis.conflicts.length === 0,
    adapter_present: analysis.missing_adapters.length === 0,
    legacy_clean: analysis.legacy_mounts.length === 0,
  };
}

// CLI interface for ES modules
const isMainModule = import.meta.url === `file://${process.argv[1]}`;
if (isMainModule) {
  generateUIRouteReport().catch(console.error);
}