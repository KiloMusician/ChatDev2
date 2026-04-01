#!/usr/bin/env tsx
import { spawn, ChildProcess } from "node:child_process";
import { setTimeout as wait } from "node:timers/promises";

const API = process.env.OLLAMA_HOST || "http://127.0.0.1:11434";
let child: ChildProcess | null = null;

async function healthy(): Promise<boolean> {
  try {
    const response = await fetch(`${API}/api/version`, {
      method: "GET",
      signal: AbortSignal.timeout(4000)
    });
    return response.ok;
  } catch {
    return false;
  }
}

async function start() {
  if (await healthy()) {
    console.log("[ollama] already healthy");
    return;
  }
  console.log("[ollama] starting daemon…");
  child = spawn("ollama", ["serve"], { 
    stdio: "inherit", 
    env: process.env 
  });
  child.on("exit", (code, sig) => {
    console.error(`[ollama] exited code=${code} sig=${sig}`);
  });
  
  // wait for readiness
  for (let i = 0; i < 30; i++) {
    if (await healthy()) {
      console.log("[ollama] healthy ✅");
      return;
    }
    await wait(1000);
  }
  console.error("[ollama] failed to become healthy in time");
}

async function loop() {
  let backoff = 1000;
  while (true) {
    const ok = await healthy();
    if (!ok) {
      console.error("[ollama] unhealthy, restarting…");
      try {
        child?.kill("SIGTERM");
      } catch {}
      await start();
      backoff = 1000;
    } else {
      backoff = Math.min(backoff + 500, 5000);
    }
    await wait(backoff);
  }
}

start().then(loop);