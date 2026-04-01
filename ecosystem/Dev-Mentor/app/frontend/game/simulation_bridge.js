/**
 * Terminal Depths — Simulation Bridge v1
 * ════════════════════════════════════════════════════════════════════════════
 * Tripartite Architecture — Layer: Browser ↔ Simulation
 *
 * This file is the membrane between the graphical UI and the Simulation.
 * It does NOT replace the client-side game.js engine (which runs instantly).
 * It runs IN PARALLEL, forwarding every command to the Python Simulation
 * so state is persistent, multi-surface, and agent-aware.
 *
 * What it provides:
 *   window._bridge.serverState   — authoritative state from the Simulation
 *   window._bridge.send(cmd)     — fire a command to the Simulation
 *   window._bridge.sync()        — request fresh state push
 *   window._bridge.connected     — boolean connection status
 *   window._bridge.sessionId     — server-side session ID
 *   td:bridge:state — CustomEvent dispatched on each server state push
 *   td:bridge:output — CustomEvent dispatched on each server command result
 *
 * Design principle: The Simulation is the truth. The client engine is the speed.
 */

(function () {
  'use strict';

  // ── Configuration ──────────────────────────────────────────────────────
  const WS_PROTOCOL = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const WS_BASE     = `${WS_PROTOCOL}//${location.host}`;
  const WS_URL      = `${WS_BASE}/ws/game`;
  const RECONNECT_MS_BASE = 2000;
  const RECONNECT_MAX_MS  = 30000;
  const STORAGE_SESSION   = 'td_server_session';

  // ── State ──────────────────────────────────────────────────────────────
  let _ws            = null;
  let _connected     = false;
  let _sessionId     = null;
  let _reconnectMs   = RECONNECT_MS_BASE;
  let _reconnectTimer= null;
  let _pingTimer     = null;
  let _lastPong      = Date.now();

  // Server-authoritative state cache — panels read from this
  let _serverState   = null;

  // Command queue for when WS is temporarily disconnected
  const _queue = [];

  // ── Helpers ────────────────────────────────────────────────────────────
  function _log(...args) {
    console.log('[Bridge]', ...args);
  }

  function _dispatch(name, detail) {
    document.dispatchEvent(new CustomEvent(name, { detail }));
  }

  function _saveSession(sid) {
    try { localStorage.setItem(STORAGE_SESSION, sid); } catch (_) {}
    _sessionId = sid;
  }

  function _loadSession() {
    try { return localStorage.getItem(STORAGE_SESSION) || null; } catch (_) { return null; }
  }

  // ── WebSocket lifecycle ────────────────────────────────────────────────
  function _connect() {
    if (_ws) {
      try { _ws.close(); } catch (_) {}
      _ws = null;
    }

    const sid = _loadSession();
    const url = sid ? `${WS_URL}?session_id=${encodeURIComponent(sid)}` : WS_URL;

    try {
      _ws = new WebSocket(url);
    } catch (err) {
      _log('WebSocket construction failed:', err.message);
      _scheduleReconnect();
      return;
    }

    _ws.addEventListener('open', () => {
      _log('Connected to Simulation ✓');
      _connected = true;
      _reconnectMs = RECONNECT_MS_BASE;
      _lastPong = Date.now();
      _startPingWatch();
      // Flush queued commands
      while (_queue.length) {
        _send(_queue.shift());
      }
    });

    _ws.addEventListener('message', (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (_) { return; }
      _handleMessage(msg);
    });

    _ws.addEventListener('close', () => {
      _connected = false;
      _stopPingWatch();
      _ws = null;
      _log('Disconnected — reconnecting in', _reconnectMs, 'ms');
      _scheduleReconnect();
    });

    _ws.addEventListener('error', () => {
      // close event will handle reconnect
    });
  }

  function _scheduleReconnect() {
    if (_reconnectTimer) clearTimeout(_reconnectTimer);
    _reconnectTimer = setTimeout(() => {
      _reconnectMs = Math.min(_reconnectMs * 1.5, RECONNECT_MAX_MS);
      _connect();
    }, _reconnectMs);
  }

  function _send(payload) {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
      _ws.send(JSON.stringify(payload));
    } else {
      // Queue non-ping messages for delivery on reconnect
      if (payload.type === 'command') {
        _queue.push(payload);
        if (_queue.length > 50) _queue.shift(); // cap queue
      }
    }
  }

  function _startPingWatch() {
    _stopPingWatch();
    _pingTimer = setInterval(() => {
      if (Date.now() - _lastPong > 45000) {
        _log('Pong timeout — reconnecting');
        _ws && _ws.close();
        return;
      }
    }, 10000);
  }

  function _stopPingWatch() {
    if (_pingTimer) { clearInterval(_pingTimer); _pingTimer = null; }
  }

  // ── Message handler ────────────────────────────────────────────────────
  function _handleMessage(msg) {
    const type = msg.type;

    if (type === 'ping') {
      _lastPong = Date.now();
      _send({ type: 'pong' });
      return;
    }

    if (type === 'connected') {
      _saveSession(msg.session_id);
      _serverState = msg.state || null;
      _log('Session:', msg.session_id.slice(0, 8), '  Level:', msg.state && msg.state.level);
      _dispatch('td:bridge:state', {
        state: _serverState,
        cwd: msg.cwd,
        sessionId: msg.session_id,
        source: 'connected',
      });
      // Update status indicator
      _updateStatusDot(true);
      return;
    }

    if (type === 'state_push') {
      _serverState = msg.state || _serverState;
      _dispatch('td:bridge:state', {
        state: _serverState,
        cwd: msg.cwd,
        source: 'sync',
      });
      return;
    }

    if (type === 'command_result') {
      _serverState = msg.state || _serverState;
      _dispatch('td:bridge:output', {
        command: msg.command,
        output: msg.output || [],
        state: _serverState,
        cwd: msg.cwd,
        levelUp: msg.level_up,
        storyBeats: msg.story_beats || [],
        xpGained: msg.xp_gained || 0,
      });
      _dispatch('td:bridge:state', {
        state: _serverState,
        cwd: msg.cwd,
        source: 'command',
      });
      // Sync panel system if it's listening
      if (window._panelSys && msg.level_up) {
        window._panelSys.refresh();
      }
      return;
    }

    if (type === 'error') {
      // Surface server errors as a dim status line (don't spam toasts)
      _log('Server error:', msg.message);
      return;
    }
  }

  // ── Status dot (tiny indicator in faction bar) ─────────────────────────
  let _dot = null;

  function _createStatusDot() {
    const factionBar = document.getElementById('faction-bar');
    if (!factionBar || document.getElementById('bridge-dot')) return;
    _dot = document.createElement('span');
    _dot.id    = 'bridge-dot';
    _dot.title = 'Simulation connection status';
    _dot.style.cssText = [
      'display:inline-block',
      'width:6px', 'height:6px',
      'border-radius:50%',
      'background:#555',
      'margin-left:8px',
      'vertical-align:middle',
      'transition:background 0.4s',
      'cursor:default',
    ].join(';');
    factionBar.appendChild(_dot);
  }

  function _updateStatusDot(ok) {
    if (!_dot) return;
    _dot.style.background = ok ? '#00ff88' : '#ff4040';
    _dot.title = ok
      ? `Simulation connected (${_sessionId ? _sessionId.slice(0, 8) : '?'})`
      : 'Simulation disconnected — reconnecting…';
  }

  // ── Intercept terminal commands ────────────────────────────────────────
  // Hook into game.js's runCommand by listening to the command input Enter key.
  // We fire-and-forget to the Simulation — the client-side engine handles display.
  function _hookCommandInput() {
    const cmdInput = document.getElementById('cmd-input');
    if (!cmdInput) return;

    // Listen at capture phase to run BEFORE game.js's keydown handler
    cmdInput.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter') return;
      const cmd = cmdInput.value.trim();
      if (!cmd) return;
      // Fire to Simulation (non-blocking — client engine handles display)
      _send({ type: 'command', command: cmd });
    }, true); // capture = true → runs before game.js bubble handler
  }

  // ── Public API ─────────────────────────────────────────────────────────
  window._bridge = {
    get connected()   { return _connected; },
    get sessionId()   { return _sessionId; },
    get serverState() { return _serverState; },

    /** Send a command to the Simulation */
    send(cmd) {
      _send({ type: 'command', command: String(cmd) });
    },

    /** Request a fresh state push from the Simulation */
    sync() {
      _send({ type: 'sync' });
    },

    /** Get server state field (falls back to local gs state) */
    get(field) {
      if (_serverState && _serverState[field] !== undefined) {
        return _serverState[field];
      }
      if (window._game && window._game.gs) {
        const st = window._game.gs.getState();
        return st[field];
      }
      return null;
    },
  };

  // ── Bootstrap ──────────────────────────────────────────────────────────
  function _init() {
    _createStatusDot();
    _hookCommandInput();
    _connect();

    // Reconnect on visibility change (tab comes back from background)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && !_connected) {
        _log('Tab became visible — reconnecting');
        _connect();
      }
    });

    // Periodic sync for panels (every 30s — keep server state fresh)
    setInterval(() => {
      if (_connected) _send({ type: 'sync' });
    }, 30000);

    _log('Simulation Bridge initialised ✓');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', _init);
  } else {
    _init();
  }

})();
