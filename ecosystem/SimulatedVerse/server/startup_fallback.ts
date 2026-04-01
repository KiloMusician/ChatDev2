import { spawn, type ChildProcess } from "node:child_process";
import http from "node:http";

const HOST = process.env.SIMULATEDVERSE_HOST || "127.0.0.1";
const PORT = Number(process.env.SIMULATEDVERSE_PORT || process.env.PORT || 5002);
const SHADOW_FULL_PORT = Number(process.env.SIMULATEDVERSE_SHADOW_FULL_PORT || PORT + 1);
const STARTUP_TIMEOUT_MS = Number(
  process.env.SIMULATEDVERSE_STARTUP_TIMEOUT_MS || process.env.SIMULATEDVERSE_FULL_STARTUP_TIMEOUT_MS || 90_000,
);
const FULL_STARTUP_TIMEOUT_MS = STARTUP_TIMEOUT_MS;
const DEGRADED_STARTUP_TIMEOUT_MS = Number(process.env.SIMULATEDVERSE_DEGRADED_STARTUP_TIMEOUT_MS || 40_000);
const BACKGROUND_FULL_RETRY_INTERVAL_MS = Number(
  process.env.SIMULATEDVERSE_BACKGROUND_FULL_RETRY_INTERVAL_MS || 60_000,
);
const BACKGROUND_FULL_STARTUP_TIMEOUT_MS = Number(
  process.env.SIMULATEDVERSE_BACKGROUND_FULL_STARTUP_TIMEOUT_MS || FULL_STARTUP_TIMEOUT_MS * 2,
);

function healthUrlsForPort(port: number): string[] {
  return [
    `http://${HOST}:${port}/api/health`,
    `http://${HOST}:${port}/healthz`,
    `http://${HOST}:${port}/readyz`,
  ];
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function probe(url: string, timeoutMs = 3000): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: timeoutMs }, (res) => {
      res.resume();
      resolve((res.statusCode || 500) < 500);
    });
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
    req.on("error", () => resolve(false));
  });
}

function spawnScript(script: "dev:full" | "dev:degraded", port = PORT): ChildProcess {
  const entrypoint = script === "dev:full" ? "server/index.ts" : "server/minimal_server.ts";
  const child = spawn(process.execPath, ["--env-file=.env", "--import", "tsx/esm", entrypoint], {
    stdio: "inherit",
    env: {
      ...process.env,
      PORT: String(port),
      SIMULATEDVERSE_PORT: String(port),
      TMPDIR: process.env.TMPDIR || "/tmp",
    },
  });
  return child;
}

function stopChildProcess(child: ChildProcess, timeoutMs = 10_000): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    let finished = false;
    let forceKillTimer: ReturnType<typeof setTimeout> | undefined;
    const finish = () => {
      if (finished) {
        return;
      }
      finished = true;
      if (forceKillTimer) {
        clearTimeout(forceKillTimer);
      }
      child.removeListener("exit", onExit);
      resolve();
    };

    const onExit = () => {
      finish();
    };

    forceKillTimer = setTimeout(() => {
      if (child.exitCode === null && child.signalCode === null) {
        try {
          child.kill("SIGKILL");
        } catch {
          finish();
        }
      }
    }, timeoutMs);

    child.once("exit", onExit);

    try {
      child.kill("SIGTERM");
    } catch {
      finish();
    }
  });
}

async function waitForHealthy(timeoutMs: number, port = PORT): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  const healthUrls = healthUrlsForPort(port);
  while (Date.now() < deadline) {
    for (const url of healthUrls) {
      if (await probe(url)) {
        return true;
      }
    }
    await wait(1000);
  }
  return false;
}

async function monitorFullServerReadiness(): Promise<void> {
  while (true) {
    await wait(BACKGROUND_FULL_RETRY_INTERVAL_MS);
    console.log(
      `[startup_fallback] background full-server retry on shadow port ${SHADOW_FULL_PORT} (timeout ${BACKGROUND_FULL_STARTUP_TIMEOUT_MS}ms)`,
    );

    const candidate = spawnScript("dev:full", SHADOW_FULL_PORT);
    const healthy = await waitForHealthy(BACKGROUND_FULL_STARTUP_TIMEOUT_MS, SHADOW_FULL_PORT);
    await stopChildProcess(candidate);

    if (healthy) {
      console.log(
        `[startup_fallback] full server became healthy on shadow port ${SHADOW_FULL_PORT}; degraded service remains active on ${PORT}`,
      );
      return;
    }

    console.warn("[startup_fallback] shadow full-server retry did not become healthy; will retry later");
  }
}

async function main(): Promise<void> {
  console.log(
    `[startup_fallback] starting full server on ${HOST}:${PORT} with timeout ${FULL_STARTUP_TIMEOUT_MS}ms`,
  );
  let active = spawnScript("dev:full");
  let healthy = await waitForHealthy(FULL_STARTUP_TIMEOUT_MS);
  let degradedModeActive = false;

  if (!healthy) {
    console.warn("[startup_fallback] full server did not become healthy in time; switching to degraded mode");
    await stopChildProcess(active);
    active = spawnScript("dev:degraded");
    healthy = await waitForHealthy(DEGRADED_STARTUP_TIMEOUT_MS);
    degradedModeActive = healthy;
  }

  if (!healthy) {
    console.error("[startup_fallback] neither full nor degraded mode became healthy");
    process.exit(1);
  }

  console.log(`[startup_fallback] healthy at http://${HOST}:${PORT}`);
  if (degradedModeActive) {
    void monitorFullServerReadiness();
  }
  active.on("exit", (code) => {
    process.exit(code ?? 0);
  });

  const shutdown = async (signal: NodeJS.Signals) => {
    console.log(`[startup_fallback] received ${signal}; stopping active server`);
    await stopChildProcess(active);
    process.exit(signal === "SIGTERM" ? 143 : 130);
  };

  process.once("SIGINT", () => {
    void shutdown("SIGINT");
  });
  process.once("SIGTERM", () => {
    void shutdown("SIGTERM");
  });
}

main().catch((error) => {
  console.error("[startup_fallback] fatal error:", error);
  process.exit(1);
});
