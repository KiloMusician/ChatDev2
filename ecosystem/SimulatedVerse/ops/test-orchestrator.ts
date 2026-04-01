
import { CultureShipOrchestrator } from "../server/services/culture-ship-orchestrator.ts";

async function testActivation() {
  const orchestrator = new CultureShipOrchestrator();
  const result = await orchestrator.deployAgentSwarm();
  console.log("[test] Result:", JSON.stringify(result, null, 2));
  return result;
}

testActivation().catch(console.error);
