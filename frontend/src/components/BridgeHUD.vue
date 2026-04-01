<template>
  <div class="bridge-hud" @mouseenter="expanded = true" @mouseleave="expanded = false">
    <!-- Compact dot strip -->
    <div class="hud-dots">
      <span class="hud-icon">🌉</span>
      <span
        v-for="svc in dotServices"
        :key="svc.id"
        class="svc-dot"
        :class="svc.cls"
        :title="svc.label"
      ></span>
      <span class="hud-event-badge" v-if="eventCount > 0" :title="`${eventCount} events received`">
        {{ eventCount > 99 ? '99+' : eventCount }}
      </span>
      <span class="hud-sse-dot" :class="sseConnected ? 'sse-on' : 'sse-off'" title="Event stream"></span>
    </div>

    <!-- Expanded tooltip panel -->
    <transition name="hud-drop">
      <div class="hud-panel" v-if="expanded && status">
        <div class="hud-panel-title">Bridge Status</div>

        <div class="hud-section">
          <div class="hud-row" v-for="svc in panelServices" :key="svc.id">
            <span class="hud-svc-dot" :class="svc.cls"></span>
            <span class="hud-svc-name">{{ svc.label }}</span>
            <span class="hud-svc-state" :class="svc.cls">{{ svc.state }}</span>
          </div>
        </div>

        <div class="hud-divider"></div>

        <div class="hud-section">
          <div class="hud-stat">
            <span class="hud-stat-l">Quests synced</span>
            <span class="hud-stat-v quest">{{ status.quests?.synced_count ?? 0 }}</span>
          </div>
          <div class="hud-stat">
            <span class="hud-stat-l">Sessions</span>
            <span class="hud-stat-v">{{ status.sessions_active ?? 0 }}</span>
          </div>
          <div class="hud-stat">
            <span class="hud-stat-l">Uptime</span>
            <span class="hud-stat-v">{{ formatUptime(status.uptime_s) }}</span>
          </div>
          <div class="hud-stat">
            <span class="hud-stat-l">Events</span>
            <span class="hud-stat-v">{{ eventCount }}</span>
          </div>
        </div>

        <div class="hud-divider" v-if="recentEvents.length"></div>

        <div class="hud-events" v-if="recentEvents.length">
          <div class="hud-events-title">Recent Events</div>
          <div class="hud-event-row" v-for="ev in recentEvents" :key="ev.id">
            <span class="ev-type" :class="`ev-${ev.type}`">{{ ev.type }}</span>
            <span class="ev-data">{{ ev.summary }}</span>
          </div>
        </div>

        <div class="hud-footer">
          <a class="hud-link" href="/ecosystem">Ecosystem ↗</a>
          <a class="hud-link" href="/orchestrator">Orchestrator ↗</a>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const status = ref(null)
const expanded = ref(false)
const sseConnected = ref(false)
const eventCount = ref(0)
const recentEvents = ref([])

let pollTimer = null
let evtSource = null

// ── Service dots ────────────────────────────────────────────────────────────
const LIVE_SERVICES = [
  { id: 'chatdev',         label: 'ChatDev :6400',         port: 6400 },
  { id: 'dev_mentor',     label: 'Dev-Mentor :8008',      port: 8008 },
  { id: 'nusyq_hub',      label: 'NuSyQ-Hub :3003',       port: 3003 },
  { id: 'concept_samurai',label: 'CONCEPT_SAMURAI :3002',  port: 3002 },
]

const dotServices = computed(() => {
  if (!status.value) return []
  const online = new Set(status.value.repos?.online ?? [])
  return LIVE_SERVICES.map(s => ({
    ...s, cls: online.has(s.id) ? 'dot-g' : 'dot-r',
  }))
})

const panelServices = computed(() => {
  if (!status.value) return []
  const online = new Set(status.value.repos?.online ?? [])
  const all = status.value.repos?.total ?? 0
  const named = LIVE_SERVICES.map(s => ({
    ...s, cls: online.has(s.id) ? 'dot-g' : 'dot-r', state: online.has(s.id) ? 'Online' : 'Offline',
  }))
  const extra = Math.max(0, all - LIVE_SERVICES.length)
  if (extra > 0) named.push({ id: 'others', label: `Other repos (${extra})`, cls: 'dot-b', state: 'CLI/lib', port: null })
  return named
})

// ── Data ────────────────────────────────────────────────────────────────────
async function loadStatus() {
  try {
    const r = await fetch('/api/bridge/status')
    status.value = await r.json()
  } catch (e) {}
}

function formatUptime(s) {
  if (!s) return '—'
  if (s < 60) return `${Math.round(s)}s`
  if (s < 3600) return `${Math.round(s / 60)}m`
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60)
  return `${h}h ${m}m`
}

// ── SSE ─────────────────────────────────────────────────────────────────────
function connectSSE() {
  if (evtSource) evtSource.close()
  evtSource = new EventSource('/api/bridge/events')

  evtSource.addEventListener('open', () => { sseConnected.value = true })

  evtSource.addEventListener('ping', () => {
    sseConnected.value = true
  })

  evtSource.addEventListener('log', (e) => {
    try {
      const d = JSON.parse(e.data)
      eventCount.value++
      recentEvents.value.unshift({ id: Date.now(), type: 'log', summary: `${d.action ?? '?'} (${d.repo ?? '?'})` })
      if (recentEvents.value.length > 5) recentEvents.value.pop()
    } catch {}
  })

  evtSource.addEventListener('health', (e) => {
    try {
      const d = JSON.parse(e.data)
      eventCount.value++
      recentEvents.value.unshift({ id: Date.now(), type: 'health', summary: `${d.online} repos online` })
      if (recentEvents.value.length > 5) recentEvents.value.pop()
      // Update status inline
      if (status.value && d.repos) status.value.repos = d.repos
    } catch {}
  })

  evtSource.addEventListener('project', (e) => {
    try {
      const d = JSON.parse(e.data)
      eventCount.value++
      recentEvents.value.unshift({ id: Date.now(), type: 'project', summary: `${d.name}` })
      if (recentEvents.value.length > 5) recentEvents.value.pop()
    } catch {}
  })

  evtSource.onerror = () => {
    sseConnected.value = false
    evtSource.close()
    setTimeout(connectSSE, 10000)
  }
}

onMounted(() => {
  loadStatus()
  connectSSE()
  pollTimer = setInterval(loadStatus, 30000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  if (evtSource) evtSource.close()
})
</script>

<style scoped>
.bridge-hud {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 200;
  user-select: none;
}

.hud-dots {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: default;
}

.hud-icon {
  font-size: 0.85rem;
  opacity: 0.7;
  margin-right: 2px;
}

.svc-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.dot-g { background: #3fb950; box-shadow: 0 0 4px #3fb95066; }
.dot-r { background: #f85149; box-shadow: 0 0 4px #f8514966; }
.dot-b { background: #58a6ff; box-shadow: 0 0 4px #58a6ff55; }

.hud-event-badge {
  font-size: 0.6rem;
  background: rgba(210,153,34,.3);
  border: 1px solid #d2992266;
  color: #e3b341;
  border-radius: 8px;
  padding: 0 5px;
  font-weight: 700;
  min-width: 16px;
  text-align: center;
}

.hud-sse-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  margin-left: 2px;
}
.sse-on  { background: #3fb950; animation: pulse-sse 2s infinite; }
.sse-off { background: #f85149; }
@keyframes pulse-sse { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ── Panel ── */
.hud-panel {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  width: 230px;
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 10px;
  padding: 0.9rem 1rem;
  box-shadow: 0 8px 32px rgba(0,0,0,.6);
  z-index: 300;
}

.hud-panel-title {
  font-size: 0.72rem;
  font-weight: 700;
  color: #58a6ff;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.6rem;
}

.hud-section { display: flex; flex-direction: column; gap: 5px; }

.hud-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
}

.hud-svc-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}

.hud-svc-name { color: #c9d1d9; flex: 1; }
.hud-svc-state { font-size: 0.7rem; font-weight: 600; }
.hud-svc-state.dot-g { color: #3fb950; }
.hud-svc-state.dot-r { color: #f85149; }
.hud-svc-state.dot-b { color: #58a6ff; }

.hud-divider { height: 1px; background: #21262d; margin: 0.55rem 0; }

.hud-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
}
.hud-stat-l { color: #8b949e; }
.hud-stat-v { color: #e6edf3; font-weight: 600; }
.hud-stat-v.quest { color: #e3b341; }

.hud-events-title {
  font-size: 0.65rem;
  text-transform: uppercase;
  color: #8b949e;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}

.hud-event-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  padding: 2px 0;
}

.ev-type {
  font-size: 0.6rem;
  padding: 1px 5px;
  border-radius: 5px;
  font-weight: 700;
  text-transform: uppercase;
  white-space: nowrap;
}
.ev-log     { background: rgba(88,166,255,.15); color: #58a6ff; }
.ev-health  { background: rgba(63,185,80,.15);  color: #3fb950; }
.ev-project { background: rgba(210,153,34,.15); color: #e3b341; }

.ev-data { color: #8b949e; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.hud-footer {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.6rem;
}

.hud-link {
  font-size: 0.7rem;
  color: #58a6ff;
  text-decoration: none;
  opacity: 0.75;
  transition: opacity .15s;
}
.hud-link:hover { opacity: 1; }

/* ── Transition ── */
.hud-drop-enter-active { transition: all .18s ease; }
.hud-drop-leave-active { transition: all .12s ease; }
.hud-drop-enter-from  { opacity: 0; transform: translateY(-6px); }
.hud-drop-leave-to    { opacity: 0; transform: translateY(-4px); }
</style>
