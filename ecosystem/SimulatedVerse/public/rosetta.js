(async function(){
  const res = await fetch("/knowledge/rosetta/tiers.min.json").catch(()=>null);
  const data = res && res.ok ? await res.json() : {tiers:[]};
  const tiers = data.tiers || [];
  const list = document.getElementById("list");
  const search = document.getElementById("search");
  const render = () => {
    const q = (search.value||"").toLowerCase();
    list.innerHTML = "";
    tiers.filter(t => {
      if (!q) return true;
      const hay = [t.title, String(t.tier), ...(t.nodes||[]).map(n=>n.slug)].join(" ").toLowerCase();
      return hay.includes(q);
    }).forEach(t=>{
      const div = document.createElement("div"); div.className="card";
      div.innerHTML = `
        <div class="title">Tier ${t.tier}: ${t.title}</div>
        <div class="meta">${t.development_insight ? t.development_insight.split("\n")[0] : "—"}</div>
        <div class="nodes">${(t.nodes||[]).map(n=>n.slug).slice(0,8).join(" · ")}</div>
      `;
      list.appendChild(div);
    });
  };
  search.addEventListener("input", render); render();
})();