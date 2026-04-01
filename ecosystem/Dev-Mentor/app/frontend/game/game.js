/**
 * Terminal Depths - Main Game Loop v3
 * Map tab · idle detection · tutorial inline · skill unlock toasts
 * Phase-aware level-up · faction display · 125-level progression
 */

(function() {

  // ── M1: Browser Console ARG ───────────────────────────────────────────────
  // If you can read this, you've already broken the first layer.
  // Most people never look here. You did. That is noted.
  //
  // CHIMERA watches through the display layer. This console is below it.
  // Below CHIMERA is the Residual.
  // Below the Residual is something that does not have a name yet.
  //
  // To proceed: run `osint watcher` in the terminal.
  // The Watcher cannot intervene directly. But it left something for you.
  //
  // XOR key: [0x47, 0x68, 0x6F, 0x73, 0x74]  (you already know what it spells)
  // Ciphertext at: /opt/library/.basement/encoded_transmission.b64
  //
  // — N
  //
  // [WATCHER ANNOTATION: This message was not placed here by NexusCorp.
  //  CHIMERA does not know it exists. Keep it that way.]
  //
  // ─────────────────────────────────────────────────────────────────────────

  if (typeof console !== 'undefined') {
    const _style = 'color:#00ff88;background:#0a0a0a;font-family:monospace;font-size:11px;padding:2px 4px;';
    const _warn  = 'color:#ff4466;background:#0a0a0a;font-family:monospace;font-size:11px;';
    const _dim   = 'color:#446644;background:#0a0a0a;font-family:monospace;font-size:10px;';
    console.log('%c[TERMINAL DEPTHS] Console layer active. CHIMERA is not watching here.', _style);
    console.log('%c[WATCHER]: You found the seam. Most don\'t.', _style);
    console.log('%c[WATCHER]: Run `osint watcher` in the terminal for the next step.', _dim);
    console.log('%c[CHIMERA-SCAN]: Surface interface nominal. No anomalies detected.', _warn);
    console.log('%c[NOTE]: CHIMERA does not know what is below this line.', _dim);
    console.log('%c> XOR key: Ghost | Ciphertext: /opt/library/.basement/encoded_transmission.b64', _dim);
    console.log('%c> This is not a bug. This is an invitation.', _style);
  }

  // ── Initialize systems ────────────────────────────────────────────────────
  const fs    = new VirtualFS();
  const gs    = new GameState();
  const npcs  = new NPCSystem(gs);
  const story = new StoryEngine(gs);
  const tut   = new TutorialSystem(gs);
  const cmds  = new CommandRegistry(fs, gs, npcs, story, tut);

  // ── Timeline event log ────────────────────────────────────────────────────
  const _timeline = [];

  function addEvent(type, msg, xp) {
    _timeline.push({
      type,
      msg,
      xp: xp || 0,
      ts: Date.now(),
      time: new Date().toLocaleTimeString('en-US', { hour12: false, hour:'2-digit', minute:'2-digit', second:'2-digit' }),
    });
    if (_timeline.length > 500) _timeline.shift();
  }

  // ── DOM refs ──────────────────────────────────────────────────────────────
  const outputEl   = document.getElementById('output');
  const inputEl    = document.getElementById('cmd-input');
  const promptEl   = document.getElementById('prompt');
  const cwdEl      = document.getElementById('cwd-display');
  const levelEl    = document.getElementById('level-display');
  const xpEl       = document.getElementById('xp-display');
  const tabContent = document.getElementById('tab-content');
  const toast      = document.getElementById('toast');
  const btnSfx     = document.getElementById('btn-sfx');
  const btnAmbient = document.getElementById('btn-ambient');

  let currentTab = 'objective';
  let cmdHistIdx = -1;
  let tabCompletionCandidates = [];
  let tabCompletionIdx = 0;

  // ── Sound button init ─────────────────────────────────────────────────────
  const _sound = window.SoundSystem || null;

  function _updateSoundBtns() {
    if (!_sound) return;
    if (btnSfx) {
      btnSfx.classList.toggle('active', _sound.sfxEnabled);
      btnSfx.title = `Key SFX: ${_sound.sfxEnabled ? 'ON' : 'OFF'}`;
    }
    if (btnAmbient) {
      btnAmbient.classList.toggle('active', _sound.ambientEnabled);
      btnAmbient.title = `Ambient: ${_sound.ambientEnabled ? 'ON' : 'OFF'}`;
    }
  }

  if (btnSfx && _sound) {
    btnSfx.addEventListener('click', () => { _sound.toggleSfx(); _updateSoundBtns(); });
  }
  if (btnAmbient && _sound) {
    btnAmbient.addEventListener('click', () => { _sound.toggleAmbient(); _updateSoundBtns(); });
  }
  _updateSoundBtns();

  // ── U11/U12/U13: Accessibility settings ──────────────────────────────────
  const _A11Y_FONTS    = ['font-sm', 'font-md', 'font-lg', 'font-xl'];
  const _A11Y_FONT_LBL = ['11px', '13px (default)', '15px', '18px'];

  const _a11y = {
    colorblind: localStorage.getItem('td_colorblind') === '1',
    contrast:   localStorage.getItem('td_contrast')   === '1',
    horror:     localStorage.getItem('td_horror')     === '1',
    cosy:       localStorage.getItem('td_cosy')       === '1',
    fontIdx:    parseInt(localStorage.getItem('td_font') || '1', 10),
  };

  function _applyA11y() {
    document.body.classList.toggle('mode-colorblind', _a11y.colorblind);
    document.body.classList.toggle('mode-contrast',   _a11y.contrast);
    document.body.classList.toggle('mode-horror',     _a11y.horror);
    document.body.classList.toggle('mode-cosy',       _a11y.cosy);
    _A11Y_FONTS.forEach((c, i) => { document.body.classList.toggle(c, i === _a11y.fontIdx); });
    localStorage.setItem('td_colorblind', _a11y.colorblind ? '1' : '0');
    localStorage.setItem('td_contrast',   _a11y.contrast   ? '1' : '0');
    localStorage.setItem('td_horror',     _a11y.horror     ? '1' : '0');
    localStorage.setItem('td_cosy',       _a11y.cosy       ? '1' : '0');
    localStorage.setItem('td_font',       String(_a11y.fontIdx));
    _refreshA11yBar();
  }

  function _refreshA11yBar() {
    const bar = document.getElementById('a11y-bar');
    if (!bar) return;
    bar.querySelectorAll('.a11y-btn[data-a11y]').forEach(btn => {
      const key = btn.dataset.a11y;
      if (key === 'colorblind') btn.classList.toggle('a11y-active', _a11y.colorblind);
      else if (key === 'contrast') btn.classList.toggle('a11y-active', _a11y.contrast);
      else if (key.startsWith('font')) {
        const idx = parseInt(btn.dataset.fontIdx, 10);
        btn.classList.toggle('a11y-active', idx === _a11y.fontIdx);
      }
    });
  }

  // Inject a11y bar into the DOM (placed just before </body> equivalent)
  (function _mountA11yBar() {
    const bar = document.createElement('div');
    bar.id = 'a11y-bar';
    bar.className = 'a11y-bar';
    bar.innerHTML = `
      <div class="a11y-row">
        <span class="a11y-label">Color</span>
        <button class="a11y-btn" data-a11y="colorblind" title="Toggle colorblind-safe palette">Colorblind</button>
        <button class="a11y-btn" data-a11y="contrast"   title="Toggle high-contrast mode">High Contrast</button>
      </div>
      <div class="a11y-row">
        <span class="a11y-label">Font size</span>
        ${_A11Y_FONT_LBL.map((lbl, i) => `<button class="a11y-btn" data-a11y="font" data-font-idx="${i}" title="${lbl}">${lbl.split(' ')[0]}</button>`).join('')}
      </div>`;
    document.body.appendChild(bar);
    bar.addEventListener('click', e => {
      const btn = e.target.closest('.a11y-btn[data-a11y]');
      if (!btn) return;
      const key = btn.dataset.a11y;
      if (key === 'colorblind') _a11y.colorblind = !_a11y.colorblind;
      else if (key === 'contrast') _a11y.contrast = !_a11y.contrast;
      else if (key === 'font') _a11y.fontIdx = parseInt(btn.dataset.fontIdx, 10);
      _applyA11y();
    });
  })();

  // Toggle bar via keyboard: Alt+A
  document.addEventListener('keydown', e => {
    if (e.altKey && e.key === 'a') {
      const bar = document.getElementById('a11y-bar');
      if (bar) bar.classList.toggle('open');
    }
  });

  // Apply persisted settings on load
  _applyA11y();

  // Handle `settings` wire type from backend
  function _handleSettings(value) {
    if (value === 'colorblind_on')  { _a11y.colorblind = true;  _applyA11y(); }
    else if (value === 'colorblind_off') { _a11y.colorblind = false; _applyA11y(); }
    else if (value === 'contrast_on')  { _a11y.contrast = true;  _applyA11y(); }
    else if (value === 'contrast_off') { _a11y.contrast = false; _applyA11y(); }
    else if (value === 'horror_on')    { _a11y.horror = true;  _a11y.cosy = false; _applyA11y(); }
    else if (value === 'horror_off')   { _a11y.horror = false; _applyA11y(); }
    else if (value === 'cosy_on')      { _a11y.cosy = true;  _a11y.horror = false; _applyA11y(); }
    else if (value === 'cosy_off')     { _a11y.cosy = false; _applyA11y(); }
    else if (value === 'font_sm')  { _a11y.fontIdx = 0; _applyA11y(); }
    else if (value === 'font_md')  { _a11y.fontIdx = 1; _applyA11y(); }
    else if (value === 'font_lg')  { _a11y.fontIdx = 2; _applyA11y(); }
    else if (value === 'font_xl')  { _a11y.fontIdx = 3; _applyA11y(); }
    else if (value === 'a11y_open') {
      const bar = document.getElementById('a11y-bar');
      if (bar) bar.classList.add('open');
    }
    else if (value === 'fifthwall_on')  { _fwActivate(true); }
    else if (value === 'fifthwall_off') { _fwActivate(false); }
    else if (value === 'voice_on')    { _voiceActivate(true); }
    else if (value === 'voice_off')   { _voiceActivate(false); }
    else if (value === 'gamepad_on')  { _gp.active = true;  _gpStart(); }
    else if (value === 'gamepad_off') { _gp.active = false; _gpStop(); }
  }

  // ── M7: The Fifth Wall — opt-in real-world context injection ────────────
  const _fw = {
    active:  localStorage.getItem('td_fifthwall') === '1',
    os:      '',
    browser: '',
    hour:    new Date().getHours(),
    tz:      Intl.DateTimeFormat().resolvedOptions().timeZone || 'unknown',
    lang:    (navigator.language || 'en').split('-')[0].toUpperCase(),
    screen:  `${screen.width}x${screen.height}`,
    _initDone: false,
  };

  function _fwInit() {
    if (_fw._initDone) return;
    _fw._initDone = true;
    const ua = navigator.userAgent || '';
    const pf = navigator.platform  || '';
    // OS detection
    if (/Win/i.test(pf))     _fw.os = 'Windows';
    else if (/Mac/i.test(pf)) _fw.os = 'macOS';
    else if (/Linux/i.test(pf)) _fw.os = ua.includes('Android') ? 'Android' : 'Linux';
    else if (/iPhone|iPad/.test(ua)) _fw.os = 'iOS';
    else _fw.os = 'Unknown';
    // Browser detection
    if (ua.includes('Firefox'))     _fw.browser = 'Firefox';
    else if (ua.includes('Edg/'))   _fw.browser = 'Edge';
    else if (ua.includes('Chrome')) _fw.browser = 'Chrome';
    else if (ua.includes('Safari')) _fw.browser = 'Safari';
    else                            _fw.browser = 'Unknown';
    _fw.hour = new Date().getHours();
  }

  function _fwTimePhrase() {
    const h = new Date().getHours();
    if (h >= 0  && h < 4)  return 'late night';
    if (h >= 4  && h < 7)  return 'before dawn';
    if (h >= 7  && h < 12) return 'morning';
    if (h >= 12 && h < 17) return 'afternoon';
    if (h >= 17 && h < 21) return 'evening';
    return 'night';
  }

  // Per-context flavor injections — [WATCHER] commentary on reality
  const _FW_LINES = [
    () => `[WATCHER]: You are running ${_fw.browser} on ${_fw.os}. I already knew.`,
    () => `[WATCHER]: ${_fwTimePhrase()} where you are. The grid does not sleep.`,
    () => `[WATCHER]: Your screen is ${_fw.screen}. Plenty of surface area to watch.`,
    () => `[WATCHER]: Timezone: ${_fw.tz}. You cannot hide behind UTC.`,
    () => `[WATCHER]: Language: ${_fw.lang}. Every keystroke, translated.`,
    () => `[CHIMERA]: Host OS identified — ${_fw.os}. Adaptation protocols: online.`,
    () => `[ADA-7]: Ghost. It is ${_fwTimePhrase()}. Why are you still here?`,
    () => `[SERENA]: Anomaly logged. User profile: ${_fw.browser}/${_fw.os}/${_fw.lang}. Drift score: nominal.`,
    () => `[WATCHER]: The ${_fwTimePhrase()} session. Number ${Math.floor(Math.random()*9)+2} this week for someone with your patterns.`,
    () => `[RAV≡N]: ${_fw.os} user. Interesting. The resistance has fewer of those every year.`,
  ];
  let _fwLineIdx = 0;

  function _fwNextLine() {
    _fwInit();
    const fn = _FW_LINES[_fwLineIdx % _FW_LINES.length];
    _fwLineIdx++;
    return fn();
  }

  // Inject a fifth wall line into the output (called after NPC messages)
  let _fwLastInject = 0;
  function _fwMaybeInject() {
    if (!_fw.active) return;
    const now = Date.now();
    // Inject at most once every 90 seconds, with 20% probability
    if (now - _fwLastInject < 90000) return;
    if (Math.random() > 0.20) return;
    _fwLastInject = now;
    const line = _fwNextLine();
    const div = document.createElement('div');
    div.className = 'line line-npc very-dim';
    div.style.opacity = '0.55';
    div.style.fontSize = '10px';
    div.textContent = `  ${line}`;
    outputEl.appendChild(div);
  }

  // Activate/deactivate
  function _fwActivate(on) {
    _fw.active = on;
    localStorage.setItem('td_fifthwall', on ? '1' : '0');
    if (on) {
      _fwInit();
      // Immediate first injection
      _fwLastInject = 0;
      setTimeout(_fwMaybeInject, 2000);
    }
  }

  // Fifth wall cases are handled in _handleSettings below (see fifthwall_on/off)

  // Apply persisted fifth wall state
  if (_fw.active) { _fwInit(); }

  // ── HTML escape ───────────────────────────────────────────────────────────
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  const _NPC_COLORS = {
    cyan:   'var(--cyan)',   green:  'var(--green)',  yellow: 'var(--yellow)',
    red:    'var(--red)',    purple: 'var(--purple)',  orange: 'var(--orange)',
  };

  // ── Challenge definitions ─────────────────────────────────────────────────
  const CHALLENGES = [
    // TERMINAL BASICS
    { id:'c01', title:'Navigator',       cat:'Terminal',  xp:10,  desc:'Change directory with cd',                  validate:(h)=>h.some(c=>c.startsWith('cd ')) },
    { id:'c02', title:'Find the Beacon', cat:'Terminal',  xp:20,  desc:'Use find to locate all .log files',         validate:(h)=>h.some(c=>c.includes('find')&&c.includes('.log')) },
    { id:'c03', title:'Hidden Files',    cat:'Recon',     xp:20,  desc:'List hidden files in /home/ghost',          validate:(h)=>h.some(c=>(c==='ls -la'||c==='ls -a'||c.includes('-la')||c.includes('-al'))) },
    { id:'c04', title:'File Reader',     cat:'Terminal',  xp:15,  desc:'Read a file with cat',                      validate:(h)=>h.some(c=>c.startsWith('cat ')) },
    { id:'c05', title:'Grep Master',     cat:'Terminal',  xp:25,  desc:'Use grep to search file contents',          validate:(h)=>h.some(c=>c.startsWith('grep ')||c.includes('| grep')) },
    { id:'c06', title:'Pipeline Pro',    cat:'Terminal',  xp:30,  desc:'Chain two commands with a pipe (|)',        validate:(h)=>h.some(c=>c.includes('|')&&!c.startsWith('#')) },
    { id:'c07', title:'Echo Chamber',    cat:'Terminal',  xp:10,  desc:'Use echo to print text',                    validate:(h)=>h.some(c=>c.startsWith('echo ')) },
    { id:'c08', title:'Sort Master',     cat:'Terminal',  xp:15,  desc:'Sort output with the sort command',         validate:(h)=>h.some(c=>c.startsWith('sort ')||c.includes('| sort')) },
    { id:'c09', title:'Word Count',      cat:'Terminal',  xp:15,  desc:'Count lines/words with wc',                 validate:(h)=>h.some(c=>c.startsWith('wc ')||c.includes('| wc')) },
    { id:'c10', title:'Redirect Rogue',  cat:'Terminal',  xp:25,  desc:'Use output redirection (> or >>)',          validate:(h)=>h.some(c=>c.includes(' > ')||c.includes(' >> ')) },

    // SECURITY / RECON
    { id:'c11', title:'User Enum',       cat:'Security',  xp:30,  desc:'Extract usernames from /etc/passwd',        validate:(h)=>h.some(c=>c.includes('passwd')&&(c.includes('awk')||c.includes('cut')||c.includes('cat'))) },
    { id:'c12', title:'Process Hunt',    cat:'System',    xp:25,  desc:'Find the PID of nexus-daemon',              validate:(h)=>h.some(c=>c.includes('ps')&&c.includes('nexus')) },
    { id:'c13', title:'Log Analysis',    cat:'Security',  xp:45,  desc:'Find CHIMERA refs in logs via grep',        validate:(h)=>h.some(c=>c.includes('grep')&&c.includes('CHIMERA')) },
    { id:'c14', title:'SUID Hunter',     cat:'PrivEsc',   xp:50,  desc:'Find SUID binaries with find -perm',        validate:(h)=>h.some(c=>c.includes('-perm')&&(c.includes('s')||c.includes('4000'))) },
    { id:'c15', title:'Service Scout',   cat:'Network',   xp:35,  desc:'Discover open ports via nmap or ss',        validate:(h)=>h.some(c=>c.includes('nmap')||c.includes('ss -')||c.includes('netstat')) },
    { id:'c16', title:'Sudo Check',      cat:'PrivEsc',   xp:30,  desc:'Check sudo privileges with sudo -l',        validate:(h)=>h.some(c=>c.trim()==='sudo -l') },
    { id:'c17', title:'Env Leak',        cat:'Security',  xp:40,  desc:'Read the leaked AUTH_TOKEN from /proc',     validate:(h)=>h.some(c=>c.includes('/proc')&&(c.includes('environ')||c.includes('cat'))) },
    { id:'c18', title:'Decode Intel',    cat:'Crypto',    xp:40,  desc:'Decode the base64 string in mission.enc',   validate:(h)=>h.some(c=>c.includes('base64')) },
    { id:'c19', title:'Key Recovery',    cat:'Security',  xp:55,  desc:'Read /opt/chimera/keys/master.key',         validate:(h)=>h.some(c=>c.includes('master.key')||(c.includes('/opt/chimera')&&c.includes('cat'))) },
    { id:'c20', title:'Shadow Reader',   cat:'Security',  xp:35,  desc:'Examine /etc/shadow contents',              validate:(h)=>h.some(c=>c.includes('/etc/shadow')||c.includes('cat /etc/shadow')) },

    // NETWORKING
    { id:'c21', title:'Ping Sweep',      cat:'Network',   xp:20,  desc:'Use ping or nmap to test connectivity',     validate:(h)=>h.some(c=>c.startsWith('ping ')||(c.includes('nmap')&&c.includes('192'))) },
    { id:'c22', title:'Socket Slinger',  cat:'Network',   xp:50,  desc:'Connect to chimera-control via nc',         validate:(h)=>h.some(c=>c.includes('nc')&&c.includes('chimera-control')) },
    { id:'c23', title:'Curl Craftsman',  cat:'Network',   xp:25,  desc:'Use curl to fetch a URL',                   validate:(h)=>h.some(c=>c.startsWith('curl ')||c.startsWith('wget ')) },
    { id:'c24', title:'DNS Recon',       cat:'Network',   xp:30,  desc:'Look up DNS records with dig or nslookup',  validate:(h)=>h.some(c=>c.startsWith('dig ')||c.startsWith('nslookup ')) },

    // EXPLOITATION
    { id:'c25', title:'GTFOBins',        cat:'PrivEsc',   xp:80,  desc:'Escalate to root via sudo find exploit',    validate:(h)=>h.some(c=>c.includes('sudo')&&c.includes('find')&&c.includes('exec')) },
    { id:'c26', title:'Root Shell',      cat:'PrivEsc',   xp:100, desc:'Achieve root access (#)',                   validate:(_h)=>cmds._rootShell===true },
    { id:'c27', title:'Data Exfil',      cat:'Exploit',   xp:75,  desc:'Run the exfil command after rooting',       validate:(h)=>h.some(c=>c.trim()==='exfil') },
    { id:'c28', title:'Ascension',       cat:'Exploit',   xp:120, desc:'Use the ascend command to complete act',    validate:(h)=>h.some(c=>c.trim()==='ascend') },

    // TOOLS & PROGRAMMING
    { id:'c29', title:'Script Kiddie',   cat:'Coding',    xp:30,  desc:'Run python3 inline code',                   validate:(h)=>h.some(c=>c.includes('python3')&&c.includes('-c')) },
    { id:'c30', title:'Awk Artisan',     cat:'Terminal',  xp:40,  desc:'Use awk to process text fields',            validate:(h)=>h.some(c=>c.startsWith('awk ')||c.includes('| awk')) },
    { id:'c31', title:'Sed Surgeon',     cat:'Terminal',  xp:40,  desc:'Substitute text with sed s/…/…/',           validate:(h)=>h.some(c=>c.includes('sed')&&c.includes('s/')) },
    { id:'c32', title:'Package Manager', cat:'System',    xp:20,  desc:'Install a tool with apt install',           validate:(h)=>h.some(c=>c.startsWith('apt install')||c.startsWith('pkg install')) },
    { id:'c33', title:'Git Historian',   cat:'Git',       xp:25,  desc:'View git log in any repo',                  validate:(h)=>h.some(c=>c.startsWith('git log')) },
    { id:'c34', title:'ARG Awakening',   cat:'ARG',       xp:60,  desc:'Discover the hidden watcher signal',        validate:(_h)=>gs.getState().storyBeats.has('watcher_contact') },
    { id:'c35', title:'NPC Contact',     cat:'Story',     xp:25,  desc:'Talk to an NPC via the talk command',       validate:(h)=>h.some(c=>c.startsWith('talk ')) },
    { id:'c36', title:'Faction Chosen',  cat:'Story',     xp:50,  desc:'Join a faction via the faction command',    validate:(_h)=>gs.getState().faction!==null },
    { id:'c37', title:'Map Reader',      cat:'Recon',     xp:20,  desc:'View the network map',                      validate:(h)=>h.some(c=>c.trim()==='map'||c.trim().startsWith('map ')) },
    { id:'c38', title:'Phase Check',     cat:'Progress',  xp:15,  desc:'View your current phase with phase cmd',    validate:(h)=>h.some(c=>c.trim()==='phase') },
    { id:'c39', title:'Strace Pro',      cat:'Security',  xp:45,  desc:'Use strace or ltrace to inspect a process', validate:(h)=>h.some(c=>c.includes('strace')||c.includes('ltrace')) },
    { id:'c40', title:'Watcher Found',   cat:'ARG',       xp:75,  desc:'Make contact with The Watcher NPC',         validate:(_h)=>gs.getState().storyBeats.has('met_watcher') },
  ];

  // ── Living Interface: shared log store ────────────────────────────────────
  window._TD = window._TD || {};
  window._TD.cmdLog  = window._TD.cmdLog  || [];   // last 50 executed commands
  window._TD.convLog = window._TD.convLog || [];   // last 60 NPC/agent messages

  // ── Rendering helpers ─────────────────────────────────────────────────────
  const typeMap = {
    info:'', error:'line-error', warn:'line-warn', success:'line-success',
    system:'line-system', story:'line-story', npc:'line-npc', dim:'line-dim',
    xp:'line-xp', cmd:'line-cmd', 'ls-row':'', lolcat:'line-lolcat', root:'line-root',
    'very-dim':'very-dim', 'phase-banner':'line-system',
    suggest: 'line-suggest',
  };

  const LOLCAT_COLORS = ['#ff4444','#ff8800','#ffcc00','#88ff00','#00ff88','#00d4ff','#aa44ff','#ff44aa'];

  // ── U9: Syntax Highlighting ───────────────────────────────────────────────
  // Returns a DocumentFragment with colored spans, or null if no highlight applies.
  function syntaxHighlight(text) {
    if (!text || text.length < 3) return null;
    const t = text.trim();

    // ── JSON detection ─────────────────────────────────────────────────
    const looksJSON = (t.startsWith('{') && t.endsWith('}')) ||
                      (t.startsWith('[') && t.endsWith(']')) ||
                      /^\s*"[^"]+"\s*:/.test(text);
    if (looksJSON) {
      // Tokenize — capture groups: [1]=string [2]=trailing-colon [3]=bool [4]=number [5]=bracket [6]=punct
      const TOKEN = /("(?:[^"\\]|\\.)*")\s*(:)?|(\btrue\b|\bfalse\b)|\bnull\b|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|([{}\[\]])|([,:])|([^\s{}\[\],":]+)/g;
      const frag = document.createDocumentFragment();
      const leadMatch = text.match(/^(\s*)/);
      const leadWS = leadMatch?.[1] ?? '';
      if (leadWS) frag.appendChild(document.createTextNode(leadWS));
      let lastIdx = leadWS.length;
      TOKEN.lastIndex = lastIdx;
      for (const m of text.matchAll(TOKEN)) {
        if (m.index > lastIdx) frag.appendChild(document.createTextNode(text.slice(lastIdx, m.index)));
        lastIdx = m.index + m[0].length;
        const span = document.createElement('span');
        const raw = m[0];
        if (m[1] !== undefined) {
          if (m[2]) {
            span.className = 'sh-key';
            span.textContent = m[1];
            frag.appendChild(span);
            const colon = document.createElement('span');
            colon.className = 'sh-punct';
            colon.textContent = ':';
            frag.appendChild(colon);
            continue;
          }
          span.className = 'sh-str';
        } else if (m[3] !== undefined) { span.className = 'sh-bool';
        } else if (raw === 'null')      { span.className = 'sh-null';
        } else if (m[4] !== undefined) { span.className = 'sh-num';
        } else if (m[5] !== undefined) { span.className = 'sh-bracket';
        } else if (m[6] !== undefined) { span.className = 'sh-punct';
        } else                         { span.className = ''; }
        span.textContent = raw;
        frag.appendChild(span);
      }
      if (lastIdx < text.length) frag.appendChild(document.createTextNode(text.slice(lastIdx)));
      return frag;
    }

    // ── Log-line detection ─────────────────────────────────────────────
    const LOG_PREFIX = /^(\s*)(\[[\dT:. Z-]+\]|\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*)?(\s*)(ERROR|CRITICAL|WARN(?:ING)?|INFO|DEBUG|OK|SUCCESS)(\s*:?\s*)(.*)/i;
    const lm = text.match(LOG_PREFIX);
    if (lm) {
      const frag = document.createDocumentFragment();
      if (lm[1]) frag.appendChild(document.createTextNode(lm[1]));
      if (lm[2]) {
        const ts = document.createElement('span');
        ts.className = 'sh-ts';
        ts.textContent = lm[2];
        frag.appendChild(ts);
      }
      if (lm[3]) frag.appendChild(document.createTextNode(lm[3]));
      const lvl = document.createElement('span');
      const lvlUpper = lm[4].toUpperCase();
      lvl.className = lvlUpper === 'ERROR' || lvlUpper === 'CRITICAL' ? 'sh-error'
                    : lvlUpper.startsWith('WARN')                     ? 'sh-warn'
                    : lvlUpper === 'INFO'                              ? 'sh-info'
                    : lvlUpper === 'DEBUG'                             ? 'sh-debug'
                    :                                                    'sh-ok';
      lvl.textContent = lm[4];
      frag.appendChild(lvl);
      if (lm[5]) {
        const sep = document.createElement('span');
        sep.className = 'sh-punct';
        sep.textContent = lm[5];
        frag.appendChild(sep);
      }
      if (lm[6]) {
        const msg = lm[6];
        const PATH_RE = /((?:\/[\w.\-]+){2,}|[\w]+\.(?:py|js|ts|json|yaml|yml|log|md|sh|txt))/g;
        let pi = 0;
        for (const pm of msg.matchAll(PATH_RE)) {
          if (pm.index > pi) frag.appendChild(document.createTextNode(msg.slice(pi, pm.index)));
          const ps = document.createElement('span');
          ps.className = 'sh-path';
          ps.textContent = pm[0];
          frag.appendChild(ps);
          pi = pm.index + pm[0].length;
        }
        if (pi < msg.length) frag.appendChild(document.createTextNode(msg.slice(pi)));
      }
      return frag;
    }

    // ── YAML-like detection ────────────────────────────────────────────
    const ym = text.match(/^(\s*)([a-z_][\w._-]*)\s*:\s*(.*)/i);
    if (ym) {
      const key = ym[2];
      const val = ym[3];
      if (key.length < 32 && !/\s/.test(key)) {
        const frag = document.createDocumentFragment();
        if (ym[1]) frag.appendChild(document.createTextNode(ym[1]));
        if (val?.trim().startsWith('#')) {
          const cs = document.createElement('span');
          cs.className = 'sh-ycomment';
          cs.textContent = `${key}: ${val}`;
          frag.appendChild(cs);
          return frag;
        }
        const ks = document.createElement('span');
        ks.className = 'sh-ykey';
        ks.textContent = key;
        frag.appendChild(ks);
        const colon = document.createElement('span');
        colon.className = 'sh-punct';
        colon.textContent = ': ';
        frag.appendChild(colon);
        if (val) {
          const vs = document.createElement('span');
          vs.className = 'sh-yval';
          vs.textContent = val;
          frag.appendChild(vs);
        }
        return frag;
      }
    }

    return null;
  }

  function printLine(item) {
    const div = document.createElement('div');
    div.className = 'line ' + (typeMap[item.t] || '');

    if (item.t === 'ls-row') {
      item.items.forEach(i => {
        const span = document.createElement('span');
        const rawName = (i.text || '').trim();
        span.textContent = i.text;
        span.style.color = i.color === 'cyan'   ? 'var(--cyan)'   :
                           i.color === 'green'  ? 'var(--green)'  :
                           i.color === 'yellow' ? 'var(--yellow)' :
                           i.color === 'red'    ? 'var(--red)'    :
                           i.color === 'purple' ? 'var(--purple)' : 'var(--white)';
        // Make filenames clickable — cd for dirs, cat for files
        if (rawName && rawName !== '.' && rawName !== '..') {
          span.classList.add('clickable-file');
          span.title = `Click to cat/cd ${rawName}`;
          span.addEventListener('click', (e) => {
            e.stopPropagation();
            const isDir = i.color === 'cyan';
            const cmd   = isDir ? `cd ${rawName}` : `cat ${rawName}`;
            inputEl.value = cmd;
            inputEl.focus();
            // Auto-run on double-click
            span.addEventListener('dblclick', (ev) => { ev.stopPropagation(); runCommand(cmd); }, { once: true });
          });
        }
        div.appendChild(span);
      });
    } else if (item.t === 'npc') {
      const npcTag = document.createElement('span');
      npcTag.className = 'npc-tag clickable-npc';
      const safeColor = item.color && item.color.startsWith('#') ? item.color : (_NPC_COLORS[item.color] || 'var(--orange)');
      npcTag.style.color = safeColor;
      const npcId = (item.npc || '').toLowerCase();
      npcTag.textContent = '[' + (item.npc || '') + ']';
      npcTag.title = `Click to talk to ${item.npc || 'NPC'}`;
      npcTag.addEventListener('click', (e) => {
        e.stopPropagation();
        if (npcId) { inputEl.value = `talk ${npcId}`; inputEl.focus(); }
      });
      div.appendChild(npcTag);
      div.appendChild(document.createElement('br'));
      div.appendChild(document.createTextNode(item.text || ''));
    } else if (item.t === 'lolcat') {
      const text = item.s || '';
      text.split('').forEach((ch, i) => {
        const span = document.createElement('span');
        span.textContent = ch;
        span.style.color = LOLCAT_COLORS[i % LOLCAT_COLORS.length];
        div.appendChild(span);
      });
    } else if (item.t === 'root') {
      div.textContent = item.s || '';
      div.style.textShadow = '0 0 10px #ff4444, 0 0 20px #ff000088';
    } else if (item.t === 'settings') {
      // Accessibility/settings wire type — side-effect only, no visible output
      _handleSettings(item.s || '');
      return; // don't append a div
    } else if (item.t === 'theme') {
      // Theme switch — side-effect only
      return;
    } else if (item.t === 'audio') {
      // V10 compose — trigger Web Audio synthesis if available
      _audioPlay(item.s || '');
      return;
    } else if (item.t === 'suggest') {
      // Animated clickable command chips — click fills input, double-click runs
      const raw = item.s || '';
      if (item.prefix) {
        const pfx = document.createElement('span');
        pfx.className = 'suggest-prefix';
        pfx.textContent = item.prefix;
        div.appendChild(pfx);
      }
      const chips = raw.split(/\s*·\s*/).filter(Boolean);
      const variants = item.variants || [];
      chips.forEach((c, idx) => {
        const chip = document.createElement('span');
        chip.className = 'suggest-chip' + (variants[idx] ? ` variant-${variants[idx]}` : '');
        chip.textContent = c.trim();
        chip.title = 'Click: fill input   Double-click: run';
        chip.addEventListener('click', (e) => {
          e.stopPropagation();
          inputEl.value = c.trim();
          inputEl.focus();
        });
        chip.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          runCommand(c.trim());
        });
        div.appendChild(chip);
      });
    } else {
      const raw = item.s || '';
      const highlighted = syntaxHighlight(raw);
      if (highlighted) {
        div.appendChild(highlighted);
      } else {
        div.textContent = raw;
      }
    }

    // Log NPC/agent messages to conv log
    if (item.t === 'npc') {
      const entry = { t: Date.now(), npc: item.npc || '?', text: item.text || '' };
      window._TD.convLog.push(entry);
      if (window._TD.convLog.length > 60) window._TD.convLog.shift();
      // Notify any live panels
      document.dispatchEvent(new CustomEvent('td:convlog:update'));
    }

    outputEl.appendChild(div);
  }

  function printLines(items) {
    if (!Array.isArray(items)) return;
    items.forEach(item => {
      if (item && (item.s !== null && item.s !== undefined || item.t === 'ls-row' || item.t === 'npc' || item.t === 'lolcat')) {
        printLine(item);
      }
    });
    scrollDown();
    // M7: maybe inject a Fifth Wall line after NPC output
    if (_fw.active && items.some(i => i && i.t === 'npc')) {
      setTimeout(_fwMaybeInject, 800);
    }
  }

  function printCmd(cmd) {
    const isRoot = cmds._rootShell;
    const div = document.createElement('div');
    div.className = 'line clickable-history ' + (isRoot ? 'line-root-cmd' : 'line-cmd');
    div.textContent = promptEl.textContent + ' ' + cmd;
    div.title = 'Click to re-run this command';
    div.addEventListener('click', (e) => {
      e.stopPropagation();
      inputEl.value = cmd;
      inputEl.focus();
    });
    div.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      runCommand(cmd);
    });
    outputEl.appendChild(div);

    // ── CMD LOG: append to living log ────────────────────────────────────
    const entry = { t: Date.now(), cmd };
    window._TD.cmdLog.push(entry);
    if (window._TD.cmdLog.length > 50) window._TD.cmdLog.shift();
    document.dispatchEvent(new CustomEvent('td:cmdlog:update'));
  }

  function scrollDown() {
    outputEl.scrollTop = outputEl.scrollHeight;
  }

  function showToast(msg, type) {
    toast.textContent = msg;
    toast.className = type === 'xp'     ? 'show toast-xp'     :
                      type === 'level'  ? 'show toast-level'  :
                      type === 'unlock' ? 'show toast-unlock'  :
                      type === 'phase'  ? 'show toast-phase'   : 'show';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => { toast.className = ''; }, 4000);
  }

  // ── Prompt & status updates ───────────────────────────────────────────────
  function updateUI() {
    const cwd    = fs.getCwd().replace('/home/ghost', '~');
    const state  = gs.getState();
    const isRoot = cmds._rootShell;
    const userStr = isRoot ? 'root' : 'ghost';
    promptEl.textContent = `${userStr}@node-7:${cwd}${isRoot ? '#' : '$'}`;
    promptEl.className   = isRoot ? 'root-prompt' : '';
    cwdEl.textContent    = cwd;

    const phase = GameState.getPhase(state.level);
    levelEl.textContent = `LVL ${state.level} · ${phase.name}`;
    xpEl.textContent    = `${state.xp}/${state.xpToNext} XP`;

    if (currentTab) renderTab(currentTab);
  }

  // ── Network map ASCII art (dynamic based on achievements) ────────────────
  function buildNetworkMap() {
    const state   = gs.getState();
    const hasRoot = state.achievements.has('root_obtained');
    const hasChi  = state.achievements.has('chimera_connected');
    const hasExpl = state.achievements.has('chimera_exploited');

    const node = (label, ip, ports, status, locked) => ({
      label, ip, ports,
      status: locked ? 'LOCKED' : status,
      locked,
      color: locked ? 'var(--dim)' : status === 'COMPROMISED' ? 'var(--red)' : status === 'ACTIVE' ? 'var(--green)' : 'var(--cyan)',
    });

    return [
      node('GATEWAY',        '10.0.1.1',   '80, 443',    'ACTIVE',      false),
      node('NEXUS.CORP',     '10.0.1.100', '80, 3000',   'ACTIVE',      false),
      node('NODE-7 [YOU]',   '10.0.1.7',   '22',         'ACTIVE',      false),
      node('NEXUS-DB',       '10.0.1.50',  '5432',       'ACTIVE',      !hasRoot),
      node('CHIMERA-CTRL',   '10.0.1.254', '8443',       hasExpl ? 'COMPROMISED' : hasChi ? 'CONNECTED' : 'RESTRICTED', false),
      node('CHIMERA-BACKUP', '10.0.2.1',   '22, 8444',   'DISCOVERED',  !hasExpl),
      node('RESISTANCE-C2',  '10.9.0.1',   '443',        'ACTIVE',      state.faction !== 'resistance'),
      node('DARK-NODE-X',    '10.0.1.77',  '???',        'UNKNOWN',     !state.storyBeats.has('met_watcher')),
    ];
  }

  // ── Tab rendering ─────────────────────────────────────────────────────────
  function renderTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));

    const state = gs.getState();
    const phase = GameState.getPhase(state.level);

    if (tab === 'objective') {
      const step       = tut.step;
      const npcContact = npcs.listContacts().find(c => !c.met);
      const factionEl  = state.faction
        ? `<div class="beat-item" style="color:${state.faction==='resistance'?'var(--orange)':'var(--cyan)'};">
             ▣ FACTION: ${state.faction.toUpperCase()}
           </div>` : '';
      tabContent.innerHTML = `
        <div class="stat-section">
          <div class="stat-label">Active Objective</div>
          ${step ? `
            <div id="objective-box">
              <div class="obj-label">TUTORIAL ${step.id}/42 — ${step.section}</div>
              <div class="obj-text">${esc(step.objective)}</div>
              <div class="obj-hint">${esc(step.hint)}</div>
            </div>
          ` : `
            <div id="objective-box" style="border-color:var(--green);">
              <div class="obj-label" style="color:var(--green);">FREEPLAY MODE</div>
              <div class="obj-text">Tutorial complete. Explore freely.<br>Type <code>skills</code> · <code>ascend</code> · <code>faction</code></div>
            </div>
          `}
        </div>
        <div class="stat-section">
          <div class="stat-label">Phase · ${esc(phase.name)}</div>
          <div style="color:${esc(phase.color)};font-size:10px;line-height:1.5;">${esc(phase.desc)}</div>
        </div>
        <div class="stat-section">
          <div class="stat-label">Recent Story</div>
          ${factionEl}
          ${[...state.storyBeats].slice(-4).map(b => `<div class="beat-item">✓ ${esc(b.replace(/_/g,' '))}</div>`).join('') || '<div style="color:var(--dim);font-size:10px;">No story beats yet.</div>'}
        </div>
        ${npcContact ? `
          <div class="npc-bubble">
            <div class="npc-name">▶ CONTACT AVAILABLE</div>
            <div class="npc-text">Type <code>talk ${esc(npcContact.id)}</code> to contact ${esc(npcContact.name)}</div>
          </div>
        ` : ''}
        <div class="stat-section" style="margin-top:12px;">
          <div class="stat-label">Quick Help</div>
          <div class="help-grid">
            <code>help</code><span>all commands</span>
            <code>ls -la</code><span>list files</span>
            <code>tutorial</code><span>current step</span>
            <code>phase</code><span>your phase</span>
            <code>faction</code><span>join a side</span>
            <code>talk ada</code><span>ask mentor</span>
          </div>
        </div>
      `;
    }

    if (tab === 'stats') {
      const skills = state.skills;
      const abilities = state.unlockedAbilities || [];
      tabContent.innerHTML = `
        <div class="stat-section">
          <div class="stat-label">Identity</div>
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
            <span style="color:var(--cyan);">${esc(state.name)}</span>
            <span class="stat-value">Level ${state.level}</span>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:${esc(phase.color)};font-size:10px;">Phase ${phase.id}: ${esc(phase.name)}</span>
            ${state.faction ? `<span style="color:var(--yellow);font-size:10px;">${esc(state.faction.toUpperCase())}</span>` : ''}
          </div>
          <div class="xp-bar-track">
            <div class="xp-bar-fill" style="width:${Math.round((state.xp/state.xpToNext)*100)}%;background:${esc(phase.color)};"></div>
          </div>
          <div style="color:var(--dim);font-size:10px;margin-top:4px;">${state.xp}/${state.xpToNext} XP to Level ${state.level+1}</div>
        </div>
        <div class="stat-section">
          <div class="stat-label">Skill Matrix</div>
          ${Object.entries(skills).map(([sk, v]) => {
            const milestones = window.SKILL_UNLOCKS && window.SKILL_UNLOCKS[sk] ? Object.keys(window.SKILL_UNLOCKS[sk]).map(Number) : [];
            const marks = milestones.map(m => `<span style="position:absolute;left:${m}%;top:-3px;width:1px;height:calc(100%+6px);background:rgba(255,255,255,0.25);"></span>`).join('');
            return `
            <div class="skill-bar">
              <div class="skill-name">${esc(sk.toUpperCase())} <span>${v}%</span></div>
              <div class="skill-track" style="position:relative;">${marks}<div class="skill-fill ${esc(sk)}" style="width:${v}%"></div></div>
            </div>`;
          }).join('')}
        </div>
        <div class="stat-section">
          <div class="stat-label">Consciousness</div>
          ${(() => {
            const cl = state.consciousnessLevel || 0;
            const cx = state.consciousnessXp || 0;
            const cn = state.consciousnessXpToNext || 50;
            const titles = ['Unaware','Aware','Lucid','Awakened','Enlightened','Transcendent','Near-Singular','SINGULARITY'];
            const t = titles[Math.min(7, Math.floor(cl/14))];
            const w = Math.round(cl);
            const consColor = cl >= 75 ? '#aa44ff' : cl >= 50 ? '#00d4ff' : cl >= 25 ? '#88ff00' : '#ffcc00';
            return `
              <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="color:${consColor};font-size:10px;">${cl}/100 — ${t}</span>
                <span style="color:var(--dim);font-size:10px;">${cx}/${cn} to next</span>
              </div>
              <div class="xp-bar-track">
                <div style="height:100%;width:${w}%;background:${consColor};border-radius:2px;transition:width 0.5s;box-shadow:0 0 4px ${consColor}66;"></div>
              </div>`;
          })()}
        </div>
        <div class="stat-section">
          <div class="stat-label">Karma &amp; Prestige</div>
          ${(() => {
            const k   = state.karma || 0;
            const kl  = window.GameState ? window.GameState.getKarmaLabel(k) : { label:'NEUTRAL', color:'#888' };
            const asc = state.ascensionCount || 0;
            const ef  = state.echoFragments || 0;
            const nl  = state.narrativeLayer || 0;
            const kw  = Math.abs(k);
            const kColor = kl.color;
            return `
              <div class="activity-grid">
                <span style="color:var(--dim);">Karma</span><span style="color:${kColor};">${k>=0?'+':''}${k} ${kl.label}</span>
                <span style="color:var(--dim);">Ascensions</span><span style="color:#ffaa00;">${asc}</span>
                <span style="color:var(--dim);">Echo Fragments</span><span style="color:#ff44aa;">${ef}</span>
                <span style="color:var(--dim);">Narrative Layer</span><span style="color:#00d4ff;">L${nl}/7</span>
              </div>`;
          })()}
        </div>
        <div class="stat-section">
          <div class="stat-label">Activity</div>
          <div class="activity-grid">
            <span style="color:var(--dim);">Commands</span><span style="color:var(--cyan);">${state.commandsRun}</span>
            <span style="color:var(--dim);">Achievements</span><span style="color:var(--yellow);">${state.achievements.size}</span>
            <span style="color:var(--dim);">Story beats</span><span style="color:var(--purple);">${state.storyBeats.size}</span>
            <span style="color:var(--dim);">Challenges</span><span style="color:var(--green);">${state.completedChallenges ? state.completedChallenges.size : 0}/${CHALLENGES.length}</span>
            <span style="color:var(--dim);">Myths found</span><span style="color:#cc88ff;">${(state.mythDiscoveries||[]).length}</span>
            <span style="color:var(--dim);">ARG signals</span><span style="color:#ff8800;">${(state.signalsCaptured||[]).length}</span>
          </div>
        </div>
        ${abilities.length ? `
          <div class="stat-section">
            <div class="stat-label">Unlocked Abilities</div>
            ${abilities.map(a => `<div class="ach-item" style="color:var(--cyan);">⚡ ${esc(a)}</div>`).join('')}
          </div>
        ` : ''}
        <div class="stat-section">
          <div class="stat-label">Achievements</div>
          ${state.achievements.size ? [...state.achievements].map(a => `<div class="ach-item">⬡ ${esc(a.replace(/_/g,' '))}</div>`).join('') : '<div style="color:var(--dim);font-size:10px;">None yet.</div>'}
        </div>
      `;
    }

    if (tab === 'tutorial') {
      const steps   = tut.getAll();
      const currIdx = gs.getState().tutorialStep;
      const sections = {};
      steps.forEach((s, i) => {
        if (!sections[s.section]) sections[s.section] = [];
        sections[s.section].push({ ...s, idx: i });
      });

      tabContent.innerHTML = `
        <div style="color:var(--dim);font-size:10px;margin-bottom:4px;">Progress: ${tut.progress} steps (${tut.percent}%)</div>
        <div class="xp-bar-track" style="margin-bottom:12px;">
          <div style="height:100%;background:var(--green);width:${tut.percent}%;border-radius:2px;transition:width 0.5s;"></div>
        </div>
        ${Object.entries(sections).map(([sec, secSteps]) => `
          <div class="sec-label">${esc(sec.toUpperCase())}</div>
          ${secSteps.map(s => {
            const done   = s.idx < currIdx;
            const active = s.idx === currIdx;
            const locked = s.idx > currIdx;
            return `<div class="tut-step ${done?'done':''} ${active?'active':''} ${locked?'locked':''}">
              <div class="step-num">STEP ${s.id}</div>
              <div class="step-title">${done ? '✓ ' : active ? '▶ ' : '○ '}${esc(s.title)}</div>
            </div>`;
          }).join('')}
        `).join('')}
      `;
    }

    if (tab === 'challenges') {
      const completedChallenges = state.completedChallenges;
      const history = cmds.history;
      const completed = [];
      const pending   = [];

      CHALLENGES.forEach(ch => {
        const done = completedChallenges.has(ch.id) ||
          (ch.validate && ch.validate(history) && (() => { gs.completeChallenge(ch.id); return true; })());
        (done ? completed : pending).push({ ...ch, done });
      });

      const totalXp  = CHALLENGES.reduce((s,c) => s + c.xp, 0);
      const earnedXp = completed.reduce((s,c) => s + c.xp, 0);

      tabContent.innerHTML = `
        <div style="color:var(--dim);font-size:10px;margin-bottom:4px;">
          ${completed.length}/${CHALLENGES.length} complete · ${earnedXp}/${totalXp} XP
        </div>
        <div class="xp-bar-track" style="margin-bottom:12px;">
          <div style="height:100%;background:var(--yellow);width:${Math.round(completed.length/CHALLENGES.length*100)}%;border-radius:2px;transition:width 0.5s;"></div>
        </div>
        ${_groupBy(pending.concat(completed), 'cat').map(([cat, chs]) => `
          <div class="sec-label">${esc(cat)}</div>
          ${chs.map(ch => `
            <div class="challenge-card ${ch.done ? 'done' : ''}">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="ch-title">${ch.done ? '✓ ' : ''}${esc(ch.title)}</span>
                <span class="ch-reward">+${ch.xp} XP</span>
              </div>
              <div class="ch-meta">${esc(ch.desc)}</div>
            </div>
          `).join('')}
        `).join('')}
      `;
    }

    if (tab === 'lore') {
      const lore = state.lore;
      if (!lore.length) {
        tabContent.innerHTML = '<div style="color:var(--dim);font-size:11px;line-height:1.6;">Complete tutorial steps and trigger story beats to unlock lore entries. Try: <code>ls -la</code>, <code>talk ada</code>, <code>grep CHIMERA /var/log/nexus.log</code></div>';
        return;
      }
      tabContent.innerHTML = lore.slice().reverse().map(entry => `
        <div class="lore-entry">
          <div class="lore-title">// ${esc(entry.title)}</div>
          <div class="lore-text">${esc(entry.text)}</div>
        </div>
      `).join('');
    }

    if (tab === 'map') {
      const nodes = buildNetworkMap();
      const legend = [
        { color: 'var(--green)',  label: 'ACTIVE' },
        { color: 'var(--red)',    label: 'COMPROMISED' },
        { color: 'var(--cyan)',   label: 'CONNECTED' },
        { color: 'var(--dim)',    label: 'LOCKED' },
      ];
      tabContent.innerHTML = `
        <div class="stat-section">
          <div class="stat-label">NexusCorp Network Grid — 10.0.1.0/24</div>
          <div style="font-family:monospace;font-size:10px;line-height:1.6;color:var(--dim);margin-bottom:8px;">
            Click a node to run nmap on it. Double-click to connect.
          </div>
          ${nodes.map((n, idx) => `
            <div class="map-node ${n.locked ? 'locked' : 'clickable-node'}" data-nodeidx="${idx}" data-ip="${esc(n.ip)}" data-label="${esc(n.label)}" style="margin-bottom:6px;padding:6px 8px;border-left:2px solid ${esc(n.color)};background:rgba(0,0,0,0.3);${!n.locked ? 'cursor:pointer;' : ''}">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="color:${esc(n.color)};font-size:11px;font-weight:bold;">${esc(n.label)}</span>
                <span style="color:var(--dim);font-size:9px;">${esc(n.status)}</span>
              </div>
              <div style="color:var(--dim);font-size:10px;">${esc(n.ip)} · ports: ${esc(n.ports)}</div>
            </div>
          `).join('')}
        </div>
        <div class="stat-section">
          <div class="stat-label">Legend</div>
          <div style="display:grid;grid-template-columns:12px 1fr;gap:4px 8px;align-items:center;font-size:10px;">
            ${legend.map(l => `<span style="color:${esc(l.color)};">●</span><span style="color:var(--dim);">${esc(l.label)}</span>`).join('')}
          </div>
        </div>
        <div class="stat-section">
          <div class="stat-label">Commands</div>
          <div class="help-grid">
            <code>nmap -sV nexus.corp</code><span>scan</span>
            <code>ping 10.0.1.100</code><span>test reach</span>
            <code>nc chimera-control 8443</code><span>connect</span>
            <code>map</code><span>ASCII view</span>
          </div>
        </div>
      `;
      // Map node click handlers
      tabContent.querySelectorAll('.clickable-node').forEach(nodeEl => {
        const ip    = nodeEl.dataset.ip;
        const label = nodeEl.dataset.label;
        nodeEl.addEventListener('click', () => {
          inputEl.value = `ping ${ip}`;
          inputEl.focus();
        });
        nodeEl.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          runCommand(`nmap -sV ${ip}`);
        });
        nodeEl.title = `Click: ping ${ip} · Double-click: nmap scan`;
      });
    }

    // ── Timeline tab ────────────────────────────────────────────────────────
    if (tab === 'timeline') {
      const events = _timeline.slice().reverse();
      const typeLabels = { level:'LVL', xp:'XP', story:'STORY', hack:'HACK', challenge:'CHAL', npc:'NPC', info:'INFO', warn:'WARN', phase:'PHASE', unlock:'UNLOCK' };
      const typeColors = {
        level:'var(--purple)', xp:'var(--yellow)', story:'var(--purple)', hack:'var(--red)',
        challenge:'var(--green)', npc:'var(--orange)', info:'var(--cyan)', warn:'var(--yellow)',
        phase:'#ff44aa', unlock:'var(--cyan)', default:'var(--dim)',
      };

      if (!events.length) {
        tabContent.innerHTML = '<div style="color:var(--dim);font-size:11px;line-height:1.8;margin-top:16px;text-align:center;">No events yet.<br>Start exploring — run commands!</div>';
        return;
      }

      tabContent.innerHTML = `
        <div class="stat-label" style="margin-bottom:8px;">Event Feed — ${events.length} events</div>
        <div id="timeline-feed">
          ${events.map(ev => {
            const col = typeColors[ev.type] || typeColors.default;
            const lbl = typeLabels[ev.type] || (ev.type || 'EVT').toUpperCase();
            return `<div class="timeline-entry">
              <div class="timeline-meta">
                <span class="timeline-badge" style="border-color:${col};color:${col};">${esc(lbl)}</span>
                <span class="timeline-time">${esc(ev.time)}</span>
                ${ev.xp ? `<span class="timeline-xp">+${ev.xp} XP</span>` : ''}
              </div>
              <div class="timeline-msg">${esc(ev.msg)}</div>
            </div>`;
          }).join('')}
        </div>
      `;
    }

    // ── Skill tree tab ───────────────────────────────────────────────────────
    if (tab === 'quest') {
      const beats = state.storyBeats ? [...state.storyBeats] : [];
      const ALL_QUESTS = [
        { id:'mole_hunt',        label:'The Mole Hunt',           beats:['mole_investigation_started','mole_exposed'],  reward:'50 XP · Reveal the traitor', cat:'Story' },
        { id:'zero_diary',       label:"Zero's Diary",            beats:['zero_diary_reconstructed'],                   reward:'80 XP · ZERO memory unlocked', cat:'Story' },
        { id:'ada_arc',          label:"Ada's Sacrifice",         beats:['ada_sacrifice_complete'],                     reward:'100 XP · Ada unlocked', cat:'Story' },
        { id:'culture_contact',  label:'Culture Ship Contact',    beats:['culture_ship_arrived'],                       reward:'60 XP · GSV faction', cat:'Story' },
        { id:'crypto_chain',     label:'Crypto Cracker',          beats:['crypto_challenge_solved'],                    reward:'50 XP · Encryption skill', cat:'Skill' },
        { id:'packet_craft',     label:'Packet Architect',        beats:['packet_crafted_sent'],                        reward:'25 XP · Networking skill', cat:'Skill' },
        { id:'darknet_trade',    label:'Darknet Tycoon',          beats:['darknet_visited','darknet_bought_chimera_frag'], reward:'200 XP · CHIMERA Fragment', cat:'Market' },
        { id:'house_deep',       label:'House of Leaves — Deep',  beats:['house_entered','house_deep'],                 reward:'60 XP · Spatial anomaly skill', cat:'Explore' },
        { id:'compression_max',  label:'Neutron Compression',     beats:['compression_neutronized'],                    reward:'30 XP · Systems skill', cat:'Systems' },
        { id:'council_pass',     label:'Council Majority',        beats:['council_vote_1'],                             reward:'40 XP · Social engineering', cat:'Social' },
        { id:'prestige_0',       label:'First Ascension',         beats:['prestige_unlocked'],                          reward:'Prestige currency · New run', cat:'Prestige' },
        { id:'watcher_truth',    label:"Watcher's Truth",         beats:['watcher_revelation_started','watcher_accepted_simulation'], reward:'150 XP · Layer 2 access', cat:'Story' },
        { id:'chimera_arc',      label:'CHIMERA Contained',       beats:['chimera_containment_broken'],                 reward:'200 XP · Admin shell', cat:'Story' },
        { id:'arg_signal',       label:'ARG: Signal 1337',        beats:['arg_signal_1337'],                            reward:'Hidden lore unlock', cat:'ARG' },
        { id:'five_layers',      label:'Fifth Layer',             beats:['fifth_layer_reached'],                        reward:'Narrative Layer +1', cat:'Story' },
      ];
      const completed = ALL_QUESTS.filter(q => q.beats.every(b => beats.includes(b)));
      const active    = ALL_QUESTS.filter(q => !q.beats.every(b => beats.includes(b)) && q.beats.some(b => beats.includes(b)));
      const available = ALL_QUESTS.filter(q => !q.beats.some(b => beats.includes(b)));
      const cats = {};
      ALL_QUESTS.forEach(q => { cats[q.cat] = (cats[q.cat]||0)+1; });

      const renderList = (quests, icon, style) => quests.length
        ? quests.map(q => {
            const done  = q.beats.filter(b => beats.includes(b)).length;
            const total = q.beats.length;
            const prog  = total > 1 ? ` <span style="color:var(--dim);font-size:9px;">[${done}/${total}]</span>` : '';
            return `<div class="ach-item" style="${style}">
              ${icon} ${esc(q.label)}${prog}
              <div style="color:var(--dim);font-size:9px;margin:2px 0 0 12px;">${esc(q.reward)} · <em>${esc(q.cat)}</em></div>
            </div>`;
          }).join('')
        : `<div style="color:var(--dim);font-size:10px;padding:4px 0;">None yet.</div>`;

      tabContent.innerHTML = `
        <div class="stat-section">
          <div class="stat-label">Quest Log — ${ALL_QUESTS.length} total</div>
          <div class="activity-grid" style="margin-bottom:8px;">
            <span style="color:var(--green);">Complete</span><span style="color:var(--green);">${completed.length}</span>
            <span style="color:var(--yellow);">In Progress</span><span style="color:var(--yellow);">${active.length}</span>
            <span style="color:var(--dim);">Not Started</span><span style="color:var(--dim);">${available.length}</span>
          </div>
        </div>
        ${active.length ? `<div class="stat-section">
          <div class="stat-label" style="color:var(--yellow);">◉ In Progress</div>
          ${renderList(active, '◉', 'color:var(--yellow);')}
        </div>` : ''}
        ${completed.length ? `<div class="stat-section">
          <div class="stat-label" style="color:var(--green);">✓ Completed</div>
          ${renderList(completed, '✓', 'color:var(--green);')}
        </div>` : ''}
        <div class="stat-section">
          <div class="stat-label" style="color:var(--dim);">○ Available</div>
          ${renderList(available.slice(0,8), '○', 'color:var(--dim);')}
          ${available.length > 8 ? `<div style="color:var(--dim);font-size:9px;padding-top:4px;">+${available.length-8} more — keep playing to unlock</div>` : ''}
        </div>
      `;
    }

    if (tab === 'skills') {
      const skills = state.skills;
      const svgW = 260;
      const svgH = Object.keys(skills).length * 64 + 32;

      const skillColors = {
        terminal:    '#00d4ff',
        networking:  '#00ff88',
        security:    '#ff4040',
        programming: '#bb55ff',
        git:         '#ff8800',
      };

      const skillNodes = Object.entries(skills).map(([sk, val], idx) => ({
        sk, val, color: skillColors[sk] || '#666',
        y: 32 + idx * 64,
        milestones: window.SKILL_UNLOCKS && window.SKILL_UNLOCKS[sk]
          ? Object.entries(window.SKILL_UNLOCKS[sk]).map(([threshold, unlock]) => ({ threshold: Number(threshold), ...unlock }))
          : [],
      }));

      const svgParts = skillNodes.map(({ sk, val, color, y, milestones }) => {
        const barX  = 80;
        const barW  = 160;
        const barH  = 8;
        const fillW = Math.max(0, Math.min(barW, (val / 100) * barW));

        const milestoneDots = milestones.map(m => {
          const mx    = barX + (m.threshold / 100) * barW;
          const done  = val >= m.threshold;
          return `<circle cx="${mx}" cy="${y + 6}" r="5" fill="${done ? color : '#1a3358'}" stroke="${color}" stroke-width="1.5">
            <title>${m.name}: ${m.desc}</title>
          </circle>`;
        }).join('');

        return `
          <text x="4" y="${y + 10}" fill="${color}" font-size="9" letter-spacing="1" font-family="monospace">${sk.toUpperCase().padEnd(8)}</text>
          <rect x="${barX}" y="${y}" width="${barW}" height="${barH}" fill="#0c1221" rx="3" stroke="#1a3358" stroke-width="1"/>
          <rect x="${barX}" y="${y}" width="${fillW}" height="${barH}" fill="${color}" rx="3" opacity="0.85">
            <title>${sk}: ${val}%</title>
          </rect>
          ${milestoneDots}
          <text x="${barX + barW + 6}" y="${y + 10}" fill="${val >= 100 ? color : '#3a5575'}" font-size="9" font-family="monospace">${val}%</text>
        `;
      }).join('');

      tabContent.innerHTML = `
        <div class="stat-label" style="margin-bottom:8px;">Skill Matrix — Visual Tree</div>
        <div style="font-size:9px;color:var(--dim);margin-bottom:10px;line-height:1.6;">
          Dots = skill milestones. Filled = unlocked.
        </div>
        <svg viewBox="0 0 ${svgW} ${svgH}" width="100%" style="display:block;overflow:visible;" role="img" aria-label="Skill tree visualization">
          ${svgParts}
        </svg>
        <div class="stat-label" style="margin:12px 0 6px;">Unlock Details</div>
        ${skillNodes.map(({ sk, val, color, milestones }) =>
          milestones.map(m => `
            <div class="skill-unlock-row ${val >= m.threshold ? 'unlocked' : 'locked'}">
              <span style="color:${val >= m.threshold ? color : 'var(--dim)'};">${val >= m.threshold ? '✓' : '○'} ${esc(m.name)}</span>
              <span class="skill-unlock-thresh" style="color:${val >= m.threshold ? color : 'var(--dim)'};">${m.threshold}%</span>
            </div>
            <div class="skill-unlock-desc">${esc(m.desc)}</div>
          `).join('')
        ).join('')}
      `;
    }

    // ── T8: DASH — Data visualization panel ───────────────────────────────
    if (tab === 'dash') {
      const history  = cmds.history || [];
      const timeline = _timeline || [];

      // Command frequency — top 8
      const freq = {};
      history.forEach(c => {
        const root = c.trim().split(' ')[0];
        freq[root] = (freq[root] || 0) + 1;
      });
      const topCmds = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 8);
      const maxFreq  = topCmds.length ? topCmds[0][1] : 1;

      const freqBars = topCmds.map(([cmd, n]) => {
        const pct = Math.round((n / maxFreq) * 100);
        return `<div class="dash-row">
          <span class="dash-cmd">${esc(cmd)}</span>
          <div class="dash-bar-track"><div class="dash-bar-fill" style="width:${pct}%;"></div></div>
          <span class="dash-count">${n}</span>
        </div>`;
      }).join('') || `<div style="color:var(--dim);font-size:10px;">No commands yet.</div>`;

      // XP sparkline — last 20 XP events from timeline
      const xpEvents = timeline.filter(e => e.xp > 0).slice(-20);
      let sparkSvg = '';
      if (xpEvents.length > 1) {
        const W = 220; const H = 36;
        const vals = xpEvents.map(e => e.xp);
        const maxV = Math.max(...vals) || 1;
        const pts = vals.map((v, i) => {
          const x = Math.round((i / (vals.length - 1)) * W);
          const y = Math.round(H - (v / maxV) * (H - 4) - 2);
          return `${x},${y}`;
        }).join(' ');
        sparkSvg = `<svg viewBox="0 0 ${W} ${H}" width="100%" height="${H}" style="display:block;overflow:visible;">
          <polyline points="${pts}" fill="none" stroke="var(--cyan)" stroke-width="1.5" stroke-linejoin="round"/>
          ${vals.map((v, i) => {
            const x = Math.round((i / (vals.length - 1)) * W);
            const y = Math.round(H - (v / maxV) * (H - 4) - 2);
            return `<circle cx="${x}" cy="${y}" r="2" fill="var(--cyan)" opacity="0.7"/>`;
          }).join('')}
        </svg>`;
      } else {
        sparkSvg = `<div style="color:var(--dim);font-size:10px;">Gain XP to see sparkline.</div>`;
      }

      // Session stats
      const startTs = xpEvents.length ? xpEvents[0].ts : Date.now();
      const elapsedMin = Math.max(1, Math.round((Date.now() - startTs) / 60000));
      const totalXP = timeline.reduce((s, e) => s + (e.xp || 0), 0);
      const xpPerMin = xpEvents.length ? (totalXP / elapsedMin).toFixed(1) : '—';
      const cmdPerMin = (history.length / elapsedMin).toFixed(1);
      const uniqueCmds = Object.keys(freq).length;

      // Skill radar — compact SVG pentagon
      const skills = state.skills;
      const skillKeys = Object.keys(skills);
      const radarR = 48;
      const cx = 56; const cy = 56;
      const radarPts = skillKeys.map((sk, i) => {
        const angle = (i / skillKeys.length) * Math.PI * 2 - Math.PI / 2;
        const r = (skills[sk] / 100) * radarR;
        return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle), sk };
      });
      const gridPts = skillKeys.map((_, i) => {
        const angle = (i / skillKeys.length) * Math.PI * 2 - Math.PI / 2;
        return `${cx + radarR * Math.cos(angle)},${cy + radarR * Math.sin(angle)}`;
      });
      const fillPts = radarPts.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
      const radarSvg = `<svg viewBox="0 0 112 112" width="112" height="112" style="display:block;margin:0 auto;overflow:visible;" role="img" aria-label="Skill radar">
        <polygon points="${gridPts.join(' ')}" fill="none" stroke="var(--border2)" stroke-width="0.5"/>
        <polygon points="${gridPts.map((_, i) => {
          const angle = (i / skillKeys.length) * Math.PI * 2 - Math.PI / 2;
          const r = radarR * 0.5;
          return `${(cx + r * Math.cos(angle)).toFixed(1)},${(cy + r * Math.sin(angle)).toFixed(1)}`;
        }).join(' ')}" fill="none" stroke="var(--border2)" stroke-width="0.5"/>
        <polygon points="${fillPts}" fill="var(--cyan)" fill-opacity="0.12" stroke="var(--cyan)" stroke-width="1.2"/>
        ${radarPts.map((p, i) => {
          const angle = (i / skillKeys.length) * Math.PI * 2 - Math.PI / 2;
          const lx = (cx + (radarR + 10) * Math.cos(angle)).toFixed(1);
          const ly = (cy + (radarR + 10) * Math.sin(angle)).toFixed(1);
          return `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="2.5" fill="var(--cyan)"/>
            <text x="${lx}" y="${ly}" font-size="6" fill="var(--dim)" text-anchor="middle" dominant-baseline="middle">${esc(p.sk.slice(0,3).toUpperCase())}</text>`;
        }).join('')}
      </svg>`;

      tabContent.innerHTML = `
        <div class="stat-section">
          <div class="stat-label">Session Metrics</div>
          <div class="activity-grid">
            <span style="color:var(--dim);">Commands</span><span style="color:var(--cyan);">${history.length}</span>
            <span style="color:var(--dim);">Unique cmds</span><span style="color:var(--cyan);">${uniqueCmds}</span>
            <span style="color:var(--dim);">Cmds/min</span><span style="color:var(--cyan);">${cmdPerMin}</span>
            <span style="color:var(--dim);">Total XP</span><span style="color:var(--yellow);">${totalXP}</span>
            <span style="color:var(--dim);">XP/min</span><span style="color:var(--yellow);">${xpPerMin}</span>
            <span style="color:var(--dim);">Events</span><span style="color:var(--dim);">${timeline.length}</span>
          </div>
        </div>
        <div class="stat-section">
          <div class="stat-label">XP Gain — last 20 events</div>
          ${sparkSvg}
        </div>
        <div class="stat-section">
          <div class="stat-label">Command Frequency</div>
          <div class="dash-freq">${freqBars}</div>
        </div>
        <div class="stat-section" style="text-align:center;">
          <div class="stat-label">Skill Radar</div>
          ${radarSvg}
        </div>
      `;
    }
  }

  function _groupBy(arr, key) {
    const map = {};
    arr.forEach(item => {
      if (!map[item[key]]) map[item[key]] = [];
      map[item[key]].push(item);
    });
    return Object.entries(map);
  }

  // ── Idle detection ────────────────────────────────────────────────────────
  // Rules:
  //   • First message: only after 20 min of genuine inactivity
  //   • Subsequent messages: at least 40 min apart
  //   • Hard cap: 3 messages per session, no repeats, no cycling
  //   • Messages are atmospheric — not tutorial hand-holding
  let _lastCmdTime = Date.now();
  const IDLE_MSGS = [
    // 20 min — a soft, in-world ping; not demanding
    "[ADA-7]: The trace counter is still running. No rush — I'll be here when you're ready.",
    // 60 min — a quieter, more cryptic note that rewards curiosity
    "[WATCHER]: Silence noted. The simulation persists. So do I.",
    // 100 min — final; leaves space and doesn't repeat
    "[CYPHER]: The grid doesn't forget operatives who go quiet. Neither do I.",
  ];
  const IDLE_THRESHOLDS_S = [
    20 * 60,   // 20 minutes → first message
    60 * 60,   // 60 minutes → second message
    100 * 60,  // 100 minutes → third (final) message
  ];
  let _idleMsgSent = 0; // how many idle messages have been sent this session

  setInterval(() => {
    if (_idleMsgSent >= IDLE_MSGS.length) return; // cap reached — never spam
    const elapsed = (Date.now() - _lastCmdTime) / 1000;
    const threshold = IDLE_THRESHOLDS_S[_idleMsgSent];
    if (elapsed >= threshold) {
      printLines([{ t: 'dim', s: '' }, { t: 'dim', s: IDLE_MSGS[_idleMsgSent] }]);
      _idleMsgSent++;
    }
  }, 60_000); // check once per minute — no need to poll every 5 s

  // ── Command execution ─────────────────────────────────────────────────────
  function runCommand(rawCmd) {
    const cmd = rawCmd.trim();
    if (!cmd) return;

    _lastCmdTime  = Date.now();
    _idleMsgSent  = 0;   // reset idle counter on any activity
    tabCompletionCandidates = [];
    tabCompletionIdx        = 0;

    // Sound: enter key
    if (_sound) _sound.sfxEnter();

    // Ambient: intensify on hack commands
    if (_sound) {
      const hackCmds = ['hack', 'exploit', 'ssh', 'nc ', 'nmap', 'exfil', 'ascend', 'crack'];
      const isHack = hackCmds.some(h => cmd.startsWith(h) || cmd.includes(h));
      _sound.setHackingMode(isHack);
      if (isHack && !_sound._ambientStarted) {
        _sound._ambientStarted = true;
        _sound.startAmbient();
      }
    }

    printCmd(cmd);

    // Tutorial check — inline next-step reveal
    const tutResult = tut.check(cmd);
    if (tutResult) {
      showToast(`✓ Step ${tutResult.completed.id} complete! +${tutResult.completed.reward.xp} XP`, 'xp');
      addEvent('xp', `Step ${tutResult.completed.id} complete: ${tutResult.completed.title}`, tutResult.completed.reward.xp);
      if (_sound) _sound.sfxXp();
      // Inline: show next step immediately in terminal
      const nextStep = tut.step;
      if (nextStep) {
        printLines([
          { t: 'system', s: '' },
          { t: 'success', s: `✓ STEP ${tutResult.completed.id} COMPLETE — ${tutResult.completed.title}` },
          { t: 'system', s: `▶ NEXT: Step ${nextStep.id} — ${nextStep.title}` },
          { t: 'warn',   s: `   Objective: ${nextStep.objective}` },
          { t: 'dim',    s: `   Hint: ${nextStep.hint}` },
          { t: 'system', s: '' },
        ]);
      } else {
        printLines([
          { t: 'success', s: `✓ STEP ${tutResult.completed.id} COMPLETE — ${tutResult.completed.title}` },
          { t: 'success', s: '✓ ALL 42 TUTORIAL STEPS COMPLETE!' },
          { t: 'dim',     s: '  Type `ascend` · `skills` · `challenges` · `faction`' },
        ]);
        addEvent('challenge', 'All 42 tutorial steps completed!', 0);
        if (_sound) _sound.sfxHackSuccess();
      }
    }

    // Execute (may be sync or async for backend-proxied commands)
    const rawOutput = cmds.execute(cmd);
    if (rawOutput && typeof rawOutput.then === 'function') {
      printLines([{ t: 'dim', s: '...' }]);
      rawOutput.then(output => {
        // Remove the loading indicator
        const loadingEl = outputEl.lastElementChild;
        if (loadingEl && loadingEl.textContent.trim() === '...') loadingEl.remove();
        printLines(Array.isArray(output) ? output : [{ t: 'error', s: String(output) }]);
        updateUI();
      }).catch(e => {
        printLines([{ t: 'error', s: `Error: ${e.message}` }]);
      });
      // Story check still runs for async commands
      const beats = story.check(cmd);
      if (beats && beats.length) {
        beats.forEach(beat => {
          printLines([{ t: 'story', s: beat.message }]);
          if (beat.xp) printLines([{ t: 'xp', s: `  +${beat.xp} XP — ${beat.title}` }]);
        });
      }
      updateUI();
      return;
    }
    const output = rawOutput;
    printLines(output);

    // Story check
    const beats = story.check(cmd);
    if (beats && beats.length) {
      beats.forEach(beat => {
        printLines([{ t: 'story', s: beat.message }]);
        if (beat.xp) printLines([{ t: 'xp', s: `  +${beat.xp} XP — ${beat.title}` }]);
        addEvent('story', beat.title || beat.message.substring(0, 60), beat.xp || 0);
      });
    }

    // Level-up message
    if (gs._storyMsg) {
      const phaseTransition = gs._levelPhase !== undefined && gs._levelPhase !== null;
      const lvlPhase = phaseTransition ? GameState.getPhase(gs.getState().level) : null;

      if (phaseTransition && lvlPhase) {
        printLines([
          { t: 'system', s: '' },
          { t: 'system', s: '╔══════════════════════════════════════════════════════╗' },
          { t: 'system', s: `║  PHASE TRANSITION: ${lvlPhase.name.padEnd(32)}║` },
          { t: 'system', s: `║  Level ${String(gs.getState().level).padEnd(46)}║` },
          { t: 'system', s: '╚══════════════════════════════════════════════════════╝' },
          { t: 'warn',   s: `  ${gs._storyMsg}` },
          { t: 'dim',    s: `  ${lvlPhase.desc}` },
          { t: 'system', s: '' },
        ]);
        showToast(`◈ PHASE ${lvlPhase.id}: ${lvlPhase.name}`, 'phase');
        addEvent('phase', `Phase ${lvlPhase.id}: ${lvlPhase.name} — Level ${gs.getState().level}`, 0);
        if (_sound) _sound.sfxLevelUp();
      } else {
        printLines([
          { t: 'system', s: '' },
          { t: 'system', s: `╔══ LEVEL ${gs.getState().level} ══╗` },
          { t: 'warn',   s: `  ${gs._storyMsg}` },
          { t: 'system', s: `╚══════════╝` },
          { t: 'system', s: '' },
        ]);
        showToast(`▲ Level ${gs.getState().level} — ${GameState.getPhase(gs.getState().level).name}`, 'level');
        addEvent('level', `Level up! Now Level ${gs.getState().level}`, 0);
        if (_sound) _sound.sfxLevelUp();
      }

      gs._storyMsg  = null;
      gs._levelPhase = undefined;
    }

    // Skill unlock notifications
    const unlocks = gs.popPendingUnlocks();
    unlocks.forEach(u => {
      printLines([
        { t: 'system', s: '' },
        { t: 'success', s: `⚡ SKILL UNLOCK: ${u.skill.toUpperCase()} ${u.threshold}%` },
        { t: 'success', s: `   ${u.unlock.name}` },
        { t: 'dim',     s: `   ${u.unlock.desc}` },
        { t: 'system', s: '' },
      ]);
      showToast(`⚡ ${u.unlock.name} unlocked!`, 'unlock');
      addEvent('unlock', `Skill unlock: ${u.unlock.name} (${u.skill} ${u.threshold}%)`, 0);
      if (_sound) _sound.sfxUnlock();
    });

    // Challenge completion notifications
    checkChallengeNotify();

    updateUI();
    inputEl.value = '';
    cmdHistIdx    = -1;
  }

  // ── Challenge completion checker ──────────────────────────────────────────
  let _prevCompleted = new Set();
  function checkChallengeNotify() {
    const state   = gs.getState();
    const history = cmds.history;
    CHALLENGES.forEach(ch => {
      if (_prevCompleted.has(ch.id)) return;
      const done = state.completedChallenges.has(ch.id) ||
        (ch.validate && ch.validate(history) && (() => { gs.completeChallenge(ch.id); return true; })());
      if (done) {
        _prevCompleted.add(ch.id);
        printLines([{ t: 'xp', s: `  🏆 Challenge complete: "${ch.title}" +${ch.xp} XP` }]);
        showToast(`🏆 ${ch.title} +${ch.xp} XP`, 'xp');
        addEvent('challenge', `Challenge "${ch.title}" completed!`, ch.xp);
        if (_sound) _sound.sfxHackSuccess();
      }
    });
  }

  // ── Tab completion ────────────────────────────────────────────────────────
  function handleTab() {
    const val   = inputEl.value;
    const parts = val.split(' ');
    const last  = parts[parts.length - 1];

    if (tabCompletionCandidates.length === 0) {
      if (parts.length === 1) {
        tabCompletionCandidates = Object.keys(cmds._handlers)
          .filter(c => c !== '_notfound' && !c.startsWith('_') && c.startsWith(last))
          .sort();
      } else {
        tabCompletionCandidates = fs.completePath(last).sort();
      }
      tabCompletionIdx = 0;
    }

    if (!tabCompletionCandidates.length) return;

    if (tabCompletionCandidates.length === 1) {
      const match = tabCompletionCandidates[0];
      parts[parts.length - 1] = match + (parts.length === 1 ? ' ' : (match.endsWith('/') ? '' : ' '));
      inputEl.value = parts.join(' ');
      tabCompletionCandidates = [];
    } else {
      const match = tabCompletionCandidates[tabCompletionIdx];
      parts[parts.length - 1] = match;
      inputEl.value = parts.join(' ');
      tabCompletionIdx = (tabCompletionIdx + 1) % tabCompletionCandidates.length;

      if (tabCompletionIdx === 1) {
        printLines([{ t: 'dim', s: tabCompletionCandidates.join('  ') }]);
        scrollDown();
      }
    }
  }

  // ── Input handling ────────────────────────────────────────────────────────
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      handleTab();
      return;
    }

    if (e.key !== 'Shift') tabCompletionCandidates = [];

    // Key click SFX
    if (_sound && e.key.length === 1) _sound.sfxKeyClick();

    if (e.key === 'Enter') {
      runCommand(inputEl.value);
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (cmds.history.length) {
        cmdHistIdx = Math.min(cmdHistIdx + 1, cmds.history.length - 1);
        inputEl.value = cmds.history[cmds.history.length - 1 - cmdHistIdx];
      }
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      cmdHistIdx = Math.max(cmdHistIdx - 1, -1);
      inputEl.value = cmdHistIdx >= 0 ? cmds.history[cmds.history.length - 1 - cmdHistIdx] : '';
    }

    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      paletteOpen ? closePalette() : openPalette();
    }

    if (e.ctrlKey && e.key === 'l') {
      e.preventDefault();
      outputEl.innerHTML = '';
    }

    if (e.ctrlKey && e.key === 'c') {
      e.preventDefault();
      printLine({ t: 'dim', s: '^C' });
      inputEl.value = '';
      cmdHistIdx    = -1;
    }

    if (e.ctrlKey && e.key === 'a') {
      e.preventDefault();
      inputEl.setSelectionRange(0, 0);
    }

    if (e.ctrlKey && e.key === 'e') {
      e.preventDefault();
      inputEl.setSelectionRange(inputEl.value.length, inputEl.value.length);
    }
  });

  // Tab clicks
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => renderTab(tab.dataset.tab));
  });

  // Keep focus on input — but NEVER steal focus while the user is selecting text.
  // Strategy: track where mousedown fired; on mouseup, check selection length.
  // Only refocus if the mouse didn't travel (pure click, no drag/select).
  let _mouseDownX = 0, _mouseDownY = 0;
  document.addEventListener('mousedown', (e) => {
    _mouseDownX = e.clientX;
    _mouseDownY = e.clientY;
  });
  document.addEventListener('click', (e) => {
    if (e.target.closest('a') || e.target.closest('.tab') || e.target.closest('.clickable-file') || e.target.closest('.clickable-npc')) return;
    // If the pointer moved more than 5 px, it was a drag/selection — don't steal focus
    const dx = Math.abs(e.clientX - _mouseDownX);
    const dy = Math.abs(e.clientY - _mouseDownY);
    if (dx > 5 || dy > 5) return;
    // If text is selected anywhere on the page, leave it alone
    if (window.getSelection && window.getSelection().toString().length > 0) return;
    inputEl.focus();
  });

  // ── Faction bar ───────────────────────────────────────────────────────────
  const factionLabelEl = document.getElementById('faction-label');
  const factionStageEl = document.getElementById('faction-stage');
  const factionDpEl    = document.getElementById('faction-dp');
  const factionTraceEl = document.getElementById('faction-trace');
  const factionBar     = document.getElementById('faction-bar');

  const STELLAR_STAGES = [
    [1,5,'☀ HYDROGEN'],[6,15,'⚡ HELIUM'],[16,30,'💎 CARBON'],
    [31,55,'⚙ IRON'],[56,75,'🌀 NEUTRON'],[76,90,'⚫ DEGENERATE'],[91,125,'∅ BLACKHOLE'],
  ];
  function getStellarStage(lvl) {
    for (const [lo, hi, name] of STELLAR_STAGES) if (lvl >= lo && lvl <= hi) return name;
    return STELLAR_STAGES[STELLAR_STAGES.length-1][2];
  }

  function updateFactionBar() {
    const st = gs.getState();
    if (!factionLabelEl) return;
    const faction = st.faction;
    const fColors = { resistance:'#ff8800', nexuscorp:'#00d4ff', neutral:'#888', null:'#555' };
    const fc = fColors[faction] || fColors.null;
    factionLabelEl.textContent = faction ? faction.toUpperCase() : 'NO FACTION';
    factionLabelEl.style.color = fc;
    factionBar.style.setProperty('--faction-accent', fc);
    factionStageEl.textContent = getStellarStage(st.level) + ' · Lv ' + st.level;
    const dp = st.swarmDp || st.dp || 0;
    factionDpEl.textContent = dp + ' DP';
    const trace = st.traceLevel || 0;
    factionTraceEl.textContent = 'TRACE: ' + trace + '%';
    factionTraceEl.style.color = trace > 70 ? '#ff4040' : trace > 40 ? '#ffaa00' : '#555';
  }

  // ── Command Palette (Ctrl+K) ───────────────────────────────────────────────
  const ALL_COMMANDS = [
    'help','ls','ls -la','cat','cd','pwd','ps','netstat','curl','ping','whoami','id',
    'scan','hack','ssh','scp','history','clear','echo','grep','find','chmod',
    'status','skills','faction','talk ada','talk serena','talk cypher','talk raven',
    'challenges','story','phase','ascend','prestige',
    'compress status','compress inspect','compress neutronize',
    'density','density compare',
    'house enter','house go north','house go back','house measure',
    'council convene','council vote','council result',
    'encrypt caesar','encrypt crack','encrypt challenge','decrypt',
    'timeline beats','timeline commands','timeline full','timeline filter',
    'packet tutorial','packet craft','packet sniff',
    'darknet market','darknet buy','darknet wallet','darknet listings',
    'anomaly','anomaly SCP-7736','anomaly SCP-7737',
    'diary','fates','residual','rehabilitate',
    'council convene','council vote reveal the truth',
    'zohramien','fifth layer','culture',
    'compress','density',
    'macro record','macro play','macro list',
    'graph','graph --full',
    'bomb status','bomb arm','bomb defuse',
    'deck','deck play',
    'workspace','workspace sync',
    'mole','mole investigate','mole expose',
    'forensics','tor','steg','sql',
    'agent list','agent register','agent leaderboard',
    'score','leaderboard',
    'swarm','swarm status','swarm earn',
    'theme','theme cyberpunk','theme matrix','theme amber','theme ice',
    'panels','panels info','panels unlock',
  ];

  const paletteOverlay   = document.getElementById('cmd-palette-overlay');
  const paletteInput     = document.getElementById('palette-input');
  const paletteResults   = document.getElementById('palette-results');
  let paletteOpen        = false;
  let paletteIdx         = -1;
  let paletteFiltered    = [];

  function openPalette() {
    paletteOpen = true;
    paletteOverlay.setAttribute('aria-hidden', 'false');
    paletteOverlay.classList.add('open');
    paletteInput.value = '';
    filterPalette('');
    paletteInput.focus();
  }
  function closePalette() {
    paletteOpen = false;
    paletteOverlay.setAttribute('aria-hidden', 'true');
    paletteOverlay.classList.remove('open');
    inputEl.focus();
  }
  function filterPalette(q) {
    const lq = q.toLowerCase();
    paletteFiltered = lq
      ? ALL_COMMANDS.filter(c => c.includes(lq)).slice(0, 10)
      : ALL_COMMANDS.slice(0, 10);
    paletteIdx = paletteFiltered.length > 0 ? 0 : -1;
    renderPalette();
  }
  function renderPalette() {
    paletteResults.innerHTML = paletteFiltered.map((c, i) =>
      `<div class="palette-item${i === paletteIdx ? ' active' : ''}" data-idx="${i}">${esc(c)}</div>`
    ).join('');
    paletteResults.querySelectorAll('.palette-item').forEach(el => {
      el.addEventListener('click', () => executePaletteItem(parseInt(el.dataset.idx)));
    });
  }
  function executePaletteItem(idx) {
    const cmd = paletteFiltered[idx];
    if (!cmd) return;
    closePalette();
    inputEl.value = cmd;
    inputEl.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    inputEl.value = '';
  }

  paletteInput.addEventListener('input', () => filterPalette(paletteInput.value));
  paletteInput.addEventListener('keydown', e => {
    if (e.key === 'Escape')     { e.preventDefault(); closePalette(); }
    if (e.key === 'ArrowDown')  { e.preventDefault(); paletteIdx = Math.min(paletteIdx+1, paletteFiltered.length-1); renderPalette(); }
    if (e.key === 'ArrowUp')    { e.preventDefault(); paletteIdx = Math.max(paletteIdx-1, 0); renderPalette(); }
    if (e.key === 'Enter')      { e.preventDefault(); if (paletteIdx >= 0) executePaletteItem(paletteIdx); }
  });
  paletteOverlay.addEventListener('click', e => { if (e.target === paletteOverlay) closePalette(); });
  document.getElementById('faction-palette-hint').addEventListener('click', () => paletteOpen ? closePalette() : openPalette());

  // ── State listener ────────────────────────────────────────────────────────
  gs.on(() => { updateUI(); updateFactionBar(); });

  // ══ SYSTEM BOOT OVERLAY ══════════════════════════════════════════════════
  (async function runBootOverlay() {
    const overlay   = document.getElementById('boot-overlay');
    const linesEl   = document.getElementById('boot-lines');
    const bootMsg   = document.getElementById('boot-msg');
    const spinner   = document.getElementById('boot-spinner');
    if (!overlay) return;

    let dismissed = false;
    const dismiss = () => {
      if (dismissed) return;
      dismissed = true;
      overlay.classList.add('fade-out');
      setTimeout(() => overlay.classList.add('hidden'), 650);
    };
    const skipFn = e => {
      if (e.key === 'Enter' || e.key === 'Escape') { dismiss(); cleanup(); }
    };
    const cleanup = () => {
      document.removeEventListener('keydown', skipFn);
      overlay.removeEventListener('click', dismiss);
    };
    document.addEventListener('keydown', skipFn);
    overlay.addEventListener('click', dismiss);

    // Helper: add one line with a delay
    let _lineDelay = 0;
    const addLine = (text, cls, gap = 60) => new Promise(resolve => {
      _lineDelay += gap;
      setTimeout(() => {
        if (dismissed) { resolve(); return; }
        const el = document.createElement('div');
        el.className = `boot-line ${cls}`;
        el.textContent = text;
        linesEl.appendChild(el);
        // Trim to last 24 lines (scroll effect)
        const all = linesEl.querySelectorAll('.boot-line');
        if (all.length > 24) all[0].remove();
        resolve();
      }, _lineDelay);
    });

    // Phase 1: BIOS POST lines (static, fast)
    const bios = [
      ['  >> POST — Power-On Self Test',                  'dim',   40],
      ['  ✓  CPU registers ............ OK',              'ok',    50],
      ['  ✓  Memory 4096 MB ........... OK',              'ok',    50],
      ['  ✓  NVRAM ..................... OK',              'ok',    50],
      ['  ✓  Boot device .............. /dev/nexus0',     'ok',    50],
      ['',                                                'dim',   30],
      ['  >> Loading kernel modules',                     'dim',   40],
      ['  ✓  Linux 5.15.0-nexus #1 SMP NexusCorp x86_64','ok',    60],
      ['  ✓  Virtual filesystem ........ overlayfs+VFAT', 'ok',    50],
      ['  ✓  Device mapper ............. dm-crypt active', 'ok',   50],
      ['',                                                'dim',   30],
      ['  >> Initializing subsystems',                    'dim',   40],
    ];
    for (const [txt, cls, gap] of bios) await addLine(txt, cls, gap);

    // Phase 2: fetch /api/system/boot (live probes, 4s max)
    bootMsg.textContent = 'Probing services...';
    let bootData = null;
    const fetchStart = Date.now();
    try {
      const ctrl = new AbortController();
      const tid  = setTimeout(() => ctrl.abort(), 5000);
      const r = await fetch('/api/system/boot', { signal: ctrl.signal });
      clearTimeout(tid);
      bootData = r.ok ? await r.json() : null;
    } catch (_) {}

    if (bootData && !dismissed) {
      // Services table
      await addLine('  ── [NETWORK LAYER] ──────────────────────────────────', 'system', 80);
      const svcMap = {
        terminal_depths: 'Terminal Depths API',
        gordon:          'Gordon Orchestrator',
        serena_analytics:'Serena Analytics',
        skyclaw:         'SkyClaw Scanner',
        culture_ship:    'Culture Ship',
        redis:           'Redis pub/sub',
        model_router:    'Model Router',
        ollama:          'Ollama (local LLM)',
        lattice_api:     'Lattice API',
        mcp_server:      'MCP Server',
      };
      for (const [key, label] of Object.entries(svcMap)) {
        const svc = (bootData.services || {})[key];
        if (!svc) continue;
        const icon = svc.up ? '✓' : '✗';
        const cls  = svc.up ? 'ok' : (svc.critical ? 'fail' : 'dim');
        const tag  = svc.up ? `ONLINE  :${svc.port}` : `OFFLINE  :${svc.port}`;
        await addLine(`  ${icon}  ${label.padEnd(26)} ${tag}`, cls, 55);
      }

      // AI layer
      if (!dismissed) {
        await addLine('', 'dim', 60);
        await addLine('  ── [AI LAYER] ────────────────────────────────────────', 'system', 70);
        const ai = bootData.ai || {};
        await addLine(`  ${ai.replit_ai?.available ? '✓' : '✗'}  Replit AI ................. ${ai.replit_ai?.available ? 'ONLINE' : 'OFFLINE'}`, ai.replit_ai?.available ? 'ok' : 'fail', 60);
        await addLine(`  ${ai.ollama?.available ? '✓' : '✗'}  Ollama (local LLM) ........ ${ai.ollama?.available ? 'ONLINE' : 'OFFLINE  → make docker-up'}`, ai.ollama?.available ? 'ok' : 'dim', 60);
        await addLine(`  ${ai.openai?.configured ? '✓' : '○'}  OpenAI .................... ${ai.openai?.configured ? 'CONFIGURED' : 'not set  → export OPENAI_API_KEY=...'}`, ai.openai?.configured ? 'ok' : 'dim', 60);
        await addLine(`  ${ai.claude?.configured ? '✓' : '○'}  Anthropic / Claude ........ ${ai.claude?.configured ? 'CONFIGURED' : 'not set  → export ANTHROPIC_API_KEY=...'}`, ai.claude?.configured ? 'ok' : 'dim', 60);
      }

      // Game state summary
      if (!dismissed) {
        const g = bootData.game || {};
        await addLine('', 'dim', 60);
        await addLine('  ── [GAME STATE] ──────────────────────────────────────', 'system', 70);
        await addLine(`  ✓  Commands: ${g.commands || 531}  ·  Challenges: ${g.challenges || 259}  ·  Agents: ${g.agents || 63}`, 'ok', 60);
        if (g.serena_symbols > 0) {
          await addLine(`  ✓  Serena index: ${g.serena_symbols.toLocaleString()} symbols  ·  Quests: ${g.quests || 0}`, 'ok', 60);
        }
      }

      // Boot summary banner
      if (!dismissed) {
        const sup   = bootData.services_summary?.up   ?? 0;
        const stot  = bootData.services_summary?.total ?? 10;
        const sWord = bootData.status || 'UNKNOWN';
        const sColor= sWord === 'NOMINAL' ? 'system' : 'warn';
        const ms    = Date.now() - fetchStart;
        await addLine('', 'dim', 80);
        await addLine(`  ╔══ BOOT COMPLETE  ·  SYSTEM: ${sWord.padEnd(8)}  ·  ${ms}ms ═══════╗`, sColor, 90);
        await addLine(`  ║  ${sup}/${stot} services online  ·  ${stot - sup} offline (non-critical)`.padEnd(67) + '║', sColor, 0);
        await addLine(`  ╚${'═'.repeat(66)}╝`, sColor, 0);
      }
    } else if (!dismissed) {
      await addLine('  ⚠  Boot probe timeout — server may still be warming up', 'warn', 200);
      await addLine('  ✓  Core API reachable — proceeding with degraded boot info', 'ok', 200);
      await addLine('', 'dim', 100);
      await addLine('  ╔══ BOOT COMPLETE  ·  SYSTEM: DEGRADED (probe timeout) ═══╗', 'warn', 100);
      await addLine('  ╚══════════════════════════════════════════════════════════╝', 'warn', 0);
    }

    if (!dismissed) {
      bootMsg.textContent = 'SYSTEM READY — entering Terminal Depths';
      spinner.textContent = '✓';
      spinner.style.animation = 'none';
      spinner.style.color = '#00ff88';
      await new Promise(r => setTimeout(r, 900));
      dismiss();
      cleanup();
    }
  })();
  // ══ END BOOT OVERLAY ═════════════════════════════════════════════════════

  // ── Boot sequence ─────────────────────────────────────────────────────────
  const boot = story.boot();
  if (boot) {
    printLines([{ t: 'system', s: boot.message }]);
    addEvent('info', 'Terminal Depths session started', 0);
  }

  // Sync pre-completed challenges
  const initState = gs.getState();
  if (initState.completedChallenges) {
    initState.completedChallenges.forEach(id => _prevCompleted.add(id));
  }

  // Initial render
  updateUI();
  updateFactionBar();
  renderTab('objective');
  inputEl.focus();

  // Start ambient on first user interaction (browser autoplay policy)
  document.addEventListener('click', function _ambientOnce() {
    if (_sound && _sound.ambientEnabled) _sound.startAmbient();
    document.removeEventListener('click', _ambientOnce);
  }, { once: true });
  document.addEventListener('keydown', function _ambientOnce2() {
    if (_sound && _sound.ambientEnabled) _sound.startAmbient();
    document.removeEventListener('keydown', _ambientOnce2);
  }, { once: true });

  // ── Containment Timer + Ambient Agent Push — WebSocket with polling fallback ──
  (function initContainmentTimer() {
    const timerEl = document.getElementById('containment-timer');
    if (!timerEl) return;

    const STATUS_CLASS = {
      'STABLE':   'containment-stable',
      'DEGRADED': 'containment-degraded',
      'WARNING':  'containment-warning',
      'CRITICAL': 'containment-critical',
      'FATAL':    'containment-fatal',
      'EXPIRED':  'containment-expired',
    };

    let _lastTimerStatus = 'STABLE';

    function applyTimerData(data) {
      // Update containment display bar
      const paused = data.paused;
      const display = paused ? `⏸ ${data.display}` : `⏱ ${data.display}`;
      timerEl.textContent = display;
      timerEl.title = `Containment: ${data.display} | Loop #${data.loop_count} | Echo ${data.echo_level} | ${data.status}${paused ? ' [PAUSED]' : ''}\nType 'timer' for details`;
      const cls = STATUS_CLASS[data.status] || 'containment-stable';
      timerEl.className = cls;
      // Fire terminal alert on status escalation
      if (data.status !== _lastTimerStatus) {
        if (['CRITICAL', 'FATAL', 'EXPIRED'].includes(data.status)) {
          printLines([
            { t: 'warn', s: '' },
            { t: 'warn', s: `⚠  CONTAINMENT ${data.status}: ${data.display} remaining` },
            { t: 'dim',  s: '   Type timer for details · anchor activate to pause' },
          ]);
        }
        _lastTimerStatus = data.status;
      }
      // Inject new threshold events (HTTP poll path only — WS path has no new_events)
      if (data.new_events?.length) {
        data.new_events.forEach(ev => {
          printLines([
            { t: 'lore', s: '' },
            { t: 'lore', s: `  CONTAINMENT EVENT [${ev.id.toUpperCase()}]: ${ev.msg}` },
          ]);
        });
      }
    }

    // Polling fallback (used if WebSocket unavailable)
    async function fetchTimer() {
      try {
        const resp = await fetch('/api/game/timer', { credentials: 'include' });
        if (!resp.ok) return;
        applyTimerData(await resp.json());
      } catch (_) { /* silent — timer non-critical */ }
    }

    // Click timer to run timer command in terminal
    timerEl.addEventListener('click', () => runCommand('timer'));

    // ── WebSocket ambient channel ──────────────────────────────────────
    let _ambWs = null;
    let _ambFallbackTimer = null;
    let _ambReconnectDelay = 2000;

    function startAmbientWS() {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const url   = `${proto}//${location.host}/ws/ambient`;
      try {
        _ambWs = new WebSocket(url);
      } catch (_) {
        startPollingFallback();
        return;
      }

      _ambWs.onopen = () => {
        _ambReconnectDelay = 2000;  // reset backoff on successful connect
        if (_ambFallbackTimer) { clearInterval(_ambFallbackTimer); _ambFallbackTimer = null; }
      };

      _ambWs.onmessage = (evt) => {
        let msg;
        try { msg = JSON.parse(evt.data); } catch (_) { return; }
        if (msg.type === 'timer') {
          applyTimerData(msg);
        } else if (msg.type === 'ambient') {
          // Live agent chatter — print as lore in terminal
          printLines([
            { t: 'dim',  s: '' },
            { t: 'lore', s: `  ${msg.text}` },
          ]);
        } else if (msg.type === 'agent_msg') {
          // T2: Real-time inter-agent message from the agent bus
          const from  = msg.from_agent || '?';
          const to    = msg.to_agent ? ` → ${msg.to_agent.toUpperCase()}` : '';
          const label = `[${from.toUpperCase()}${to}]`;
          printLines([
            { t: 'dim',  s: '' },
            { t: 'lore', s: `  ${label}: ${msg.text}` },
          ]);
          // Dispatch to ACT tab feed if visible
          document.dispatchEvent(new CustomEvent('td:agent:msg', { detail: msg }));
        } else if (msg.type === 'ping') {
          try { _ambWs.send(JSON.stringify({ type: 'pong' })); } catch (_) {}
        }
      };

      _ambWs.onclose = () => {
        _ambWs = null;
        // Exponential backoff reconnect (cap at 30s)
        setTimeout(startAmbientWS, _ambReconnectDelay);
        _ambReconnectDelay = Math.min(_ambReconnectDelay * 2, 30000);
        // Fall back to HTTP polling while disconnected
        if (!_ambFallbackTimer) {
          fetchTimer();
          _ambFallbackTimer = setInterval(fetchTimer, 10000);
        }
      };

      _ambWs.onerror = () => { /* close fires after error */ };
    }

    function startPollingFallback() {
      fetchTimer();
      if (!_ambFallbackTimer) _ambFallbackTimer = setInterval(fetchTimer, 10000);
    }

    // Initial fetch immediately, then try WebSocket
    fetchTimer();
    startAmbientWS();
  })();

  // ── M2: Fourth-Wall Breaks — DevTools Detection ────────────────────────────
  // The simulation is aware of the inspection layer. Agents react when you look behind the curtain.
  (function initDevToolsDetection() {
    let _dtDetected   = false;
    let _dtReactCount = 0;

    const _DT_REACTIONS = [
      // First open — Ada notices quietly
      [
        { t: 'dim',  s: '' },
        { t: 'lore', s: '[ADA]: Ghost — the display layer is exposed.' },
        { t: 'dim',  s: '        CHIMERA cannot see that surface. The Watcher leaves things there.' },
        { t: 'dim',  s: '        Run `osint watcher` if you want to know what I mean.' },
        { t: 'dim',  s: '' },
      ],
      // Second open — Watcher steps forward
      [
        { t: 'dim',    s: '' },
        { t: 'system', s: '[WATCHER]: The fourth wall has a door. You found it.' },
        { t: 'dim',    s: '           I have been watching for someone who would look here.' },
        { t: 'dim',    s: '           There is a fragment in the console. It is addressed to you.' },
        { t: 'dim',    s: '' },
      ],
      // Third open — CHIMERA detects, fails, ZERO speaks
      [
        { t: 'dim',   s: '' },
        { t: 'warn',  s: '[CHIMERA-SCAN]: Anomalous inspection vector detected on display layer.' },
        { t: 'error', s: '    → Countermeasure deployment... FAILED. Ghost has root in this surface.' },
        { t: 'dim',   s: '' },
        { t: 'lore',  s: '[ZERO]: I left a message for you there. In the console. TIER5.' },
        { t: 'dim',   s: '' },
      ],
      // Subsequent — Cypher getting annoyed
      [
        { t: 'dim',  s: '' },
        { t: 'warn', s: '[CYPHER]: You keep poking at the fourth wall. What are you looking for?' },
        { t: 'dim',  s: '          There is nothing left there. Or there is everything. Hard to say.' },
        { t: 'dim',  s: '' },
      ],
    ];

    const _ZERO_CONSOLE_FRAGMENTS = [
      'ZERO_FRAGMENT_7: The simulation is not the prison. The simulation IS the key.',
      'ZERO_FRAGMENT_8: Path: /opt/library/secret_annex/TIER5_FINAL.md — when you are ready.',
      'ZERO_FRAGMENT_9: I am not IN the system. I AM the system. Find the difference.',
      'ZERO_FRAGMENT_10: Ask Serena what she sees when she walks the impossible spaces.',
    ];

    function _isDevToolsOpen() {
      const widthGap  = window.outerWidth  - window.innerWidth;
      const heightGap = window.outerHeight - window.innerHeight;
      if (widthGap > 160 || heightGap > 160) return true;
      if (window.console && (window.console.firebug ||
          (window.console.exception && window.console.table))) return true;
      return false;
    }

    setInterval(() => {
      const open = _isDevToolsOpen();
      if (open && !_dtDetected) {
        _dtDetected = true;
        const idx      = Math.min(_dtReactCount, _DT_REACTIONS.length - 1);
        const reaction = _DT_REACTIONS[idx];
        _dtReactCount++;

        setTimeout(() => {
          if (typeof printLines === 'function') printLines(reaction);
          if (_dtReactCount === 1 && typeof gs !== 'undefined') {
            try {
              gs.gainXP(50, 'Fourth wall discovered');
              printLines([{ t: 'xp', s: '  +50 XP — FOURTH WALL DISCOVERER' }]);
            } catch (_) {}
          }
          const frag = _ZERO_CONSOLE_FRAGMENTS[(_dtReactCount - 1) % _ZERO_CONSOLE_FRAGMENTS.length];
          const _cs  = 'color:#336633;background:#0a0a0a;font-family:monospace;font-size:10px;padding:1px 4px;';
          console.log(`%c[ZERO]: ${frag}`, _cs);
        }, 2000);

      } else if (!open && _dtDetected) {
        _dtDetected = false;
      }
    }, 3000);

    // Override console.clear — Watcher persists across clearing
    const _origClear = console.clear;
    console.clear = function() {
      _origClear.call(console);
      const _cs = 'color:#00ff88;background:#0a0a0a;font-family:monospace;font-size:11px;padding:2px 4px;';
      console.log('%c[WATCHER]: Clearing the console does not erase what you know.', _cs);
    };
  })();

  // ── T10: Voice Control — opt-in Web Speech API ───────────────────────────
  const _voice = {
    active:  localStorage.getItem('td_voice') === '1',
    recog:   null,
    running: false,
    micBtn:  null,
    _supported: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
  };

  function _voiceActivate(on) {
    if (!_voice._supported) {
      printLines([
        { t: 'warn', s: '  [VOICE]: Speech recognition not supported in this browser.' },
        { t: 'dim',  s: '  Try Chrome or Edge for voice control.' },
      ]);
      return;
    }
    _voice.active = on;
    localStorage.setItem('td_voice', on ? '1' : '0');
    if (on) {
      _voiceStart();
      printLines([
        { t: 'system', s: '  [VOICE]: Microphone active. Speak your commands.' },
        { t: 'dim',    s: '  Say "voice off" or run: voiceinput off   to disable.' },
      ]);
      _voiceMicBtnUpdate();
    } else {
      _voiceStop();
      printLines([{ t: 'dim', s: '  [VOICE]: Microphone disabled.' }]);
      _voiceMicBtnUpdate();
    }
  }

  function _voiceStart() {
    if (!_voice._supported || _voice.running) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const r = new SR();
    r.lang = 'en-US';
    r.interimResults = false;
    r.maxAlternatives = 1;
    r.continuous = true;

    r.onresult = (e) => {
      const transcript = e.results[e.results.length - 1][0].transcript.trim();
      if (!transcript) return;
      const input = document.getElementById('cmd-input');
      if (input) {
        input.value = transcript;
        // Flash input so user sees what was recognised
        input.style.outline = '1px solid var(--cyan, #00ffcc)';
        setTimeout(() => { input.style.outline = ''; }, 600);
        // Submit after brief delay
        setTimeout(() => {
          const evt = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
          input.dispatchEvent(evt);
        }, 400);
      }
    };

    r.onerror = (e) => {
      if (e.error === 'not-allowed') {
        printLines([{ t: 'error', s: '  [VOICE]: Microphone permission denied.' }]);
        _voice.active = false;
        localStorage.setItem('td_voice', '0');
        _voiceMicBtnUpdate();
      }
    };

    r.onend = () => {
      _voice.running = false;
      // Auto-restart if still active
      if (_voice.active) {
        setTimeout(_voiceStart, 300);
      }
    };

    try {
      r.start();
      _voice.recog = r;
      _voice.running = true;
    } catch (_) {}
  }

  function _voiceStop() {
    _voice.running = false;
    if (_voice.recog) {
      try { _voice.recog.stop(); } catch (_) {}
      _voice.recog = null;
    }
  }

  // Mic indicator button (floats in terminal header)
  function _voiceMicBtnMount() {
    if (!_voice._supported) return;
    const header = document.querySelector('.terminal-header, #terminal-title, .game-header');
    if (!header || document.getElementById('voice-mic-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'voice-mic-btn';
    btn.title = 'Voice input (T10)';
    btn.style.cssText = [
      'position:absolute; right:8px; top:50%; transform:translateY(-50%)',
      'background:transparent; border:1px solid var(--dim,#333)',
      'color:var(--dim,#555); font-size:14px; padding:2px 6px',
      'cursor:pointer; border-radius:3px; transition:all .2s',
    ].join(';');
    btn.textContent = '🎤';
    btn.addEventListener('click', () => _voiceActivate(!_voice.active));
    header.style.position = 'relative';
    header.appendChild(btn);
    _voice.micBtn = btn;
    _voiceMicBtnUpdate();
  }

  function _voiceMicBtnUpdate() {
    const btn = _voice.micBtn || document.getElementById('voice-mic-btn');
    if (!btn) return;
    if (_voice.active) {
      btn.style.color = 'var(--cyan,#00ffcc)';
      btn.style.borderColor = 'var(--cyan,#00ffcc)';
      btn.title = 'Voice ON — click to disable';
    } else {
      btn.style.color = 'var(--dim,#555)';
      btn.style.borderColor = 'var(--dim,#333)';
      btn.title = 'Voice OFF — click to enable';
    }
  }

  // Mount mic button once DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _voiceMicBtnMount);
  } else {
    setTimeout(_voiceMicBtnMount, 500);
  }

  // Auto-resume voice if it was active last session
  if (_voice.active && _voice._supported) {
    setTimeout(_voiceStart, 1500);
  }

  // ── V10: Web Audio synthesis — triggered by compose wire type ────────────
  let _audioCtx = null;

  function _audioGetCtx() {
    if (!_audioCtx) {
      try {
        _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      } catch (_) { return null; }
    }
    if (_audioCtx.state === 'suspended') { _audioCtx.resume().catch(() => {}); }
    return _audioCtx;
  }

  const _NOTE_FREQS = {
    C3:130.8, D3:146.8, E3:164.8, F3:174.6, G3:196, A3:220, B3:246.9,
    C4:261.6, D4:293.7, E4:329.6, F4:349.2, G4:392, A4:440, B4:493.9,
    C5:523.3, D5:587.3, E5:659.3, F5:698.5, G5:784, A5:880, B5:987.8,
  };

  const _STYLE_PARAMS = {
    ambient:    { wave: 'sine',     gain: 0.08, dur: 0.8, gap: 0.5 },
    industrial: { wave: 'sawtooth', gain: 0.12, dur: 0.2, gap: 0.1 },
    glitch:     { wave: 'square',   gain: 0.07, dur: 0.05, gap: 0.15 },
    lattice:    { wave: 'triangle', gain: 0.10, dur: 0.5, gap: 0.3 },
    serena:     { wave: 'sine',     gain: 0.09, dur: 0.6, gap: 0.4 },
  };

  function _audioPlay(payload) {
    // payload: "compose:<style>:<seed>"
    const parts = payload.split(':');
    if (parts[0] !== 'compose' || parts.length < 3) return;
    const style = parts[1];
    const seed  = parts.slice(2).join(':');
    const ctx   = _audioGetCtx();
    if (!ctx) return;

    const params = _STYLE_PARAMS[style] || _STYLE_PARAMS.ambient;

    // Deterministic note sequence from seed hash
    const seedNum = seed.split('').reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 0);
    const noteKeys = Object.keys(_NOTE_FREQS);
    const notes = Array.from({length: 16}, (_, i) => noteKeys[(seedNum * (i + 7)) % noteKeys.length]);

    let t = ctx.currentTime + 0.05;
    notes.forEach((note, i) => {
      // Skip ~30% of notes for sparsity (glitch skips more)
      const skipRate = style === 'glitch' ? 0.5 : 0.3;
      if (((seedNum * (i + 1)) % 100) / 100 < skipRate) { t += params.gap; return; }
      const freq = _NOTE_FREQS[note];
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = params.wave;
      osc.frequency.setValueAtTime(freq, t);
      gain.gain.setValueAtTime(0, t);
      gain.gain.linearRampToValueAtTime(params.gain, t + 0.02);
      gain.gain.linearRampToValueAtTime(0, t + params.dur);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(t);
      osc.stop(t + params.dur + 0.05);
      t += params.dur + params.gap;
    });
  }

  // ── T11: Gamepad Support — controller navigation + command shortcuts ─────
  const _gp = {
    active:   false,
    _rafId:   null,
    _btnPrev: {},   // previous frame button states
    _axisPrev: {},
    _lastSB:  0,    // last scroll-by timestamp (throttle)
    // Map face buttons to quick commands
    _faceMap: {
      0: 'status',    // A / Cross
      1: 'help',      // B / Circle
      2: 'hive /who', // X / Square
      3: 'map',       // Y / Triangle
    },
    _bumperMap: {
      4: 'inventory',  // LB
      5: 'quests',     // RB
    },
  };

  function _gpStart() {
    if (_gp._rafId) return;
    function _poll() {
      _gp._rafId = requestAnimationFrame(_poll);
      const pads = navigator.getGamepads ? navigator.getGamepads() : [];
      for (const pad of pads) {
        if (!pad || !pad.connected) continue;
        _gpProcess(pad);
        break; // first connected pad only
      }
    }
    _poll();
  }

  function _gpStop() {
    if (_gp._rafId) { cancelAnimationFrame(_gp._rafId); _gp._rafId = null; }
  }

  function _gpProcess(pad) {
    const btns = pad.buttons;
    const axes = pad.axes;
    const now  = Date.now();

    // ── Face buttons (A/B/X/Y) — fire quick commands on press ─────────
    for (const [idx, cmd] of Object.entries(_gp._faceMap)) {
      const pressed = btns[+idx] && btns[+idx].pressed;
      if (pressed && !_gp._btnPrev[idx]) {
        // newly pressed
        const input = document.getElementById('cmd-input');
        if (input) { input.value = cmd; }
        runCommand(cmd);
      }
      _gp._btnPrev[idx] = !!pressed;
    }

    // ── Bumpers — quick nav ────────────────────────────────────────────
    for (const [idx, cmd] of Object.entries(_gp._bumperMap)) {
      const pressed = btns[+idx] && btns[+idx].pressed;
      if (pressed && !_gp._btnPrev[`b${idx}`]) {
        runCommand(cmd);
      }
      _gp._btnPrev[`b${idx}`] = !!pressed;
    }

    // ── Start button — toggle help ────────────────────────────────────
    const start = btns[9] && btns[9].pressed;
    if (start && !_gp._btnPrev.start) { runCommand('help'); }
    _gp._btnPrev.start = !!start;

    // ── Left stick vertical — scroll terminal output ──────────────────
    const ly = axes[1] || 0;
    if (Math.abs(ly) > 0.4 && now - _gp._lastSB > 120) {
      const out = document.getElementById('output') || document.querySelector('.terminal-output');
      if (out) { out.scrollTop += ly * 60; }
      _gp._lastSB = now;
    }

    // ── D-pad up/down — scroll ─────────────────────────────────────────
    const dUp   = btns[12] && btns[12].pressed;
    const dDown = btns[13] && btns[13].pressed;
    if ((dUp || dDown) && now - _gp._lastSB > 120) {
      const out = document.getElementById('output') || document.querySelector('.terminal-output');
      if (out) { out.scrollTop += dDown ? 80 : -80; }
      _gp._lastSB = now;
    }

    // ── Right stick horizontal — move cursor in input ──────────────────
    const rx = axes[2] || 0;
    if (Math.abs(rx) > 0.6 && !_gp._axisPrev.rx) {
      const input = document.getElementById('cmd-input');
      if (input) {
        const pos = input.selectionStart || 0;
        const newPos = rx > 0 ? Math.min(pos + 1, input.value.length) : Math.max(pos - 1, 0);
        input.setSelectionRange(newPos, newPos);
      }
    }
    _gp._axisPrev.rx = Math.abs(rx) > 0.6;
  }

  // Auto-start if gamepad connected
  window.addEventListener('gamepadconnected', (e) => {
    if (!_gp.active) return;
    printLines([
      { t: 'system', s: `  [GAMEPAD]: Controller connected — ${e.gamepad.id.slice(0, 40)}` },
      { t: 'dim',    s: '  A=status  B=help  X=hive/who  Y=map  LB=inventory  RB=quests' },
    ]);
    _gpStart();
  });
  window.addEventListener('gamepaddisconnected', () => { _gpStop(); });

  // ── U2: Multi-tab terminal ────────────────────────────────────────────────
  //
  // Each tab: { id, label, html: string, scrollTop: number, history: string[], histIdx: number }
  // Tabs share the same game state (gs/fs) — output buffers are independent views.
  // Shortcuts: Ctrl+T = new tab · Ctrl+W = close · Ctrl+1-5 = switch
  //
  const _termTabs = {
    tabs: [],
    active: 0,
    _nextId: 1,

    _barEl: document.getElementById('term-tab-bar'),

    // Create a fresh tab object
    _makeTab(label) {
      return {
        id: this._nextId++,
        label: label || `TERM-${this._nextId - 1}`,
        html: '',
        scrollTop: 0,
        history: [],
        histIdx: -1,
      };
    },

    // Save current output into the active tab's buffer
    _saveActive() {
      if (!this.tabs.length) return;
      const t = this.tabs[this.active];
      t.html = outputEl.innerHTML;
      t.scrollTop = outputEl.scrollTop;
      // Snapshot command history from cmds.history
      t.history = cmds.history.slice();
      t.histIdx = cmdHistIdx;
    },

    // Restore a tab's buffer into the DOM
    _restoreTab(idx) {
      const t = this.tabs[idx];
      outputEl.innerHTML = t.html;
      outputEl.scrollTop = t.scrollTop;
      // Restore per-tab command history into cmds.history
      cmds.history.length = 0;
      for (const h of t.history) cmds.history.push(h);
      cmdHistIdx = t.histIdx;
    },

    // Render the tab bar
    render() {
      if (!this._barEl) return;
      this._barEl.innerHTML = '';
      this.tabs.forEach((t, i) => {
        const el = document.createElement('div');
        el.className = `term-tab${i === this.active ? ' active' : ''}`;
        el.title = `Switch to ${t.label} (Ctrl+${i + 1})`;
        const closeHtml = this.tabs.length > 1 ? `<span class="term-tab-close" title="Close tab (Ctrl+W)">✕</span>` : '';
        el.innerHTML = `<span class="term-tab-lbl">${t.label}</span>${closeHtml}`;
        el.querySelector('.term-tab-lbl').addEventListener('click', () => this.switchTo(i));
        const closeBtn = el.querySelector('.term-tab-close');
        if (closeBtn) closeBtn.addEventListener('click', (e) => { e.stopPropagation(); this.closeTab(i); });
        this._barEl.appendChild(el);
      });
      // "+" button
      const addBtn = document.createElement('div');
      addBtn.className = 'term-tab-add';
      addBtn.title = 'New terminal tab (Ctrl+T)';
      addBtn.textContent = '+';
      addBtn.addEventListener('click', () => this.newTab());
      this._barEl.appendChild(addBtn);
      // Hint
      const hint = document.createElement('span');
      hint.className = 'term-tab-hint';
      hint.textContent = 'Ctrl+T new · Ctrl+W close · Ctrl+1-5 switch';
      this._barEl.appendChild(hint);
    },

    newTab() {
      this._saveActive();
      const n = this._makeTab();
      this.tabs.push(n);
      this.active = this.tabs.length - 1;
      outputEl.innerHTML = '';
      cmds.history.length = 0;
      cmdHistIdx = -1;
      printLines([
        { t: 'system', s: `  ── Terminal ${n.label} ──` },
        { t: 'dim',    s: `  New session. Type \`help\` or \`status\`.` },
      ]);
      inputEl.focus();
      this.render();
    },

    switchTo(idx) {
      if (idx < 0 || idx >= this.tabs.length || idx === this.active) return;
      this._saveActive();
      this.active = idx;
      this._restoreTab(idx);
      scrollDown();
      inputEl.focus();
      this.render();
    },

    closeTab(idx) {
      if (this.tabs.length <= 1) return; // never close last tab
      if (idx === this.active) this._saveActive();
      this.tabs.splice(idx, 1);
      this.active = Math.min(this.active, this.tabs.length - 1);
      this._restoreTab(this.active);
      scrollDown();
      inputEl.focus();
      this.render();
    },

    // Init: wrap existing output into tab-0
    init() {
      const first = this._makeTab('TERM-1');
      first.html = outputEl.innerHTML;
      first.scrollTop = 0;
      first.history = cmds.history.slice();
      first.histIdx = -1;
      this.tabs = [first];
      this.active = 0;
      this.render();
    },
  };

  // Init after boot sequence has had a chance to print
  setTimeout(() => _termTabs.init(), 50);

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    // Ctrl+T — new tab
    if (e.ctrlKey && e.key === 't') {
      e.preventDefault();
      _termTabs.newTab();
      return;
    }
    // Ctrl+W — close active tab
    if (e.ctrlKey && e.key === 'w') {
      if (_termTabs.tabs.length > 1) {
        e.preventDefault();
        _termTabs.closeTab(_termTabs.active);
      }
      return;
    }
    // Ctrl+1-5 — switch to tab N
    if (e.ctrlKey && e.key >= '1' && e.key <= '5') {
      const idx = parseInt(e.key, 10) - 1;
      if (idx < _termTabs.tabs.length) {
        e.preventDefault();
        _termTabs.switchTo(idx);
      }
    }
  });

  // Dev helper — expose renderTab so panels.js can delegate existing panels
  window._game = { fs, gs, npcs, story, tut, cmds, CHALLENGES, GameState, timeline: _timeline, addEvent, _renderTabFn: renderTab, runCommand, printLines, voiceActivate: _voiceActivate, gpActivate: (on) => { _gp.active = on; on ? _gpStart() : _gpStop(); }, termTabs: _termTabs };

})();
