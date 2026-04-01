import { EventEmitter } from "events";
import fs from "node:fs";
import path from "node:path";

export type ChatMessage = {
  id: string;
  ts: number;
  role: "system" | "agent" | "user";
  agent: string;
  channel: "council" | "ops" | "dev" | "game" | "sim";
  content: string;
  actions_suggested?: string[];
  actions_taken?: string[];
  artifacts?: string[];
  meta?: Record<string, any>;
};

export const councilChatBus = new EventEmitter();
const CHAT_LOG = path.resolve("public/chat-log.ndjson");
const CHAT_STATE = path.resolve("public/chat-state.json");

// In-memory chat state for SSE streaming
const chatHistory: ChatMessage[] = [];
const MAX_HISTORY = 200;

export function appendChat(msg: ChatMessage) {
  // Add to in-memory history
  chatHistory.unshift(msg);
  if (chatHistory.length > MAX_HISTORY) {
    chatHistory.length = MAX_HISTORY;
  }

  // Write to persistent log
  fs.mkdirSync(path.dirname(CHAT_LOG), { recursive: true });
  fs.appendFileSync(CHAT_LOG, JSON.stringify(msg) + "\n");
  
  // Update JSON state for polling fallback
  fs.writeFileSync(CHAT_STATE, JSON.stringify({
    last_updated: Date.now(),
    recent_messages: chatHistory.slice(0, 50)
  }, null, 2));

  // Emit for SSE streaming
  councilChatBus.emit("message", msg);
}

export function getChatHistory(limit = 50): ChatMessage[] {
  return chatHistory.slice(0, limit);
}

export function createChatMessage(
  agent: string, 
  content: string, 
  channel: "council" | "ops" | "dev" | "game" | "sim" = "council",
  role: "agent" | "system" | "user" = "agent"
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    ts: Date.now(),
    role,
    agent,
    channel,
    content,
    actions_suggested: [],
    actions_taken: [],
    artifacts: []
  };
}