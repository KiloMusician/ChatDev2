import { bus } from "../../../ascii/core/Bus";

export function mountAsciiHud(target:HTMLElement){
  const bar = document.createElement("div");
  bar.style.cssText = "position:fixed;right:8px;bottom:8px;padding:6px 8px;background:#0f1320cc;border:1px solid #283046;border-radius:6px;font-family:var(--ascii-font);font-size:12px;color:#cfd2dc;z-index:9999;display:flex;gap:6px;align-items:center;";
  
  const backendBtn = mkBtn("Backend"); 
  backendBtn.onclick = ()=>bus.emit("ascii/toggleBackend");
  
  const vantageBtn = mkBtn("Vantage"); 
  vantageBtn.onclick = ()=>bus.emit("ascii/switchVantage");
  
  const pauseBtn   = mkBtn("Pause");   
  pauseBtn.onclick   = ()=>bus.emit("ascii/pause");
  
  const bigRed     = mkBtn("Cascade"); 
  bigRed.style.background="#f7768e"; 
  bigRed.onclick=()=>bus.emit("ascii/bigRedButton");
  
  bar.append(backendBtn, vantageBtn, pauseBtn, bigRed);
  target.appendChild(bar);
  
  function mkBtn(txt:string){ 
    const b=document.createElement("button"); 
    b.textContent=txt; 
    b.style.cssText="all:unset;cursor:pointer;background:#1a2133;padding:4px 6px;border-radius:4px;border:1px solid #283046;"; 
    b.onpointerdown=e=>e.preventDefault(); 
    return b;
  }
}