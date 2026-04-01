import { tokenGovernor } from './token_governor';

function assert(cond: boolean, msg: string) {
  if (!cond) {
    console.error('[test_token_governor] FAILED:', msg);
    process.exit(2);
  }
}

async function main() {
  // Ensure fresh state
  tokenGovernor.emergency();

  const stepLocal = { kind: 'search', title: 'Local search', cost: 1, local_alternative: true };
  const allowed = tokenGovernor.permit(stepLocal as any);
  assert(allowed === true, 'expected local alternative to be permitted');

  const stepPaid = { kind: 'llm', title: 'Paid LLM call', cost: 10, local_alternative: false };
  const allowedPaid = tokenGovernor.permit(stepPaid as any);
  // default_mode is 'off' so paid ops should be blocked
  assert(allowedPaid === false, 'expected paid operation to be blocked in zero-token mode');

  const usage = tokenGovernor.getUsage();
  assert(usage.used >= 1, 'usage should reflect permitted local step');

  // test escalation small auto-approve
  const escSmall = tokenGovernor.requestEscalation('small test', 2);
  assert(escSmall === true, 'small escalation should auto-approve');

  // test escalation large requires manual (returns false)
  const escLarge = tokenGovernor.requestEscalation('big test', 100);
  assert(escLarge === false, 'large escalation should not auto-approve');

  console.log('[test_token_governor] OK');
  process.exit(0);
}

main();
