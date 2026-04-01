import { log } from "./log.js";

type Msg = { rune: string; data?: any; ts?: number };

export function emitMsg(m: Msg){
  const frame = { ...m, ts: Date.now() };
  // fan-out: SSE, WS, in-mem ring, optional persist
  log.info({ msg: frame.rune, data: m.data }, "Msg⛛");
  
  // Bridge to SSE/WS hubs
  try {
    // Publish to Council Bus if available
    import('./council_bus.js').then(({ councilBus }) => {
      councilBus.publish(`msg.${frame.rune.toLowerCase()}`, frame);
    }).catch(() => {
      // Council Bus not available, continue gracefully
    });
    
    // WebSocket broadcasting to connected clients
    import('../index.js').then((mod) => {
      const wss = (mod as { wss?: any }).wss;
      if (wss && wss.clients) {
        wss.clients.forEach((client: any) => {
          if (client.readyState === 1) { // WebSocket.OPEN
            client.send(JSON.stringify({ type: 'msg_event', ...frame }));
          }
        });
      }
    }).catch(() => {
      // WebSocket server not available, continue gracefully
    });
    
    // SSE broadcasting via Council Bus
    import('./council_bus.js').then(({ councilBus }) => {
      councilBus.publish(`sse.${frame.rune.toLowerCase()}`, frame);
    }).catch(() => {
      // SSE not available, continue gracefully  
    });
    
  } catch (error) {
    console.warn('[Msg] Failed to bridge to hubs:', error);
  }
}
