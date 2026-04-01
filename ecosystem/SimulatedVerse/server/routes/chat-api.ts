import { Router } from "express";
import { appendChat, createChatMessage } from "../../packages/council/group-chat";
import { startConversation } from "../../packages/council/turn-engine";

export const chatApiRouter = Router();

// Handle user messages
chatApiRouter.post("/user-message", async (req, res) => {
  try {
    const { message } = req.body;
    if (!message || typeof message !== "string") {
      return res.status(400).json({ error: "Message is required" });
    }

    // Add user message to chat
    const userMessage = createChatMessage("human", message, "council", "user");
    appendChat(userMessage);

    res.json({ ok: true, message_id: userMessage.id });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

// Start agent conversation
chatApiRouter.post("/start-conversation", async (req, res) => {
  try {
    const { topic, initiator } = req.body;
    if (!topic || typeof topic !== "string") {
      return res.status(400).json({ error: "Topic is required" });
    }

    await startConversation(topic, initiator);
    
    res.json({ ok: true, topic });
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});