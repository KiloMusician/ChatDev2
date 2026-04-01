const el = document.getElementById("app");
el.innerHTML = `
  <main class="desktop">
    <header>ΞNuSyQ — Desktop</header>
    <aside>
      <ul>
        <li><a href="#" id="a-cascade">Cascade</a></li>
        <li><a href="#" id="a-pause">Toggle Pause</a></li>
        <li><a href="#" id="a-docs">Temple</a></li>
      </ul>
    </aside>
    <section id="stage">Dev dashboard here. (Add charts/logs/components as you iterate.)</section>
  </main>
`;
document.getElementById("a-cascade").onclick = () => fetch("/api/state/toggle-pause",{method:"POST"}).then(()=>alert("Cascade scheduled."));
document.getElementById("a-pause").onclick = () => fetch("/api/state/toggle-pause",{method:"POST"}).then(r=>r.json()).then(s=>alert("Paused: "+s.paused));
document.getElementById("a-docs").onclick = () => alert("Open docs/temple in the repo.");