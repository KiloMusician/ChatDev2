#!/usr/bin/env tsx
/**
 * Godot ↔ ΞNuSyQ Hybrid Bridge
 * - WebSocket server for Godot editor/runtime (GDScript client below).
 * - OSC out/in for TouchDesigner.
 * - Mirrors state into QGL (emit events on Council bus if you have it).
 */
import { WebSocketServer, WebSocket } from "ws";
import dgram from "node:dgram";
import { nanoid } from "nanoid";
import fs from "node:fs";
import path from "node:path";
import YAML from "js-yaml";

type Msg = { type: string; id?: string; [k: string]: any };

const PORT_WS = Number(process.env.GODOT_WS_PORT || 8765);
const OSC_HOST = process.env.TD_OSC_HOST || "127.0.0.1";
const OSC_PORT = Number(process.env.TD_OSC_PORT || 9000);

const oscSock = dgram.createSocket("udp4");
const clients = new Set<WebSocket>();

function sendOSC(address: string, nums: number[] = []) {
  // super-minimal OSC packer
  const enc = (s: string) => Buffer.from(s + "\0");
  const pad = (b: Buffer) => Buffer.concat([b, Buffer.alloc((4 - (b.length % 4)) % 4)]);
  const addr = pad(enc(address));
  const tags = pad(enc("," + "f".repeat(nums.length)));
  const args = Buffer.concat(nums.map(n => { const b = Buffer.alloc(4); b.writeFloatBE(n,0); return b; }));
  const packet = Buffer.concat([addr, tags, args]);
  oscSock.send(packet, OSC_PORT, OSC_HOST);
}

function qglWrite(kind: string, payload: any) {
  const out = path.join("yap_archive", "qgl");
  fs.mkdirSync(out, { recursive: true });
  const id = nanoid();
  fs.writeFileSync(path.join(out, `godot_bridge_${id}.json`), JSON.stringify({
    qgl_version: "0.2",
    id: `godot_bridge:${id}`,
    kind,
    created_at: new Date().toISOString(),
    content: payload,
    tags: { "bridge/source": "godot", "omnitag/kind": kind }
  }, null, 2));
}

const wss = new WebSocketServer({ port: PORT_WS });
wss.on("connection", (ws) => {
  clients.add(ws);
  console.log(`[godot-bridge] Client connected (${clients.size} total)`);
  
  ws.on("message", (raw) => {
    let msg: Msg;
    try { msg = JSON.parse(String(raw)); } catch { return; }

    if (msg.type === "hello") {
      ws.send(JSON.stringify({ type: "hello_ack", id: msg.id || nanoid() }));
      console.log(`[godot-bridge] Hello from client: ${msg.id}`);
    }

    if (msg.type === "state") {
      // fwd to UI (if any), log to QGL, emit OSC summaries
      qglWrite("godot.state", msg.payload);
      sendOSC("/xinusyq/state", [msg.payload?.fps ?? 0, msg.payload?.entities ?? 0]);
      console.log(`[godot-bridge] State update: fps=${msg.payload?.fps}, entities=${msg.payload?.entities}`);
    }

    if (msg.type === "eval_ready") {
      // Godot says it's ready to run code patches (file-based, not eval strings)
      qglWrite("godot.eval_ready", { ok: true });
      console.log("[godot-bridge] Godot ready for code execution");
    }

    if (msg.type === "apply_actions") {
      // High-level commands, like spawning, loading scenes, toggles
      qglWrite("godot.apply_actions", msg.actions);
      ws.send(JSON.stringify({ type: "apply_ack", ok: true }));
      console.log(`[godot-bridge] Applied ${msg.actions?.length || 0} actions`);
    }
  });

  ws.on("close", () => {
    clients.delete(ws);
    console.log(`[godot-bridge] Client disconnected (${clients.size} total)`);
  });
});

console.log(`[godot-bridge] WebSocket on ws://127.0.0.1:${PORT_WS}`);
console.log(`[godot-bridge] OSC out to ${OSC_HOST}:${OSC_PORT}`);
console.log(`[godot-bridge] QGL receipts in yap_archive/qgl/`);

// Broadcast system status every 10 seconds
setInterval(() => {
  const statusUpdate = {
    type: "system_status",
    payload: {
      connected_clients: clients.size,
      timestamp: Date.now(),
      bridge_version: "1.0.0"
    }
  };
  
  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify(statusUpdate));
    }
  });
  
  qglWrite("godot.bridge_status", statusUpdate.payload);
}, 10000);

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("[godot-bridge] Shutting down...");
  clients.forEach(client => client.close());
  oscSock.close();
  process.exit(0);
});