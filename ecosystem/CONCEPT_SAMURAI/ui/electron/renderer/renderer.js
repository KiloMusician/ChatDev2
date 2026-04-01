(async function(){
  const btnToggle = document.getElementById('btnToggle');
  const btnStatus = document.getElementById('btnStatus');
  const statusEl = document.getElementById('status');

  async function refreshStatus() {
    statusEl.textContent = 'Checking...';
    try {
      const s = await window.keeper.getListenerStatus();
      if (s.running) {
        statusEl.textContent = 'Running\n' + (s.state ? JSON.stringify(s.state, null, 2) : '(no state file)');
      } else {
        statusEl.textContent = 'Not running';
      }
    } catch (e) {
      statusEl.textContent = 'Error: ' + e.message;
    }
  }

  btnToggle.addEventListener('click', async () => {
    btnToggle.disabled = true;
    await window.keeper.toggleListener();
    await new Promise(r => setTimeout(r, 500));
    await refreshStatus();
    btnToggle.disabled = false;
  });

  btnStatus.addEventListener('click', refreshStatus);

  // initial
  refreshStatus();
})();
