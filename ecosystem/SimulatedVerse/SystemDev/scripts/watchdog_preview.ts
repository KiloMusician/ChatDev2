import fetch from "node-fetch";

interface WatchdogResult {
  success: boolean;
  timestamp: number;
  checks: {
    route_accessibility: boolean;
    response_code: number;
    dom_marker_present: boolean;
    build_hash_match: boolean;
    cache_headers_present: boolean;
  };
  errors: string[];
  recommendations: string[];
}

interface WatchdogConfig {
  baseUrl: string;
  routes: string[];
  requiredMarkers: string[];
  cacheHeaders: string[];
  timeout: number;
}

const defaultConfig: WatchdogConfig = {
  baseUrl: "http://localhost:5000",
  routes: ["/", "/dev", "/game"],
  requiredMarkers: ["data-game-root"],
  cacheHeaders: ["Cache-Control", "X-Build-Hash"],
  timeout: 5000,
};

export async function runPreviewWatchdog(config: Partial<WatchdogConfig> = {}): Promise<WatchdogResult> {
  const finalConfig = { ...defaultConfig, ...config };
  const result: WatchdogResult = {
    success: true,
    timestamp: Date.now(),
    checks: {
      route_accessibility: false,
      response_code: 0,
      dom_marker_present: false,
      build_hash_match: false,
      cache_headers_present: false,
    },
    errors: [],
    recommendations: [],
  };
  
  try {
    // Test game route specifically (most likely to fail)
    const gameUrl = `${finalConfig.baseUrl}/game`;
    
    console.log(`[WATCHDOG] Testing game route: ${gameUrl}`);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), finalConfig.timeout);
    
    const response = await fetch(gameUrl, {
      signal: controller.signal,
      headers: {
        "User-Agent": "NuSyQ-Watchdog/1.0",
      },
    });
    
    clearTimeout(timeoutId);
    
    result.checks.response_code = response.status;
    result.checks.route_accessibility = response.status === 200;
    
    if (!result.checks.route_accessibility) {
      result.errors.push(`Game route returned ${response.status}`);
      if (response.status === 404) {
        result.recommendations.push("Run preview_launcher patch to add game route");
      } else if (response.status >= 500) {
        result.recommendations.push("Check server logs for internal errors");
      }
    }
    
    // Check cache headers
    let cacheHeadersFound = 0;
    for (const headerName of finalConfig.cacheHeaders) {
      if (response.headers.get(headerName)) {
        cacheHeadersFound++;
      }
    }
    result.checks.cache_headers_present = cacheHeadersFound >= finalConfig.cacheHeaders.length * 0.5;
    
    if (!result.checks.cache_headers_present) {
      result.errors.push("Missing cache-busting headers");
      result.recommendations.push("Apply cache headers via preview_launcher middleware");
    }
    
    // Parse HTML and check for required markers
    if (response.status === 200) {
      const html = await response.text();
      const { JSDOM } = await import("jsdom");
      const dom = new JSDOM(html);
      const document = dom.window.document;
      
      let markersFound = 0;
      for (const marker of finalConfig.requiredMarkers) {
        const element = document.querySelector(`[${marker}]`);
        if (element) {
          markersFound++;
          console.log(`[WATCHDOG] Found required marker: ${marker}=${element.getAttribute(marker)}`);
        } else {
          console.log(`[WATCHDOG] Missing marker: ${marker}`);
        }
      }
      
      result.checks.dom_marker_present = markersFound >= finalConfig.requiredMarkers.length;
      
      if (!result.checks.dom_marker_present) {
        result.errors.push(`Missing DOM markers: ${finalConfig.requiredMarkers.join(", ")}`);
        result.recommendations.push("Ensure game HTML includes data-game-root marker");
      }
      
      // Check build hash consistency
      const buildHashHeader = response.headers.get("X-Build-Hash");
      const buildHashInContent = html.includes("Build Hash:") ? 
        html.match(/Build Hash: ([a-zA-Z0-9]+)/)?.[1] : null;
      
      result.checks.build_hash_match = Boolean(
        buildHashHeader && buildHashInContent && buildHashHeader === buildHashInContent
      );
      
      if (!result.checks.build_hash_match) {
        result.errors.push("Build hash mismatch between header and content");
        result.recommendations.push("Regenerate and sync build hash across launcher components");
      }
    }
    
    // Test other critical routes
    for (const route of finalConfig.routes.filter(r => r !== "/game")) {
      try {
        const routeController = new AbortController();
        const routeTimeoutId = setTimeout(() => routeController.abort(), finalConfig.timeout / 2);
        
        const routeResponse = await fetch(`${finalConfig.baseUrl}${route}`, {
          signal: routeController.signal,
        });
        
        clearTimeout(routeTimeoutId);
        
        if (routeResponse.status !== 200) {
          result.errors.push(`Route ${route} returned ${routeResponse.status}`);
        }
      } catch (error) {
        result.errors.push(`Route ${route} failed: ${error}`);
      }
    }
    
  } catch (error) {
    result.success = false;
    result.errors.push(`Watchdog failed: ${error}`);
    result.recommendations.push("Check if server is running and accessible");
  }
  
  // Overall success determination
  result.success = result.checks.route_accessibility && 
                   result.checks.dom_marker_present && 
                   result.errors.length === 0;
  
  // Generate specific recommendations based on failures
  if (!result.success) {
    if (!result.checks.route_accessibility) {
      result.recommendations.push("Priority: Fix game route accessibility");
    }
    if (!result.checks.cache_headers_present) {
      result.recommendations.push("Apply cache-busting headers to prevent stale UI");
    }
    if (!result.checks.dom_marker_present) {
      result.recommendations.push("Add required DOM markers for UI validation");
    }
  }
  
  return result;
}

export function generateWatchdogReceipt(result: WatchdogResult) {
  return {
    timestamp: result.timestamp,
    operation: "preview_watchdog",
    success: result.success,
    checks_passed: Object.values(result.checks).filter(Boolean).length,
    total_checks: Object.keys(result.checks).length,
    errors: result.errors,
    recommendations: result.recommendations,
    status: result.success ? "healthy" : "anomalies_detected",
    next_action: result.success ? "continue" : "apply_recommendations",
  };
}

// CLI interface for ES modules — only run when invoked directly, not when bundled
const isMainModule = import.meta.url === `file://${process.argv[1]}`
  && (process.argv[1] ?? "").includes("watchdog_preview");
if (isMainModule) {
  (async () => {
    console.log("[WATCHDOG] Starting preview validation...");
    const result = await runPreviewWatchdog();
    
    console.log("\n=== PREVIEW WATCHDOG REPORT ===");
    console.log(`Status: ${result.success ? "✅ HEALTHY" : "❌ ANOMALIES DETECTED"}`);
    console.log(`Timestamp: ${new Date(result.timestamp).toISOString()}`);
    
    console.log("\nChecks:");
    for (const [check, passed] of Object.entries(result.checks)) {
      console.log(`  ${passed ? "✅" : "❌"} ${check}: ${passed}`);
    }
    
    if (result.errors.length > 0) {
      console.log("\nErrors:");
      result.errors.forEach(error => console.log(`  🔥 ${error}`));
    }
    
    if (result.recommendations.length > 0) {
      console.log("\nRecommendations:");
      result.recommendations.forEach(rec => console.log(`  💡 ${rec}`));
    }
    
    process.exit(result.success ? 0 : 1);
  })();
}
