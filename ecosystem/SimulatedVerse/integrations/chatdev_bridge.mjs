import { enqueue } from "../modules/culture_ship/queue/mega_queue.js";
const hasOllama = !!process.env.OLLAMA_HOST;
const hasChatDev = !!process.env.CHATDEV_HOME;

export function maybeUseChatDev(taskSpec){
  if (hasOllama && hasChatDev && process.env.TOKEN_SPEND_PER_OP !== "0") {
    enqueue({ kind:"chatdev.run", data:{spec:taskSpec}, priority:4, allowExternalCalls:true });
    return true;
  }
  enqueue({ kind:"chatdev.mock", data:{spec:taskSpec}, priority:6 }); // zero-token placeholder dev path
  return false;
}