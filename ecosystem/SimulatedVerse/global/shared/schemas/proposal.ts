import { z } from "zod";

export const Proposal = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  type: z.enum(["enhancement", "fix", "feature", "refactor"]),
  priority: z.enum(["low", "medium", "high", "critical"]),
  status: z.enum(["draft", "review", "approved", "rejected", "implemented"]),
  author: z.string(),
  createdAt: z.number(),
  updatedAt: z.number(),
  metadata: z.record(z.any()).optional()
});

export type Proposal = z.infer<typeof Proposal>;