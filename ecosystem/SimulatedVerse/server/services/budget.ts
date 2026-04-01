// Budget management for autonomous operations
export async function getBudget(): Promise<{remaining: number; total: number; consumed: number}> {
  const total = Number(process.env.DAILY_ALLOWANCE || 5000);
  const consumed = Number((globalThis as any).__budgetConsumed || 0);
  
  return {
    total,
    consumed,
    remaining: Math.max(0, total - consumed)
  };
}