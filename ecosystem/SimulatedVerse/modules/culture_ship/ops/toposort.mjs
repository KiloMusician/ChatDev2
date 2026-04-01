export function topo(tasks) {
  // Simple topological sort for task dependencies
  const sorted = [];
  const visited = new Set();
  
  function visit(task) {
    if (visited.has(task.id)) return;
    visited.add(task.id);
    
    // Visit dependencies first
    if (task.deps) {
      for (const depId of task.deps) {
        const depTask = tasks.find(t => t.id === depId);
        if (depTask) visit(depTask);
      }
    }
    
    sorted.push(task);
  }
  
  for (const task of tasks) {
    if (!task.id) task.id = `task_${Math.random().toString(36).slice(2, 8)}`;
    visit(task);
  }
  
  return sorted;
}