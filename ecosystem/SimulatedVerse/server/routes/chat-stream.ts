import { Router } from "express";
import type { Request, Response } from "express";
import { councilChatBus, getChatHistory } from "../../packages/council/group-chat";

export const chatStreamRouter = Router();

const clients = new Set<Response>();

// SSE endpoint for real-time chat updates
chatStreamRouter.get("/stream", (req: Request, res: Response) => {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Access-Control-Allow-Origin": "*"
  });

  // Send recent history on connect
  const history = getChatHistory(20);
  res.write(`event: history\ndata: ${JSON.stringify(history)}\n\n`);

  // Send heartbeat
  res.write(`event: connected\ndata: ${JSON.stringify({ ts: Date.now(), msg: "Chat stream connected" })}\n\n`);

  clients.add(res);

  req.on("close", () => {
    clients.delete(res);
  });
});

// Broadcast new messages to all connected clients
councilChatBus.on("message", (message) => {
  const data = `event: message\ndata: ${JSON.stringify(message)}\n\n`;
  for (const client of clients) {
    try {
      client.write(data);
    } catch (e) {
      clients.delete(client);
    }
  }
});

// Get chat history (polling fallback)
chatStreamRouter.get("/history", (req: Request, res: Response) => {
  const limit = parseInt(req.query.limit as string) || 50;
  const history = getChatHistory(limit);
  res.json({ history });
});