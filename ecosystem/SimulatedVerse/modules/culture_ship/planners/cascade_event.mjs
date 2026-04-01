export async function planCascade({ trigger, ctx }) {
  console.log(`🌊 Planning cascade for trigger: ${trigger}`);
  // Simple cascade planning - can be expanded
  return { planned: true, trigger, ctx };
}