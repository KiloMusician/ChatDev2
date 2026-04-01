import fetch from "node-fetch";
import { getStore } from "../state/store.js";

interface AutoplayConfig {
  agentUrl?: string;
  tickMs?: number;
  enabled?: boolean;
}

let autoplayActive = false;
let autoplayInterval: NodeJS.Timeout | null = null;

export function startAutoplay(config: AutoplayConfig = {}) {
  const { agentUrl, tickMs = 400, enabled = true } = config;
  
  if (!enabled || autoplayActive) {
    console.log(`[AUTOPLAY] Already active or disabled`);
    return;
  }
  
  autoplayActive = true;
  console.log(`[AUTOPLAY] Starting with ${tickMs}ms interval${agentUrl ? ` and agent URL: ${agentUrl}` : ''}`);
  
  autoplayInterval = setInterval(async () => {
    try {
      const snapshot = getStore().readGameSnapshot();
      
      // Only act if game is in playing state and autopilot is on
      if (snapshot.phase !== "playing" || !snapshot.autopilot) {
        return;
      }
      
      let nextAction = { action: "tick", payload: {} };
      
      // Try to get action from external agent
      if (agentUrl) {
        try {
          const observation = {
            phase: snapshot.phase,
            tick: snapshot.tick,
            resources: snapshot.resources ?? {},
            ui: snapshot.ui ?? {}
          };
          
          const response = await fetch(`${agentUrl}/next`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(observation)
          });
          
          if (response.ok) {
            const agentResponse = await response.json() as any;
            if (agentResponse?.action) {
              nextAction = agentResponse as { action: string; payload: any };
            }
          }
        } catch (agentError) {
          // Fall back to default tick action if agent fails
          console.warn(`[AUTOPLAY] Agent failed, falling back to tick:`, agentError);
        }
      }
      
      // Apply the action
      const result = getStore().applyAction("system:autoplay", nextAction.action, nextAction.payload);
      
      if (!result.success) {
        console.warn(`[AUTOPLAY] Action failed:`, result.error);
      }
      
    } catch (error) {
      console.error(`[AUTOPLAY] Loop error:`, error);
    }
  }, tickMs);
}

export function stopAutoplay() {
  if (autoplayInterval) {
    clearInterval(autoplayInterval);
    autoplayInterval = null;
  }
  autoplayActive = false;
  console.log(`[AUTOPLAY] Stopped`);
}

export function isAutoplayActive(): boolean {
  return autoplayActive;
}

// Simple built-in agent behaviors
export function getBuiltinAgentAction(snapshot: any): { action: string; payload: any } {
  const { resources = {}, tick } = snapshot;
  
  // Simple strategy: buy materials when energy is high
  if (resources.energy > 50 && tick % 10 === 0) {
    return { action: "buy", payload: { item: "materials" } };
  }
  
  // Upgrade components occasionally
  if (resources.materials > 20 && tick % 25 === 0) {
    return { action: "buy", payload: { item: "components" } };
  }
  
  // Default to tick
  return { action: "tick", payload: {} };
}