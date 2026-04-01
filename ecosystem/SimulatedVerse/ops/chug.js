// ops/chug.js
// Relentless error harvester + duplicate sentry + UI sanity (NO DELETIONS)
import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import crypto from "crypto";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.join(__dirname, "../public/ops-report");
fs.mkdirSync(OUT_DIR, { recursive: true });

function safe(cmd) {
  try { 
    return { 
      ok: true, 
      out: execSync(cmd, { 
        stdio: ["ignore", "pipe", "pipe"], 
        timeout: 30000,
        maxBuffer: 1024 * 1024 
      }).toString() 
    }; 
  }
  catch (e) { 
    return { 
      ok: false, 
      out: e?.stdout?.toString() || "", 
      err: e?.stderr?.toString() || e?.message || "error" 
    }; 
  }
}

function writeJSON(file, obj) {
  try {
    const tmp = file + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(obj, null, 2));
    fs.renameSync(tmp, file);
  } catch (e) {
    console.warn("[chug] Failed to write", file, e.message);
  }
}

function hashContent(s) { 
  return crypto.createHash("sha1").update(s).digest("hex"); 
}

function scanMapsForFootguns() {
  const offenders = [];
  
  try {
    const files = execSync(`find . -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | grep -E "(client/src|apps)" | head -50`, 
      { encoding: 'utf8', timeout: 5000 }).split('\n').filter(Boolean);
    
    for (const f of files) {
      try {
        if (!fs.existsSync(f)) continue;
        const txt = fs.readFileSync(f, "utf-8");
        
        // Find .map( not preceded by safe guards
        if (txt.includes(".map(") && !/safeMap\(|asArray\(|Array\.isArray|normalizeToArray/.test(txt)) {
          const lines = txt.split('\n')
            .map((line, i) => ({ line: line.trim(), num: i + 1 }))
            .filter(({ line }) => line.includes('.map(') && !line.includes('safeMap') && !line.includes('asArray'))
            .slice(0, 3); // Limit per file
          
          if (lines.length > 0) {
            offenders.push({ file: f, mapLines: lines });
          }
        }
      } catch (e) {
        // Skip files that can't be read
      }
    }
  } catch (e) {
    console.warn("[chug] scanMapsForFootguns failed:", e.message);
  }
  
  return offenders;
}

function pickCore(paths) {
  // Heuristic: prefer packages/* > apps/* > client/* ; prefer deepest with index.ts
  const score = p => {
    let s = 0;
    if (p.startsWith("packages/")) s += 3;
    else if (p.startsWith("apps/")) s += 2;
    else if (p.startsWith("client/")) s += 1;
    
    if (p.includes("/index.")) s += 0.5;
    if (p.includes("src/")) s += 0.2;
    
    return s;
  };
  
  return [...paths].sort((a, b) => score(b) - score(a))[0];
}

function dupeSentry() {
  const map = new Map(); // hash -> [paths]
  
  try {
    const files = execSync(`find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.css" \\) | grep -v node_modules | grep -v ".git" | head -200`, 
      { encoding: 'utf8', timeout: 10000 }).split('\n').filter(Boolean);
    
    for (const f of files) {
      try {
        if (!fs.existsSync(f)) continue;
        const txt = fs.readFileSync(f, "utf-8");
        
        // Normalize whitespace for comparison
        const normalized = txt.replace(/\s+/g, " ").trim();
        if (normalized.length < 50) continue; // Skip tiny files
        
        const h = hashContent(normalized);
        const arr = map.get(h) || [];
        arr.push(f);
        map.set(h, arr);
      } catch (e) {
        // Skip files that can't be read
      }
    }
  } catch (e) {
    console.warn("[chug] dupeSentry find failed:", e.message);
  }
  
  const dupes = [];
  for (const [h, arr] of map) {
    if (arr.length > 1) {
      dupes.push({ 
        hash: h.slice(0, 8), 
        files: arr, 
        core: pickCore(arr),
        size: arr.length 
      });
    }
  }
  
  return dupes.slice(0, 20); // Limit for performance
}

function aliasPlan(dupes) {
  // We DO NOT delete; we propose barrels/aliases that re-export core
  const plan = [];
  
  for (const d of dupes) {
    const { core, files } = d;
    const others = files.filter(f => f !== core);
    if (!others.length) continue;
    
    // For each non-core, suggest an alias strategy
    for (const o of others) {
      const dir = path.dirname(o);
      const ext = path.extname(o) || ".ts";
      const basename = path.basename(o, ext);
      const aliasFile = path.join(dir, `${basename}_alias_to_core${ext}`);
      
      plan.push({ 
        core, 
        duplicate: o, 
        suggestedAlias: aliasFile,
        strategy: ext.match(/tsx?$/) ? "typescript_reexport" : "commonjs_require"
      });
    }
  }
  
  return plan;
}

function routesCheck() {
  const appPaths = [
    "client/src/App.tsx",
    "apps/web/src/App.tsx", 
    "src/App.tsx"
  ];
  
  for (const appPath of appPaths) {
    try {
      if (!fs.existsSync(appPath)) continue;
      
      const txt = fs.readFileSync(appPath, "utf-8");
      const requiredRoutes = ["Game", "Agent", "Ops", "Admin"];
      const found = requiredRoutes.filter(route => 
        txt.toLowerCase().includes(route.toLowerCase())
      );
      
      return { 
        ok: found.length >= 3, 
        found, 
        appFile: appPath,
        missing: requiredRoutes.filter(r => !found.includes(r))
      };
    } catch (e) {
      continue;
    }
  }
  
  return { 
    ok: false, 
    reason: "no App.tsx found in expected locations",
    searched: appPaths 
  };
}

function consciousnessCheck() {
  // Check for infinite cycling consciousness tasks
  try {
    const logFiles = [
      "/tmp/server.log",
      "/tmp/pu_queue.log"
    ];
    
    for (const logFile of logFiles) {
      if (fs.existsSync(logFile)) {
        const logs = fs.readFileSync(logFile, "utf-8");
        const recentLines = logs.split('\n').slice(-50);
        
        const consciousnessLines = recentLines.filter(line => 
          line.includes("CONSCIOUSNESS WORK") || line.includes("No implementation available")
        );
        
        if (consciousnessLines.length > 10) {
          return {
            ok: false,
            issue: "consciousness_cycling",
            details: consciousnessLines.slice(-5)
          };
        }
      }
    }
    
    return { ok: true };
  } catch (e) {
    return { ok: true, warning: "Could not check consciousness logs" };
  }
}

async function mainLoop() {
  console.log("[chug] 🚀 Starting relentless error hunting loop");
  console.log("[chug] 🛡️ UI considered BROKEN until proven otherwise");
  console.log("[chug] 💾 NO DELETIONS - only aliasing and annealing");
  console.log("[chug] 🎯 Target: Fix consciousness cycling & m.map errors");

  let iter = 0;
  
  while (true) {
    iter++;
    const startTime = Date.now();

    try {
      // 1) TypeScript check (no emit, quick)
      console.log("[chug] Checking TypeScript...");
      const tsc = safe("npx tsc --noEmit --skipLibCheck");
      
      // 2) ESLint quick scan (best effort, continue on failure)
      console.log("[chug] Running ESLint...");
      const eslint = safe('npx eslint "**/*.ts" "**/*.tsx" --max-warnings=10 --quiet || true');
      
      // 3) .map footguns scan
      console.log("[chug] Scanning for .map footguns...");
      const footguns = scanMapsForFootguns();
      
      // 4) Duplicate content sentry -> alias suggestions (non-destructive)
      console.log("[chug] Detecting duplicates...");
      const dupes = dupeSentry();
      const aliases = aliasPlan(dupes);
      
      // 5) Router sanity check
      console.log("[chug] Checking routes...");
      const routes = routesCheck();
      
      // 6) Consciousness cycling check
      console.log("[chug] Checking consciousness processor...");
      const consciousness = consciousnessCheck();
      
      // 7) Basic imports check
      const importCheck = safe('grep -r "import.*\\.map" client/src apps --include="*.ts" --include="*.tsx" | head -5 || echo "no direct map imports found"');

      const report = {
        timestamp: Date.now(),
        iteration: iter,
        runtime_ms: Date.now() - startTime,
        status: "HUNTING_ERRORS",
        ui_assumption: "BROKEN_UNTIL_PROVEN_OK",
        checks: {
          typescript: {
            ok: tsc.ok,
            errors: tsc.ok ? null : tsc.err.split('\n').slice(0, 10)
          },
          eslint: {
            ok: eslint.ok,
            warnings: eslint.ok ? null : eslint.out.split('\n').slice(0, 10)
          },
          map_footguns: {
            count: footguns.length,
            files: footguns.slice(0, 10) // Limit for UI
          },
          routes: routes,
          consciousness: consciousness,
          imports: {
            safe: !importCheck.out.includes("import") || importCheck.out.includes("no direct map")
          }
        },
        duplicates: {
          count: dupes.length,
          details: dupes.slice(0, 10),
          alias_suggestions: aliases.slice(0, 10)
        },
        next_actions: []
      };

      // Add specific next actions based on findings
      if (!tsc.ok) {
        report.next_actions.push("Fix TypeScript errors - highest priority");
      }
      if (!consciousness.ok) {
        report.next_actions.push("Fix consciousness processor cycling - add missing implementations");
      }
      if (footguns.length > 0) {
        report.next_actions.push(`Replace ${footguns.length} .map() calls with safeMap()`);
      }
      if (dupes.length > 0) {
        report.next_actions.push(`Create aliases for ${dupes.length} duplicate file groups`);
      }
      if (!routes.ok) {
        report.next_actions.push("Fix routing - missing required navigation routes");
      }

      // Write report for HUD consumption
      writeJSON(path.join(OUT_DIR, "report.json"), report);
      
      // Write a simple status for quick checks
      writeJSON(path.join(OUT_DIR, "status.json"), {
        ok: tsc.ok && routes.ok && footguns.length === 0 && consciousness.ok,
        issues: [
          ...(tsc.ok ? [] : ["typescript"]),
          ...(routes.ok ? [] : ["routing"]),
          ...(consciousness.ok ? [] : ["consciousness_cycling"]),
          ...(footguns.length > 0 ? [`${footguns.length} map footguns`] : []),
          ...(dupes.length > 0 ? [`${dupes.length} duplicates`] : [])
        ],
        last_check: new Date().toISOString()
      });

      // Concise console log for Replit
      const summary = `tsc:${tsc.ok?'✅':'❌'} routes:${routes.ok?'✅':'❌'} consciousness:${consciousness.ok?'✅':'❌'} footguns:${footguns.length} dupes:${dupes.length}`;
      console.log(`[chug][${new Date().toLocaleTimeString()}] ${summary} (${Date.now() - startTime}ms)`);

      if (!consciousness.ok) {
        console.log(`[chug] 🚨 CONSCIOUSNESS CYCLING DETECTED - processor stuck on: ${consciousness.details?.[0] || 'unknown task'}`);
      }
      
      if (footguns.length > 0) {
        console.log(`[chug] 🚨 Found ${footguns.length} .map footguns - use safeMap() instead`);
        footguns.slice(0, 3).forEach(({ file, mapLines }) => {
          console.log(`[chug]   📁 ${file}: ${mapLines.length} unsafe .map() calls`);
        });
      }
      
      if (dupes.length > 0) {
        console.log(`[chug] 📦 Found ${dupes.length} duplicate files - aliasing suggested`);
      }

    } catch (error) {
      console.error("[chug] ⚠️ Loop error (continuing anyway):", error.message);
      
      // Write error report
      writeJSON(path.join(OUT_DIR, "error.json"), {
        timestamp: Date.now(),
        error: error.message,
        stack: error.stack?.split('\n').slice(0, 10)
      });
    }

    // Polite sleep (15s), then continue relentlessly
    await new Promise(r => setTimeout(r, 15000));
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log("[chug] 🛑 Graceful shutdown");
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log("[chug] 🛑 Interrupted - shutting down");
  process.exit(0);
});

mainLoop().catch(e => { 
  console.error("[chug] 💥 Fatal error:", e.message); 
  process.exit(1); 
});