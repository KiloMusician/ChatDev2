export async function dryrunGuard(task) {
  // Simple dry-run guard - always allow for now
  // Can be enhanced with more sophisticated safety checks
  console.log(`🔍 Checking task: ${task.kind}`);
  return true;
}