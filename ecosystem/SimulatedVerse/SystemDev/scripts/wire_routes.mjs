import fs from "fs";
import path from "path";

const candidates = [
  { file: "server/index.ts" },
  { file: "src/server.js" },
  { file: "server.js" }
];

const processTrackerRoutes = `
// **PROCESS TRACKING ROUTES** - Real-time OmniTag monitoring
import { Router } from "express";
const processRouter = Router();

processRouter.get("/metrics", async (req, res) => {
  try {
    const { exec } = await import("child_process");
    exec("python3 -c \\"import sys; sys.path.append('.'); from src.process_tracker import tracker; import json; print(json.dumps(tracker.get_performance_metrics()))\\"", 
         (error, stdout, stderr) => {
      if (error) {
        res.status(500).json({ error: "Failed to get metrics", details: error.message });
      } else {
        const metrics = JSON.parse(stdout.trim());
        res.json({ ok: true, timestamp: Date.now(), ...metrics });
      }
    });
  } catch (error) {
    res.status(500).json({ error: "Process tracking unavailable", details: error.message });
  }
});

processRouter.get("/recent-events/:limit?", async (req, res) => {
  try {
    const limit = req.params.limit || 10;
    const { exec } = await import("child_process");
    exec(\`python3 -c "import sys; sys.path.append('.'); from src.process_tracker import tracker; import json; print(json.dumps(tracker.get_recent_events(\${limit})))"\`, 
         (error, stdout, stderr) => {
      if (error) {
        res.status(500).json({ error: "Failed to get events", details: error.message });
      } else {
        const events = JSON.parse(stdout.trim());
        res.json({ ok: true, events, timestamp: Date.now() });
      }
    });
  } catch (error) {
    res.status(500).json({ error: "Event tracking unavailable", details: error.message });
  }
});

processRouter.post("/track", async (req, res) => {
  try {
    const { event_type, metadata = {} } = req.body;
    const { exec } = await import("child_process");
    const trackingData = JSON.stringify({ event_type, metadata });
    exec(\`python3 -c "import sys; sys.path.append('.'); from src.process_tracker import tracker; tracker.track_agent_execution('api', '\${event_type}', **\${trackingData})"\`,
         (error, stdout, stderr) => {
      if (error) {
        res.status(500).json({ error: "Failed to track event", details: error.message });
      } else {
        res.json({ ok: true, tracked: event_type, timestamp: Date.now() });
      }
    });
  } catch (error) {
    res.status(500).json({ error: "Event tracking failed", details: error.message });
  }
});

app.use("/api/process", processRouter);
`;

function ensureFile(fp){ if (!fs.existsSync(fp)) fs.writeFileSync(fp, "", "utf8"); }

function inject(serverPath){
  let code = fs.readFileSync(serverPath, "utf8");
  
  // Add process tracking routes if not already present
  if (!code.includes("/api/process")) {
    // Find a good place to insert (after other route definitions)
    const insertPoint = code.lastIndexOf("app.use(") + code.substring(code.lastIndexOf("app.use(")).indexOf(";") + 1;
    if (insertPoint > 0) {
      code = code.substring(0, insertPoint) + "\n" + processTrackerRoutes + "\n" + code.substring(insertPoint);
    } else {
      // Fallback: append at end
      code += "\n" + processTrackerRoutes;
    }
  }

  // Add performance monitoring if not present
  if (!code.includes("/perf")) {
    const perfRoute = `
app.get("/api/perf", (req, res) => {
  const memUsage = process.memoryUsage();
  const uptime = process.uptime();
  res.json({
    ok: true,
    timestamp: Date.now(),
    uptime_seconds: uptime,
    memory: {
      rss: memUsage.rss,
      heapUsed: memUsage.heapUsed,
      heapTotal: memUsage.heapTotal,
      external: memUsage.external
    },
    tick: Math.floor(uptime)
  });
});
`;
    code += perfRoute;
  }

  fs.writeFileSync(serverPath, code, "utf8");
  console.log("✓ Wired process tracking routes:", serverPath);
}

for (const c of candidates){
  if (fs.existsSync(c.file)) inject(c.file);
}

console.log("✓ Route wiring complete");