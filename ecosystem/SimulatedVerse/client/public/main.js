// Device & capability detector + responsive controller for the ASCII stage.

(() => {
  const $ = (q) => document.querySelector(q);
  const $$ = (q) => Array.from(document.querySelectorAll(q));
  const root = document.documentElement;
  const app  = $('#app');
  const ascii = $('#ascii');
  const stageWrap = $('#stageWrap');
  const viewLabel = $('#viewLabel');
  const modeLabel = $('#modeLabel');
  const perfLabel = $('#perfLabel');
  const dprEl = $('#dpr');
  const fpsEl = $('#fps');

  // UI Toggles
  const reduceMotion = $('#reduceMotion');
  const highContrast = $('#highContrast');
  const monospaceOnly = $('#monospaceOnly');
  const hamburger = $('#hamburger');
  const scrim = $('#scrim');
  const pauseBtn = $('#pause');

  // State
  let paused = false;
  let perfMode = 'adaptive'; // 'adaptive' | 'eco' | 'turbo'
  let last = performance.now();
  let frames = 0, lastFPS = performance.now();

  // Persisted prefs
  const getPref = (k, def) => JSON.parse(localStorage.getItem(k) ?? JSON.stringify(def));
  const setPref = (k, v) => localStorage.setItem(k, JSON.stringify(v));

  // Apply stored prefs
  (function initPrefs(){
    reduceMotion.checked = getPref('ui.reduceMotion', false);
    highContrast.checked = getPref('ui.highContrast', false);
    monospaceOnly.checked = getPref('ui.mono', false);
    if (reduceMotion.checked) root.style.setProperty('scroll-behavior','auto');
    if (highContrast.checked) document.body.classList.add('high-contrast');
    if (monospaceOnly.checked) document.body.classList.add('mono-ui');
  })();

  // Capability detection
  function detect(){
    const w = window.innerWidth, h = window.innerHeight;
    const pointer = matchMedia('(pointer:coarse)').matches ? 'coarse' : 'fine';
    const hover = matchMedia('(hover:hover)').matches ? 'hover' : 'nohover';
    const dpr = Math.round(window.devicePixelRatio * 100)/100;
    const isMobileish = w <= 960 || pointer === 'coarse';

    root.dataset.pointer = pointer;
    root.dataset.hover = hover;
    root.dataset.orientation = (w>=h?'landscape':'portrait');
    root.dataset.mobile = String(isMobileish);
    root.style.setProperty('--vw', `${w}px`);
    root.style.setProperty('--vh', `${h}px`);
    dprEl.textContent = dpr;

    // Update mode label for clarity
    modeLabel.textContent = isMobileish ? 'Mobile' : 'Desktop';
  }
  detect();
  addEventListener('resize', detect);
  addEventListener('orientationchange', detect);

  // Drawer (mobile)
  hamburger?.addEventListener('click', () => app.classList.toggle('drawer-open'));
  scrim?.addEventListener('click', () => app.classList.remove('drawer-open'));

  // Sidebar/tab buttons -> change view
  function setView(view){
    root.dataset.view = view;
    viewLabel.textContent = `View: ${view[0].toUpperCase()}${view.slice(1)}`;
    app.classList.remove('drawer-open');
    // Let the ASCII stage know to redraw with different content
    if (window.ASCII_STAGE) window.ASCII_STAGE.setScene(view);
  }
  $$('#sidebar .nav-btn, .tabbar .tab').forEach(btn => {
    btn.addEventListener('click', () => setView(btn.dataset.view));
  });

  // Pref toggles
  reduceMotion.addEventListener('change', () => {
    setPref('ui.reduceMotion', reduceMotion.checked);
    // notify stage
    if (window.ASCII_STAGE) window.ASCII_STAGE.setReduceMotion(reduceMotion.checked);
  });
  highContrast.addEventListener('change', () => {
    setPref('ui.highContrast', highContrast.checked);
    document.body.classList.toggle('high-contrast', highContrast.checked);
  });
  monospaceOnly.addEventListener('change', () => {
    setPref('ui.mono', monospaceOnly.checked);
    document.body.classList.toggle('mono-ui', monospaceOnly.checked);
  });

  // Pause/Resume
  pauseBtn.addEventListener('click', () => {
    paused = !paused;
    pauseBtn.textContent = paused ? '▶️' : '⏸';
    if (!paused && window.ASCII_STAGE) window.ASCII_STAGE.tick(); // kick
  });

  // Performance governor (simple & effective)
  function perfLoop(now){
    if (paused) { requestAnimationFrame(perfLoop); return; }

    frames++;
    if (now - lastFPS >= 1000){
      fpsEl.textContent = frames.toString().padStart(2,' ');
      // adapt perf mode
      if (frames < 24) perfMode = 'eco';
      else if (frames > 55) perfMode = 'turbo';
      else perfMode = 'adaptive';
      perfLabel.textContent = perfMode[0].toUpperCase() + perfMode.slice(1);
      if (window.ASCII_STAGE) window.ASCII_STAGE.setPerfMode(perfMode);
      frames = 0; lastFPS = now;
    }
    if (window.ASCII_STAGE) window.ASCII_STAGE.tick(now);
    requestAnimationFrame(perfLoop);
  }

  // Initialize stage
  window.addEventListener('DOMContentLoaded', () => {
    if (window.ASCII_STAGE) {
      window.ASCII_STAGE.mount(ascii, stageWrap);
      window.ASCII_STAGE.setReduceMotion(reduceMotion.checked);
      window.ASCII_STAGE.tick(); // seed
      requestAnimationFrame(perfLoop);
    }
  });

  // Keyboard quick switches (desktop)
  addEventListener('keydown', (e) => {
    if (e.key === ' ') { e.preventDefault(); pauseBtn.click(); }
    const map = { '1':'base','2':'map','3':'colony','4':'defense','5':'logs' };
    if (map[e.key]) setView(map[e.key]);
  });
})();