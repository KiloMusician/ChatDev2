export async function findDuplicates(scan) {
  const tasks = [];
  // Simple duplicate detection
  if (scan.duplicates?.length > 0) {
    tasks.push({
      kind: "duplicate.remove",
      priority: 2,
      data: { duplicates: scan.duplicates }
    });
  }
  return tasks;
}