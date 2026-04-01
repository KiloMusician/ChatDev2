type BootEvent = { t:number; phase:string; ok:boolean; note?:string };
const q: BootEvent[] = [];

export function trace(phase:string, ok=true, note?:string) {
  q.push({ t: Date.now(), phase, ok, note }); 
  if (q.length>200) q.shift();
  console.log(`[BOOT-TRACE] ${phase}: ${ok ? '✅' : '❌'} ${note || ''}`);
}

export function mountBootTrace(app:any) {
  app.get("/api/trace/boot", (_:any, res:any) => res.json({ events:q }));
}