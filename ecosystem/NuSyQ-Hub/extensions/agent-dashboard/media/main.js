(() => {
  const vscode = acquireVsCodeApi();

  function renderAgents(agents) {
    const el = document.getElementById('agents-list');
    if (!agents || agents.length === 0) return (el.innerHTML = '<div>No agents found</div>');
    el.innerHTML = agents
      .map(
        (a) =>
          `<div class="agent-item"><strong>${a.name || a.id || 'agent'}</strong> - ${a.status || 'unknown'}</div>`
      )
      .join('\n');
  }

  function renderQuests(quests) {
    const el = document.getElementById('quests-list');
    if (!quests || quests.length === 0) return (el.innerHTML = '<div>No quests found</div>');
    el.innerHTML = quests
      .map(
        (q) =>
          `<div class="quest-item"><strong>${q.action || q.name || q.type || 'quest'}</strong> - ${q.status || q.state || ''}</div>`
      )
      .join('\n');
  }

  function renderErrors(errors) {
    const el = document.getElementById('errors-list');
    if (!errors) return (el.textContent = 'No errors available');
    try {
      el.textContent = JSON.stringify(errors, null, 2);
    } catch {
      el.textContent = String(errors);
    }
  }

  document.getElementById('refresh').addEventListener('click', () => {
    vscode.postMessage({ command: 'requestData' });
  });

  window.addEventListener('message', (event) => {
    const msg = event.data;
    if (msg.command === 'initialData' || msg.command === 'update') {
      renderAgents(msg.payload.agents || []);
      renderQuests(msg.payload.quests || []);
      renderErrors(msg.payload.errors || null);
    }
  });

  // Request initial data
  vscode.postMessage({ command: 'requestData' });
})();
