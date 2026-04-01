#!/usr/bin/env tsx
// SystemDev/scripts/simple_preview.ts  
// Minimal Preview Orchestrator - single front door on port 3000

import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import fs from 'fs';

const app = express();
const PORT = 3000;
const BUILD_ID = Date.now().toString();

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    ok: true,
    time: new Date().toISOString(),
    build_id: BUILD_ID,
    env: process.env.NODE_ENV || 'development',
    preview_mode: true,
    mobile_ready: true
  });
});

// Serve probe and static files
app.use('/web', express.static(path.join(process.cwd(), 'PreviewUI/web'), {
  setHeaders: (res) => {
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Preview-Build', BUILD_ID);
    res.setHeader('X-Mobile-Safe', 'true');
  }
}));

// Proxy API calls to main server
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:5000',
  changeOrigin: true,
  onError: (err, req, res) => {
    console.error('Proxy error:', err.message);
    res.status(502).json({ error: 'Backend unavailable' });
  }
}));

// SPA fallback for /app/* routes  
app.get('/app/*', async (req, res) => {
  try {
    const response = await fetch('http://localhost:5000' + req.path.replace('/app', ''));
    const html = await response.text();
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Preview-Build', BUILD_ID);
    res.send(html);
  } catch (error) {
    console.error('App proxy error:', error);
    res.status(502).json({ error: 'Backend unavailable' });
  }
});

// Default route
app.get('/', (req, res) => {
  res.redirect('/web/preview_probe.html');
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🎯 Simple Preview running on port ${PORT}`);
  console.log(`📱 Mobile-safe headers enabled`);
  console.log(`🔗 Proxying /api/* to localhost:5000`);
  console.log(`📁 Static files from PreviewUI/web/`);
  
  // Write receipt
  const receipt = {
    timestamp: new Date().toISOString(),
    build_id: BUILD_ID,
    port: PORT,
    status: 'operational',
    endpoints: {
      health: '/health',
      static: '/web/*',
      api_proxy: '/api/*', 
      app_spa: '/app/*'
    }
  };
  
  try {
    fs.writeFileSync(
      path.join(process.cwd(), `SystemDev/receipts/preview_orchestrator_start_${BUILD_ID}.json`),
      JSON.stringify(receipt, null, 2)
    );
    console.log(`📋 Receipt written: preview_orchestrator_start_${BUILD_ID}.json`);
  } catch (error) {
    console.error('Receipt write failed:', error);
  }
});

export default app;