/**
 * Terminal Depths — Panel Evolution System v1
 * ════════════════════════════════════════════════════════════════════════════
 * Compression Ladder: panels unlock as the player grows.
 * Drag-resize, 4 themes, 5 new panels, API sync, layout persistence.
 *
 * Designed to augment game.js without touching it. Loaded AFTER game.js.
 * All state lives in: window._panelSys (singleton)
 */

(function () {

  // ── Wait for game.js systems to initialise ──────────────────────────────
  function _ready(fn) {
    if (window._game && window._game.gs) fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  // ── Constants ─────────────────────────────────────────────────────────
  const STORAGE_KEY_THEME  = 'td_theme';
  const STORAGE_KEY_WIDTH  = 'td_panel_width';
  const STORAGE_KEY_TAB    = 'td_active_tab';

  // ── Compression ladder unlock table ───────────────────────────────────
  // Tabs that exist from the start of game.js are "core" — we extend them.
  // New panels are injected dynamically when the player reaches the level.
  const PANEL_UNLOCKS = [
    // tab-id          | min-level | hint text (shown while locked)
    { id: 'objective',  minLevel: 1,  label: 'OBJ',     title: 'Objectives',          alwaysOn: true },
    { id: 'stats',      minLevel: 1,  label: 'STATS',   title: 'Statistics',          alwaysOn: true },
    { id: 'tutorial',   minLevel: 1,  label: 'TUT',     title: 'Tutorial',            alwaysOn: true },
    { id: 'challenges', minLevel: 1,  label: 'CHAL',    title: 'Challenges',          alwaysOn: true },
    { id: 'lore',       minLevel: 2,  label: 'LORE',    title: 'Lore Library',        alwaysOn: false, hint: 'Reach Lv 2' },
    { id: 'map',        minLevel: 3,  label: 'MAP',     title: 'Network Map',         alwaysOn: false, hint: 'Reach Lv 3' },
    { id: 'timeline',   minLevel: 5,  label: 'LOG',     title: 'Event Timeline',      alwaysOn: false, hint: 'Reach Lv 5' },
    { id: 'skills',     minLevel: 7,  label: 'TREE',    title: 'Skill Tree',          alwaysOn: false, hint: 'Reach Lv 7' },
    { id: 'quest',      minLevel: 2,  label: 'QUEST',   title: 'Quest Board',         alwaysOn: false, hint: 'Reach Lv 2' },
    // ── NEW panels injected by this file ──────────────────────────────
    { id: 'faction',    minLevel: 4,  label: 'FAC',     title: 'Faction Status',      alwaysOn: false, hint: 'Reach Lv 4', injected: true },
    { id: 'agents',     minLevel: 12, label: 'AGENTS',  title: 'Agent Leaderboard',   alwaysOn: false, hint: 'Reach Lv 12', injected: true },
    { id: 'inventory',  minLevel: 1,  label: 'INV',     title: 'Inventory',           alwaysOn: true,  injected: true },
    { id: 'achievements', minLevel: 1, label: 'ACH',   title: 'Achievements',        alwaysOn: true,  injected: true },
    { id: 'compress',   minLevel: 20, label: 'Ξ COMP', title: 'Compression Engine',  alwaysOn: false, hint: 'Reach Lv 20', injected: true },
    { id: 'cmdlog',     minLevel: 1,  label: 'CMD',    title: 'Command Log',         alwaysOn: true,  injected: true },
    { id: 'convlog',    minLevel: 1,  label: 'MSGS',   title: 'Agent Messages',      alwaysOn: true,  injected: true },
  ];

  // ── Themes ────────────────────────────────────────────────────────────
  const THEMES = {
    cyberpunk: {
      label: 'CYBERPUNK',
      vars: {
        '--bg': '#080d16', '--bg2': '#0c1221', '--bg3': '#111927',
        '--border': '#1a3358', '--border2': '#224070',
        '--cyan': '#00d4ff', '--green': '#00ff88', '--yellow': '#ffcc00',
        '--red': '#ff4040', '--orange': '#ff8800', '--purple': '#bb55ff',
        '--pink': '#ff44bb', '--white': '#c8d8ec', '--dim': '#3a5575', '--dim2': '#2a3f55',
      },
    },
    matrix: {
      label: 'MATRIX',
      vars: {
        '--bg': '#000d00', '--bg2': '#001400', '--bg3': '#001a00',
        '--border': '#004400', '--border2': '#007700',
        '--cyan': '#00ff41', '--green': '#00ff41', '--yellow': '#88ff44',
        '--red': '#ff2200', '--orange': '#88ff00', '--purple': '#33ff88',
        '--pink': '#00ff88', '--white': '#88cc88', '--dim': '#224422', '--dim2': '#113311',
      },
    },
    amber: {
      label: 'AMBER',
      vars: {
        '--bg': '#110a00', '--bg2': '#1a0e00', '--bg3': '#201200',
        '--border': '#442200', '--border2': '#664400',
        '--cyan': '#ffaa00', '--green': '#ff8800', '--yellow': '#ffcc44',
        '--red': '#ff3300', '--orange': '#ffaa22', '--purple': '#ff6644',
        '--pink': '#ff4400', '--white': '#cc8844', '--dim': '#442200', '--dim2': '#331a00',
      },
    },
    ice: {
      label: 'ICE',
      vars: {
        '--bg': '#020b18', '--bg2': '#050e1f', '--bg3': '#071226',
        '--border': '#0d2444', '--border2': '#153060',
        '--cyan': '#88ddff', '--green': '#44bbff', '--yellow': '#aaccff',
        '--red': '#ff6688', '--orange': '#66aaff', '--purple': '#8888ff',
        '--pink': '#aa88ff', '--white': '#aabbcc', '--dim': '#2a4466', '--dim2': '#1a3055',
      },
    },
  };

  // ── Helpers ───────────────────────────────────────────────────────────
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function saveLayout(panelWidth) {
    try {
      if (panelWidth !== undefined) localStorage.setItem(STORAGE_KEY_WIDTH, String(panelWidth));
    } catch (_) {}
  }

  function loadLayout() {
    try {
      return {
        width: parseInt(localStorage.getItem(STORAGE_KEY_WIDTH) || '288', 10),
        tab:   localStorage.getItem(STORAGE_KEY_TAB) || 'objective',
        theme: localStorage.getItem(STORAGE_KEY_THEME) || 'cyberpunk',
      };
    } catch (_) { return { width: 288, tab: 'objective', theme: 'cyberpunk' }; }
  }

  // ── Theme system ──────────────────────────────────────────────────────
  function applyTheme(name, { silent = false } = {}) {
    const theme = THEMES[name] || THEMES.cyberpunk;
    const root  = document.documentElement;
    Object.entries(theme.vars).forEach(([k, v]) => root.style.setProperty(k, v));
    document.body.dataset.theme = name;
    try { localStorage.setItem(STORAGE_KEY_THEME, name); } catch (_) {}

    // Update theme button label
    const btn = document.getElementById('btn-theme');
    if (btn) btn.textContent = theme.label;

    if (!silent) {
      document.dispatchEvent(new CustomEvent('td:toast', { detail: { msg: `Theme: ${theme.label}`, type: 'unlock' } }));
    }
  }

  function cycleTheme() {
    const keys = Object.keys(THEMES);
    const cur  = document.body.dataset.theme || 'cyberpunk';
    const next = keys[(keys.indexOf(cur) + 1) % keys.length];
    applyTheme(next);
  }

  // ── Tab unlock / injection ────────────────────────────────────────────
  let _lastUnlockedLevel = 0;

  function getPlayerLevel() {
    if (!window._game || !window._game.gs) return 1;
    return window._game.gs.getState().level || 1;
  }

  function injectMissingTabs(tabsEl) {
    PANEL_UNLOCKS.filter(p => p.injected).forEach(p => {
      if (!document.querySelector(`.tab[data-tab="${p.id}"]`)) {
        const t = document.createElement('div');
        t.className = 'tab tab-injected';
        t.dataset.tab = p.id;
        t.dataset.unlock = p.minLevel;
        t.setAttribute('role', 'tab');
        t.setAttribute('aria-selected', 'false');
        t.setAttribute('tabindex', '-1');
        t.textContent = p.label;
        t.title = p.title;
        tabsEl.appendChild(t);
        t.addEventListener('click', () => {
          if (parseInt(t.dataset.unlock, 10) <= getPlayerLevel()) {
            sys.renderPanel(p.id);
          } else {
            document.dispatchEvent(new CustomEvent('td:toast', {
              detail: { msg: `🔒 ${p.title} — ${p.hint}`, type: 'warn' }
            }));
          }
        });
      }
    });
  }

  function refreshTabVisibility() {
    const level = getPlayerLevel();
    if (level === _lastUnlockedLevel) return;

    PANEL_UNLOCKS.forEach(p => {
      const tab = document.querySelector(`.tab[data-tab="${p.id}"]`);
      if (!tab) return;
      const unlocked = level >= p.minLevel;
      tab.classList.toggle('tab-locked', !unlocked);
      tab.classList.toggle('tab-unlocked', unlocked);
      tab.title = unlocked ? p.title : `${p.title} — ${p.hint}`;

      if (!unlocked && tab.classList.contains('active')) {
        // Was active but now locked (shouldn't happen but guard it)
        sys.renderPanel('objective');
      }

      // Announce fresh unlock
      if (unlocked && level > _lastUnlockedLevel && level === p.minLevel && !p.alwaysOn) {
        document.dispatchEvent(new CustomEvent('td:toast', {
          detail: { msg: `🔓 PANEL UNLOCKED: ${p.title}`, type: 'unlock' }
        }));
      }
    });

    _lastUnlockedLevel = level;
  }

  // ── Drag-resize between terminal and right panel ───────────────────────
  function initDragResize(handle, termPanel, rightPanel) {
    let dragging = false;
    let startX   = 0;
    let startW   = 0;

    handle.addEventListener('mousedown', (e) => {
      dragging = true;
      startX   = e.clientX;
      startW   = rightPanel.offsetWidth;
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const delta = startX - e.clientX;
      const newW  = Math.max(200, Math.min(600, startW + delta));
      rightPanel.style.width = newW + 'px';
      saveLayout(newW);
    });

    document.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    });

    // Touch support
    handle.addEventListener('touchstart', (e) => {
      dragging = true;
      startX   = e.touches[0].clientX;
      startW   = rightPanel.offsetWidth;
      e.preventDefault();
    }, { passive: false });

    document.addEventListener('touchmove', (e) => {
      if (!dragging) return;
      const delta = startX - e.touches[0].clientX;
      const newW  = Math.max(200, Math.min(600, startW + delta));
      rightPanel.style.width = newW + 'px';
      saveLayout(newW);
    }, { passive: true });

    document.addEventListener('touchend', () => { dragging = false; });
  }

  // ── Panel renders ─────────────────────────────────────────────────────

  function renderFactionPanel(gs, tabContent) {
    const state = gs.getState();
    const faction = state.faction;
    const rep = state.factionReputation || {};

    const factions = [
      { id: 'resistance',  name: 'The Resistance',   color: '#ff8800', icon: '⚡', desc: 'Fight NexusCorp. Protect the grid.' },
      { id: 'nexuscorp',   name: 'NexusCorp',         color: '#00d4ff', icon: '▣', desc: 'Power. Control. Profit.' },
      { id: 'booleanmonks',name: 'Boolean Monks',     color: '#bb55ff', icon: '∅', desc: 'Logic as religion. Truth as law.' },
      { id: 'serialists',  name: 'The Serialists',    color: '#ff44bb', icon: '≋', desc: 'Sequence is sacred.' },
      { id: 'atonalcult',  name: 'Atonal Cult',       color: '#88ff00', icon: '♩', desc: 'Chaos as music. Music as power.' },
      { id: 'algoguild',   name: 'Algorithmic Guild', color: '#ffcc00', icon: '⚙', desc: 'Efficiency is the only virtue.' },
    ];

    const rows = factions.map(f => {
      const r    = rep[f.id] || 0;
      const pct  = Math.max(0, Math.min(100, r));
      const mine = faction === f.id;
      return `
        <div class="fac-row${mine ? ' fac-active' : ''}">
          <div class="fac-header">
            <span class="fac-icon" style="color:${f.color};">${f.icon}</span>
            <span class="fac-name" style="color:${mine ? f.color : 'var(--white)'};">${f.name}${mine ? ' ★' : ''}</span>
            <span class="fac-rep" style="color:${f.color};">${r > 0 ? '+' : ''}${r}</span>
          </div>
          <div class="fac-bar-track">
            <div class="fac-bar-fill" style="width:${pct}%;background:${f.color};"></div>
          </div>
          <div class="fac-desc">${f.desc}</div>
        </div>`;
    }).join('');

    tabContent.innerHTML = `
      <div class="stat-section">
        <div class="stat-label">Your Faction</div>
        ${faction
          ? `<div class="fac-chosen">${faction.toUpperCase()}</div>`
          : `<div style="color:var(--dim);font-size:10px;">No faction chosen. Type <code>faction</code> to join.</div>`}
      </div>
      <div class="stat-section">
        <div class="stat-label">Reputation Matrix</div>
        ${rows}
      </div>
      <div class="stat-section">
        <div class="stat-label">Quick Actions</div>
        <div class="panel-actions">
          <button class="panel-btn" data-cmd="faction">View Factions</button>
          <button class="panel-btn" data-cmd="faction join resistance">Join Resistance</button>
          <button class="panel-btn" data-cmd="faction join nexuscorp">Join NexusCorp</button>
        </div>
      </div>`;
  }

  let _leaderboardCache = null;
  let _leaderboardFetched = 0;

  async function renderAgentsPanel(tabContent) {
    const now = Date.now();
    let data = null;

    if (_leaderboardCache && (now - _leaderboardFetched < 60_000)) {
      data = _leaderboardCache;
    } else {
      tabContent.innerHTML = '<div style="color:var(--dim);padding:12px;font-size:11px;">Loading agent leaderboard…</div>';
      try {
        const r = await fetch('/api/agent/leaderboard');
        if (r.ok) {
          data = await r.json();
          _leaderboardCache = data;
          _leaderboardFetched = now;
        }
      } catch (_) { data = null; }
    }

    const rows = (data && data.leaderboard && data.leaderboard.length)
      ? data.leaderboard.slice(0, 12).map((a, i) => {
          const medal = ['🥇','🥈','🥉'][i] || `${i+1}.`;
          const typeColor = {
            claude:'#bb55ff', copilot:'#00d4ff', gordon:'#ff8800',
            human:'#00ff88', ollama:'#ffcc00',
          }[a.agent_type] || '#88aacc';
          return `
            <div class="agent-card">
              <span class="agent-rank">${medal}</span>
              <span class="agent-name" style="color:${typeColor};">${esc(a.name)}</span>
              <span class="agent-type" style="color:var(--dim);">[${esc(a.agent_type || 'agent')}]</span>
              <span class="agent-xp" style="color:var(--yellow);">${a.xp || 0} XP</span>
            </div>`;
        }).join('')
      : '<div style="color:var(--dim);font-size:10px;padding:4px;">No agents registered yet.<br>Type <code>agent register</code> to be first.</div>';

    tabContent.innerHTML = `
      <div class="stat-section">
        <div class="stat-label">Agent Leaderboard <span style="color:var(--dim);font-size:9px;">(auto-refresh 60s)</span></div>
        <div class="agent-list">${rows}</div>
      </div>
      <div class="stat-section">
        <div class="stat-label">Agent Integration</div>
        <div style="font-size:10px;color:var(--dim);line-height:1.7;">
          Any AI can play Terminal Depths.<br>
          <code>POST /api/agent/register</code><br>
          <code>python bootstrap/td_quickstart.py</code>
        </div>
      </div>
      <div class="stat-section">
        <div class="panel-actions">
          <button class="panel-btn" data-cmd="agent list">Agent List</button>
          <button class="panel-btn" data-cmd="agent leaderboard">In-game LB</button>
          <button class="panel-btn" data-cmd="score">My Score</button>
        </div>
      </div>`;
  }

  function renderInventoryPanel(gs, tabContent) {
    const state = gs.getState();
    const items = state.inventory || [];
    const cards  = state.hackCards || [];
    const dp     = state.swarmDp || state.dp || 0;
    const echoFr = state.echoFragments || 0;

    const ITEM_ICONS = {
      chimera_fragment: { icon: '◈', color: '#ff4040', label: 'CHIMERA Fragment' },
      darknet_tool:     { icon: '⚒', color: '#bb55ff', label: 'Darknet Tool' },
      master_key:       { icon: '🗝', color: '#ffcc00', label: 'Master Key' },
      nova_key:         { icon: '⚡', color: '#00d4ff', label: 'Nova Private Key' },
      echo_fragment:    { icon: '◇', color: '#ff44bb', label: 'Echo Fragment' },
    };

    const itemRows = items.length
      ? items.map(it => {
          const def = ITEM_ICONS[it] || { icon: '▪', color: 'var(--dim)', label: it.replace(/_/g,' ') };
          return `<div class="inv-item"><span style="color:${def.color};">${def.icon}</span> <span>${def.label}</span></div>`;
        }).join('')
      : '<div style="color:var(--dim);font-size:10px;">No items. Explore to find them.</div>';

    const cardRows = cards.length
      ? cards.map(c => `<div class="inv-item"><span style="color:#ff4040;">🃏</span> <span style="color:#ff8800;">${esc(c)}</span></div>`).join('')
      : '';

    tabContent.innerHTML = `
      <div class="stat-section">
        <div class="stat-label">Resources</div>
        <div class="activity-grid" style="margin-bottom:8px;">
          <span style="color:var(--dim);">Dev Points</span><span style="color:var(--yellow);">${dp} DP</span>
          <span style="color:var(--dim);">Echo Frags</span><span style="color:#ff44bb;">${echoFr}</span>
        </div>
      </div>
      <div class="stat-section">
        <div class="stat-label">Items</div>
        <div class="inv-list">${itemRows}</div>
      </div>
      ${cards.length ? `
      <div class="stat-section">
        <div class="stat-label">Hack Card Deck</div>
        <div class="inv-list">${cardRows}</div>
      </div>` : ''}
      <div class="stat-section">
        <div class="panel-actions">
          <button class="panel-btn" data-cmd="swarm status">Swarm Status</button>
          <button class="panel-btn" data-cmd="deck">Card Deck</button>
          <button class="panel-btn" data-cmd="darknet market">Darknet</button>
        </div>
      </div>`;
  }

  function renderAchievementsPanel(gs, tabContent) {
    const state = gs.getState();
    const earned = state.achievements ? [...state.achievements] : [];
    const totalCmds = state.commandsRun || 0;

    const KNOWN_ACHS = [
      { id:'root_obtained',        icon:'🔴', label:'Root Shell',          color:'#ff4040' },
      { id:'chimera_connected',     icon:'◈',  label:'CHIMERA Contact',     color:'#ff8800' },
      { id:'chimera_exploited',     icon:'💥', label:'CHIMERA Exploited',   color:'#ff4040' },
      { id:'mole_exposed',          icon:'🔍', label:'Mole Exposed',        color:'#ffcc00' },
      { id:'faction_joined',        icon:'⚡', label:'Faction Member',      color:'#00ff88' },
      { id:'first_ascension',       icon:'♾',  label:'First Ascension',     color:'#bb55ff' },
      { id:'prestige_unlocked',     icon:'★',  label:'Prestige Unlocked',   color:'#ffcc00' },
      { id:'watcher_contact',       icon:'👁',  label:'Watcher Contact',     color:'#00d4ff' },
      { id:'met_watcher',           icon:'∅',  label:'Watcher Met',         color:'#bb55ff' },
      { id:'zero_diary_reconstructed', icon:'📓', label:"Zero's Diary",      color:'#ff44bb' },
      { id:'ada_sacrifice_complete',icon:'💔', label:"Ada's Arc",           color:'#ff8800' },
      { id:'crypto_challenge_solved', icon:'🔑', label:'Crypto Cracker',    color:'#00d4ff' },
      { id:'packet_crafted_sent',   icon:'📡', label:'Packet Architect',    color:'#00ff88' },
      { id:'darknet_visited',       icon:'🌑', label:'Darknet Visitor',     color:'#bb55ff' },
      { id:'first_forensics',       icon:'🔬', label:'First Forensics',     color:'#88aaff' },
      { id:'compression_neutronized', icon:'Ξ', label:'Neutron Compressed', color:'#00d4ff' },
      { id:'culture_ship_arrived',  icon:'🚀', label:'Culture Contact',     color:'#44ff88' },
      { id:'arg_signal_1337',       icon:'📻', label:'ARG: Signal 1337',    color:'#ff44bb' },
      { id:'fifth_layer_reached',   icon:'∞',  label:'Fifth Layer',         color:'#bb55ff' },
    ];

    const earnedSet = new Set(earned);
    const pct = KNOWN_ACHS.length ? Math.round(earnedSet.size / KNOWN_ACHS.length * 100) : 0;

    const grid = KNOWN_ACHS.map(a => {
      const done = earnedSet.has(a.id);
      return `<div class="ach-badge ${done ? 'ach-done' : 'ach-locked'}" title="${done ? a.label : '???'}">
        <div class="ach-badge-icon" style="color:${done ? a.color : 'var(--dim2)'};">${done ? a.icon : '○'}</div>
        <div class="ach-badge-label" style="color:${done ? a.color : 'var(--dim2)'};">${done ? a.label : '???'}</div>
      </div>`;
    }).join('');

    // Unknown earned ones (not in known list)
    const unknownEarned = earned.filter(a => !KNOWN_ACHS.find(k => k.id === a));
    const extra = unknownEarned.map(a =>
      `<div class="ach-item" style="color:var(--cyan);">⬡ ${esc(a.replace(/_/g,' '))}</div>`
    ).join('');

    tabContent.innerHTML = `
      <div class="stat-section">
        <div class="stat-label">Achievement Gallery — ${earnedSet.size}/${KNOWN_ACHS.length} (${pct}%)</div>
        <div class="xp-bar-track" style="margin-bottom:10px;">
          <div style="height:100%;background:var(--yellow);width:${pct}%;border-radius:2px;transition:width 0.5s;"></div>
        </div>
        <div class="ach-grid">${grid}</div>
        ${extra ? `<div class="stat-label" style="margin-top:10px;">Secret Achievements</div>${extra}` : ''}
      </div>
      <div class="stat-section">
        <div class="stat-label">Activity</div>
        <div class="activity-grid">
          <span style="color:var(--dim);">Commands run</span><span style="color:var(--cyan);">${totalCmds}</span>
          <span style="color:var(--dim);">Achievements</span><span style="color:var(--yellow);">${earnedSet.size}</span>
        </div>
      </div>`;
  }

  // ── CMD LOG panel ──────────────────────────────────────────────────────────
  function renderCmdLogPanel(tabContent) {
    const log = (window._TD && window._TD.cmdLog) ? window._TD.cmdLog : [];
    if (!log.length) {
      tabContent.innerHTML = '<div class="cmdlog-empty">No commands yet.<br>Start typing — your history builds here.</div>';
      return;
    }
    const rows = log.slice().reverse().map(entry => {
      const time = new Date(entry.t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      return `<div class="cmdlog-row" data-cmd="${esc(entry.cmd)}">
        <span class="cmdlog-time">${esc(time)}</span>
        <span class="cmdlog-cmd">${esc(entry.cmd)}</span>
      </div>`;
    }).join('');
    tabContent.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 8px 2px;">
        <span class="stat-label" style="margin:0;">Recent Commands</span>
        <span style="color:var(--dim);font-size:9px;">${log.length}/50 — click to fill · dblclick to run</span>
      </div>
      <div class="cmdlog-list">${rows}</div>`;
    tabContent.querySelectorAll('.cmdlog-row').forEach(row => {
      const cmd = row.dataset.cmd;
      row.addEventListener('click', () => {
        const inp = document.getElementById('terminal-input');
        if (inp) { inp.value = cmd; inp.focus(); }
      });
      row.addEventListener('dblclick', () => {
        if (window._game && window._game.runCommand) window._game.runCommand(cmd);
      });
    });
  }

  // ── CONV LOG panel ─────────────────────────────────────────────────────────
  const _NPC_COLOR_MAP = {
    ada: '#ff8800', watcher: '#aa44ff', raven: '#00d4ff',
    cypher: '#00ff88', gordon: '#ffcc00', nova: '#ff44bb',
    serena: '#ff44bb', unknown: '#88aacc',
  };

  function renderConvLogPanel(tabContent) {
    const log = (window._TD && window._TD.convLog) ? window._TD.convLog : [];
    if (!log.length) {
      tabContent.innerHTML = '<div class="convlog-empty">No messages yet.<br>Talk to an agent — try: <code>talk ada</code></div>';
      return;
    }
    const rows = log.slice().reverse().map(entry => {
      const time  = new Date(entry.t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const npcId = (entry.npc || 'unknown').toLowerCase();
      const color = _NPC_COLOR_MAP[npcId] || 'var(--orange)';
      return `<div class="convlog-entry">
        <div class="convlog-header">
          <span class="convlog-npc" style="color:${esc(color)};">[${esc(entry.npc || '?')}]</span>
          <span class="convlog-time">${esc(time)}</span>
        </div>
        <div class="convlog-text">${esc(entry.text || '')}</div>
      </div>`;
    }).join('');
    tabContent.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:4px 8px 2px;">
        <span class="stat-label" style="margin:0;">Agent Messages</span>
        <span style="color:var(--dim);font-size:9px;">${log.length}/60</span>
      </div>
      <div class="convlog-list">${rows}</div>`;
  }

  function renderCompressPanel(gs, tabContent) {
    const state = gs.getState();
    const phase = window.GameState ? window.GameState.getPhase(state.level) : { name: 'Unknown', id: '?', color: '#888' };
    const lvl   = state.level;

    const STAGES = [
      { name: 'HYDROGEN',   range: [1,5],   color: '#ff8800', desc: 'Single terminal. Raw survival.' },
      { name: 'HELIUM',     range: [6,15],  color: '#ffcc00', desc: 'Split view. Two panels unlock.' },
      { name: 'CARBON',     range: [16,30], color: '#00ff88', desc: 'Tab groups. Layout memory.' },
      { name: 'IRON',       range: [31,55], color: '#00d4ff', desc: 'Full workspace. Plugin hooks.' },
      { name: 'NEUTRON',    range: [56,75], color: '#bb55ff', desc: 'Meta-UI. Panels modify panels.' },
      { name: 'DEGENERATE', range: [76,90], color: '#ff44bb', desc: 'Custom panels. API-first mode.' },
      { name: 'BLACK HOLE', range: [91,125],color: '#ff4040', desc: 'Pure command. UI transcended.' },
    ];

    const rows = STAGES.map(s => {
      const inRange = lvl >= s.range[0] && lvl <= s.range[1];
      const past    = lvl > s.range[1];
      const color   = inRange ? s.color : past ? '#2a5040' : 'var(--dim2)';
      const icon    = inRange ? '▶' : past ? '✓' : '○';
      return `
        <div class="compress-stage ${inRange ? 'compress-active' : past ? 'compress-past' : ''}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="color:${color};">${icon} ${s.name}</span>
            <span style="color:var(--dim);font-size:9px;">Lv ${s.range[0]}–${s.range[1]}</span>
          </div>
          <div class="compress-desc" style="color:${inRange ? 'var(--white)' : 'var(--dim)'};">${s.desc}</div>
        </div>`;
    }).join('');

    // Panel inventory
    const unlockedPanels = PANEL_UNLOCKS.filter(p => lvl >= p.minLevel);
    const lockedPanels   = PANEL_UNLOCKS.filter(p => lvl < p.minLevel);

    tabContent.innerHTML = `
      <div class="stat-section">
        <div class="stat-label">Compression Ladder — Level ${lvl}</div>
        <div class="stat-label" style="color:${esc(phase.color)};margin-bottom:8px;">${esc(phase.name)}</div>
        ${rows}
      </div>
      <div class="stat-section">
        <div class="stat-label">Unlocked Panels (${unlockedPanels.length})</div>
        ${unlockedPanels.map(p => `<div style="color:var(--green);font-size:10px;">✓ ${p.title}</div>`).join('')}
      </div>
      <div class="stat-section">
        <div class="stat-label">Locked Panels (${lockedPanels.length})</div>
        ${lockedPanels.map(p => `<div style="color:var(--dim);font-size:10px;">○ ${p.title} — ${p.hint}</div>`).join('')}
      </div>
      <div class="stat-section">
        <div class="panel-actions">
          <button class="panel-btn" data-cmd="compress status">Compress Status</button>
          <button class="panel-btn" data-cmd="density">Density Check</button>
          <button class="panel-btn" data-cmd="phase">Current Phase</button>
        </div>
      </div>`;
  }

  // ── Panel button click delegation ─────────────────────────────────────
  function bindPanelButtons(tabContent) {
    tabContent.addEventListener('click', (e) => {
      const btn = e.target.closest('.panel-btn[data-cmd]');
      if (!btn) return;
      const cmdInput = document.getElementById('cmd-input');
      if (!cmdInput) return;
      const cmd = btn.dataset.cmd;
      cmdInput.value = cmd;
      cmdInput.focus();
      // Auto-run
      cmdInput.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    });
  }

  // ── Main system object ─────────────────────────────────────────────────
  const sys = {
    currentTab: null,

    renderPanel(tabId) {
      const level = getPlayerLevel();
      const def   = PANEL_UNLOCKS.find(p => p.id === tabId);
      if (def && level < def.minLevel) {
        document.dispatchEvent(new CustomEvent('td:toast', {
          detail: { msg: `🔒 ${def.title} unlocks at Level ${def.minLevel}`, type: 'warn' }
        }));
        return;
      }

      this.currentTab = tabId;
      try { localStorage.setItem(STORAGE_KEY_TAB, tabId); } catch (_) {}

      // Update tab active state
      document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === tabId);
        t.setAttribute('aria-selected', t.dataset.tab === tabId ? 'true' : 'false');
        t.setAttribute('tabindex', t.dataset.tab === tabId ? '0' : '-1');
      });

      const tabContent = document.getElementById('tab-content');
      if (!tabContent) return;

      const gs = window._game ? window._game.gs : null;
      if (!gs) return;

      // New panels handled here; existing ones handled in game.js
      if (tabId === 'faction') { renderFactionPanel(gs, tabContent); return; }
      if (tabId === 'agents')  { renderAgentsPanel(tabContent); return; }
      if (tabId === 'inventory') { renderInventoryPanel(gs, tabContent); return; }
      if (tabId === 'achievements') { renderAchievementsPanel(gs, tabContent); return; }
      if (tabId === 'compress')    { renderCompressPanel(gs, tabContent); return; }
      if (tabId === 'cmdlog')      { renderCmdLogPanel(tabContent); return; }
      if (tabId === 'convlog')     { renderConvLogPanel(tabContent); return; }

      // Delegate existing panels back to game.js renderTab function
      if (window._game && window._game._renderTabFn) {
        window._game._renderTabFn(tabId);
      }
    },

    refresh() {
      refreshTabVisibility();
      if (this.currentTab) this.renderPanel(this.currentTab);
    },
  };

  // ── Toast event bridge ─────────────────────────────────────────────────
  document.addEventListener('td:toast', (e) => {
    // game.js doesn't expose showToast, so we write directly
    const toastEl = document.getElementById('toast');
    if (!toastEl) return;
    const { msg, type } = e.detail;
    toastEl.textContent = msg;
    toastEl.className = type === 'xp'     ? 'show toast-xp'     :
                        type === 'level'  ? 'show toast-level'  :
                        type === 'unlock' ? 'show toast-unlock'  :
                        type === 'warn'   ? 'show toast-warn'    :
                        type === 'phase'  ? 'show toast-phase'   : 'show';
    clearTimeout(toastEl._timer2);
    toastEl._timer2 = setTimeout(() => { toastEl.className = ''; }, 4000);
  });

  // ── Initialise ────────────────────────────────────────────────────────
  _ready(() => {
    const layout = loadLayout();

    // Apply saved theme (silent = no toast on initial load)
    applyTheme(layout.theme, { silent: true });

    // Apply saved panel width
    const rightPanel = document.getElementById('right-panel');
    if (rightPanel && layout.width !== 288) {
      rightPanel.style.width = layout.width + 'px';
    }

    // Inject tabs that don't exist yet
    const tabsEl = document.getElementById('tabs');
    if (tabsEl) {
      injectMissingTabs(tabsEl);

      // Wire existing tabs to go through sys.renderPanel
      document.querySelectorAll('.tab:not(.tab-injected)').forEach(tab => {
        // Clone to remove old game.js listener, then re-add via sys
        const clone = tab.cloneNode(true);
        tab.parentNode.replaceChild(clone, tab);
        clone.addEventListener('click', () => sys.renderPanel(clone.dataset.tab));
      });
    }

    // Initial visibility
    refreshTabVisibility();

    // Intercept game.js's renderTab so updateUI() re-renders our panels correctly
    if (window._game && window._game._renderTabFn) {
      const origRenderTab = window._game._renderTabFn;
      // Replace the exported function with a proxy
      const _PANEL_SYS_TABS = ['faction','agents','inventory','achievements','compress','cmdlog','convlog'];
      window._game._renderTabFn = function (tab) {
        if (_PANEL_SYS_TABS.includes(tab)) {
          sys.renderPanel(tab);
        } else {
          origRenderTab(tab);
        }
      };
      // Also patch it so game.js's internal updateUI() path routes through here.
      // game.js calls renderTab(currentTab) inside updateUI — we patch by
      // subscribing to the same gs state listener AFTER game.js registers its own.
      if (window._game.gs && window._game.gs.on) {
        window._game.gs.on(() => {
          refreshTabVisibility();
          if (sys.currentTab && _PANEL_SYS_TABS.includes(sys.currentTab)) {
            // game.js updateUI will call its own renderTab with the OLD tab
            // We re-render ours shortly after to win the race
            requestAnimationFrame(() => {
              if (sys.currentTab) sys.renderPanel(sys.currentTab);
            });
          }
        });
      }

      // Live re-render when logs update
      document.addEventListener('td:cmdlog:update', () => {
        if (sys.currentTab === 'cmdlog') renderCmdLogPanel(document.getElementById('tab-content'));
      });
      document.addEventListener('td:convlog:update', () => {
        if (sys.currentTab === 'convlog') renderConvLogPanel(document.getElementById('tab-content'));
      });
      window._game._panelSys = sys;
    }

    // Drag resize
    const handle   = document.getElementById('resize-handle');
    const termPanel = document.getElementById('terminal-panel');
    if (handle && rightPanel && termPanel) {
      initDragResize(handle, termPanel, rightPanel);
    }

    // Theme button
    const themeBtn = document.getElementById('btn-theme');
    if (themeBtn) themeBtn.addEventListener('click', cycleTheme);

    // Panel button delegation
    const tabContent = document.getElementById('tab-content');
    if (tabContent) bindPanelButtons(tabContent);

    // Periodic refresh: unlock checks + current panel refresh
    setInterval(() => {
      refreshTabVisibility();
      // Only auto-refresh data panels (don't interrupt terminal focus)
      if (sys.currentTab === 'agents') renderAgentsPanel(tabContent);
    }, 5000);

    // Render the saved tab (or default)
    const startTab = layout.tab || 'objective';
    setTimeout(() => sys.renderPanel(startTab), 100);

    // Keyboard shortcut: Ctrl+T = cycle tabs
    document.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        const allTabs = [...document.querySelectorAll('.tab:not(.tab-locked)')];
        const curIdx  = allTabs.findIndex(t => t.dataset.tab === sys.currentTab);
        const nextTab = allTabs[(curIdx + 1) % allTabs.length];
        if (nextTab) sys.renderPanel(nextTab.dataset.tab);
      }
    });

    // ── Register `theme` as a frontend-side terminal command ──────────────
    if (window._game && window._game.cmds && window._game.cmds._handlers) {
      window._game.cmds._handlers['theme'] = function (args) {
        const name = (args || []).join(' ').trim().toLowerCase();
        if (!name) {
          return [
            { t: 'system', s: '╔═ THEME ENGINE ════════════════════════╗' },
            { t: 'system', s: '║  Available themes:                    ║' },
            ...Object.entries(THEMES).map(([k, v]) => ({ t: 'info', s: `  theme ${k.padEnd(12)} — ${v.label}` })),
            { t: 'system', s: '╚═══════════════════════════════════════╝' },
            { t: 'dim',    s: '  Current: ' + (document.body.dataset.theme || 'cyberpunk') },
            { t: 'dim',    s: '  Also: click CYBERPUNK button in header, or Ctrl+T to cycle tabs' },
          ];
        }
        if (THEMES[name]) {
          applyTheme(name);
          return [{ t: 'success', s: `✓ Theme applied: ${THEMES[name].label}` }];
        }
        return [{ t: 'error', s: `Unknown theme "${name}". Available: ${Object.keys(THEMES).join(', ')}` }];
      };
    }

    window._panelSys = sys;

    // ── Simulation Bridge integration ──────────────────────────────────────
    // Server state (snake_case) → client player state (camelCase) map.
    // Only keys present here are merged; everything else stays client-local.
    const SERVER_TO_PLAYER = {
      level:                 'level',
      xp:                    'xp',
      xp_to_next:            'xpToNext',
      skills:                'skills',
      commands_run:          'commandsRun',
      achievements:          (v, p) => { p.achievements = new Set(Array.isArray(v) ? v : []); },
      story_beats:           (v, p) => { p.storyBeats   = new Set(Array.isArray(v) ? v : []); },
      completed_challenges:  (v, p) => { p.completedChallenges = new Set(Array.isArray(v) ? v : []); },
      faction_reps:          (v, p) => { p.factionReputation = v; },
      ascension_count:       'ascensionCount',
      karma:                 'karma',
      lore:                  'lore',
    };

    document.addEventListener('td:bridge:state', (ev) => {
      const { state, source } = ev.detail || {};
      if (!state || !window._game || !window._game.gs) return;

      const player = window._game.gs.player; // direct mutable reference
      let changed = false;

      for (const [serverKey, mapping] of Object.entries(SERVER_TO_PLAYER)) {
        if (state[serverKey] === undefined || state[serverKey] === null) continue;
        if (typeof mapping === 'function') {
          mapping(state[serverKey], player);
          changed = true;
        } else {
          const newVal = state[serverKey];
          if (JSON.stringify(player[mapping]) !== JSON.stringify(newVal)) {
            player[mapping] = newVal;
            changed = true;
          }
        }
      }

      if (changed || source === 'connected') {
        sys.refresh();
      }
    });

    // Level-up refresh from bridge command result
    document.addEventListener('td:bridge:output', (ev) => {
      if (ev.detail && ev.detail.levelUp) {
        sys.refresh();
      }
    });

    console.log('[TD Panels] Loaded — compression ladder, themes, drag-resize, 7 new panels, CMD/MSGS logs, suggest chips ✓');
  });

})();
