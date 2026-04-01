export async function suggestEdits(scan) {
  const tasks = [];
  // Simple suggestions based on scan results
  if (scan.imports?.length > 0) {
    tasks.push({
      kind: "import.fix",
      priority: 1,
      data: { imports: scan.imports.slice(0, 10) }
    });
  }
  return tasks;
}