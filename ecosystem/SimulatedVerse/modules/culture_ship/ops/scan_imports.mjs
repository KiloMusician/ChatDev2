export async function importAudit(scan) {
  const tasks = [];
  // Convert import issues to tasks
  for (const imp of scan.imports || []) {
    if (imp.missing) {
      tasks.push({
        kind: "surgical-edit",
        action: "fix_import_path",
        priority: 1,
        data: imp
      });
    }
  }
  return tasks;
}