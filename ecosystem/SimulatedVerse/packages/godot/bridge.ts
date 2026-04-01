import WebSocket from "ws";
import { councilBus } from "../council/events/eventBus";
import { speak } from "../comms/speak";

export function connectGodot(url="ws://127.0.0.1:8765"){
  const ws = new WebSocket(url);
  ws.on("open", ()=> speak({from:"godot-bridge", title:"Godot connected", text:url}));
  ws.on("message", (buf)=> {
    try { const msg = JSON.parse(String(buf)); councilBus.publish(`godot.${msg.topic}`, msg.payload); }
    catch(e){ /* ignore */ }
  });
  const sub = councilBus.subscribeAll(ev=>{
    if (ev.topic.startsWith("game.")) ws.send(JSON.stringify({ topic: ev.topic, payload: ev.payload }));
  });
  ws.on("close", ()=> sub && sub());
}