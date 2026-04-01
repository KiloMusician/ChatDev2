// ops/yap-monitor.js
import { attachConsoleCapture, attachBusListeners } from "../packages/yap/yapMonitor.js";

console.log("[yap] monitor starting…");
attachConsoleCapture();
attachBusListeners();
console.log("[yap] console capture + bus listeners attached");

// keep alive forever (headless mode)
setInterval(()=>{}, 1<<30);