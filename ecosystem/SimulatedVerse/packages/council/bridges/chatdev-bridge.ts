import { council } from "../../chatdev-adapter";
import { writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

// Listen for ChatDev turns and generate receipts/PUs
council.on("chatdev.turn", (evt) => {
  try {
    // Create reports directory for ChatDev interactions
    mkdirSync("reports/chatdev", { recursive: true });
    const ts = new Date().toISOString().replace(/[:.]/g,"-");
    const fname = join("reports/chatdev", `${ts}-${evt.agent}.json`);
    
    // Store the interaction with metadata
    const receipt = {
      timestamp: ts,
      agent: evt.agent,
      input: evt.input,
      reply: evt.reply,
      backend_used: evt.reply.backend,
      session: process.pid // Simple session tracking
    };
    
    writeFileSync(fname, JSON.stringify(receipt, null, 2));
    
    // Optionally generate PU if this was a significant action
    if (evt.input.includes('implement') || evt.input.includes('fix') || evt.input.includes('create')) {
      const puSummary = {
        type: 'chatdev_generated',
        agent: evt.agent,
        task: evt.input.slice(0, 100),
        receipt_path: fname,
        suggested_priority: 60
      };
      
      const puFname = join("reports/chatdev", `PU-${ts}-${evt.agent}.json`);
      writeFileSync(puFname, JSON.stringify(puSummary, null, 2));
    }
    
  } catch (e) {
    console.warn('[chatdev-bridge] receipt error:', String(e));
  }
});

// Emit bridge status for monitoring
setTimeout(() => {
  council.emit('bridge.status', { 
    bridge: 'chatdev', 
    status: 'online', 
    timestamp: new Date().toISOString() 
  });
}, 1000);