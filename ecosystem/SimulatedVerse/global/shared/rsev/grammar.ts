// RSEV Grammar stub for proposal compilation
export const grammar = {
  proposal: /^proposal\s+(\w+)/,
  action: /^action\s+(\w+)/,
  condition: /^if\s+(.+)/,
  variable: /^\$(\w+)/
};

export function parseRSEV(input: string) {
  return {
    type: "rsev",
    parsed: input.split("\n").filter(Boolean),
    valid: true
  };
}

export function estimateTokens(input: string): number {
  // Simple token estimation: ~4 chars per token
  return Math.ceil(input.length / 4);
}