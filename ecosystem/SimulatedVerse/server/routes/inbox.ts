// server/routes/inbox.ts
import { Router } from "express";
import { councilBus } from "../../packages/council/events/eventBus";

export const inboxRouter = Router();

inboxRouter.post("/reply", async (req, res) => {
  const { reply, to, ctx } = req.body || {};
  if (!reply || typeof reply !== "string") return res.status(400).json({ ok:false, error:"missing reply" });
  const payload = { ts: Date.now(), from: "human", to: to ?? "any", reply, ctx: ctx ?? {} };
  councilBus.publish("human.reply", payload);
  return res.json({ ok:true });
});