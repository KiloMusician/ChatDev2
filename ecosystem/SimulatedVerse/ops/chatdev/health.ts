#!/usr/bin/env tsx
import { request } from "undici";
const base = process.env.CHATDEV_URL || "http://127.0.0.1:4466";

async function main() {
  try {
    const r = await request(`${base}/chatdev/agents`, { method:"GET", headersTimeout:2000, bodyTimeout:2000 });
    const ok = r.statusCode === 200;
    const j: any = ok ? await r.body.json() : {};
    console.log(JSON.stringify({ ok, agents: j.agents ?? [] }));
    process.exit(ok ? 0 : 1);
  } catch(e:any) {
    console.log(JSON.stringify({ ok:false, reason:String(e?.message||e) }));
    process.exit(1);
  }
}
main();