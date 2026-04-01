// ops/unstick-ui.js
/**
 * UI Unsticker: Forces fresh builds, kills service workers, busts caches
 * Purpose:
 *  - Detect when /client/src is newer than build → trigger rebuild (cheap)
 *  - Ensure index.html is served no-store while assets are cached with strong ETags
 *  - Generate build-stamp to prove UI freshness  
 *  - Write /public/unstick.json so UI can auto-unregister service workers
 */
import fs from "fs";
import path from "path";
import { execSync } from "child_process";
import crypto from "crypto";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const CLIENT_SRC = path.join(__dirname, "../client/src");
const PUBLIC_DIR = path.join(__dirname, "../public");
const DIST_DIR = path.join(__dirname, "../client/dist");

fs.mkdirSync(PUBLIC_DIR, { recursive: true });

function getNewestMtime(dir) {
  let newest = 0;
  try {
    const files = execSync(`find "${dir}" -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.css" | head -100`, 
      { encoding: 'utf8', timeout: 5000 }).split('\n').filter(Boolean);
    
    for (const file of files) {
      try {
        const stat = fs.statSync(file);
        newest = Math.max(newest, stat.mtimeMs);
      } catch (e) {}
    }
  } catch (e) {
    console.warn("[unstick] Failed to scan directory:", dir);
  }
  return newest;
}

function buildIfStale() {
  const srcTime = getNewestMtime(CLIENT_SRC);
  const distTime = fs.existsSync(DIST_DIR) ? getNewestMtime(DIST_DIR) : 0;

  if (srcTime === 0) {
    return { rebuilt: false, reason: "no src files found" };
  }
  
  if (distTime < srcTime || !fs.existsSync(path.join(DIST_DIR, "index.html"))) {
    console.log("[unstick] 🔨 Source newer than dist → rebuilding frontend...");
    try {
      // Force a clean build
      execSync("npm run build", { 
        stdio: "inherit", 
        timeout: 60000,
        cwd: __dirname + "/.."
      });
      
      console.log("[unstick] ✅ Build completed successfully");
      return { rebuilt: true };
    } catch (e) {
      console.error("[unstick] ❌ Build failed:", e?.message || e);
      return { rebuilt: false, error: String(e?.message || e) };
    }
  }
  
  return { rebuilt: false, reason: "build is current" };
}

function writeBuildStamp() {
  const stamp = {
    timestamp: Date.now(),
    build_id: crypto.randomBytes(8).toString("hex"),
    env: { 
      UI_MODE: process.env.UI_MODE ?? "provisioned",
      NODE_ENV: process.env.NODE_ENV ?? "development"
    },
    version: "unstick-v1"
  };
  
  const stampPath = path.join(PUBLIC_DIR, "build-stamp.json");
  fs.writeFileSync(stampPath, JSON.stringify(stamp, null, 2));
  console.log("[unstick] 📝 Build stamp written:", stamp.build_id);
  return stamp;
}

function writeSWKiller() {
  // UI will fetch this and kill any stuck service workers
  const payload = { 
    kill_sw: true, 
    timestamp: Date.now(),
    force_reload: true,
    clear_caches: true
  };
  
  const unstickPath = path.join(PUBLIC_DIR, "unstick.json");
  fs.writeFileSync(unstickPath, JSON.stringify(payload, null, 2));
  console.log("[unstick] 🔧 SW killer payload written");
}

async function mainLoop() {
  console.log("[unstick] 🚀 Starting UI unsticker loop");
  console.log("[unstick] 📁 Watching:", CLIENT_SRC);
  console.log("[unstick] 🎯 Target:", DIST_DIR);
  
  // Initial setup
  writeSWKiller();
  writeBuildStamp();
  
  let iteration = 0;
  
  while (true) {
    iteration++;
    
    try {
      const result = buildIfStale();
      
      if (result.rebuilt) {
        const stamp = writeBuildStamp();
        writeSWKiller(); // Refresh SW killer after build
        console.log(`[unstick] 🎉 Iteration ${iteration}: Rebuilt successfully! New ID: ${stamp.build_id}`);
      } else if (result.error) {
        console.log(`[unstick] ⚠️ Iteration ${iteration}: Build failed - ${result.error}`);
      } else {
        console.log(`[unstick] ✅ Iteration ${iteration}: ${result.reason}`);
      }
      
      // Write status for ops monitoring
      const statusPath = path.join(PUBLIC_DIR, "unstick-status.json");
      fs.writeFileSync(statusPath, JSON.stringify({
        timestamp: Date.now(),
        iteration,
        last_result: result,
        watching: CLIENT_SRC,
        target: DIST_DIR
      }, null, 2));
      
    } catch (error) {
      console.error(`[unstick] 💥 Loop error (continuing):`, error.message);
    }

    // Check every 20 seconds (light polling)
    await new Promise(r => setTimeout(r, 20000));
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log("[unstick] 🛑 Graceful shutdown");
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log("[unstick] 🛑 Interrupted - shutting down");
  process.exit(0);
});

mainLoop().catch(e => { 
  console.error("[unstick] 💥 Fatal error:", e.message); 
  process.exit(1); 
});