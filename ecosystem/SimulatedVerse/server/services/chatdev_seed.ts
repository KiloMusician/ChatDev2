import fs from "node:fs";
import yaml from "yaml";
import { ChatDev } from "./chatdev.js";
import { log } from "./log.js";

export async function seedChatDev() {
  try {
    // Load roles
    const roles = yaml.parse(fs.readFileSync("data/chatdev_roles.yaml", "utf8"));
    roles.agents.forEach((a: any) => ChatDev.registerAgent(a));
    log.info({ count: roles.agents.length }, "[ChatDev.Seed] Registered agents");

    // Load pipelines
    const pipes = yaml.parse(fs.readFileSync("data/chatdev_pipelines.yaml", "utf8"));
    pipes.pipelines.forEach((p: any) => ChatDev.registerPipeline(p));
    log.info({ count: pipes.pipelines.length }, "[ChatDev.Seed] Registered pipelines");

    // Load prompts
    const prompts = yaml.parse(fs.readFileSync("data/chatdev_prompts.yaml", "utf8"));
    Object.entries(prompts.prompts).forEach(([id, txt]) => 
      ChatDev.registerPrompt(id, String(txt))
    );
    log.info({ count: Object.keys(prompts.prompts).length }, "[ChatDev.Seed] Registered prompts");
    
    log.info({}, "[ChatDev.Seed] ChatDev registry fully seeded");
  } catch (error) {
    log.error({ error }, "[ChatDev.Seed] Failed to seed");
  }
}
