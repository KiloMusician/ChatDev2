/**
 * Wrap "modules with prints" as agent-aware services:
 * - expose runTask({input}) → {output, logs, metrics}
 * - emit Msg⛛ on start/finish
 * - optionally publish to /events for HUD
 */
import { emitMsg } from "./msg.js";
import { log } from "./log.js";
import { AGENT_CONFIG } from "../config/constants.js";

export type AgentTask = { name: string; input?: any; timeoutMs?: number };
export type AgentResult = { ok: boolean; output?: any; logs?: any[]; err?: string; ms: number };

export async function runAgentTask(task: AgentTask, fn: ()=>Promise<any>): Promise<AgentResult> {
  const t0 = Date.now();
  emitMsg({ rune: "agent:start", data: { name: task.name } });
  try{
    const output = await Promise.race([
      fn(), new Promise((_r,rej)=>setTimeout(()=>rej(new Error("timeout")), task.timeoutMs||AGENT_CONFIG.TASK_TIMEOUT_MS))
    ]);
    const ms = Date.now()-t0;
    const res = { ok:true, output, logs:[], ms };
    log.info({ task: task.name, ms }, "agent done");
    emitMsg({ rune: "agent:done", data: { name: task.name, ms }});
    return res;
  }catch(e:any){
    const ms = Date.now()-t0;
    log.error({ err:String(e), task: task.name, ms }, "agent fail");
    emitMsg({ rune: "agent:fail", data: { name: task.name, err: String(e) }});
    return { ok:false, err:String(e), ms };
  }
}