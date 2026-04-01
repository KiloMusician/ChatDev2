#!/usr/bin/env tsx
import { createServer } from "node:http";
import { ChatDevRuntime } from "./index.js";
import { ChatDevRegistry } from "./registry.js";

const runtime = new ChatDevRuntime(ChatDevRegistry);

createServer(async (req, res) => {
  // CORS headers for local development
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method === "GET" && req.url === "/chatdev/agents") {
    const list = runtime.listAgents();
    res.writeHead(200, {"content-type":"application/json"});
    res.end(JSON.stringify({ agents: list }));
    return;
  }
  
  if (req.method === "POST" && req.url === "/chatdev/turn") {
    const chunks: Buffer[] = [];
    for await (const c of req) chunks.push(c as Buffer);
    const { agent, input, json } = JSON.parse(Buffer.concat(chunks).toString());
    try {
      const reply = await runtime.turn({ agent, input, json });
      res.writeHead(200, {"content-type":"application/json"});
      res.end(JSON.stringify(reply));
    } catch (e:any) {
      res.writeHead(500, {"content-type":"application/json"});
      res.end(JSON.stringify({error:String(e?.message||e)}));
    }
    return;
  }
  
  res.writeHead(404);
  res.end();
}).listen(process.env.CHATDEV_PORT || 4466, () => {
  console.log(`[chatdev] ready on :${process.env.CHATDEV_PORT || 4466}`);
});