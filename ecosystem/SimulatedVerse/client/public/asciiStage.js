// Lightweight, DPI-aware ASCII renderer with adaptive scaling & scenes.
window.ASCII_STAGE = (() => {
  let pre, wrap;
  let reduceMotion = false;
  let perfMode = 'adaptive';
  let scene = 'base';
  let t = 0;

  // Compute monospace metrics to scale text to viewport width without blur
  function measureMono(preEl){
    const test = document.createElement('span');
    test.textContent = 'MMMMMMMMMM';
    test.style.font = getComputedStyle(preEl).font;
    preEl.appendChild(test);
    const w = test.getBoundingClientRect().width / 10;
    preEl.removeChild(test);
    return { cw: w }; // char width
  }

  function fit(){
    if (!pre || !wrap) return;
    const { width: W, height: H } = wrap.getBoundingClientRect();
    const { cw } = measureMono(pre);
    // Aim for ~80 cols on phone, ~120 on desktop (feel free to tweak)
    const targetCols = (document.documentElement.dataset.mobile === 'true') ? 80 : 120;
    const fontSize = Math.max(10, Math.floor((W / (targetCols * cw))));
    pre.style.fontSize = `${fontSize}px`;
    // Scale down if height is too tight
    const lines = pre.textContent.split('\n').length;
    const lineH = fontSize * 1.0; // matches CSS line-height
    const contentH = lines * lineH + 16; // with padding
    const scale = contentH > H ? Math.max(0.6, H / contentH) : 1;
    pre.style.transform = `scale(${scale})`;
  }

  // Simple scenes: base, map, colony, defense, logs
  function render(now = 0){
    t = now / 1000;
    const wave = (n, charA='░', charB='▒') => (Math.sin(t*2 + n) > 0 ? charA : charB);

    let out = '';
    if (scene === 'base'){
      out = drawPanel('BASE BUILDER', [
        `Workers:   ${spark(32)}  Energy: ${spark(48)}`,
        `Materials: ${bar(40, 23)}  Alloy:  ${bar(24, 9)}`,
        '',
        waveLine(64),
        `Blueprint: ${wave(0.0,'╴','╶')} Grid ${wave(1.0,'╴','╶')} Rooms ${wave(2.0,'╴','╶')} Routes`,
        waveLine(64),
      ]) + '\n' + grid(32, 12, t);
    }
    else if (scene === 'map'){
      out = drawPanel('WORLD MAP', [
        `Explorers: ${spark(18)}  Beacons: ${spark(6)}`,
        '',
      ]) + '\n' + noiseMap(64, 18, t);
    }
    else if (scene === 'colony'){
      out = drawPanel('COLONY', [
        `Population: ${bar(30, 22)}  Mood: ${spark(10)}`,
        `Food:       ${bar(20, 17)}  Water: ${bar(20, 19)}`
      ]) + '\n' + cityBlock(60, 16, t);
    }
    else if (scene === 'defense'){
      out = drawPanel('DEFENSE GRID', [
        `Cores: ${spark(12)}  Towers: ${spark(8)}  Paths: ${spark(5)}`
      ]) + '\n' + lanes(62, 18, t, perfMode);
    }
    else if (scene === 'logs'){
      out = drawLog([
        `[${stamp()}] Cascade: benchmarking mobile layout…`,
        `[${stamp()}] Auto-governor: perf=${perfMode} reducedMotion=${reduceMotion}`,
        `[${stamp()}] Hint: tap ①②③④⑤ or sidebar to switch views; Space = pause.`,
      ]);
    }

    pre.textContent = out;
    fit();
  }

  // Helpers for ASCII content
  function drawPanel(title, lines){
    const width = Math.max(title.length+6, ...lines.map(l => l.length)) + 2;
    const top = `╭${'─'.repeat(width)}╮`;
    const mid = `│  ${title.padEnd(width-2,' ')} │`;
    const body = lines.map(l => `│ ${l.padEnd(width,' ')}│`).join('\n');
    const bot = `╰${'─'.repeat(width)}╯`;
    return [top, mid, body, bot].join('\n');
  }
  function drawLog(rows){
    const width = Math.max(...rows.map(r => r.length), 32);
    const header = `╔ LOG ${'═'.repeat(Math.max(0,width-6))}╗`;
    const body = rows.map(r => `║ ${r.padEnd(width-2,' ')} ║`).join('\n');
    const footer = `╚${'═'.repeat(width+2)}╝`;
    return [header, body, footer].join('\n');
  }
  const stamp = () => new Date().toLocaleTimeString();
  const spark = (n) => '█'.repeat(n % 10).padEnd(10,'·');
  const bar = (w, v) => `[${'■'.repeat(v)}${' '.repeat(Math.max(0, w - v))}]`;
  const waveLine = (w) => Array.from({length:w}, (_,i)=> (Math.sin((i/5)+t*3)>0?'~':'-')).join('');
  function grid(w,h,time){
    let s=''; for(let y=0;y<h;y++){ let row=''; for(let x=0;x<w;x++){
      const pulse = Math.sin(time*2 + (x+y)*0.2)>0 ? '·':' ';
      row += (x%4===0||y%3===0) ? (pulse) : ' ';
    } s+=row+'\n';} return s;
  }
  function noiseMap(w,h,time){
    let s=''; for(let y=0;y<h;y++){ let row=''; for(let x=0;x<w;x++){
      const v = Math.sin(x*.25+time*0.6)+Math.cos(y*.3+time*0.5);
      row += v>1 ? '▲' : v>0.25 ? '░' : v>-0.75 ? '·' : '≈';
    } s+=row+'\n';} return s;
  }
  function cityBlock(w,h,time){
    let s=''; for(let y=0;y<h;y++){ let row=''; for(let x=0;x<w;x++){
      const v = (x%8===0 || y%4===0) ? '│' : (Math.sin((x+y+time*3)*.3)>0?'▢':' ');
      row += v;
    } s+=row+'\n'; } return s;
  }
  function lanes(w,h,time,mode){
    const density = mode==='turbo'? 0.9 : mode==='eco'? 0.4 : 0.65;
    let s=''; for(let y=0;y<h;y++){
      let row=''; for(let x=0;x<w;x++){
        const lane = (y%4===0);
        if (lane) row += '═';
        else {
          const v = Math.random();
          row += v < density*0.02 ? '•' : ' ';
        }
      } s+=row+'\n';
    } return s;
  }

  // Public API
  return {
    mount(preEl, wrapEl){ pre = preEl; wrap = wrapEl; addEventListener('resize', fit); },
    setScene(v){ scene = v; render(performance.now()); },
    setReduceMotion(v){ reduceMotion = v; },
    setPerfMode(v){ perfMode = v; },
    tick(now){ if (reduceMotion) { if ((now|0)%500<16) render(now); } else { render(now); } },
  };
})();