import { speak } from "../packages/comms/speak";
import { councilBus } from "../packages/council/events/eventBus";

setInterval(()=> {
  speak({ from:"culture-ship", level:"info", title:"Heartbeat", text:"All decks nominal.", tags:{
    queueDepth: (global as any)?.PU_QUEUE_DEPTH ?? null,
    uiProvisionLagSec: (global as any)?.PROVISION_LAG ?? null
  }});
}, 60_000);

councilBus.subscribe("ops.alert", ev=>{
  speak({ from:"culture-ship", level:"warn", title:"Ops alert", text: JSON.stringify(ev.payload).slice(0,400) });
});