const el = document.getElementById("app");
el.innerHTML = `
  <main class="mobile">
    <header>ΞNuSyQ — Mobile</header>
    <nav>
      <button id="btn-cascade">Cascade</button>
      <button id="btn-pause">Pause</button>
      <button id="btn-tui">Open TUI</button>
    </nav>
    <section id="pane">Welcome. Minimal, big touch targets. ASCII HUD available in TUI profile.</section>
  </main>
`;
document.getElementById("btn-cascade").onclick = () => fetch("/api/state/toggle-pause", {method:"POST"}).then(()=>alert("Cascade scheduled. Check TUI/Logs."));
document.getElementById("btn-pause").onclick = () => fetch("/api/state/toggle-pause", {method:"POST"}).then(r=>r.json()).then(s=>alert("Paused: "+s.paused));
document.getElementById("btn-tui").onclick = () => alert("Switch to the TUI profile in Replit to open ASCII cockpit.");