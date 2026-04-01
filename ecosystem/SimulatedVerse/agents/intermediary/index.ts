import fs from "node:fs";
import path from "node:path";
import { Agent, TAgentManifest, TAgentInput } from "../../shared/agents/contract.js";

const MANIFEST: TAgentManifest = {
  id: "intermediary", role: "intermediary",
  name: "Intermediary",
  description: "Routes messages through the bus and manages communication",
  capabilities: ["route","act","compose"],
  version: "0.1.0",
  runner: "in-process", 
  enabled: true
};

export const IntermediaryAgent: Agent = {
  manifest: () => MANIFEST,
  async health() { return { ok: true, notes: "ready" }; },
  async run(input: TAgentInput) {
    // Real work: route a message and write routing receipt
    const message = input.ask.payload?.message || "System ping";
    const busDir = path.resolve("data", "bus");
    fs.mkdirSync(busDir, { recursive: true });
    
    const busEvent = {
      id: `msg-${Date.now()}`,
      type: "ROUTE",
      from: "intermediary",
      to: input.ask.payload?.to || "system",
      message,
      timestamp: input.utc,
      tick: input.t
    };
    
    const busFile = path.join(busDir, `messages-${Date.now()}.json`);
    fs.writeFileSync(busFile, JSON.stringify([busEvent], null, 2));
    
    const receiptDir = path.resolve("data","artifacts","intermediary");
    fs.mkdirSync(receiptDir, { recursive: true });
    const receipt = path.join(receiptDir, `receipt-${Date.now()}.json`);
    fs.writeFileSync(receipt, JSON.stringify({
      routingId: busEvent.id,
      message,
      routed: true,
      t: input.t,
      utc: input.utc
    }, null, 2));
    
    return {
      ok: true,
      effects: {
        artifactPath: receipt,
        busEvents: [busEvent],
        stateDelta: { messagesRouted: 1 }
      }
    };
  }
};

export default IntermediaryAgent;