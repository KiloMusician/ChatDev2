<template>
  <div class="orch-view">
    <!-- Header -->
    <div class="orch-header">
      <div>
        <h1 class="orch-title">NuSyQ Orchestrator</h1>
        <p class="orch-subtitle">Central control layer — CHUG cycle engine</p>
      </div>
      <div class="orch-actions">
        <button class="btn-scan" @click="runScan" :disabled="scanning">
          {{ scanning ? 'Scanning...' : '🔍 Scan' }}
        </button>
        <button
          class="btn-cycle"
          @click="triggerCycle"
          :disabled="cycleRunning || triggering"
        >
          {{ cycleRunning ? '⏳ Cycle Running...' : triggering ? 'Starting...' : '⚡ CHUG Cycle' }}
        </button>
        <button class="btn-refresh" @click="loadAll">↻</button>
      </div>
    </div>

    <!-- Status Bar -->
    <div class="status-bar">
      <div class="stat-pill" :class="cycleRunning ? 'running' : 'idle'">
        <span class="stat-dot"></span>
        {{ cycleRunning ? 'Cycle Running' : 'Idle' }}
      </div>
      <div class="stat-pill neutral" v-if="status">
        <span class="stat-label">Cycle</span>
        <span class="stat-num">#{{ status.orchestrator?.last_cycle || '—' }}</span>
      </div>
      <div class="stat-pill neutral" v-if="status">
        <span class="stat-label">Agents</span>
        <span class="stat-num">{{ status.agents?.length || 0 }}</span>
      </div>
      <div class="stat-pill neutral" v-if="status">
        <span class="stat-label">Tools</span>
        <span class="stat-num">{{ status.tools?.total || 0 }}</span>
      </div>
      <div class="stat-pill neutral" v-if="taskStats">
        <span class="stat-label">Tasks (total)</span>
        <span class="stat-num">{{ taskStats.total }}</span>
      </div>
      <div class="stat-pill" :class="daemon?.running ? 'daemon-on' : 'daemon-off'" v-if="daemon">
        <span class="stat-dot"></span>
        Daemon {{ daemon.running ? 'ON' : 'OFF' }}
        <span v-if="daemon.running" class="stat-interval">· {{ formatInterval(daemon.interval_s) }}</span>
      </div>
    </div>

    <div class="orch-grid">

      <!-- Left: Scan + Cycle History -->
      <div class="orch-col">

        <!-- Live Scan -->
        <div class="panel" v-if="scanResult">
          <h3 class="panel-title">🔍 System Scan</h3>
          <div class="scan-services">
            <div
              v-for="(s, name) in scanResult.services"
              :key="name"
              class="scan-svc"
              :class="s.online ? 'svc-up' : 'svc-down'"
            >
              <span class="scan-dot"></span>
              <span class="scan-name">{{ name.replace(/_/g,' ') }}</span>
              <span class="scan-code" v-if="s.code">{{ s.code }}</span>
            </div>
          </div>
          <div class="scan-meta">
            <div class="meta-row">
              <span>Memory keys</span><span>{{ scanResult.memory_keys }}</span>
            </div>
            <div class="meta-row">
              <span>Active agents</span><span>{{ scanResult.agents }}</span>
            </div>
            <div class="meta-row">
              <span>Registered tools</span><span>{{ scanResult.tools }}</span>
            </div>
          </div>
          <div class="scan-issues" v-if="scanResult.issues?.length">
            <div v-for="issue in scanResult.issues" :key="issue" class="issue-item">⚠ {{ issue }}</div>
          </div>
          <div class="scan-opps" v-if="scanResult.opportunities?.length">
            <div v-for="opp in scanResult.opportunities" :key="opp" class="opp-item">→ {{ opp }}</div>
          </div>
        </div>

        <!-- Cycle History -->
        <div class="panel">
          <h3 class="panel-title">⚡ Cycle History</h3>
          <div v-if="!cycles.length" class="empty-state">No cycles run yet</div>
          <div v-for="c in cycles" :key="c.cycle_num" class="cycle-row">
            <div class="cycle-num">#{{ c.cycle_num }}</div>
            <div class="cycle-phase" :class="phaseClass(c.phase)">{{ c.phase }}</div>
            <div class="cycle-status" :class="c.status === 'done' ? 'ok' : 'fail'">
              {{ c.status }}
            </div>
            <div class="cycle-time">{{ formatTime(c.started_at) }}</div>
          </div>
        </div>

        <!-- CHUG Daemon Control -->
        <div class="panel daemon-panel">
          <h3 class="panel-title">
            🔄 CHUG Daemon
            <span class="daemon-badge" :class="daemon?.running ? 'badge-on' : 'badge-off'">
              {{ daemon?.running ? 'RUNNING' : 'STOPPED' }}
            </span>
          </h3>

          <!-- Stats row -->
          <div class="daemon-stats" v-if="daemon">
            <div class="ds-item">
              <span class="ds-label">Interval</span>
              <span class="ds-val">{{ formatInterval(daemon.interval_s) }}</span>
            </div>
            <div class="ds-item">
              <span class="ds-label">Daemon cycles</span>
              <span class="ds-val">{{ daemon.total_cycles ?? 0 }}</span>
            </div>
            <div class="ds-item">
              <span class="ds-label">Errors</span>
              <span class="ds-val" :class="daemon.errors ? 'val-err' : ''">{{ daemon.errors ?? 0 }}</span>
            </div>
          </div>

          <!-- Last / Next run -->
          <div class="daemon-times" v-if="daemon">
            <div class="dt-row" v-if="daemon.last_run_at">
              <span class="dt-label">Last run</span>
              <span class="dt-val">{{ formatTime(daemon.last_run_at) }}</span>
              <span class="dt-cycle" v-if="daemon.last_run_cycle">cycle #{{ daemon.last_run_cycle }}</span>
            </div>
            <div class="dt-row" v-if="daemon.next_run_at && daemon.running">
              <span class="dt-label">Next run</span>
              <span class="dt-val next-run">{{ formatTime(daemon.next_run_at) }}</span>
              <span class="dt-countdown">{{ countdown }}</span>
            </div>
            <div class="dt-row" v-if="daemon.last_error">
              <span class="dt-label err-label">Last error</span>
              <span class="dt-val err-val">{{ daemon.last_error }}</span>
            </div>
          </div>

          <!-- Interval slider -->
          <div class="daemon-interval-ctrl">
            <label class="interval-label">Interval: {{ formatInterval(intervalInput) }}</label>
            <input
              type="range"
              min="60" max="3600" step="60"
              v-model.number="intervalInput"
              class="interval-slider"
            />
            <div class="interval-presets">
              <button v-for="pre in intervalPresets" :key="pre.s"
                class="preset-btn" :class="{ active: intervalInput === pre.s }"
                @click="intervalInput = pre.s">{{ pre.label }}</button>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="daemon-btns">
            <button
              v-if="!daemon?.running"
              class="dbtn dbtn-start"
              @click="daemonStart"
              :disabled="daemonBusy"
            >▶ Start</button>
            <button
              v-if="daemon?.running"
              class="dbtn dbtn-stop"
              @click="daemonStop"
              :disabled="daemonBusy"
            >⏹ Stop</button>
            <button
              v-if="daemon?.running"
              class="dbtn dbtn-cfg"
              @click="daemonUpdateInterval"
              :disabled="daemonBusy"
            >⏱ Update Interval</button>
            <button
              class="dbtn dbtn-now"
              @click="daemonRunNow"
              :disabled="daemonBusy || cycleRunning"
            >⚡ Run Now</button>
          </div>
        </div>

        <!-- Task Queue -->
        <div class="panel" v-if="taskStats">
          <h3 class="panel-title">📋 Task Queue</h3>
          <div class="task-counts">
            <div class="task-count" v-for="(cnt, st) in taskStats.by_status" :key="st"
                 :class="`tcount-${st}`">
              <span class="tc-num">{{ cnt }}</span>
              <span class="tc-label">{{ st }}</span>
            </div>
          </div>
          <div class="task-list" v-if="taskStats.recent?.length">
            <div v-for="t in taskStats.recent" :key="t.task_id" class="task-item">
              <span class="task-action">{{ t.action }}</span>
              <span class="task-repo">{{ t.repo }}</span>
              <span class="task-st" :class="`ts-${t.status}`">{{ t.status }}</span>
            </div>
          </div>

          <!-- Enqueue form -->
          <div class="enqueue-form">
            <input v-model="newTask.action" placeholder="action" class="eq-input" />
            <input v-model="newTask.repo" placeholder="repo" class="eq-input" />
            <button class="btn-enqueue" @click="enqueueTask">+ Enqueue</button>
          </div>
        </div>
      </div>

      <!-- Right: Agents + Tools + Memory + Logs -->
      <div class="orch-col">

        <!-- Agents -->
        <div class="panel">
          <h3 class="panel-title">🤖 Agent Registry</h3>
          <div v-if="!agents.length" class="empty-state">No agents registered</div>
          <div v-for="a in agents" :key="a.agent_id" class="agent-row">
            <div class="agent-dot" :class="a.status === 'active' ? 'a-active' : 'a-idle'"></div>
            <div class="agent-info">
              <span class="agent-name">{{ a.name }}</span>
              <span class="agent-repo">{{ a.repo }}</span>
            </div>
            <div class="agent-caps">
              <span v-for="cap in parseCaps(a.capabilities)" :key="cap" class="cap-tag">{{ cap }}</span>
            </div>
          </div>
        </div>

        <!-- Tools -->
        <div class="panel">
          <h3 class="panel-title">🔧 Tool Registry</h3>
          <div class="tools-filter">
            <button
              v-for="repo in toolRepos"
              :key="repo"
              class="repo-filter"
              :class="{ active: toolFilter === repo }"
              @click="toolFilter = toolFilter === repo ? null : repo"
            >{{ repo }}</button>
          </div>
          <div class="tool-list">
            <div
              v-for="t in filteredTools"
              :key="t.tool_id"
              class="tool-item"
            >
              <span class="tool-name">{{ t.name }}</span>
              <span class="tool-repo-badge">{{ t.repo }}</span>
              <p class="tool-desc">{{ t.description }}</p>
            </div>
          </div>
        </div>

        <!-- Execution Logs -->
        <div class="panel">
          <h3 class="panel-title">📊 Execution Log</h3>
          <div v-if="!logs.length" class="empty-state">No logs yet</div>
          <div v-for="l in logs" :key="l.log_id" class="log-row">
            <span class="log-status" :class="l.status === 'success' ? 'ls-ok' : 'ls-err'">
              {{ l.status === 'success' ? '✓' : '✗' }}
            </span>
            <span class="log-action">{{ l.action }}</span>
            <span class="log-repo">{{ l.repo }}</span>
            <span class="log-ms" v-if="l.duration_ms">{{ l.duration_ms }}ms</span>
            <span class="log-time">{{ formatTime(l.created_at) }}</span>
          </div>
        </div>

        <!-- Shared Memory -->
        <div class="panel">
          <h3 class="panel-title">🧠 Shared Memory</h3>
          <div class="mem-ns-filter">
            <button
              v-for="ns in memNamespaces"
              :key="ns"
              class="ns-btn"
              :class="{ active: memNs === ns }"
              @click="memNs = ns"
            >{{ ns }}</button>
          </div>
          <div class="mem-list">
            <div v-for="item in filteredMemory" :key="item.key" class="mem-item">
              <span class="mem-key">{{ item.key }}</span>
              <span class="mem-val">{{ JSON.stringify(item.value).slice(0, 80) }}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const status = ref(null)
const scanResult = ref(null)
const cycles = ref([])
const taskStats = ref(null)
const agents = ref([])
const tools = ref([])
const logs = ref([])
const memory = ref([])
const memNs = ref('all')
const toolFilter = ref(null)

const scanning = ref(false)
const triggering = ref(false)
const cycleRunning = ref(false)
const newTask = ref({ action: '', repo: 'ecosystem' })

// Daemon state
const daemon = ref(null)
const daemonBusy = ref(false)
const intervalInput = ref(600)
const countdown = ref('')

const intervalPresets = [
  { label: '1 min',  s: 60 },
  { label: '5 min',  s: 300 },
  { label: '10 min', s: 600 },
  { label: '30 min', s: 1800 },
  { label: '1 hr',   s: 3600 },
]

let pollTimer = null

// ── Computed ───────────────────────────────────────────────────────────────

const toolRepos = computed(() => [...new Set(tools.value.map(t => t.repo))])

const filteredTools = computed(() =>
  toolFilter.value ? tools.value.filter(t => t.repo === toolFilter.value) : tools.value
)

const memNamespaces = computed(() => {
  const ns = new Set(['all'])
  memory.value.forEach(m => ns.add(m.namespace || 'global'))
  return [...ns]
})

const filteredMemory = computed(() =>
  memNs.value === 'all'
    ? memory.value
    : memory.value.filter(m => m.namespace === memNs.value)
)

// ── Loaders ────────────────────────────────────────────────────────────────

async function loadAll() {
  await Promise.all([loadStatus(), loadCycles(), loadTasks(), loadAgents(), loadTools(), loadLogs(), checkRunning(), loadDaemon()])
}

async function loadStatus() {
  try {
    const r = await fetch('/api/orchestrator/status')
    const d = await r.json()
    status.value = d
    agents.value = d.agents || []
    memory.value = Array.isArray(d.memory) ? d.memory : []
    logs.value = d.recent_logs || []
  } catch (e) { console.error(e) }
}

async function loadCycles() {
  try {
    const r = await fetch('/api/orchestrator/cycle/history?limit=8')
    const d = await r.json()
    cycles.value = d.cycles || []
  } catch (e) { }
}

async function loadTasks() {
  try {
    const r = await fetch('/api/orchestrator/tasks')
    taskStats.value = await r.json()
  } catch (e) { }
}

async function loadAgents() {
  try {
    const r = await fetch('/api/orchestrator/agents')
    const d = await r.json()
    agents.value = d.agents || []
  } catch (e) { }
}

async function loadTools() {
  try {
    const r = await fetch('/api/orchestrator/tools')
    const d = await r.json()
    tools.value = d.tools || []
  } catch (e) { }
}

async function loadLogs() {
  try {
    const r = await fetch('/api/orchestrator/logs?limit=30')
    const d = await r.json()
    logs.value = d.logs || []
  } catch (e) { }
}

async function checkRunning() {
  try {
    const r = await fetch('/api/orchestrator/running')
    const d = await r.json()
    cycleRunning.value = d.running
  } catch (e) { }
}

async function runScan() {
  scanning.value = true
  try {
    const r = await fetch('/api/orchestrator/scan')
    scanResult.value = await r.json()
  } finally {
    scanning.value = false
  }
}

async function triggerCycle() {
  triggering.value = true
  try {
    await fetch('/api/orchestrator/cycle', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    cycleRunning.value = true
    // Poll until done
    const poll = setInterval(async () => {
      await checkRunning()
      if (!cycleRunning.value) {
        clearInterval(poll)
        await loadAll()
      }
    }, 1500)
  } finally {
    triggering.value = false
  }
}

async function enqueueTask() {
  if (!newTask.value.action) return
  await fetch('/api/orchestrator/tasks/enqueue', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: newTask.value.action, repo: newTask.value.repo }),
  })
  newTask.value.action = ''
  await loadTasks()
}

// ── Daemon ─────────────────────────────────────────────────────────────────

async function loadDaemon() {
  try {
    const r = await fetch('/api/orchestrator/daemon/status')
    daemon.value = await r.json()
    if (daemon.value?.interval_s && !daemonBusy.value) {
      intervalInput.value = daemon.value.interval_s
    }
    updateCountdown()
  } catch (e) { }
}

function updateCountdown() {
  if (!daemon.value?.next_run_at || !daemon.value?.running) { countdown.value = ''; return }
  const next = new Date(daemon.value.next_run_at + 'Z')
  const diff = Math.max(0, Math.round((next - Date.now()) / 1000))
  if (diff === 0) { countdown.value = 'now'; return }
  const m = Math.floor(diff / 60), s = diff % 60
  countdown.value = m > 0 ? `in ${m}m ${s}s` : `in ${s}s`
}

async function daemonStart() {
  daemonBusy.value = true
  try {
    await fetch('/api/orchestrator/daemon/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval_s: intervalInput.value }),
    })
    await loadDaemon()
  } finally { daemonBusy.value = false }
}

async function daemonStop() {
  daemonBusy.value = true
  try {
    await fetch('/api/orchestrator/daemon/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    await loadDaemon()
  } finally { daemonBusy.value = false }
}

async function daemonUpdateInterval() {
  daemonBusy.value = true
  try {
    await fetch('/api/orchestrator/daemon/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval_s: intervalInput.value }),
    })
    await loadDaemon()
  } finally { daemonBusy.value = false }
}

async function daemonRunNow() {
  daemonBusy.value = true
  cycleRunning.value = true
  try {
    await fetch('/api/orchestrator/daemon/run-now', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    await loadAll()
  } finally { daemonBusy.value = false; cycleRunning.value = false }
}

function formatInterval(s) {
  if (!s) return '—'
  if (s < 60) return `${s}s`
  if (s < 3600) return `${Math.round(s / 60)}m`
  return `${(s / 3600).toFixed(1)}h`
}

// ── Helpers ────────────────────────────────────────────────────────────────

function parseCaps(caps) {
  try { return JSON.parse(caps) } catch { return [] }
}

function formatTime(ts) {
  if (!ts) return '—'
  try { return new Date(ts).toLocaleTimeString() } catch { return ts }
}

function phaseClass(phase) {
  const map = {
    ASSESS: 'phase-assess', CULTIVATE: 'phase-cultivate',
    HARVEST: 'phase-harvest', UPGRADE: 'phase-upgrade',
    GROW: 'phase-grow', COMPLETE: 'phase-done', FAILED: 'phase-fail',
  }
  return map[phase] || ''
}

// ── Lifecycle ──────────────────────────────────────────────────────────────

let countdownTimer = null

onMounted(() => {
  loadAll()
  pollTimer = setInterval(() => {
    checkRunning()
    loadDaemon()
    if (cycleRunning.value) loadAll()
  }, 5000)
  countdownTimer = setInterval(updateCountdown, 1000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  clearInterval(countdownTimer)
})
</script>

<style scoped>
.orch-view {
  background: #0d1117;
  min-height: 100vh;
  padding: 2rem;
  color: #c9d1d9;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.orch-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.orch-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #8957e5;
  margin: 0 0 0.25rem;
}

.orch-subtitle { color: #8b949e; margin: 0; font-size: 0.9rem; }

.orch-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; }

.btn-scan, .btn-cycle, .btn-refresh {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid #30363d;
  font-size: 0.85rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.15s;
}

.btn-scan { background: #21262d; color: #c9d1d9; }
.btn-scan:hover:not(:disabled) { background: #30363d; }
.btn-refresh { background: #21262d; color: #8b949e; padding: 0.5rem 0.75rem; }
.btn-refresh:hover { color: #c9d1d9; }
.btn-cycle { background: linear-gradient(135deg, #6e40c9, #8957e5); color: #fff; border-color: transparent; }
.btn-cycle:hover:not(:disabled) { opacity: 0.85; }
button:disabled { opacity: 0.5; cursor: not-allowed; }

/* Status Bar */
.status-bar {
  display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap;
}

.stat-pill {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.82rem;
}

.stat-pill.running { background: rgba(139,87,229,0.15); border: 1px solid #8957e5; color: #bc8cff; }
.stat-pill.idle { background: rgba(139,148,158,0.1); border: 1px solid #30363d; }
.stat-pill.neutral { background: #161b22; border: 1px solid #30363d; }

.stat-dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.stat-label { color: #8b949e; }
.stat-num { font-weight: 600; color: #e6edf3; }

/* Grid */
.orch-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 900px) { .orch-grid { grid-template-columns: 1fr; } }

.orch-col { display: flex; flex-direction: column; gap: 1rem; }

/* Panel */
.panel {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.1rem;
}

.panel-title {
  font-size: 0.9rem; font-weight: 600; color: #e6edf3;
  margin: 0 0 0.9rem;
}

.empty-state { color: #8b949e; font-size: 0.82rem; padding: 0.5rem 0; }

/* Scan */
.scan-services { display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.75rem; }
.scan-svc {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.8rem;
}
.svc-up { background: rgba(46,160,67,0.1); color: #3fb950; }
.svc-down { background: rgba(248,81,73,0.1); color: #f85149; }
.scan-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
.scan-name { flex: 1; }
.scan-code { opacity: 0.6; font-family: monospace; font-size: 0.75rem; }

.scan-meta { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.5rem; }
.meta-row { display: flex; justify-content: space-between; font-size: 0.78rem; color: #8b949e; }
.meta-row span:last-child { color: #c9d1d9; font-weight: 500; }

.scan-issues { border-top: 1px solid #30363d; padding-top: 0.5rem; }
.issue-item { font-size: 0.78rem; color: #f85149; padding: 0.2rem 0; }
.scan-opps { border-top: 1px solid #30363d; padding-top: 0.5rem; }
.opp-item { font-size: 0.78rem; color: #2ea043; padding: 0.2rem 0; }

/* Cycles */
.cycle-row {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.35rem 0; border-bottom: 1px solid #21262d; font-size: 0.78rem;
}
.cycle-num { color: #8b949e; font-family: monospace; width: 30px; flex-shrink: 0; }
.cycle-phase { padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.7rem; font-weight: 500; }
.phase-assess   { background: #1f6feb22; color: #58a6ff; }
.phase-cultivate{ background: #2ea04322; color: #3fb950; }
.phase-harvest  { background: #e3b34122; color: #e3b341; }
.phase-upgrade  { background: #8957e522; color: #bc8cff; }
.phase-grow     { background: #2ea04322; color: #56d364; }
.phase-done     { background: #2ea04322; color: #3fb950; }
.phase-fail     { background: #f8514922; color: #ff7b72; }
.cycle-status   { font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 3px; }
.ok   { background: rgba(46,160,67,0.15); color: #3fb950; }
.fail { background: rgba(248,81,73,0.15); color: #f85149; }
.cycle-time { margin-left: auto; color: #8b949e; font-family: monospace; font-size: 0.7rem; }

/* Tasks */
.task-counts { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.task-count {
  display: flex; flex-direction: column; align-items: center;
  padding: 0.3rem 0.6rem; border-radius: 6px;
  min-width: 50px;
}
.tcount-queued  { background: #1f6feb22; border: 1px solid #1f6feb44; }
.tcount-running { background: #e3b34122; border: 1px solid #e3b34144; }
.tcount-done    { background: #2ea04322; border: 1px solid #2ea04344; }
.tcount-failed  { background: #f8514922; border: 1px solid #f8514944; }
.tc-num  { font-size: 1.1rem; font-weight: 700; color: #e6edf3; }
.tc-label{ font-size: 0.65rem; color: #8b949e; text-transform: uppercase; }

.task-list { display: flex; flex-direction: column; gap: 0.25rem; margin-bottom: 0.75rem; }
.task-item {
  display: flex; gap: 0.5rem; align-items: center;
  font-size: 0.75rem; padding: 0.25rem 0; border-bottom: 1px solid #21262d;
}
.task-action { flex: 1; color: #c9d1d9; font-family: monospace; }
.task-repo { color: #8b949e; font-size: 0.7rem; }
.task-st  { font-size: 0.68rem; padding: 0.1rem 0.3rem; border-radius: 3px; }
.ts-done   { background: rgba(46,160,67,0.15); color: #3fb950; }
.ts-queued { background: rgba(31,111,235,0.15); color: #58a6ff; }
.ts-running{ background: rgba(227,179,65,0.15); color: #e3b341; }
.ts-failed { background: rgba(248,81,73,0.15); color: #f85149; }

.enqueue-form { display: flex; gap: 0.4rem; margin-top: 0.5rem; }
.eq-input {
  flex: 1; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9;
  border-radius: 4px; padding: 0.3rem 0.5rem; font-size: 0.78rem;
}
.eq-input:focus { outline: none; border-color: #8957e5; }
.btn-enqueue {
  background: #8957e5; color: #fff; border: none; border-radius: 4px;
  padding: 0.3rem 0.6rem; font-size: 0.78rem; cursor: pointer;
}

/* Agents */
.agent-row {
  display: flex; align-items: flex-start; gap: 0.6rem;
  padding: 0.5rem 0; border-bottom: 1px solid #21262d;
}
.agent-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
.a-active { background: #2ea043; box-shadow: 0 0 6px #2ea04377; }
.a-idle   { background: #8b949e; }
.agent-info { flex: 1; display: flex; flex-direction: column; gap: 0.1rem; }
.agent-name { font-size: 0.82rem; font-weight: 500; color: #e6edf3; }
.agent-repo { font-size: 0.7rem; color: #8b949e; }
.agent-caps { display: flex; flex-wrap: wrap; gap: 0.25rem; }
.cap-tag {
  font-size: 0.62rem; padding: 0.1rem 0.3rem; border-radius: 3px;
  background: #8957e522; border: 1px solid #8957e544; color: #bc8cff;
}

/* Tools */
.tools-filter { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.75rem; }
.repo-filter {
  font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 20px;
  background: #21262d; border: 1px solid #30363d; color: #8b949e; cursor: pointer;
}
.repo-filter.active { background: #8957e522; border-color: #8957e5; color: #bc8cff; }
.tool-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 300px; overflow-y: auto; }
.tool-item {
  padding: 0.5rem; background: #0d1117; border-radius: 4px;
  border: 1px solid #21262d;
}
.tool-name { font-size: 0.8rem; font-weight: 500; color: #e6edf3; }
.tool-repo-badge {
  font-size: 0.65rem; padding: 0.1rem 0.3rem; border-radius: 3px;
  background: #21262d; color: #8b949e; margin-left: 0.4rem;
}
.tool-desc { font-size: 0.72rem; color: #8b949e; margin: 0.2rem 0 0; line-height: 1.4; }

/* Logs */
.log-row {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.25rem 0; border-bottom: 1px solid #21262d; font-size: 0.75rem;
}
.log-status { width: 14px; flex-shrink: 0; text-align: center; }
.ls-ok  { color: #3fb950; }
.ls-err { color: #f85149; }
.log-action { flex: 1; color: #c9d1d9; font-family: monospace; font-size: 0.72rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-repo { color: #8b949e; font-size: 0.68rem; white-space: nowrap; }
.log-ms   { color: #8b949e; font-size: 0.68rem; font-family: monospace; white-space: nowrap; }
.log-time { color: #8b949e; font-size: 0.68rem; font-family: monospace; white-space: nowrap; }

/* Memory */
.mem-ns-filter { display: flex; gap: 0.3rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.ns-btn {
  font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 20px;
  background: #21262d; border: 1px solid #30363d; color: #8b949e; cursor: pointer;
}
.ns-btn.active { background: #8957e522; border-color: #8957e5; color: #bc8cff; }
.mem-list { display: flex; flex-direction: column; gap: 0.3rem; max-height: 200px; overflow-y: auto; }
.mem-item {
  display: flex; gap: 0.5rem; font-size: 0.72rem;
  padding: 0.2rem 0; border-bottom: 1px solid #21262d;
}
.mem-key  { color: #58a6ff; font-family: monospace; white-space: nowrap; flex-shrink: 0; min-width: 120px; }
.mem-val  { color: #8b949e; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Status-bar daemon pill ─────────────────────────────────────── */
.daemon-on  { background: rgba(35,134,54,.20); border-color: #2ea043; color: #3fb950; }
.daemon-off { background: rgba(248,81,73,.15); border-color: #f85149; color: #f85149; }
.stat-dot   { display: inline-block; width: 7px; height: 7px; border-radius: 50%;
              background: currentColor; margin-right: 4px; vertical-align: middle;
              animation: pulse-dot 1.5s infinite; }
@keyframes pulse-dot { 0%,100% { opacity:1; } 50% { opacity:.3; } }
.stat-interval { margin-left: 4px; opacity: .75; font-size: .78rem; }

/* ── Daemon panel ──────────────────────────────────────────────── */
.daemon-panel { border-color: #58a6ff44; }
.daemon-badge {
  font-size: 0.7rem; font-weight: 700; padding: 1px 7px; border-radius: 10px;
  margin-left: 8px; vertical-align: middle; letter-spacing: 0.03em;
}
.badge-on  { background: rgba(35,134,54,.3); color: #3fb950; }
.badge-off { background: rgba(248,81,73,.2); color: #f85149; }

.daemon-stats  { display: flex; gap: 1rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.ds-item       { display: flex; flex-direction: column; gap: 2px; }
.ds-label      { font-size: 0.68rem; color: #8b949e; text-transform: uppercase; }
.ds-val        { font-size: 1rem; font-weight: 700; color: #e6edf3; }
.val-err       { color: #f85149; }

.daemon-times  { margin-bottom: 0.85rem; display: flex; flex-direction: column; gap: 4px; }
.dt-row        { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; }
.dt-label      { color: #8b949e; min-width: 60px; }
.dt-val        { color: #e6edf3; font-family: monospace; }
.next-run      { color: #58a6ff; }
.dt-countdown  { color: #58a6ff99; font-size: 0.75rem; }
.dt-cycle      { color: #8b949e; font-size: 0.75rem; }
.err-label     { color: #f85149; }
.err-val       { color: #f85149; font-family: monospace; font-size: 0.75rem; }

.daemon-interval-ctrl { margin-bottom: 0.85rem; }
.interval-label { font-size: 0.78rem; color: #8b949e; display: block; margin-bottom: 4px; }
.interval-slider {
  width: 100%; accent-color: #58a6ff; cursor: pointer;
  margin-bottom: 6px; display: block;
}
.interval-presets { display: flex; gap: 4px; flex-wrap: wrap; }
.preset-btn {
  font-size: 0.72rem; padding: 2px 9px; border-radius: 10px;
  border: 1px solid #30363d; background: #161b22; color: #8b949e;
  cursor: pointer; transition: all .15s;
}
.preset-btn:hover { border-color: #58a6ff; color: #58a6ff; }
.preset-btn.active { border-color: #58a6ff; background: rgba(88,166,255,.15); color: #58a6ff; }

.daemon-btns { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.dbtn {
  font-size: 0.8rem; padding: 5px 14px; border-radius: 6px; cursor: pointer;
  border: 1px solid; font-weight: 600; transition: all .15s;
}
.dbtn:disabled { opacity: 0.45; cursor: not-allowed; }
.dbtn-start { border-color: #2ea043; background: rgba(35,134,54,.2); color: #3fb950; }
.dbtn-start:hover:not(:disabled) { background: rgba(35,134,54,.35); }
.dbtn-stop  { border-color: #f85149; background: rgba(248,81,73,.15); color: #f85149; }
.dbtn-stop:hover:not(:disabled)  { background: rgba(248,81,73,.3); }
.dbtn-cfg   { border-color: #58a6ff; background: rgba(88,166,255,.12); color: #58a6ff; }
.dbtn-cfg:hover:not(:disabled)   { background: rgba(88,166,255,.25); }
.dbtn-now   { border-color: #d29922; background: rgba(210,153,34,.12); color: #e3b341; }
.dbtn-now:hover:not(:disabled)   { background: rgba(210,153,34,.28); }
</style>
