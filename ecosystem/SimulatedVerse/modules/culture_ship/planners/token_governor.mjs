export const tokenGovernor = {
  currentBudget() {
    const cap = Number(process.env.TOKEN_BUDGET_CAP ?? "0"); // default 0 = free-only
    const left = Number(process.env.TOKENS_LEFT ?? "0");
    return {
      enforceFrugality: left <= cap,
      maySpend: (need) => left - need >= 0 && need <= (Number(process.env.TOKEN_SPEND_PER_OP ?? "0")),
    };
  }
};