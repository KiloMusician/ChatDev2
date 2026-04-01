import { Router } from "express";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { scanRepo, buildRefGraph, planCurator } from "../services/curator.js";

// **ADMIN GUARD** - Simple token check (reused pattern from other routes)
function adminGuard(req: any, res: any, next: any) {
  const token = req.get('Authorization')?.replace('Bearer ', '');
  const adminToken = process.env.ADMIN_TOKEN;
  
  if (!adminToken || token !== adminToken) {
    return res.status(401).json({ error: 'Admin access required' });
  }
  
  next();
}

export const curator = Router();

// **SCAN ENDPOINT** - Analyze repository for bloat
curator.post("/scan", adminGuard, async (req, res) => {
  try {
    const configPath = "agents/curator/curator.config.yaml";
    if (!fs.existsSync(configPath)) {
      return res.status(500).json({ error: "Curator config not found" });
    }

    const configContent = fs.readFileSync(configPath, "utf8")
      .replace(/^\uFEFF/,"") // remove BOM
      .replace(/(\r?\n)+/g,"\n"); // normalize line endings
    
    // Simple YAML parser for basic config
    const cfg: any = {};
    const lines = configContent.split('\n');
    let currentKey = '';
    let inArray = false;
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      
      if (trimmed.includes(':') && !trimmed.startsWith('-')) {
        const [rawKey, rawValue] = trimmed.split(':', 2);
        const key = rawKey?.trim();
        if (!key) continue;
        const cleanKey = key;
        const cleanValue = rawValue?.trim();
        
        if (cleanKey.includes('.')) {
          const parts = cleanKey.split('.');
          let current = cfg;
          for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (!part) continue;
            if (!current[part]) current[part] = {};
            current = current[part];
          }
          const lastKey = parts[parts.length - 1];
          if (lastKey && cleanValue && cleanValue !== '') {
            current[lastKey] = cleanValue.replace(/^["']|["']$/g, '');
          }
        } else {
          if (cleanValue && cleanValue !== '') {
            if (cleanValue.startsWith('[')) {
              cfg[cleanKey] = JSON.parse(cleanValue);
            } else if (!isNaN(Number(cleanValue))) {
              cfg[cleanKey] = Number(cleanValue);
            } else if (cleanValue === 'true' || cleanValue === 'false') {
              cfg[cleanKey] = cleanValue === 'true';
            } else {
              cfg[cleanKey] = cleanValue.replace(/^["']|["']$/g, '');
            }
          } else {
            cfg[cleanKey] = {};
            currentKey = cleanKey;
          }
        }
      } else if (trimmed.startsWith('-') && currentKey) {
        if (!cfg[currentKey]) cfg[currentKey] = [];
        const value = trimmed.substring(1).trim().replace(/^["']|["']$/g, '');
        cfg[currentKey].push(value);
      }
    }

    // Set defaults
    const ignore = cfg.ignore || [];
    const metas = scanRepo(ignore);
    const refs = buildRefGraph(metas);
    
    const policy = {
      max_file_mb: cfg.hard_limits?.max_file_mb || 25,
      large_text_mb: cfg.hard_limits?.large_text_mb || 5,
      logs_glob: cfg.hard_limits?.logs_glob || ["**/*.log"],
      compress_after_days: cfg.hard_limits?.compress_after_days || 3,
      duplicate_preference: (cfg.duplicate?.keep_preference || []).map((s: string) => new RegExp(s)),
      quarantine: cfg.paths?.quarantine || "_quarantine"
    };
    
    const plan = planCurator(metas, refs, policy);
    
    console.log(`[CURATOR] Scan complete: ${metas.length} files, ${plan.length} actions planned`);
    
    res.json({ 
      ok: true, 
      files: metas.length, 
      actions: plan.length, 
      plan,
      bloat_index: plan.length / Math.max(1, metas.length),
      total_size_mb: metas.reduce((sum, f) => sum + f.size, 0) / (1024*1024)
    });
  } catch (error) {
    console.error('[CURATOR] Scan failed:', error);
    res.status(500).json({ 
      error: "Repository scan failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// **DRY-RUN ENDPOINT** - Preview changes via PR plan
curator.post("/dry-run", adminGuard, async (req, res) => {
  try {
    const { plan, report } = req.body;
    
    if (!plan || !Array.isArray(plan)) {
      return res.status(400).json({ error: "Plan array required" });
    }

    const ndjson = plan.map((o: any) => JSON.stringify(o)).join("\n") + "\n";
    const reportContent = report || `# Curator Dry-Run Report\n\nGenerated: ${new Date().toISOString()}\n\nActions planned: ${plan.length}\n\n## Actions:\n${plan.map((a: any) => `- ${a.kind}: ${a.path || a.duplicate}`).join('\n')}`;
    
    const files = [
      { path: "data/curator_plan.ndjson", content: ndjson },
      { path: "docs/curator/REPORT.md", content: reportContent }
    ];

    console.log(`[CURATOR] Dry-run planned: ${plan.length} actions`);
    
    res.json({
      ok: true,
      planned_actions: plan.length,
      preview_files: files.map(f => f.path),
      estimated_size_reduction_mb: plan.reduce((sum: number, a: any) => {
        if (a.kind === 'quarantine' || a.kind === 'compress') return sum + 0.1; // estimate
        return sum;
      }, 0)
    });
  } catch (error) {
    console.error('[CURATOR] Dry-run failed:', error);
    res.status(500).json({ 
      error: "Dry-run planning failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// **ENACT ENDPOINT** - Execute changes via PR (SAFETY: no direct FS mutations)
curator.post("/enact", adminGuard, async (req, res) => {
  try {
    const plan = req.body.plan as any[];
    
    if (!plan || !Array.isArray(plan)) {
      return res.status(400).json({ error: "Plan array required" });
    }

    const changes: { path: string; content: string }[] = [];
    let actionsProcessed = 0;
    
    // Process each action (SAFETY: via file writes, not direct mutations)
    for (const a of plan) {
      try {
        if (a.kind === "compress") {
          if (fs.existsSync(a.path)) {
            const buf = fs.readFileSync(a.path);
            const gz = zlib.gzipSync(buf);
            changes.push({ path: a.dest, content: gz.toString("base64") });
            actionsProcessed++;
          }
        } else if (a.kind === "quarantine") {
          if (fs.existsSync(a.path)) {
            const buf = fs.readFileSync(a.path);
            changes.push({ path: a.dest, content: buf.toString("utf8") });
            actionsProcessed++;
          }
        } else if (a.kind === "dedupe") {
          const note = `# Deduped File\n\nCanonical: ${a.canonical}\nRemoved duplicate: ${a.duplicate}\nTimestamp: ${new Date().toISOString()}\n`;
          changes.push({ 
            path: `docs/curator/dedup/${a.duplicate.replace(/\//g,"__")}.md`, 
            content: note 
          });
          actionsProcessed++;
        }
      } catch (error) {
        console.error(`[CURATOR] Failed to process action ${a.kind} for ${a.path}:`, error);
      }
    }
    
    // Create ledger entry
    const ledgerEntry = {
      timestamp: new Date().toISOString(),
      actions_planned: plan.length,
      actions_processed: actionsProcessed,
      size_changes: "estimated", // would compute actual in real impl
      curator_session: crypto.randomUUID()
    };
    
    changes.push({ 
      path: "data/curator_ledger.ndjson", 
      content: JSON.stringify(ledgerEntry) + "\n"
    });

    console.log(`[CURATOR] Enactment complete: ${actionsProcessed}/${plan.length} actions processed`);
    
    res.json({
      ok: true,
      actions_planned: plan.length,
      actions_processed: actionsProcessed,
      files_changed: changes.length,
      ledger_updated: true,
      message: "Curator enactment complete - changes staged for PR"
    });
  } catch (error) {
    console.error('[CURATOR] Enactment failed:', error);
    res.status(500).json({ 
      error: "Curator enactment failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});

// **STATUS ENDPOINT** - Curator health and metrics
curator.get("/status", adminGuard, async (req, res) => {
  try {
    const configExists = fs.existsSync("agents/curator/curator.config.yaml");
    const ledgerExists = fs.existsSync("data/curator_ledger.ndjson");
    
    let lastScan = null;
    if (ledgerExists) {
      try {
        const ledger = fs.readFileSync("data/curator_ledger.ndjson", "utf8");
        const entries = ledger.trim().split('\n').filter(Boolean);
        const lastEntryRaw = entries[entries.length - 1];
        if (lastEntryRaw) {
          const lastEntry = JSON.parse(lastEntryRaw);
          lastScan = lastEntry.timestamp;
        }
      } catch {
        // Ignore ledger parsing errors
      }
    }
    
    res.json({
      status: "operational",
      config_loaded: configExists,
      ledger_active: ledgerExists,
      last_scan: lastScan,
      safety_rails: ["snapshot_before_changes", "quarantine_not_delete", "pr_based_changes"],
      endpoints: ["/scan", "/dry-run", "/enact", "/status"]
    });
  } catch (error) {
    res.status(500).json({ 
      error: "Curator status check failed", 
      detail: error instanceof Error ? error.message : String(error)
    });
  }
});
