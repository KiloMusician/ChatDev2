// ops/replit_runner.ts
import { setTimeout as wait } from "node:timers/promises";
const BASE = process.env.BASE || "http://127.0.0.1:5000";
const ADMIN_TOKEN = process.env.ADMIN_TOKEN!;
const HEADERS = { "Authorization": `Bearer ${ADMIN_TOKEN}`, "Content-Type":"application/json" };

async function lease() {
  const r = await fetch(`${BASE}/api/agent/lease?runner=replit&n=5`, { headers: HEADERS });
  return r.ok ? r.json() : { items: [] };
}
async function ack(id: string, status: "ok"|"fail", logs: string, error?: string) {
  await fetch(`${BASE}/api/agent/ack`, {
    method: "POST", headers: HEADERS,
    body: JSON.stringify({ id, status, logs, error })
  });
}

async function main() {
  if (!ADMIN_TOKEN) throw new Error("ADMIN_TOKEN missing");
  console.log("[REPLIT-RUNNER] Starting watchdog for autonomous queue execution...");
  
  for (;;) {
    try {
      const { items = [] } = await lease();
      if (items.length > 0) {
        console.log(`[REPLIT-RUNNER] Leased ${items.length} PUs for execution`);
      }
      
      for (const pu of items) {
        console.log(`[REPLIT-RUNNER] Executing PU: ${pu.title || pu.id}`);
        let logs = "";
        try {
          // Minimal executor: file writes + shell commands
          if (pu.files?.length) {
            const fs = await import("node:fs/promises");
            const path = await import("node:path");
            for (const f of pu.files) {
              const dir = path.dirname(f.path);
              await fs.mkdir(dir, { recursive: true });
              await fs.writeFile(f.path, f.contents ?? f.content ?? "");
              logs += `wrote:${f.path}\n`;
            }
          }
          if (pu.commands?.length) {
            const { spawn } = await import("node:child_process");
            for (const c of pu.commands) {
              const p = spawn("bash", ["-lc", c], { stdio: "pipe" });
              const out = await new Promise<string>((resolve) => {
                let data = "";
                p.stdout.on("data", (chunk) => data += chunk);
                p.stdout.on("end", () => resolve(data));
              });
              const err = await new Promise<string>((resolve) => {
                let data = "";
                p.stderr.on("data", (chunk) => data += chunk);
                p.stderr.on("end", () => resolve(data));
              });
              logs += `$ ${c}\n${out}${err}`;
            }
          }
          await ack(pu.id, "ok", logs);
          console.log(`[REPLIT-RUNNER] ✅ Completed: ${pu.title || pu.id}`);
        } catch (e:any) {
          await ack(pu.id, "fail", logs, String(e?.message||e));
          console.log(`[REPLIT-RUNNER] ❌ Failed: ${pu.title || pu.id} - ${e?.message}`);
        }
      }
      await wait(items.length ? 1000 : 5000);
    } catch (e) {
      console.log(`[REPLIT-RUNNER] Error in main loop: ${e}`);
      await wait(5000);
    }
  }
}
main();