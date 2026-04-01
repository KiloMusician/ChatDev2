/**
 * Preview Router - Kill "old UI" ghosts with pinned builds and smart routing
 * Integrates with existing Express server to provide stable preview endpoints
 */
import type { Express } from "express";
import pino from "pino";

const logger = pino({ level: 'info' });

// Import compression and proxy middleware with graceful fallbacks
let compression: any, createProxyMiddleware: any;

try {
  compression = (await import("compression")).default;
} catch {
  compression = (req: any, res: any, next: any) => next(); // No-op fallback
}

try {
  const proxyModule = await import("http-proxy-middleware");
  createProxyMiddleware = proxyModule.createProxyMiddleware;
} catch {
  // Fallback proxy implementation
  createProxyMiddleware = (options: any) => (req: any, res: any, next: any) => {
    logger.warn("Proxy middleware not available, passing through");
    next();
  };
}

export interface PreviewConfig {
  latestTarget?: string;
  pinnedTarget?: string;
  enableCompression?: boolean;
  cacheControl?: {
    latest: string;
    pinned: string;
  };
}

/**
 * Mount preview routing with smart build selection
 */
export function mountPreview(app: Express, config: PreviewConfig = {}) {
  const {
    latestTarget = "http://localhost:5173", // Vite dev server
    pinnedTarget = "http://localhost:4173", // Built static server
    enableCompression = true,
    cacheControl = {
      latest: "no-store, max-age=0",
      pinned: "public, max-age=300" // 5 minute cache for pinned builds
    }
  } = config;

  logger.info("🎯 Mounting preview router...");

  // Enable compression if available
  if (enableCompression && compression) {
    app.use("/preview", compression());
  }

  // Latest build route (dev/hot-reload)
  app.use("/preview/latest", createProxyMiddleware({
    target: latestTarget,
    changeOrigin: true,
    pathRewrite: { "^/preview/latest": "" },
    headers: { 
      "Cache-Control": cacheControl.latest,
      "X-Preview-Mode": "latest"
    },
    onError: (err, req, res) => {
      logger.error("Latest preview proxy error:", err);
      res.status(503).json({ 
        error: "Development server unavailable", 
        target: latestTarget 
      });
    }
  }));

  // Pinned build route (stable/testing)
  app.use("/preview/pinned", createProxyMiddleware({
    target: pinnedTarget,
    changeOrigin: true,
    pathRewrite: { "^/preview/pinned": "" },
    headers: { 
      "Cache-Control": cacheControl.pinned,
      "X-Preview-Mode": "pinned"
    },
    onError: (err, req, res) => {
      logger.error("Pinned preview proxy error:", err);
      res.status(503).json({ 
        error: "Pinned build unavailable", 
        target: pinnedTarget 
      });
    }
  }));

  // Default preview route - respects PREVIEW_TARGET environment variable
  const defaultTarget = process.env.PREVIEW_TARGET === "pinned" ? "/preview/pinned" : "/preview/latest";
  app.get("/preview", (req, res) => {
    logger.info(`🎯 Preview redirect: ${defaultTarget}`);
    res.redirect(defaultTarget);
  });

  // Preview status endpoint for debugging
  app.get("/preview/status", (req, res) => {
    res.json({
      status: "operational",
      targets: {
        latest: latestTarget,
        pinned: pinnedTarget
      },
      defaultRoute: defaultTarget,
      environment: {
        PREVIEW_TARGET: process.env.PREVIEW_TARGET,
        PREVIEW_FLAVOR: process.env.PREVIEW_FLAVOR
      },
      timestamp: new Date().toISOString()
    });
  });

  // Health check for preview endpoints
  app.get("/preview/health", async (req, res) => {
    const health = {
      latest: await checkEndpoint(latestTarget),
      pinned: await checkEndpoint(pinnedTarget),
      timestamp: new Date().toISOString()
    };

    const allHealthy = Object.values(health).slice(0, 2).every(status => status === "healthy");
    res.status(allHealthy ? 200 : 503).json(health);
  });

  logger.info(`✅ Preview router mounted: latest=${latestTarget}, pinned=${pinnedTarget}`);
}

/**
 * Simple health check for preview endpoints
 */
async function checkEndpoint(target: string): Promise<"healthy" | "unhealthy"> {
  try {
    const url = new URL(target);
    const response = await fetch(`${url.origin}/`, { 
      method: 'HEAD',
      signal: AbortSignal.timeout(3000) // 3 second timeout
    });
    return response.ok ? "healthy" : "unhealthy";
  } catch {
    return "unhealthy";
  }
}

/**
 * Integration with existing Culture-Ship event system
 */
export function emitPreviewEvent(event: string, data: any) {
  try {
    // Try to emit to existing Council Bus  
    // @ts-ignore - Module may not be available
    import("../server/services/council_bus.js").then(({ councilBus }) => {
      councilBus.publish(`preview.${event}`, {
        ...data,
        timestamp: new Date().toISOString()
      });
    }).catch(() => {
      // Graceful fallback if Council Bus not available
      logger.info(`Preview event: ${event}`, data);
    });
  } catch {
    // Silent fallback
  }
}

/**
 * Mobile-safe preview configuration for Samsung S23
 */
export const mobilePreviewConfig: PreviewConfig = {
  enableCompression: true,
  cacheControl: {
    latest: "no-store, no-cache, must-revalidate", // Aggressive cache busting for mobile
    pinned: "public, max-age=120" // Shorter cache for mobile testing
  }
};