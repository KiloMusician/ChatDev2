#!/usr/bin/env tsx
// SystemDev/scripts/preview_orchestrator.ts
// Single front door for Preview - ports, proxying, mobile-safe headers

import fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import fastifyHttpProxy from '@fastify/http-proxy';
import path from 'path';
import fs from 'fs';

const app = fastify({ logger: true });

// Build ID for cache busting
const BUILD_ID = Date.now().toString();
const PREVIEW_PORT = 3000;

// Health endpoint
app.get('/health', async (request, reply) => {
  return {
    ok: true,
    time: new Date().toISOString(),
    build_id: BUILD_ID,
    env: process.env.NODE_ENV || 'development',
    cwd: process.cwd(),
    preview_mode: true,
    mobile_ready: true
  };
});

// Serve static files from PreviewUI/web with mobile-safe headers
app.register(fastifyStatic, {
  root: path.join(process.cwd(), 'PreviewUI/web'),
  prefix: '/web/',
  setHeaders: (res: any) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Preview-Build', BUILD_ID);
    res.setHeader('X-Mobile-Safe', 'true');
  }
});

// Serve Godot exports under /godot/
app.register(fastifyStatic, {
  root: path.join(process.cwd(), 'PreviewUI/web/godot'),
  prefix: '/godot/',
  decorateReply: false,
  setHeaders: (res: any) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Cross-Origin-Embedder-Policy', 'credentialless');
    res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  }
});

// Proxy /app/* to main server (port 5000) with SPA fallback
app.register(async function (fastify) {
  // Proxy to main server
  fastify.register(fastifyHttpProxy, {
    upstream: 'http://localhost:5000',
    prefix: '/api',
    httpMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
    replyOptions: {
      rewriteRequestHeaders: (originalReq: any, headers: any) => {
        headers['x-preview-proxy'] = 'true';
        return headers;
      }
    }
  });

  // SPA fallback for /app/* routes (history API)
  fastify.setNotFoundHandler(async (request, reply) => {
    const url = request.url;
    
    // If it's an /app/ route, serve the main app
    if (url.startsWith('/app/')) {
      try {
        const response = await fetch('http://localhost:5000' + url.replace('/app', ''));
        const html = await response.text();
        reply.type('text/html');
        reply.header('Cache-Control', 'no-store');
        reply.header('X-Preview-Build', BUILD_ID);
        return html;
      } catch (error) {
        console.error('Proxy error:', error);
        return reply.code(502).send({ error: 'Backend unavailable' });
      }
    }
    
    // Default 404
    return reply.code(404).send({ error: 'Not found', path: url });
  });
});

// Start orchestrator
async function start() {
  try {
    await app.listen({ port: PREVIEW_PORT, host: '0.0.0.0' });
    console.log(`🎯 Preview Orchestrator running on port ${PREVIEW_PORT}`);
    console.log(`📱 Mobile-safe headers enabled`);
    console.log(`🔗 Proxying /api/* to localhost:5000`);
    console.log(`📁 Static files from PreviewUI/web/`);
    console.log(`🎮 Godot exports from /godot/`);
    
    // Write receipt
    const receipt = {
      timestamp: new Date().toISOString(),
      build_id: BUILD_ID,
      port: PREVIEW_PORT,
      proxies: {
        api: 'localhost:5000',
        static_web: 'PreviewUI/web/',
        godot: 'PreviewUI/web/godot/'
      },
      headers: {
        cache_control: 'no-store',
        preview_build: BUILD_ID,
        mobile_safe: true
      },
      status: 'operational'
    };
    
    const receiptPath = path.join(process.cwd(), `SystemDev/receipts/preview_orchestrator_start_${BUILD_ID}.json`);
    fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2));
    
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

// Start if called directly (ES module check)
if (import.meta.url.endsWith(process.argv[1])) {
  start();
}

export { app, start };