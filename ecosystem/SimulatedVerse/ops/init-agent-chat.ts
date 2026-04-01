// Initialize agent chat system
import { appendChat, createChatMessage } from "../packages/council/group-chat";
import { initiateSystemDiscussion } from "../packages/council/turn-engine";

// Send system startup message
appendChat(createChatMessage(
  "system",
  "🚀 Agent chat system initialized. Real-time conversations enabled.",
  "council",
  "system"
));

// Wait a moment, then start initial discussion
setTimeout(() => {
  console.log("[AgentChat] Starting initial system discussion...");
  initiateSystemDiscussion();
}, 2000);

console.log("[AgentChat] Initialization complete");