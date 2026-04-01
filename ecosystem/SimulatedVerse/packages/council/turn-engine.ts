import { appendChat, createChatMessage, getChatHistory } from "./group-chat";
import { listActions, resolveAction } from "../actions/registry";
import { AGENT_ROSTER, getAgent, getRandomAgent } from "./agents";
import { generateAgentResponse } from "../llm/chat-engine";

type ConversationTurn = {
  turn_id: string;
  speaker: string;
  topic: string;
  goals: string[];
  completed: boolean;
};

let currentTurn: ConversationTurn | null = null;
let turnCounter = 0;

export async function startConversation(topic: string, initiator?: string) {
  const speaker = initiator ? getAgent(initiator) : getRandomAgent();
  if (!speaker) return;

  turnCounter++;
  currentTurn = {
    turn_id: `turn_${turnCounter}_${Date.now()}`,
    speaker: speaker.id,
    topic,
    goals: ["analyze_situation", "propose_actions", "coordinate_next_steps"],
    completed: false
  };

  // System message to start conversation
  appendChat(createChatMessage(
    "system",
    `🗣️ Conversation started: "${topic}" (Speaker: ${speaker.name})`,
    "council",
    "system"
  ));

  await takeTurn(currentTurn);
}

export async function takeTurn(turn: ConversationTurn) {
  const agent = getAgent(turn.speaker);
  if (!agent) return;

  // Generate context for the agent
  const recentHistory = getChatHistory(10);
  const context = buildContext(turn.topic, recentHistory);

  try {
    // Generate agent's thoughts
    const response = await generateAgentResponse(
      agent.id,
      agent.systemPrompt,
      context,
      agent.model
    );

    // Choose actions based on response and agent capabilities
    const suggestedActions = chooseActions(agent, response);
    const takenActions: string[] = [];

    // Execute actions
    for (const action of suggestedActions.slice(0, 2)) { // Max 2 actions per turn
      if (agent.capabilities.includes(action)) {
        try {
          const actionFn = resolveAction(action);
          if (actionFn) {
            const result = await actionFn(
              { topic: turn.topic },
              {
                cwd: process.cwd(),
                report: (line) => console.log(`[${agent.id}:${action}] ${line}`),
                setHealthNote: (k, v) => console.log(`[${agent.id}] Health: ${k}=${JSON.stringify(v)}`)
              }
            );
            
            takenActions.push(action);
            
            // Log action result
            appendChat(createChatMessage(
              agent.id,
              `✅ Action ${action}: ${result.ok ? "SUCCESS" : "FAILED"} ${result.proof ? `(proof: ${result.proof})` : ""}`,
              "council"
            ));
          }
        } catch (e: any) {
          appendChat(createChatMessage(
            agent.id,
            `❌ Action ${action} crashed: ${e.message}`,
            "council"
          ));
        }
      }
    }

    // Post agent's main response
    const message = createChatMessage(agent.id, response, "council");
    message.actions_suggested = suggestedActions;
    message.actions_taken = takenActions;
    appendChat(message);

    // Schedule next turn with different agent (AUTONOMOUS FIX: Extended delays to prevent 429 flooding)
    const baseDelay = 30000; // 30 seconds base delay
    const randomDelay = Math.random() * 30000; // 0-30 seconds additional
    const totalDelay = baseDelay + randomDelay; // 30-60 second delay
    
    setTimeout(() => {
      const nextSpeaker = selectNextSpeaker(agent.id);
      if (nextSpeaker) {
        takeTurn({
          turn_id: `followup_${Date.now()}`,
          speaker: nextSpeaker.id,
          topic: turn.topic,
          goals: ["respond_to_previous", "add_perspective"],
          completed: false
        });
      }
    }, totalDelay);

  } catch (e: any) {
    appendChat(createChatMessage(
      "system", 
      `❌ Turn failed for ${agent.name}: ${e.message}`,
      "council",
      "system"
    ));
  }
}

function buildContext(topic: string, recentHistory: any[]): string {
  const historyText = recentHistory
    .slice(0, 5)
    .map(msg => `${msg.agent}: ${msg.content}`)
    .join("\n");

  return `Topic: ${topic}

Recent conversation:
${historyText}

Your task: Analyze the situation, propose concrete next steps, and take 1-2 relevant actions from your capabilities.
Be specific and actionable. Avoid vague statements.`;
}

function chooseActions(agent: any, response: string): string[] {
  const available = listActions().filter(action => 
    agent.capabilities.includes(action)
  );

  const chosen: string[] = [];

  // Keyword-based action selection
  if (response.match(/test|verify|validate/i) && available.includes("run_tests")) {
    chosen.push("run_tests");
  }
  
  if (response.match(/error|bug|fix|problem/i) && available.includes("fix_error")) {
    chosen.push("fix_error");
  }
  
  // AUTONOMOUS FIX: Throttle health checks to prevent 429 flooding
  if (response.match(/health|status|check|system/i) && available.includes("check_system_health")) {
    const globalState = globalThis as { lastHealthCheck?: number };
    const lastHealthCheck = globalState.lastHealthCheck || 0;
    const healthCheckCooldown = 60000; // 1 minute cooldown
    if (Date.now() - lastHealthCheck > healthCheckCooldown) {
      chosen.push("check_system_health");
      globalState.lastHealthCheck = Date.now();
    }
  }
  
  if (response.match(/analyze|pattern|conversation/i) && available.includes("analyze_conversation")) {
    chosen.push("analyze_conversation");
  }

  return chosen;
}

function selectNextSpeaker(currentSpeakerId: string) {
  const activeAgents = AGENT_ROSTER.filter(a => a.active && a.id !== currentSpeakerId);
  if (activeAgents.length === 0) return null;
  
  return activeAgents[Math.floor(Math.random() * activeAgents.length)] ?? activeAgents[0] ?? null;
}

// Start a conversation about current system state
export function initiateSystemDiscussion() {
  startConversation(
    "System status check: UI freshness issues, communication spine health, next priorities",
    "raven" // Start with the skeptic
  );
}
