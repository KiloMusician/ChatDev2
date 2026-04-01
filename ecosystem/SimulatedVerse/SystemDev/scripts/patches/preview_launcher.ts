import { Express } from "express";
import path from "path";
import { nanoid } from "nanoid";

// Cache-busting build hash
const BUILD_HASH = nanoid(8);

interface LauncherConfig {
  devRoute: string;
  gameRoute: string;
  fallbackEnabled: boolean;
  cacheHeaders: Record<string, string>;
}

const config: LauncherConfig = {
  devRoute: "/dev",
  gameRoute: "/game", 
  fallbackEnabled: true,
  cacheHeaders: {
    "Cache-Control": "no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
    "X-Build-Hash": BUILD_HASH,
  }
};

export function applyPreviewLauncher(app: Express) {
  // Cache-busting middleware
  app.use((req, res, next) => {
    // Apply no-cache headers to game routes
    if (req.path.startsWith("/game") || req.path.startsWith("/api")) {
      Object.entries(config.cacheHeaders).forEach(([key, value]) => {
        res.setHeader(key, value);
      });
    }
    next();
  });

  // Smart root redirect
  app.get("/", (req, res) => {
    const mode = req.query.mode as string;
    
    if (mode === "game") {
      return res.redirect(config.gameRoute);
    }
    
    // Check if user agent suggests mobile for game default
    const isMobile = /Mobi|Android/i.test(req.headers["user-agent"] || "");
    const hasGameCookie = req.cookies?.["prefer-game"] === "true";
    
    if (hasGameCookie || (isMobile && req.query.auto !== "false")) {
      return res.redirect(`${config.gameRoute}?source=auto`);
    }
    
    res.redirect(config.devRoute);
  });

  // Dev menu route (unchanged)
  app.get(config.devRoute, (req, res) => {
    res.sendFile(path.join(process.cwd(), "dist", "index.html"));
  });

  // Game route with fallback handling
  app.get(config.gameRoute, (req, res) => {
    const gameHtmlPath = path.join(process.cwd(), "dist", "game.html");
    const fallbackPath = path.join(process.cwd(), "PreviewUI", "web", "game-fallback", "index.html");
    
    // Try to serve Godot export or dedicated game HTML
    try {
      res.sendFile(gameHtmlPath, (err) => {
        if (err && config.fallbackEnabled) {
          // Serve ASCII fallback
          res.sendFile(fallbackPath, (fallbackErr) => {
            if (fallbackErr) {
              // Generate minimal game HTML on-the-fly
              res.send(generateFallbackGameHtml());
            }
          });
        } else if (err) {
          res.status(404).send("Game route not found");
        }
      });
    } catch (error) {
      if (config.fallbackEnabled) {
        res.send(generateFallbackGameHtml());
      } else {
        res.status(500).send("Game initialization failed");
      }
    }
  });

  // Cache-busting asset route
  app.get("/assets/game/*", (req, res, next) => {
    // Append build hash to asset URLs
    const originalUrl = req.url;
    if (!originalUrl.includes(`v=${BUILD_HASH}`)) {
      return res.redirect(`${originalUrl}?v=${BUILD_HASH}`);
    }
    next();
  });

  console.log(`[PREVIEW_LAUNCHER] Routes configured:
    Root: / (smart redirect)
    Dev: ${config.devRoute}
    Game: ${config.gameRoute}
    Build Hash: ${BUILD_HASH}
    Cache Busting: enabled
    Fallback: ${config.fallbackEnabled ? "enabled" : "disabled"}`);
}

function generateFallbackGameHtml(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ΞNuSyQ - Colony Interface</title>
  <style>
    body { 
      font-family: monospace; 
      background: #0a0a0a; 
      color: #00ff88; 
      margin: 0; 
      padding: 20px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    .header { 
      text-align: center; 
      border: 1px solid #00ff88; 
      padding: 10px; 
      margin-bottom: 20px;
    }
    .resource-grid { 
      display: grid; 
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
      gap: 15px; 
      margin-bottom: 20px;
    }
    .resource-card { 
      border: 1px solid #555; 
      padding: 15px; 
      background: #111;
    }
    .controls { 
      display: flex; 
      gap: 10px; 
      flex-wrap: wrap; 
      margin-bottom: 20px;
    }
    button { 
      background: #003322; 
      color: #00ff88; 
      border: 1px solid #00ff88; 
      padding: 8px 16px; 
      cursor: pointer; 
      font-family: monospace;
    }
    button:hover { background: #004433; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    .status { 
      border: 1px solid #333; 
      padding: 10px; 
      background: #0a0a0a; 
      font-size: 12px;
      flex-grow: 1;
    }
    .game-marker { display: none; }
  </style>
</head>
<body data-game-root="fallback-colony">
  <div class="header">
    <h1>🌌 ΞNuSyQ Culture-Ship Interface</h1>
    <p>Colony Management System - Tier 1 Survival Loop</p>
  </div>
  
  <div class="resource-grid">
    <div class="resource-card">
      <h3>⚡ Energy</h3>
      <div>Amount: <span id="energy">100</span></div>
      <div>Rate: <span id="energy-rate">+1.0/sec</span></div>
    </div>
    <div class="resource-card">
      <h3>🔧 Materials</h3>
      <div>Amount: <span id="materials">50</span></div>
      <div>Rate: <span id="materials-rate">+0.5/sec</span></div>
    </div>
    <div class="resource-card">
      <h3>👥 Population</h3>
      <div>Count: <span id="population">1</span></div>
      <div>Capacity: <span id="pop-capacity">10</span></div>
    </div>
    <div class="resource-card">
      <h3>🧠 Research</h3>
      <div>Points: <span id="research">0</span></div>
      <div>Rate: <span id="research-rate">+0.1/sec</span></div>
    </div>
  </div>
  
  <div class="controls">
    <button onclick="scout()">🔍 Scout Area</button>
    <button onclick="buildOutpost()">🏗️ Build Outpost</button>
    <button onclick="automate()">⚙️ Automate</button>
    <button onclick="research()">🧪 Research</button>
    <button onclick="returnToDev()">← Return to Dev Menu</button>
  </div>
  
  <div class="status">
    <div>Status: <span id="status">Colony operational</span></div>
    <div>Tier: <span id="tier">1</span></div>
    <div>Time: <span id="time">0</span>s</div>
    <div>Build Hash: ${BUILD_HASH}</div>
    <div id="activity-log">System initialized...</div>
  </div>
  
  <!-- Hidden marker for DOM validation -->
  <div class="game-marker" data-game-state="active" data-build-hash="${BUILD_HASH}"></div>
  
  <script>
    let gameState = {
      energy: 100, materials: 50, population: 1, research: 0,
      time: 0, tier: 1, status: "operational"
    };
    
    let startTime = Date.now();
    
    function updateDisplay() {
      document.getElementById('energy').textContent = Math.floor(gameState.energy);
      document.getElementById('materials').textContent = Math.floor(gameState.materials);
      document.getElementById('population').textContent = gameState.population;
      document.getElementById('research').textContent = Math.floor(gameState.research);
      document.getElementById('time').textContent = Math.floor((Date.now() - startTime) / 1000);
      document.getElementById('tier').textContent = gameState.tier;
      document.getElementById('status').textContent = gameState.status;
    }
    
    function tick() {
      gameState.energy += 1.0;
      gameState.materials += 0.5;
      gameState.research += 0.1;
      
      // Tier progression
      if (gameState.research >= 100 && gameState.tier === 1) {
        gameState.tier = 2;
        log("🎉 Advanced to Tier 2! New systems unlocked.");
      }
      
      updateDisplay();
    }
    
    function log(message) {
      const logEl = document.getElementById('activity-log');
      logEl.innerHTML = message + '<br>' + logEl.innerHTML.split('<br>').slice(0, 5).join('<br>');
    }
    
    function scout() {
      if (gameState.energy >= 10) {
        gameState.energy -= 10;
        gameState.materials += 15;
        log("🔍 Scouting complete. Found 15 materials.");
        updateDisplay();
      } else {
        log("❌ Insufficient energy for scouting.");
      }
    }
    
    function buildOutpost() {
      if (gameState.energy >= 50 && gameState.materials >= 25) {
        gameState.energy -= 50;
        gameState.materials -= 25;
        gameState.population += 1;
        log("🏗️ Outpost built. Population increased.");
        updateDisplay();
      } else {
        log("❌ Insufficient resources for outpost.");
      }
    }
    
    function automate() {
      if (gameState.energy >= 100 && gameState.research >= 25) {
        gameState.energy -= 100;
        gameState.research -= 25;
        log("⚙️ Automation installed. Efficiency improved.");
        updateDisplay();
      } else {
        log("❌ Insufficient resources for automation.");
      }
    }
    
    function research() {
      if (gameState.energy >= 20) {
        gameState.energy -= 20;
        gameState.research += 10;
        log("🧪 Research conducted. Knowledge gained.");
        updateDisplay();
      } else {
        log("❌ Insufficient energy for research.");
      }
    }
    
    function returnToDev() {
      window.location.href = '/dev';
    }
    
    // Game loop
    setInterval(tick, 1000);
    updateDisplay();
    
    // Communication with agent bus (if available)
    if (window.postMessage) {
      setInterval(() => {
        window.postMessage({
          type: 'colony_state',
          data: gameState,
          timestamp: Date.now(),
          source: 'fallback_colony'
        }, '*');
      }, 5000);
    }
    
    log("🌌 Colony interface initialized. Culture-Ship systems online.");
  </script>
</body>
</html>`;
}

// Receipt generation
export function generateLauncherReceipt() {
  return {
    timestamp: Date.now(),
    operation: "preview_launcher_patch",
    build_hash: BUILD_HASH,
    routes: {
      root: "/",
      dev: config.devRoute,
      game: config.gameRoute
    },
    cache_busting: true,
    fallback_enabled: config.fallbackEnabled,
    headers_applied: Object.keys(config.cacheHeaders),
    dom_marker: "data-game-root",
    status: "operational"
  };
}