/**
 * Terminal Depths — xterm.js Thin Client (Task 3: Agent Panel & Evolving UI)
 */
(function() {
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ── xterm.js setup ────────────────────────────────────────────────
  const term = new Terminal({
    theme: {
      background: '#080d16', foreground: '#c8d8ec', cursor: '#00d4ff',
      cursorAccent: '#080d16', black: '#080d16', red: '#ff4040',
      green: '#00ff88', yellow: '#ffcc00', blue: '#00d4ff',
      magenta: '#bb55ff', cyan: '#00d4ff', white: '#c8d8ec',
      brightBlack: '#3a5575', brightGreen: '#00ff88',
      brightYellow: '#ffcc00', brightCyan: '#00d4ff',
    },
    fontFamily: "'Courier New', 'Lucida Console', monospace",
    fontSize: 13,
    lineHeight: 1.4,
    cursorBlink: true,
    cursorStyle: 'block',
    scrollback: 5000,
    allowTransparency: true,
  });

  const fitAddon = new FitAddon.FitAddon();
  term.loadAddon(fitAddon);
  term.open(document.getElementById('terminal'));
  fitAddon.fit();
  window.addEventListener('resize', () => fitAddon.fit());

  // ── ANSI color helpers ────────────────────────────────────────────
  const A = {
    reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
    cyan: '\x1b[36m', green: '\x1b[32m', yellow: '\x1b[33m',
    red: '\x1b[31m', magenta: '\x1b[35m', blue: '\x1b[34m',
    white: '\x1b[37m', bgRed: '\x1b[41m',
  };

  const TYPE_COLOR = {
    info: '', error: A.red, warn: A.yellow, success: A.green,
    system: A.cyan, story: A.magenta, npc: '\x1b[38;5;208m',
    dim: A.dim, xp: A.yellow, cmd: A.green, root: A.red, 'ls-row': '',
    // Loot rarity tiers
    legendary: '\x1b[38;5;220m',  // gold — AUTH_TOKEN, master.key, CHIMERA key
    epic:      '\x1b[38;5;135m',  // purple — rare exploits, high-trust intel
    rare:      '\x1b[38;5;39m',   // bright blue — fragments, discovery items
    uncommon:  '\x1b[38;5;82m',   // lime green — skill unlocks, quest rewards
    glitch:    '\x1b[38;5;196m',  // bright red — gate failures, system errors
    lore:      '\x1b[38;5;245m',  // grey — lore lines, ambient narrative
  };

  function colorize(t, s) {
    const c = TYPE_COLOR[t] || '';
    if (t === 'story') return `${c}│ ${s}${A.reset}`;
    if (t === 'root') return `${c}${A.bold}${s}${A.reset}`;
    if (t === 'legendary') return `${A.bold}${c}★ ${s}${A.reset}`;
    if (t === 'epic') return `${c}◆ ${s}${A.reset}`;
    if (t === 'rare') return `${c}◇ ${s}${A.reset}`;
    if (t === 'glitch') return `${c}${A.bold}[GLITCH] ${s}${A.reset}`;
    return c + (s || '') + (c ? A.reset : '');
  }

  function writeLine(item) {
    if (item.t === 'ls-row') {
      const colorMap = { cyan: A.cyan, green: A.green, yellow: A.yellow, red: A.red, dim: A.dim };
      const row = item.items.map(i => (colorMap[i.color] || '') + i.text + A.reset).join('');
      term.writeln(row);
    } else if (item.t === 'npc') {
      term.writeln(`${'\x1b[38;5;208m'}[${item.npc || 'NPC'}]${A.reset}`);
      term.writeln((item.text || '').split('\n').join('\r\n'));
    } else if (item.t === 'clear') {
      term.clear();
    } else {
      const text = (item.s || '').replace(/\n/g, '\r\n');
      term.writeln(colorize(item.t, text));
    }
  }

  function writeLines(items) {
    if (!Array.isArray(items)) return;
    items.forEach(writeLine);
  }

  // ── State ─────────────────────────────────────────────────────────
  let sessionId = localStorage.getItem('td-cli-session') || null;
  let state = null;
  let cwd = '~';
  let isRoot = false;
  let inputBuffer = '';
  let historyArr = JSON.parse(localStorage.getItem('td-cli-cmd-history') || '[]');
  let histIdx = -1;
  let currentTab = 'stats';
  let availableCommands = [];
  let tabCandidates = [];
  let tabIdx = 0;
  let uiPhase = 0;
  let agentsPanelUnlocked = false;
  let phase0IdleActive = true;
  const phase0IdleTimers = [];
  let agents = [];
  let selectedAgentId = null;
  let agentChatHistories = {};
  let ravenLastMsg = '';
  let metaLogs = [];
  let factions = [];
  let pollInterval = 30;

  // ── Swarm Console state ────────────────────────────────────────────
  let swarmWs = null;
  let swarmMessages = [];
  let swarmUnread = 0;
  let swarmRoom = 'general';
  let swarmConnected = false;

  // ── Activity feed (U3) ─────────────────────────────────────────────
  let activityWs = null;
  let activityFeed = [];   // [{ts, agent, text, type}]
  let activityUnread = 0;
  let activityConnected = false;

  // ── UI Phase logic ─────────────────────────────────────────────────
  // Phase 0 (lvl 1-4):   Pure terminal. Nothing visible but the prompt.
  // Phase 2 (lvl 5-19):  Sidebar appears. Stats + RAV≡N widget.
  // Phase 4 (lvl 20-49): Agents & factions tabs fade in.
  // Phase 6 (lvl 50-89): Transcendent theme + Hall of Fame tab.
  // Phase 8 (lvl 90+):   Meta-developer console online.
  function computePhase(level) {
    if (level < 5)   return 0;
    if (level < 20)  return 2;
    if (level < 50)  return 4;
    if (level < 90)  return 6;
    return 8;
  }

  function applyUIPhase(phase) {
    const sidebar = document.getElementById('sidebar');
    const tabAgents = document.getElementById('tab-agents');
    const tabFactions = document.getElementById('tab-factions');
    const tabHof = document.getElementById('tab-hof');
    const tabMeta = document.getElementById('tab-meta');
    const ravenWidget = document.getElementById('raven-widget');

    // Swarm Console always shows sidebar (SWARM tab is core identity here)
    sidebar.style.display = 'flex';

    // Phase 4+: show agents/factions tabs
    if (phase >= 4 && agentsPanelUnlocked) {
      tabAgents.classList.remove('hidden');
      tabFactions.classList.remove('hidden');
      ravenWidget.style.display = 'block';
    }

    // Phase 6+: transcendent theme + hall of fame
    if (phase >= 6) {
      document.body.classList.add('theme-transcendent');
      tabHof.classList.remove('hidden');
    } else {
      document.body.classList.remove('theme-transcendent');
    }

    // Phase 8: meta console
    if (phase >= 8) {
      tabMeta.classList.remove('hidden');
      ravenWidget.classList.add('phase8');
    }

    document.getElementById('st-phase').textContent = phase;
  }

  function transitionPhase(oldPhase, newPhase) {
    if (newPhase <= oldPhase) return;
    triggerGlitch();
    const msgs = {
      2: `${A.cyan}[SYSTEM] INTERFACE UPGRADE — Sidebar modules online.${A.reset}`,
      4: `${A.magenta}[SYSTEM] AGENT PANEL UNLOCKED — New contacts available.${A.reset}`,
      6: `${A.yellow}[SYSTEM] TRANSCENDENCE THRESHOLD REACHED — You are beyond them now.${A.reset}`,
      8: `${A.yellow}[SYSTEM] META-DEVELOPER CONSOLE ONLINE — Welcome to the other side.${A.reset}`,
    };
    for (let p = oldPhase + 1; p <= newPhase; p++) {
      if (msgs[p]) {
        setTimeout(() => {
          term.writeln('\r\n' + msgs[p]);
          term.write(getPrompt() + inputBuffer);
        }, 800);
      }
    }
  }

  // ── Panel discovery ────────────────────────────────────────────────
  function checkAndRevealAgentPanel(gameState) {
    if (agentsPanelUnlocked) return;
    const beats = (gameState && gameState.story_beats) || [];
    const unlocked = (gameState && gameState.unlocked_agents) || [];
    // Panel reveals after ada_contact is established — player earned it
    if (beats.includes('ada_contact') || unlocked.length >= 3) {
      revealAgentPanel(true);
    }
  }

  function revealAgentPanel(sendWelcome) {
    if (agentsPanelUnlocked) return;
    agentsPanelUnlocked = true;
    localStorage.setItem('td-agents-unlocked', '1');
    const tabAgents = document.getElementById('tab-agents');
    const tabFactions = document.getElementById('tab-factions');
    tabAgents.classList.remove('hidden');
    tabFactions.classList.remove('hidden');
    tabAgents.classList.add('new-unlock');
    document.getElementById('raven-widget').style.display = 'block';
    showToast('AGENTS PANEL UNLOCKED', 'unlock');
    if (sendWelcome) {
      const key = `${sessionId || 'default'}_raven`;
      if (!agentChatHistories[key]) agentChatHistories[key] = [];
      const welcomeMsg = {
        role: 'agent', content: "GHOST. You found another way in. Good. I've been waiting to speak with you directly.",
        agentId: 'raven', agentName: 'RAV≡N', color: '#00d4ff',
      };
      agentChatHistories[key].push(welcomeMsg);
      saveAgentHistory(key);
      updateRavenWidget("GHOST. You found another way in. Good.");
      term.writeln(`\r\n${A.cyan}[RAV≡N] GHOST. You found another way in. Good. I've been waiting.${A.reset}`);
      term.write(getPrompt() + inputBuffer);
    }
    if (uiPhase >= 4) {
      tabFactions.classList.remove('hidden');
    }
  }

  // ── Agent chat histories ───────────────────────────────────────────
  function historyKey(agentId) {
    return `${sessionId || 'default'}_${agentId}`;
  }

  function loadAgentHistory(agentId) {
    const key = historyKey(agentId);
    if (agentChatHistories[key]) return agentChatHistories[key];
    try {
      const raw = localStorage.getItem(`td-chat-${key}`);
      agentChatHistories[key] = raw ? JSON.parse(raw) : [];
    } catch(e) {
      agentChatHistories[key] = [];
    }
    return agentChatHistories[key];
  }

  function saveAgentHistory(key) {
    try {
      localStorage.setItem(`td-chat-${key}`, JSON.stringify(agentChatHistories[key] || []));
    } catch(e) {}
  }

  function pushMessage(agentId, roleObj) {
    const key = historyKey(agentId);
    if (!agentChatHistories[key]) agentChatHistories[key] = [];
    agentChatHistories[key].push(roleObj);
    saveAgentHistory(key);
  }

  // ── Prompt ────────────────────────────────────────────────────────
  function getPrompt() {
    const user = isRoot ? `${A.red}${A.bold}root` : `${A.green}ghost`;
    const host = `@node-7`;
    const dir = `${A.blue}${cwd}${A.reset}`;
    const sym = isRoot ? `${A.red}#${A.reset}` : `${A.green}$${A.reset}`;
    return `${user}${A.reset}${host}:${dir}${sym} `;
  }

  function showPrompt() {
    term.write('\r\n' + getPrompt());
  }

  // ── API helpers ───────────────────────────────────────────────────
  async function apiPost(path, body) {
    const headers = { 'Content-Type': 'application/json' };
    if (sessionId) headers['X-Session-Id'] = sessionId;
    const r = await fetch(path, { method: 'POST', headers, body: JSON.stringify(body) });
    return r.json();
  }

  async function apiGet(path) {
    const headers = {};
    if (sessionId) headers['X-Session-Id'] = sessionId;
    const r = await fetch(path, { headers });
    return r.json();
  }

  // ── Session init ──────────────────────────────────────────────────
  async function initSession() {
    term.writeln(`${A.cyan}Connecting to Terminal Depths engine...${A.reset}`);
    try {
      const data = await apiPost('/api/game/session', { session_id: sessionId });
      sessionId = data.session_id;
      localStorage.setItem('td-cli-session', sessionId);
      state = data.state;
      cwd = data.cwd.replace('/home/ghost', '~');
      isRoot = data.is_root;

      term.writeln(`${A.green}Session: ${A.dim}${sessionId.substring(0, 16)}...${A.reset}`);
      term.writeln(`${A.cyan}Mode: Server-side Python engine${A.reset}`);
      term.writeln(`${A.dim}Type 'help' for commands. Tab completion active.${A.reset}`);
      term.writeln('');

      if (data.boot_output && data.boot_output.length) {
        writeLines(data.boot_output);
      }

      // Phase 0: gentle pre-command idle prompts (only for fresh players)
      if ((state.commands_run || 0) === 0) {
        const p0msgs = [
          { delay: 30000, text: `${A.dim}[RAV\u2261N] Still there? When you're ready — type \`tutorial\` to begin or \`ls\` to look around.${A.reset}` },
          { delay: 60000, text: `${A.dim}[RAV\u2261N] No rush. The terminal is patient. Type \`help\` if you're not sure where to start.${A.reset}` },
          { delay: 120000, text: `${A.dim}[RAV\u2261N] I'll be here when you're ready.${A.reset}` },
        ];
        for (const { delay, text } of p0msgs) {
          phase0IdleTimers.push(setTimeout(() => {
            if (!phase0IdleActive) return;
            term.writeln('\r\n' + text);
            term.write(getPrompt() + inputBuffer);
          }, delay));
        }
      } else {
        phase0IdleActive = false;
      }

      const cmdData = await apiGet('/api/game/commands');
      availableCommands = cmdData.commands || [];

      // Check if agents panel was previously unlocked
      if (localStorage.getItem('td-agents-unlocked') === '1') {
        agentsPanelUnlocked = true;
        document.getElementById('tab-agents').classList.remove('hidden');
        document.getElementById('tab-factions').classList.remove('hidden');
        document.getElementById('raven-widget').style.display = 'block';
      }

      const oldPhase = uiPhase;
      uiPhase = computePhase(state.level);
      applyUIPhase(uiPhase);
      checkAndRevealAgentPanel(state);

      updateStatusBar();
      updateTutBadge();
      renderSidebar(currentTab);
      loadAgents();
      startStatePoll();
      startArgSignalLoop();
      startDevToolsDetection();
      showPrompt();
    } catch (e) {
      term.writeln(`${A.red}Connection failed: ${e.message}${A.reset}`);
      term.writeln(`${A.dim}Make sure the server is running at /api/game/session${A.reset}`);
      showPrompt();
    }
  }

  // ── State poll ────────────────────────────────────────────────────
  function startStatePoll() {
    setInterval(async () => {
      if (!sessionId) return;
      try {
        const data = await apiGet(`/api/game/state?session_id=${sessionId}`);
        if (data.state) {
          const prevPhase = uiPhase;
          state = data.state;
          uiPhase = computePhase(state.level);
          if (uiPhase !== prevPhase) {
            transitionPhase(prevPhase, uiPhase);
            applyUIPhase(uiPhase);
          }
          checkAndRevealAgentPanel(state);
          updateStatusBar();
          if (currentTab !== 'agents') renderSidebar(currentTab);
        }
      } catch(e) {}
    }, (pollInterval || 30) * 1000);
  }

  // ── ARG signal loop ───────────────────────────────────────────────
  function startArgSignalLoop() {
    setInterval(async () => {
      try {
        const data = await apiGet('/api/game/arg/signal');
        if (data.msg) {
          const src = data.source || 'SIGNAL';
          const style = `color: #ffcc00; font-family: monospace; font-size: 12px; font-weight: bold;`;
          const bodyStyle = `color: #00d4ff; font-family: monospace;`;
          console.log(`%c[TERMINAL DEPTHS :: ${src}]%c ${data.msg}`, style, bodyStyle);
        }
      } catch(e) {}
    }, 90000);
  }

  // ── DevTools detection ────────────────────────────────────────────
  function startDevToolsDetection() {
    let devToolsOpen = false;
    setInterval(() => {
      const threshold = 160;
      const widthDiff = window.outerWidth - window.innerWidth;
      const heightDiff = window.outerHeight - window.innerHeight;
      const opened = widthDiff > threshold || heightDiff > threshold;
      if (opened && !devToolsOpen) {
        devToolsOpen = true;
        triggerGlitch();
        fetch('/api/game/arg/signal?event=devtools_open').then(r => r.json()).then(d => {
          if (d.msg) {
            term.writeln(`\r\n${A.cyan}[RAV≡N] ${d.msg}${A.reset}`);
            term.write(getPrompt() + inputBuffer);
          }
        }).catch(() => {});
      } else if (!opened) {
        devToolsOpen = false;
      }
    }, 2000);
  }

  // ── Glitch effect ─────────────────────────────────────────────────
  function triggerGlitch() {
    const overlay = document.getElementById('glitch-overlay');
    overlay.classList.remove('active');
    void overlay.offsetWidth;
    overlay.classList.add('active');
    setTimeout(() => overlay.classList.remove('active'), 3200);
  }

  // ── Load agents ───────────────────────────────────────────────────
  async function loadAgents() {
    try {
      const data = await apiGet(`/api/game/agents?session_id=${sessionId || ''}`);
      agents = data.agents || [];
      if (!selectedAgentId && agents.length) {
        const first = agents.find(a => a.unlocked) || agents[0];
        selectedAgentId = first.id;
      }
      updateRavenWidgetFromAgents();
    } catch(e) {}
  }

  async function loadFactions() {
    try {
      const data = await apiGet(`/api/game/faction/status?session_id=${sessionId || ''}`);
      factions = data.factions || [];
    } catch(e) {}
  }

  // ── Command execution ─────────────────────────────────────────────
  async function runCommand(cmd) {
    if (!cmd.trim()) {
      showPrompt();
      return;
    }

    // Cancel Phase 0 idle prompts on first real command
    if (phase0IdleActive) {
      phase0IdleActive = false;
      for (const t of phase0IdleTimers) clearTimeout(t);
    }

    // Special: unlock agents command
    if (cmd.trim().toLowerCase() === 'unlock agents') {
      revealAgentPanel(true);
      term.writeln('');
      term.writeln(`${A.cyan}[SYSTEM] Agent panel access granted. Type in the AGENTS tab to communicate.${A.reset}`);
      showPrompt();
      return;
    }

    historyArr.push(cmd);
    if (historyArr.length > 500) historyArr = historyArr.slice(-500);
    try { localStorage.setItem('td-cli-cmd-history', JSON.stringify(historyArr)); } catch (_) {}
    histIdx = -1;
    term.writeln('');

    try {
      const data = await apiPost('/api/game/command', { command: cmd, session_id: sessionId });
      sessionId = data.session_id;
      localStorage.setItem('td-cli-session', sessionId);
      state = data.state;
      cwd = (data.cwd || '/home/ghost').replace('/home/ghost', '~');
      isRoot = data.is_root;

      writeLines(data.output);

      if (data.tutorial_notification) {
        term.writeln(`\r\n${A.yellow}✓ ${data.tutorial_notification}${A.reset}`);
        showToast(data.tutorial_notification, 'xp');
      }
      if (data.level_up) {
        term.writeln(`\r\n${A.magenta}▲ LEVEL UP: ${data.level_up}${A.reset}`);
        showToast(`Level ${data.state.level}!`, 'lvl');
        const prevPhase = uiPhase;
        uiPhase = computePhase(data.state.level);
        if (uiPhase !== prevPhase) {
          transitionPhase(prevPhase, uiPhase);
          applyUIPhase(uiPhase);
        }
      }

      checkAndRevealAgentPanel(state);
      updateStatusBar();
      updateTutBadge();
      renderSidebar(currentTab);

      // ── ML next-command hint (Markov prediction) ─────────────────────
      if (data.next_predicted && uiPhase >= 1) {
        term.writeln(`${A.dim}  » ml-hint: try '${data.next_predicted}'${A.reset}`);
      }
    } catch (e) {
      term.writeln(`${A.red}Error: ${e.message}${A.reset}`);
    }

    showPrompt();
  }

  // ── Toast ─────────────────────────────────────────────────────────
  const toastEl = document.getElementById('toast');
  function showToast(msg, type) {
    toastEl.textContent = msg;
    toastEl.className = 'show' + (type === 'xp' ? ' xp' : type === 'lvl' ? ' lvl' : type === 'unlock' ? ' unlock' : '');
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(() => toastEl.className = '', 3500);
  }

  // ── Status bar ────────────────────────────────────────────────────
  function updateStatusBar() {
    if (!state) return;
    document.getElementById('st-session').textContent = sessionId ? sessionId.substring(0, 12) + '...' : '—';
    document.getElementById('st-level').textContent = state.level;
    document.getElementById('st-xp').textContent = `${state.xp}/${state.xp_to_next}`;
    document.getElementById('st-cwd').textContent = cwd;
    document.getElementById('st-phase').textContent = uiPhase;
    const rootEl = document.getElementById('st-root');
    if (isRoot) rootEl.style.display = 'inline';
    else rootEl.style.display = 'none';
  }

  // ── Sidebar ───────────────────────────────────────────────────────
  function renderSidebar(tab) {
    currentTab = tab;
    document.querySelectorAll('.stab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    const el = document.getElementById('sidebar-content');
    if (!state) { el.textContent = 'Loading...'; return; }

    if (tab === 'stats') renderStats(el);
    else if (tab === 'tutorial') renderTutorial(el);
    else if (tab === 'story') renderStory(el);
    else if (tab === 'help') renderHelp(el);
    else if (tab === 'agents') renderAgentsPanel(el);
    else if (tab === 'factions') renderFactions(el);
    else if (tab === 'hof') renderHOF(el);
    else if (tab === 'meta') renderMeta(el);
    else if (tab === 'swarm') { swarmUnread = 0; updateSwarmBadge(); renderSwarm(el); }
    else if (tab === 'activity') { activityUnread = 0; updateActivityBadge(); renderActivity(el); }
  }

  function renderStats(el) {
    const pct = Math.round(state.xp / state.xp_to_next * 100);
    const tier = state.tier || `Phase ${uiPhase}`;
    // Phase colours
    const phaseColors = ['var(--dim)','var(--cyan)','var(--green)','var(--yellow)','var(--orange)','var(--red)','var(--purple)','var(--gold)','var(--gold)'];
    const phaseColor = phaseColors[Math.min(uiPhase, 8)];

    el.innerHTML = `
      <div class="section-title">Identity</div>
      <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
        <span style="color:var(--cyan)">${esc(state.name || 'GHOST')}</span>
        <span style="color:var(--yellow)">Lv ${state.level}</span>
      </div>
      <div class="xp-bar"><div class="xp-fill" style="width:${pct}%"></div></div>
      <div style="color:var(--dim);font-size:9px;margin-bottom:6px;">${state.xp}/${state.xp_to_next} XP</div>
      <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
        <span style="color:${phaseColor};font-size:10px;letter-spacing:1px;font-weight:bold;">${esc(tier)}</span>
        <span style="color:var(--dim);font-size:9px;">· Phase ${uiPhase}</span>
      </div>
      <div class="section-title">Skill Matrix</div>
      ${Object.entries(state.skills || {}).map(([sk, v]) => `
        <div class="skill-bar">
          <div class="skill-name">${sk.replace(/_/g,' ').toUpperCase()} <span>${v}%</span></div>
          <div class="skill-track"><div class="skill-fill ${sk}" style="width:${v}%"></div></div>
        </div>
      `).join('')}
      <div class="section-title">Activity</div>
      <div class="grid2">
        <span class="lbl">Commands</span><span class="val">${state.commands_run}</span>
        <span class="lbl">Tutorial</span><span class="val">${state.tutorial_step}/42 (${state.tutorial_percent || 0}%)</span>
        <span class="lbl">Achievements</span><span class="val">${(state.achievements||[]).length}</span>
        <span class="lbl">Story beats</span><span class="val">${(state.story_beats||[]).length}</span>
        <span class="lbl">Faction</span><span class="val">${esc(state.active_faction || 'none')}</span>
        ${state.mole_id ? `<span class="lbl">Mole clues</span><span class="val" style="color:var(--yellow)">●</span>` : ''}
      </div>
      <div class="section-title">Achievements</div>
      ${(state.achievements||[]).length
        ? (state.achievements||[]).map(a => `<div class="ach-item">⬡ ${esc(a.replace(/_/g,' '))}</div>`).join('')
        : '<div style="color:var(--dim);font-size:10px;">None yet.</div>'}
    `;
  }

  // ── Tutorial tab ─────────────────────────────────────────────────
  // Sections in order (mirrors tutorial.py STEPS)
  const TUT_SECTIONS = [
    {name:'Orientation', steps:[1,2,3,4,5]},
    {name:'Navigation',  steps:[6,7,8,9,10]},
    {name:'Text Tools',  steps:[11,12,13,14,15]},
    {name:'Recon',       steps:[16,17,18,19,20]},
    {name:'Crypto',      steps:[21,22]},
    {name:'Networking',  steps:[23,24,25,26]},
    {name:'PrivEsc',     steps:[27,28,29]},
    {name:'Exploitation',steps:[30,31,32,33,34,35]},
    {name:'Skills',      steps:[36,37,38,39,40,41,42]},
  ];
  // Steps that have multi-variant sub-tasks (must try ALL variants)
  const MULTI_STEPS = {8:2, 12:2, 18:2, 22:2, 24:2};

  function tutStepDone(id) {
    const done = state.tutorial_step || 0;
    if (id < done) return true;
    if (id === done) {
      // Multi-step: check if all variants tried
      const mv = MULTI_STEPS[id];
      if (mv) {
        const tried = (state.tutorial_tried_variants || {})[String(id)] || [];
        return tried.length >= mv;
      }
      return false;
    }
    return false;
  }

  function tutCmdClick(cmd) {
    // Echo the command visually in the terminal then execute it
    term.writeln('\r\n' + getPrompt() + cmd);
    inputBuffer = '';
    runCommand(cmd);
    // Switch back to terminal focus
    term.focus();
  }
  // Expose globally so onclick= attributes in dynamically rendered HTML can reach it
  window.tutCmdClick = tutCmdClick;

  function updateTutBadge() {
    const badge = document.getElementById('tut-badge');
    if (!badge || !state) return;
    const done = state.tutorial_step || 0;
    const total = state.tutorial_total_steps || 42;
    if (done >= total) {
      badge.style.display = 'block';
      badge.textContent = '★';
      badge.style.background = 'var(--yellow)';
    } else if (done > 0) {
      badge.style.display = 'block';
      badge.textContent = '';
      badge.style.background = 'var(--green)';
    } else {
      badge.style.display = 'none';
    }
  }

  function renderTutorial(el) {
    const done = state.tutorial_step || 0;
    const total = state.tutorial_total_steps || 42;
    const pct = Math.round(done / total * 100);
    const currentStep = state.tutorial_current_step;
    const completions = state.tutorial_completions || 0;
    const triedVars = state.tutorial_tried_variants || {};
    const allDone = done >= total;

    // Build current-step card
    let stepCard = '';
    if (allDone) {
      const bonusNote = completions >= 2
        ? `<div style="color:var(--dim);font-size:9px;margin-top:4px;">Replay bonus already claimed. You've seen everything.</div>`
        : `<div style="color:var(--yellow);font-size:9px;margin-top:4px;">★ Replay for a 500 XP one-time bonus!</div>`;
      stepCard = `
        <div style="background:rgba(0,255,65,0.06);border:1px solid var(--green);border-radius:4px;padding:8px;margin-bottom:10px;">
          <div style="color:var(--green);font-size:11px;font-weight:bold;">✓ TUTORIAL COMPLETE</div>
          <div style="color:var(--dim);font-size:9px;margin-top:4px;">All ${total} steps finished · ${completions} run(s)</div>
          ${bonusNote}
          <div style="margin-top:8px;display:flex;gap:6px;">
            <button onclick="tutCmdClick('tutorial restart')" style="font-size:9px;padding:3px 7px;background:rgba(255,255,255,0.08);border:1px solid var(--border);color:var(--white);border-radius:3px;cursor:pointer;">↺ Restart</button>
            <button onclick="tutCmdClick('tutorial list')" style="font-size:9px;padding:3px 7px;background:rgba(255,255,255,0.08);border:1px solid var(--border);color:var(--white);border-radius:3px;cursor:pointer;">≡ List</button>
          </div>
        </div>`;
    } else if (currentStep) {
      const variants = MULTI_STEPS[currentStep.id];
      const tried = variants ? (triedVars[String(currentStep.id)] || []) : null;
      let variantHtml = '';
      if (variants) {
        // Show variant progress checkboxes
        variantHtml = `<div style="margin-top:6px;font-size:9px;color:var(--dim);">Multi-command step — try BOTH:</div>`;
        // We can't know exact variant cmds from state, show count progress
        const doneCount = tried ? tried.length : 0;
        variantHtml += `<div style="font-size:9px;color:var(--cyan);margin-top:3px;">${doneCount}/${variants} variants tried</div>`;
      }
      stepCard = `
        <div style="background:rgba(0,255,255,0.04);border:1px solid var(--cyan);border-radius:4px;padding:8px;margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="color:var(--cyan);font-size:10px;font-weight:bold;">STEP ${currentStep.id}/${total} · ${esc(currentStep.section)}</span>
            <span style="color:var(--dim);font-size:9px;">${variants ? '⚡ MULTI' : ''}</span>
          </div>
          <div style="color:var(--white);font-size:10px;font-weight:bold;margin-top:4px;">${esc(currentStep.title)}</div>
          <div style="color:var(--green);font-size:9px;margin-top:5px;line-height:1.5;">${esc(currentStep.objective)}</div>
          <div style="color:var(--dim);font-size:9px;margin-top:4px;border-top:1px solid var(--border);padding-top:4px;">💡 ${esc(currentStep.hint)}</div>
          ${variantHtml}
          <div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:5px;">
            <button onclick="tutCmdClick('tutorial ${currentStep.id}')" style="font-size:9px;padding:3px 6px;background:rgba(0,255,255,0.1);border:1px solid var(--cyan);color:var(--cyan);border-radius:3px;cursor:pointer;">📋 Review</button>
            ${done > 0 ? `<button onclick="tutCmdClick('tutorial back')" style="font-size:9px;padding:3px 6px;background:rgba(255,255,255,0.06);border:1px solid var(--border);color:var(--dim);border-radius:3px;cursor:pointer;">← Back</button>` : ''}
            <button onclick="tutCmdClick('tutorial list')" style="font-size:9px;padding:3px 6px;background:rgba(255,255,255,0.06);border:1px solid var(--border);color:var(--dim);border-radius:3px;cursor:pointer;">≡ All</button>
          </div>
        </div>`;
    }

    // Build section overview
    let sectionsHtml = '';
    for (const sec of TUT_SECTIONS) {
      const secDone = sec.steps.filter(id => id <= done).length;
      const isActive = currentStep && sec.steps.includes(currentStep.id);
      const allSecDone = secDone === sec.steps.length;
      const marker = allSecDone ? '✓' : (secDone > 0 ? '▶' : '○');
      const markerColor = allSecDone ? 'var(--green)' : (secDone > 0 ? 'var(--yellow)' : 'var(--dim)');
      const borderStyle = isActive ? 'border-left:2px solid var(--cyan);' : '';

      // Individual steps inside section (shown as dots or checkmarks)
      const stepsRow = sec.steps.map(id => {
        const d = id <= done;
        const isCur = currentStep && id === currentStep.id;
        const hasMulti = MULTI_STEPS[id];
        const tried = hasMulti ? (triedVars[String(id)] || []).length : null;
        const color = d ? 'var(--green)' : (isCur ? 'var(--cyan)' : 'var(--dim)');
        const sym = d ? '●' : (isCur ? '▶' : '·');
        const multiNote = hasMulti && !d ? ` <span style="font-size:7px;color:var(--purple)" title="Multi-variant step">✦</span>` : '';
        return `<span onclick="tutCmdClick('tutorial ${id}')" title="Step ${id} — click to review" style="cursor:pointer;color:${color};font-size:11px;">${sym}</span>${multiNote}`;
      }).join(' ');

      sectionsHtml += `
        <div style="padding:5px 6px;margin-bottom:3px;background:rgba(255,255,255,0.02);border-radius:3px;${borderStyle}">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">
            <span style="color:${markerColor};font-size:10px;">${marker} <b style="color:${isActive ? 'var(--cyan)' : 'var(--white)'}">${esc(sec.name)}</b></span>
            <span style="color:var(--dim);font-size:9px;">${secDone}/${sec.steps.length}</span>
          </div>
          <div style="letter-spacing:2px;">${stepsRow}</div>
        </div>`;
    }

    el.innerHTML = `
      <div class="section-title" style="color:var(--cyan);">Tutorial Progress</div>
      <div class="xp-bar" style="margin-bottom:4px;"><div class="xp-fill" style="width:${pct}%;background:var(--cyan);"></div></div>
      <div style="color:var(--dim);font-size:9px;margin-bottom:10px;">${done}/${total} steps · ${pct}% · ${completions} completion(s)</div>

      ${stepCard}

      <div class="section-title" style="margin-top:2px;">Sections <span style="color:var(--dim);font-weight:normal;font-size:9px;">(click ● to review)</span></div>
      ${sectionsHtml}

      <div style="margin-top:10px;color:var(--dim);font-size:9px;line-height:1.6;">
        <code style="color:var(--yellow)">tutorial</code> — current step<br>
        <code style="color:var(--yellow)">tutorial list</code> — section overview<br>
        <code style="color:var(--yellow)">tutorial &lt;N&gt;</code> — review step N<br>
        <code style="color:var(--yellow)">tutorial back</code> — previous step<br>
        <code style="color:var(--yellow)">tutorial restart</code> — start over
      </div>
    `;
  }

  function renderStory(el) {
    const beats = (state.story_beats || []).slice().reverse();
    // Friendly display names for known beats
    const beatNames = {
      'nexus_log_read':   '📄 Nexus log read — CHIMERA traffic found',
      'passwd_read':      '👤 /etc/passwd enumerated',
      'shadow_read':      '🔑 /etc/shadow accessed — root achieved',
      'master_key_found': '🗝 Master key retrieved',
      'chimera_connected':'📡 Connected to CHIMERA control socket',
      'chimera_exploited':'💥 CHIMERA exploited',
      'data_exfiltrated': '📤 Data exfiltrated to Ada',
      'ghost_ascended':   '🌐 Ghost ascended — mission complete',
      'ada_contacted':    '🤝 Ada contacted — handler briefed',
      'suid_found':       '⚠ SUID binary located',
      'root_shell':       '# Root shell obtained',
      'tutorial_complete':'✓ Tutorial completed',
    };
    const beatHtml = beats.length
      ? beats.map(b => {
          const label = beatNames[b] || ('✓ ' + b.replace(/_/g, ' '));
          return `<div class="beat-item">${esc(label)}</div>`;
        }).join('')
      : '<div style="color:var(--dim);font-size:10px;">No story beats yet.<br>Progress through the tutorial to unlock story events.</div>';

    el.innerHTML = `
      <div class="section-title">Story Beats <span style="color:var(--dim);font-weight:normal;font-size:9px;">${beats.length} unlocked</span></div>
      ${beatHtml}
      <div class="section-title" style="margin-top:14px;">Mission Path</div>
      <div style="font-size:9px;color:var(--dim);line-height:1.9;">
        ${[
          ['sudo -l',                              'find NOPASSWD privilege'],
          ['sudo find . -exec /bin/sh \\;',        'GTFOBins root shell'],
          ['cat /etc/shadow',                      'read password hashes'],
          ['cat /opt/chimera/keys/master.key',     'retrieve master key'],
          ['nc chimera-control 8443',              'connect to CHIMERA'],
          ['exploit chimera',                      'run payload'],
          ['exfil',                                'upload evidence to Ada'],
          ['ascend',                               'mission complete'],
        ].map(([cmd, desc], i) =>
          `<div style="display:flex;gap:6px;align-items:baseline;">
            <span style="color:var(--dim);min-width:12px;">${i+1}.</span>
            <code onclick="tutCmdClick('${cmd.replace(/'/g,"\\'")}')" style="color:var(--yellow);cursor:pointer;" title="Click to run">${esc(cmd)}</code>
            <span style="color:var(--dim);">— ${esc(desc)}</span>
          </div>`
        ).join('')}
      </div>
    `;
  }

  function renderHelp(el) {
    const helpGroups = [
      {title:'Navigation', cmds:[
        ['pwd',          'print working directory'],
        ['ls -la',       'list files (hidden too)'],
        ['cd /path',     'change directory'],
        ['cat <file>',   'read file contents'],
        ['grep PAT file','search for pattern'],
      ]},
      {title:'Keyboard Shortcuts', cmds:[
        ['Tab',          'autocomplete command'],
        ['↑ / ↓',        'history navigation'],
        ['Ctrl+C',       'cancel current input'],
        ['Ctrl+L',       'clear terminal'],
        ['Ctrl+U',       'clear to line start'],
      ]},
      {title:'Game Commands', cmds:[
        ['tutorial',     'show current tutorial step'],
        ['tutorial list','section overview'],
        ['tutorial <N>', 'review step N'],
        ['skills',       'skill matrix'],
        ['inventory',    'item loadout'],
        ['talk ada',     'contact handler'],
        ['status',       'mission status'],
        ['map',          'network map'],
      ]},
      {title:'Terminal Commands', cmds:[
        ['help',         'all available commands'],
        ['history',      'command history'],
        ['uname -a',     'system info'],
        ['ps aux',       'running processes'],
        ['ss -tulpn',    'open ports'],
        ['find / -perm -u=s', 'SUID binaries'],
      ]},
      {title:'Meta / Agents', cmds:[
        ['meta',         'ecosystem overview'],
        ['serena',       'Serena intelligence layer'],
        ['environment',  'detect current runtime'],
        ['agents',       'agent roster'],
        ['swarm',        'open Swarm Console tab'],
      ]},
    ];
    el.innerHTML = `
      ${helpGroups.map(g => `
        <div class="section-title">${esc(g.title)}</div>
        <div style="font-size:9px;color:var(--dim);line-height:1.8;margin-bottom:6px;">
          ${g.cmds.map(([cmd, desc]) =>
            `<div style="display:flex;gap:6px;">
              <code onclick="tutCmdClick('${cmd.replace(/'/g,"\\'")}${cmd.includes('<') || cmd.includes('/') ? '' : ''}')" style="color:var(--yellow);cursor:pointer;min-width:120px;flex-shrink:0;" title="Click to run">${esc(cmd)}</code>
              <span>${esc(desc)}</span>
            </div>`
          ).join('')}
        </div>
      `).join('')}
      <div class="section-title">Interfaces</div>
      <div style="font-size:9px;color:var(--dim);line-height:1.8;">
        <a href="/game/" style="color:var(--cyan);">/game/</a> — Story mode (graphical panels)<br>
        <a href="/game-cli/" style="color:var(--purple);">/game-cli/</a> — Swarm Console (this)<br>
        <a href="/api/docs" style="color:var(--dim);">/api/docs</a> — REST API reference
      </div>
    `;
  }

  function renderAgentsPanel(el) {
    if (!agentsPanelUnlocked) {
      el.innerHTML = `<div style="color:var(--dim);font-size:10px;padding:10px;text-align:center;">
        AGENTS PANEL LOCKED<br><br>
        <span style="color:var(--yellow)">Reach level 15</span> or discover<br>the hidden pathway.<br><br>
        <span style="color:var(--cyan)">Hint: ask RAV≡N about contact.</span>
      </div>`;
      return;
    }

    el.style.padding = '0';
    const currentAgent = agents.find(a => a.id === selectedAgentId);
    const history = selectedAgentId ? loadAgentHistory(selectedAgentId) : [];

    el.innerHTML = `
      <div id="agents-panel">
        <div id="agent-roster">
          ${agents.map(a => `
            <div class="agent-row ${a.unlocked ? '' : 'locked'} ${a.id === selectedAgentId ? 'selected' : ''}"
                 data-agent="${a.id}" onclick="${a.unlocked ? `selectAgent('${a.id}')` : ''}">
              <div class="agent-dot" style="background:${a.faction_color}"></div>
              <div class="agent-info">
                <div class="agent-name">${esc(a.name)}</div>
                <div class="agent-pseudo">${a.unlocked ? esc(a.pseudo || '') : '???'}</div>
              </div>
              <div class="agent-trust-mini" style="color:${a.faction_color}">
                ${a.unlocked ? `T:${a.trust}` : '🔒'}
              </div>
            </div>
          `).join('')}
        </div>

        ${currentAgent ? renderAgentDetail(currentAgent) : ''}

        <div id="agent-chat">
          ${history.length === 0 ? `<div class="chat-msg system">[Establish contact by sending a message]</div>` : ''}
          ${history.map(m => renderChatMsg(m)).join('')}
        </div>

        ${currentAgent && currentAgent.unlocked ? `
          <div id="agent-input-row">
            <input id="agent-input" type="text" placeholder="Message ${esc(currentAgent.name)}..." autocomplete="off"
              onkeydown="if(event.key==='Enter')sendAgentMessage()"/>
            <button id="agent-send" onclick="sendAgentMessage()">SEND</button>
          </div>
        ` : ''}
      </div>
    `;

    // Scroll chat to bottom
    const chat = el.querySelector('#agent-chat');
    if (chat) chat.scrollTop = chat.scrollHeight;
  }

  function renderAgentDetail(agent) {
    const isHostile = ['malice', 'chimera'].includes(agent.id) && agent.trust < 10;
    const trustHigh = agent.trust > 80;
    const relLinks = {
      'ada': 'ADA ← allies → RAV≡N',
      'malice': 'MALICE ← rivals → ADA',
      'nova': 'NOVA ← tensions → RESISTANCE',
      'raven': 'RAV≡N ← mentor → ADA',
    };
    return `
      <div id="agent-detail">
        <div class="agent-detail-header">
          <div class="agent-badge" style="background:${agent.faction_color}22;border:1px solid ${agent.faction_color}40;color:${agent.faction_color}">
            ${agent.name.substring(0,2)}
          </div>
          <div>
            <div class="agent-detail-name" style="color:${agent.faction_color}">${esc(agent.name)}</div>
            <div class="agent-detail-faction">${esc(agent.pseudo || '')} · ${esc(agent.faction || '').toUpperCase()}</div>
          </div>
        </div>
        ${isHostile ? `<div class="hostile-banner">⚠ HOSTILE — APPROACH WITH CAUTION ⚠</div>` : ''}
        <div class="trust-row">
          <span class="trust-label">TRUST</span>
          <div class="trust-track"><div class="trust-fill" style="width:${agent.trust}%;background:var(--green)"></div></div>
          <span class="trust-val">${agent.trust}</span>
        </div>
        <div class="trust-row">
          <span class="trust-label">RESPECT</span>
          <div class="trust-track"><div class="trust-fill" style="width:${agent.respect}%;background:var(--cyan)"></div></div>
          <span class="trust-val">${agent.respect}</span>
        </div>
        <div class="trust-row">
          <span class="trust-label">FEAR</span>
          <div class="trust-track"><div class="trust-fill" style="width:${agent.fear}%;background:var(--red)"></div></div>
          <span class="trust-val">${agent.fear}</span>
        </div>
        ${relLinks[agent.id] ? `<div class="relation-link">⟷ ${relLinks[agent.id]}</div>` : ''}
        ${trustHigh && agent.agenda ? `
          <div class="classified-section">
            <div class="classified-title">⬛ CLASSIFIED — TRUST THRESHOLD MET</div>
            <div class="classified-text">${esc(agent.agenda)}</div>
          </div>
        ` : ''}
      </div>
    `;
  }

  function renderChatMsg(m) {
    if (m.role === 'player') {
      return `<div class="chat-msg player"><span class="msg-prefix">GHOST &gt; </span><span class="msg-text">${esc(m.content)}</span></div>`;
    } else if (m.role === 'agent') {
      const color = m.color || 'var(--cyan)';
      return `<div class="chat-msg agent"><span class="msg-prefix" style="color:${color}">${esc(m.agentName || 'AGENT')} &gt; </span><span class="msg-text">${esc(m.content)}</span></div>`;
    } else if (m.role === 'trust_delta') {
      return `<div class="chat-msg trust-delta">▲ ${esc(m.content)}</div>`;
    } else if (m.role === 'signal_lost') {
      return `<div class="chat-msg signal-lost">⚡ SIGNAL LOST — CONNECTION INTERRUPTED ⚡</div>`;
    }
    return `<div class="chat-msg system">${esc(m.content)}</div>`;
  }

  function renderFactions(el) {
    if (!factions.length) {
      loadFactions().then(() => renderSidebar('factions'));
      el.innerHTML = '<div style="color:var(--dim);font-size:10px;padding:10px;">Loading faction data...</div>';
      return;
    }
    el.innerHTML = `
      <div class="section-title">Faction Standing</div>
      ${factions.map(f => {
        const standingColor = {
          TRUSTED: 'var(--green)', ALLIED: 'var(--cyan)', NEUTRAL: 'var(--dim)',
          WARY: 'var(--orange)', HOSTILE: 'var(--red)',
        }[f.standing] || 'var(--dim)';
        return `
          <div class="faction-block">
            <div class="faction-header">
              <div class="faction-dot" style="background:${f.color}"></div>
              <span class="faction-name" style="color:${f.color}">${esc(f.name)}</span>
              <span class="faction-standing" style="color:${standingColor}">${f.standing}</span>
            </div>
            <div class="faction-desc">${esc(f.description)}</div>
            <div class="faction-rep-track">
              <div class="faction-rep-fill" style="width:${f.rep}%;background:${f.color}"></div>
            </div>
            <div class="faction-perks">Unlocked: ${(f.current_perks || []).join(' · ') || 'None'}</div>
            ${(f.conflicts || []).map(c => `<div class="faction-conflict">⚠ ${esc(c)}</div>`).join('')}
          </div>
        `;
      }).join('')}
    `;
  }

  function renderHOF(el) {
    el.innerHTML = `
      <div class="section-title" style="color:var(--gold)">Hall of Fame</div>
      <div style="color:var(--dim);font-size:10px;margin-bottom:10px;">Top operators who reached transcendence.</div>
      ${[
        {rank:'#1', name:'GHOST_PRIME', score:'∞', note:'The First'},
        {rank:'#2', name:'NULLBYTE', score:'99,420', note:'Phase 8'},
        {rank:'#3', name:'CIPHER_X', score:'88,200', note:'Phase 7'},
        {rank:'#4', name:'DARKVECTOR', score:'77,100', note:'Phase 6'},
        {rank:'#5', name:'YOU?', score:'—', note:'Your journey'},
      ].map(e => `
        <div class="hof-entry">
          <span class="hof-rank">${e.rank}</span>
          <span class="hof-score">${e.score}</span>
          <div class="hof-name">${e.name}</div>
          <div style="color:var(--dim);font-size:9px;">${e.note}</div>
        </div>
      `).join('')}
      <div style="color:var(--dim);font-size:9px;margin-top:12px;line-height:1.6;">
        Your current score: <span style="color:var(--gold)">${state ? ((state.level * 500) + state.xp) : 0}</span>
      </div>
    `;
  }

  function renderMeta(el) {
    el.innerHTML = `
      <div id="meta-console">
        <div class="section-title" style="color:var(--orange)">Meta-Developer Console</div>
        <div class="section-title">Raw State Dump</div>
        <div class="grid2" style="margin-bottom:10px;">
          <span class="lbl">Level</span><span class="val">${state.level}</span>
          <span class="lbl">XP</span><span class="val">${state.xp}</span>
          <span class="lbl">Commands</span><span class="val">${state.commands_run}</span>
          <span class="lbl">Tutorial</span><span class="val">${state.tutorial_step}</span>
          <span class="lbl">Challenges</span><span class="val">${(state.completed_challenges||[]).length}</span>
          <span class="lbl">Dev Mode</span><span class="val" style="color:${state.dev_mode?'var(--green)':'var(--red)'}">
            ${state.dev_mode ? 'ON' : 'OFF'}
          </span>
          <span class="lbl">Phase</span><span class="val" style="color:var(--orange)">${uiPhase}</span>
          <span class="lbl">ARG Signals</span><span class="val">${metaLogs.length}</span>
        </div>
        <div class="section-title">ARG Signal Log</div>
        ${metaLogs.length === 0
          ? `<div class="meta-log-line">Awaiting transmissions...</div>`
          : metaLogs.slice().reverse().slice(0, 10).map(m => `
              <div class="meta-log-line source-${(m.source||'').toLowerCase().split(' ')[0].replace('≡','').replace('_','')}">
                [${esc(m.source||'?')}] ${esc(m.msg||'')}
              </div>
            `).join('')
        }
        <div class="section-title">Modding API</div>
        <div style="color:var(--dim);font-size:9px;line-height:1.7;">
          <code style="color:var(--cyan)">GET /api/game/agents</code><br>
          <code style="color:var(--cyan)">POST /api/game/agent/talk</code><br>
          <code style="color:var(--cyan)">GET /api/game/faction/status</code><br>
          <code style="color:var(--cyan)">GET /api/game/arg/signal</code><br>
          <code style="color:var(--cyan)">POST /api/script/run</code><br>
        </div>
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
          <button onclick="fetchArgSignal()" style="
            background:none;border:1px solid var(--orange);color:var(--orange);
            font-family:inherit;font-size:9px;padding:3px 8px;cursor:pointer;
            border-radius:3px;letter-spacing:1px;
          ">FETCH SIGNAL</button>
          <button onclick="fetchArchetype()" style="
            background:none;border:1px solid var(--cyan);color:var(--cyan);
            font-family:inherit;font-size:9px;padding:3px 8px;cursor:pointer;
            border-radius:3px;letter-spacing:1px;
          ">SCAN ARCHETYPE</button>
        </div>
        <div id="meta-archetype-panel" style="margin-top:8px;"></div>
      </div>
    `;
  }

  window.fetchArchetype = async function() {
    if (!sessionId) return;
    try {
      const data = await apiGet(`/api/ml/archetype?session_id=${sessionId}`);
      const panel = document.getElementById('meta-archetype-panel');
      if (!panel) return;
      if (data.archetype) {
        const arcColor = {
          explorer: 'var(--cyan)', fighter: 'var(--red)', social: 'var(--green)',
          builder: 'var(--orange)', balanced: 'var(--purple)', newcomer: 'var(--dim)',
        }[data.archetype] || 'var(--dim)';
        panel.innerHTML = `
          <div class="section-title">Player Model</div>
          <div style="color:${arcColor};font-size:11px;font-weight:bold;margin-bottom:4px;">
            ${data.archetype.toUpperCase()} (${Math.round((data.confidence||0)*100)}%)
          </div>
          <div style="color:var(--dim);font-size:9px;margin-bottom:6px;">Recommended next actions:</div>
          ${(data.suggestions||[]).map(s => `
            <div style="color:var(--white);font-size:10px;margin-bottom:2px;cursor:pointer;"
              onclick="document.getElementById('agent-input') && false; term.focus();"
            >⟩ ${esc(s)}</div>
          `).join('')}
        `;
      }
    } catch(e) {}
  };

  // ── Swarm Console ─────────────────────────────────────────────────
  function updateSwarmBadge() {
    const badge = document.getElementById('swarm-badge');
    if (!badge) return;
    if (swarmUnread > 0 && currentTab !== 'swarm') {
      badge.style.display = 'inline-block';
      badge.textContent = swarmUnread > 9 ? '9+' : String(swarmUnread);
    } else {
      badge.style.display = 'none';
    }
  }

  function swarmTimestamp(ts) {
    const d = ts ? new Date(ts * 1000) : new Date();
    return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'});
  }

  function renderSwarmMsg(m) {
    const senderKey = (m.sender || 'system').toLowerCase();
    const isGhost = senderKey === 'ghost' || senderKey === 'player';
    const cls = isGhost ? 'from-ghost' : (senderKey === 'system' ? 'from-system' : '');
    const color = m.color || (isGhost ? 'var(--cyan)' : '#c8d8ec');
    return `
      <div class="swarm-msg ${cls}">
        <span class="swarm-sender" style="color:${esc(color)}">${esc(m.sender || 'SYSTEM')}</span>
        <span class="swarm-ts">${esc(swarmTimestamp(m.ts))}</span>
        <div class="swarm-text">${esc(m.text || '')}</div>
      </div>`;
  }

  function renderSwarm(el) {
    const rooms = ['general', 'dev', 'lore', 'alerts'];
    el.innerHTML = `
      <div id="swarm-panel">
        <div id="swarm-header">
          <div class="swarm-title">
            <span id="swarm-status-dot" class="${swarmConnected ? 'live' : ''}"></span>
            SWARM CONSOLE
          </div>
          <div class="swarm-status">
            ${swarmConnected ? 'Ψ-link active · agents online' : 'Connecting to lattice...'}
          </div>
        </div>
        <div id="swarm-room-row">
          ${rooms.map(r => `<button class="swarm-room-btn ${r === swarmRoom ? 'active' : ''}"
            onclick="switchSwarmRoom('${r}')">#${r}</button>`).join('')}
        </div>
        <div id="swarm-messages">
          ${swarmMessages.filter(m => m.room === swarmRoom).slice(-60).map(renderSwarmMsg).join('') || '<div style="color:var(--dim);font-size:9px;padding:8px 0;">No messages yet in #' + swarmRoom + '</div>'}
        </div>
        <div id="swarm-input-row">
          <input id="swarm-input" type="text" placeholder="Message #${swarmRoom}..."
            autocomplete="off" onkeydown="if(event.key==='Enter')sendSwarmMsg()"/>
          <button id="swarm-send" onclick="sendSwarmMsg()">SEND</button>
        </div>
        <div style="color:var(--dim);font-size:8px;margin-top:6px;border-top:1px solid var(--border);padding-top:4px;line-height:1.6;">
          Agents post here via <code style="color:var(--purple)">POST /api/console/message</code><br>
          WS: <code style="color:var(--purple)">ws://…/ws/console</code>
        </div>
      </div>`;
    const msgs = el.querySelector('#swarm-messages');
    if (msgs) msgs.scrollTop = msgs.scrollHeight;
  }

  window.switchSwarmRoom = function(room) {
    swarmRoom = room;
    if (currentTab === 'swarm') renderSwarm(document.getElementById('sidebar-content'));
  };

  window.sendSwarmMsg = function() {
    const input = document.getElementById('swarm-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    const msg = { sender: 'Ghost', text, room: swarmRoom, ts: Date.now() / 1000, color: 'var(--cyan)', type: 'chat' };
    if (swarmWs && swarmWs.readyState === WebSocket.OPEN) {
      swarmWs.send(JSON.stringify({ sender: 'Ghost', text, room: swarmRoom }));
    } else {
      // Fallback: HTTP post
      fetch('/api/console/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sender: 'Ghost', text, room: swarmRoom }),
      }).catch(() => {});
      swarmMessages.push(msg);
      if (currentTab === 'swarm') renderSwarm(document.getElementById('sidebar-content'));
    }
  };

  function initConsoleWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}/ws/console`;
    try {
      swarmWs = new WebSocket(url);
    } catch (e) { return; }

    swarmWs.onopen = () => {
      swarmConnected = true;
      const dot = document.getElementById('swarm-status-dot');
      if (dot) dot.classList.add('live');
    };

    swarmWs.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === 'chat') {
          swarmMessages.push(msg);
          if (swarmMessages.length > 400) swarmMessages.shift();
          if (currentTab === 'swarm') {
            renderSwarm(document.getElementById('sidebar-content'));
          } else {
            swarmUnread++;
            updateSwarmBadge();
          }
        }
      } catch (e) {}
    };

    swarmWs.onclose = () => {
      swarmConnected = false;
      const dot = document.getElementById('swarm-status-dot');
      if (dot) dot.classList.remove('live');
      // Reconnect after 5s
      setTimeout(initConsoleWS, 5000);
    };

    swarmWs.onerror = () => { swarmWs.close(); };
  }

  // ── Activity feed WebSocket (U3) ───────────────────────────────────
  // Connects to /ws/ambient — captures agent lore push events as a
  // live activity log in the ACTIVITY sidebar tab.
  const _AGENT_COLORS = {
    ada: 'var(--cyan)', gordon: 'var(--yellow)', serena: 'var(--purple)',
    raven: 'var(--green)', zod: 'var(--red)', the_librarian: '#9b9', culture_ship: '#68f',
  };

  function updateActivityBadge() {
    const badge = document.getElementById('activity-badge');
    if (!badge) return;
    if (activityUnread > 0 && currentTab !== 'activity') {
      badge.style.display = 'block';
      badge.textContent = activityUnread > 9 ? '9+' : String(activityUnread);
    } else {
      badge.style.display = 'none';
    }
  }

  function renderActivity(el) {
    const dot = activityConnected
      ? `<span style="color:var(--cyan)">●</span> LIVE`
      : `<span style="color:var(--dim)">○</span> connecting…`;
    el.innerHTML = `
      <div style="padding:6px 8px 4px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;">
        <span style="color:var(--cyan);font-size:10px;letter-spacing:1px;">AGENT ACTIVITY</span>
        <span style="font-size:9px;color:var(--dim)">${dot}</span>
      </div>
      <div id="activity-feed" style="overflow-y:auto;flex:1;padding:6px 8px;font-size:10px;line-height:1.7;">
        ${activityFeed.length === 0
          ? `<div style="color:var(--dim);padding:10px 0;">[Waiting for agent transmissions…]</div>`
          : activityFeed.map(e => {
              const color = _AGENT_COLORS[e.agent] || 'var(--dim)';
              const ts = new Date(e.ts).toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false});
              return `<div style="margin-bottom:6px;">
                <span style="color:var(--dim);font-size:9px;">${ts}</span>
                <span style="color:${color};margin:0 4px;">[${e.agent.toUpperCase()}]</span>
                <span style="color:var(--text)">${esc(e.text)}</span>
              </div>`;
            }).join('')}
      </div>`;
    const feed = el.querySelector('#activity-feed');
    if (feed) feed.scrollTop = feed.scrollHeight;
  }

  let _actReconnectDelay = 2000;

  function initAmbientWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const sid = sessionId || 'game-cli';
    try {
      activityWs = new WebSocket(`${proto}://${location.host}/ws/ambient?session_id=${encodeURIComponent(sid)}`);
    } catch(e) {
      setTimeout(initAmbientWS, _actReconnectDelay);
      return;
    }

    activityWs.onopen = () => {
      activityConnected = true;
      _actReconnectDelay = 2000;
      if (currentTab === 'activity') renderActivity(document.getElementById('sidebar-content'));
    };

    activityWs.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === 'ping') {
          activityWs.send(JSON.stringify({type: 'pong'}));
        } else if ((msg.type === 'ambient' || msg.type === 'agent_msg') && msg.text) {
          // T2: agent_msg = real-time inter-agent bus message; ambient = timer-pushed lore
          const agentLabel = msg.type === 'agent_msg'
            ? `${(msg.from_agent || 'agent').toUpperCase()}${msg.to_agent ? ` \u2192 ${msg.to_agent.toUpperCase()}` : ''}`
            : (msg.agent || 'system');
          activityFeed.push({
            ts: Date.now(),
            agent: agentLabel,
            text: msg.text,
            bus: msg.type === 'agent_msg',
          });
          if (activityFeed.length > 100) activityFeed.shift();
          if (currentTab === 'activity') {
            renderActivity(document.getElementById('sidebar-content'));
          } else {
            activityUnread++;
            updateActivityBadge();
          }
        }
      } catch { /* ignore malformed frames */ }
    };

    activityWs.onclose = () => {
      activityConnected = false;
      if (currentTab === 'activity') renderActivity(document.getElementById('sidebar-content'));
      _actReconnectDelay = Math.min(_actReconnectDelay * 2, 30000);
      setTimeout(initAmbientWS, _actReconnectDelay);
    };

    activityWs.onerror = () => { activityWs.close(); };
  }

  // ── Agent selection & messaging ────────────────────────────────────
  window.selectAgent = function(agentId) {
    selectedAgentId = agentId;
    loadAgentHistory(agentId);
    renderSidebar('agents');
  };

  window.sendAgentMessage = async function() {
    if (!selectedAgentId) return;
    const inputEl = document.getElementById('agent-input');
    if (!inputEl) return;
    const msg = inputEl.value.trim();
    if (!msg) return;
    inputEl.value = '';

    const agent = agents.find(a => a.id === selectedAgentId);
    if (!agent || !agent.unlocked) return;

    pushMessage(selectedAgentId, {role: 'player', content: msg});

    const history = loadAgentHistory(selectedAgentId);
    const llmHistory = history.filter(m => m.role === 'player' || m.role === 'agent')
      .map(m => ({role: m.role === 'player' ? 'user' : 'assistant', content: m.content}));

    renderSidebar('agents');
    addTypingIndicator();

    try {
      const data = await apiPost('/api/game/agent/talk', {
        agent_id: selectedAgentId,
        message: msg,
        session_id: sessionId,
        history: llmHistory.slice(-6),
      });

      removeTypingIndicator();

      if (data.ok) {
        pushMessage(selectedAgentId, {
          role: 'agent', content: data.response,
          agentId: selectedAgentId, agentName: data.agent_name,
          color: data.faction_color,
        });
        if (data.trust_delta && data.trust_delta > 0) {
          pushMessage(selectedAgentId, {
            role: 'trust_delta',
            content: `+${data.trust_delta} trust with ${data.agent_name}`,
          });
          const a = agents.find(x => x.id === selectedAgentId);
          if (a) a.trust = Math.min(100, (a.trust || 0) + data.trust_delta);
        }
        if (selectedAgentId === 'raven') {
          updateRavenWidget(data.response);
        }
      } else {
        pushMessage(selectedAgentId, {role: 'signal_lost'});
      }
    } catch(e) {
      removeTypingIndicator();
      pushMessage(selectedAgentId, {role: 'signal_lost'});
    }

    renderSidebar('agents');
  };

  function addTypingIndicator() {
    const chat = document.getElementById('agent-chat');
    if (!chat) return;
    const el = document.createElement('div');
    el.className = 'chat-msg system typing-indicator';
    el.id = 'typing-indicator';
    el.textContent = '[transmitting...]';
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
  }

  function removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  // ── RAV≡N widget ──────────────────────────────────────────────────
  function updateRavenWidget(msg) {
    ravenLastMsg = msg;
    const el = document.getElementById('raven-widget-msg');
    if (el) el.textContent = msg.length > 60 ? msg.substring(0, 60) + '...' : msg;
    document.getElementById('raven-widget').classList.add('has-message');
    setTimeout(() => {
      document.getElementById('raven-widget').classList.remove('has-message');
    }, 8000);
  }

  function updateRavenWidgetFromAgents() {
    const raven = agents.find(a => a.id === 'raven');
    if (!raven || !raven.intro) return;
    const history = loadAgentHistory('raven');
    if (history.length === 0) {
      updateRavenWidget(raven.intro || 'Signal detected...');
    }
  }

  window.openAgentPanel = function(agentId) {
    if (agentId) selectedAgentId = agentId;
    if (!agentsPanelUnlocked) return;
    const tab = document.querySelector('[data-tab="agents"]');
    if (tab && !tab.classList.contains('hidden')) {
      renderSidebar('agents');
      const sidebar = document.getElementById('sidebar');
      if (sidebar) sidebar.style.display = 'flex';
    }
  };

  // ── ARG signal fetch (for meta console button) ────────────────────
  window.fetchArgSignal = async function() {
    try {
      const data = await apiGet('/api/game/arg/signal');
      if (data.msg) {
        metaLogs.push({source: data.source, msg: data.msg, ts: Date.now()});
        renderSidebar('meta');
      }
    } catch(e) {}
  };

  // ── Settings ──────────────────────────────────────────────────────
  window.openSettings = function() {
    document.getElementById('settings-modal').classList.add('open');
  };
  window.closeSettings = function() {
    document.getElementById('settings-modal').classList.remove('open');
  };

  document.getElementById('setting-fontsize').addEventListener('input', function() {
    term.options.fontSize = parseInt(this.value);
    fitAddon.fit();
  });

  document.getElementById('settings-modal').addEventListener('click', function(e) {
    if (e.target === this) closeSettings();
  });

  // ── Tab completion ────────────────────────────────────────────────
  function handleTab() {
    const parts = inputBuffer.split(' ');
    const last = parts[parts.length - 1];

    if (tabCandidates.length === 0) {
      if (parts.length === 1) {
        tabCandidates = availableCommands.filter(c => c.startsWith(last)).sort();
      } else {
        tabCandidates = [
          '/home/ghost/', '/var/log/', '/etc/', '/opt/chimera/', '/proc/1337/',
          '/dev/', '/usr/share/wordlists/',
        ].filter(p => p.startsWith(last));
      }
      tabIdx = 0;
    }

    if (!tabCandidates.length) return;

    if (tabCandidates.length === 1) {
      const match = tabCandidates[0];
      parts[parts.length - 1] = match + (parts.length === 1 ? ' ' : '');
      const newInput = parts.join(' ');
      clearInput();
      inputBuffer = newInput;
      term.write(inputBuffer);
      tabCandidates = [];
    } else {
      const match = tabCandidates[tabIdx];
      parts[parts.length - 1] = match;
      const newInput = parts.join(' ');
      clearInput();
      inputBuffer = newInput;
      term.write(inputBuffer);
      tabIdx = (tabIdx + 1) % tabCandidates.length;
      if (tabIdx === 1) {
        term.writeln('');
        term.writeln(tabCandidates.join('  '));
        term.write(getPrompt() + inputBuffer);
      }
    }
  }

  function clearInput() {
    term.write('\r' + getPrompt());
    for (let i = 0; i < inputBuffer.length + 2; i++) term.write(' ');
    term.write('\r' + getPrompt());
    inputBuffer = '';
  }

  // ── Input handling ────────────────────────────────────────────────
  term.onKey(({ key, domEvent }) => {
    const ev = domEvent;

    if (ev.key === 'Tab') {
      ev.preventDefault();
      handleTab();
      return;
    }
    if (ev.key !== 'Shift') tabCandidates = [];

    if (ev.key === 'Enter') {
      const cmd = inputBuffer;
      inputBuffer = '';
      histIdx = -1;
      runCommand(cmd);
      return;
    }

    if (ev.key === 'Backspace') {
      if (inputBuffer.length > 0) {
        inputBuffer = inputBuffer.slice(0, -1);
        term.write('\b \b');
      }
      return;
    }

    if (ev.key === 'ArrowUp') {
      if (historyArr.length) {
        histIdx = Math.min(histIdx + 1, historyArr.length - 1);
        const h = historyArr[historyArr.length - 1 - histIdx];
        clearInput();
        inputBuffer = h;
        term.write(h);
      }
      return;
    }

    if (ev.key === 'ArrowDown') {
      histIdx = Math.max(histIdx - 1, -1);
      const h = histIdx >= 0 ? historyArr[historyArr.length - 1 - histIdx] : '';
      clearInput();
      inputBuffer = h;
      term.write(h);
      return;
    }

    if (ev.ctrlKey && ev.key === 'l') {
      term.clear();
      term.write(getPrompt() + inputBuffer);
      return;
    }

    if (ev.ctrlKey && ev.key === 'c') {
      term.writeln('^C');
      inputBuffer = '';
      histIdx = -1;
      showPrompt();
      return;
    }

    if (ev.ctrlKey || ev.altKey) return;

    if (key.length === 1) {
      inputBuffer += key;
      term.write(key);
    }
  });

  // ── Sidebar tab clicks ────────────────────────────────────────────
  document.querySelectorAll('.stab').forEach(tab => {
    tab.addEventListener('click', () => {
      if (!tab.classList.contains('hidden')) {
        renderSidebar(tab.dataset.tab);
      }
    });
  });

  // ── Boot ──────────────────────────────────────────────────────────
  initSession();
  initConsoleWS();
  initAmbientWS();
})();
