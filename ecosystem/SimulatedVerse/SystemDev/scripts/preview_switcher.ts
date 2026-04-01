#!/usr/bin/env tsx
/**
 * Preview Switcher (no deletes): serves the chosen UI root with cache-busting.
 * Usage: PREVIEW_FLAVOR=web:PreviewUI/web tsx SystemDev/scripts/preview_switcher.ts
 */
import http from "node:http";
import path from "node:path";
import fs from "node:fs";
import { createReadStream } from "node:fs";

const flavor = process.env.PREVIEW_FLAVOR ?? "web:PreviewUI/web";
const [kind, root] = flavor.split(":");
const port = Number(process.env.PORT || 3000);

const rootAbs = path.resolve(process.cwd(), root);
if (!fs.existsSync(rootAbs)) {
  console.error(`[switcher] root missing: ${rootAbs}`);
  process.exit(1);
}

const noCache = {
  "Cache-Control": "no-store, max-age=0",
  "Pragma": "no-cache",
  "Expires": "0",
};

const server = http.createServer((req, res) => {
  const url = decodeURIComponent((req.url||"/").split("?")[0]);
  let fpath = path.join(rootAbs, url);
  if (fs.existsSync(fpath) && fs.statSync(fpath).isDirectory()) {
    fpath = path.join(fpath, "index.html");
  }
  if (!fs.existsSync(fpath) && /\/$/.test(url)) {
    fpath = path.join(rootAbs, "index.html"); // SPA fallback
  }
  if (!fs.existsSync(fpath)) {
    // final fallback for SPAs
    fpath = path.join(rootAbs, "index.html");
  }
  res.writeHead(200, { "Content-Type": mime(fpath), ...noCache, "X-Preview-Flavor": flavor });
  createReadStream(fpath).pipe(res);
});

server.listen(port, () => {
  console.log(`[switcher] ${kind} → ${rootAbs}`);
  console.log(`[switcher] PORT=${port}  PREVIEW_FLAVOR=${flavor}`);
});

function mime(p:string){
  const ext = path.extname(p).toLowerCase();
  if (ext===".html"||ext===".htm") return "text/html; charset=utf-8";
  if (ext===".js") return "text/javascript; charset=utf-8";
  if (ext===".css") return "text/css; charset=utf-8";
  if (ext===".json") return "application/json";
  if (ext===".png") return "image/png";
  if (ext===".jpg"||ext===".jpeg") return "image/jpeg";
  if (ext===".svg") return "image/svg+xml";
  return "application/octet-stream";
}