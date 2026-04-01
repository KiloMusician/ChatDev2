// Minimal proposal schema (patched)
import { z } from "zod";

export const Proposal = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().optional(),
  status: z.enum(['pending', 'approved', 'rejected']).default('pending'),
  created_at: z.date().optional(),
});

export type ProposalType = z.infer<typeof Proposal>;
