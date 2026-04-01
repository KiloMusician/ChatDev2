<template>
  <div class="ecosystem-view">
    <div class="eco-header">
      <div class="eco-title-block">
        <h1 class="eco-title">NuSyQ Ecosystem</h1>
        <p class="eco-subtitle">Six interconnected repos — one living organism</p>
      </div>
      <div class="eco-actions">
        <button class="btn-refresh" @click="loadStatus" :disabled="loading">
          {{ loading ? 'Scanning...' : '↻ Refresh' }}
        </button>
        <button class="btn-chug" @click="runChug" :disabled="chugging">
          {{ chugging ? 'Running...' : '⚡ CHUG Cycle' }}
        </button>
      </div>
    </div>

    <!-- Summary Bar -->
    <div class="eco-summary" v-if="status">
      <div class="summary-pill online">
        <span class="pill-num">{{ status.summary.online }}</span>
        <span class="pill-label">Online</span>
      </div>
      <div class="summary-pill cli">
        <span class="pill-num">{{ status.summary.cli_mode }}</span>
        <span class="pill-label">CLI / Library</span>
      </div>
      <div class="summary-pill total">
        <span class="pill-num">{{ status.summary.total }}</span>
        <span class="pill-label">Total Repos</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading && !status" class="eco-loading">
      <div class="spinner"></div>
      <p>Probing ecosystem services...</p>
    </div>

    <!-- Service Cards -->
    <div class="service-grid" v-if="status">
      <div
        v-for="svc in status.services"
        :key="svc.id"
        class="service-card"
        :class="cardClass(svc)"
      >
        <div class="card-header">
          <div class="card-name-row">
            <span class="status-dot" :class="dotClass(svc)"></span>
            <span class="card-name">{{ svc.name }}</span>
          </div>
          <span class="card-type-badge">{{ svc.type }}</span>
        </div>

        <p class="card-desc">{{ svc.description }}</p>

        <div class="card-meta">
          <template v-if="svc.port">
            <span class="meta-item">
              <span class="meta-label">Port</span>
              <span class="meta-val">:{{ svc.port }}</span>
            </span>
          </template>
          <template v-if="svc.repo_info?.cloned">
            <span class="meta-item">
              <span class="meta-label">Size</span>
              <span class="meta-val">{{ svc.repo_info.size_mb || '?' }} MB</span>
            </span>
            <span class="meta-item" v-if="svc.repo_info.branch">
              <span class="meta-label">Branch</span>
              <span class="meta-val">{{ svc.repo_info.branch }}</span>
            </span>
          </template>
        </div>

        <div class="card-commit" v-if="svc.repo_info?.latest_commit">
          <span class="commit-hash">{{ svc.repo_info.latest_commit.slice(0, 7) }}</span>
          <span class="commit-msg">{{ svc.repo_info.latest_commit.slice(8, 60) }}</span>
        </div>

        <div class="card-health">
          <template v-if="svc.health.online === true">
            <span class="health-ok">● Online</span>
          </template>
          <template v-else-if="svc.health.online === false">
            <span class="health-down">● Offline</span>
            <span class="health-err" v-if="svc.health.error">{{ svc.health.error }}</span>
          </template>
          <template v-else>
            <span class="health-cli">● {{ svc.health.note || 'CLI mode' }}</span>
          </template>
        </div>

        <div class="card-hub" v-if="svc.hub_health?.snapshot">
          <details>
            <summary>NuSyQ-Hub Health Snapshot</summary>
            <pre class="hub-snapshot">{{ svc.hub_health.snapshot }}</pre>
          </details>
        </div>

        <div class="card-actions" v-if="svc.url && svc.health.online">
          <a :href="svc.url.replace('localhost', getHost())" target="_blank" class="btn-open">
            Open ↗
          </a>
        </div>
      </div>
    </div>

    <!-- CHUG output -->
    <div class="chug-output" v-if="chugResult">
      <h3>⚡ CHUG Cycle Result</h3>
      <div class="chug-status" :class="chugResult.success ? 'ok' : 'fail'">
        {{ chugResult.success ? '✓ Phase 1 (ASSESS) complete' : '✗ Phase failed' }}
      </div>
      <pre v-if="chugResult.stdout" class="chug-pre">{{ chugResult.stdout }}</pre>
      <pre v-if="chugResult.error" class="chug-pre error">{{ chugResult.error }}</pre>
    </div>

    <!-- Ecosystem diagram -->
    <div class="eco-diagram">
      <h3 class="diagram-title">Architecture</h3>
      <div class="diagram-nodes">
        <div class="diagram-center">ChatDev 2.0<br/><small>Port 5000/6400</small></div>
        <div class="diagram-spoke" v-for="node in diagramNodes" :key="node.id">
          <div class="diagram-node" :class="node.cls">
            <span class="node-name">{{ node.name }}</span>
            <span class="node-port" v-if="node.port">:{{ node.port }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const status = ref(null)
const loading = ref(false)
const chugging = ref(false)
const chugResult = ref(null)

const diagramNodes = [
  { id: 'dev-mentor', name: 'Dev-Mentor', port: 8008, cls: 'node-fastapi' },
  { id: 'nusyq-hub', name: 'NuSyQ-Hub', port: null, cls: 'node-cli' },
  { id: 'simulatedverse', name: 'SimulatedVerse', port: 3000, cls: 'node-node' },
  { id: 'nusyq-ultimate', name: 'NuSyQ Ultimate', port: null, cls: 'node-lib' },
  { id: 'concept-samurai', name: 'CONCEPT_SAMURAI', port: 3001, cls: 'node-static' },
]

function getHost() {
  return window.location.hostname
}

function cardClass(svc) {
  if (svc.health.online === true) return 'card-online'
  if (svc.health.online === false) return 'card-offline'
  return 'card-cli'
}

function dotClass(svc) {
  if (svc.health.online === true) return 'dot-green'
  if (svc.health.online === false) return 'dot-red'
  return 'dot-blue'
}

async function loadStatus() {
  loading.value = true
  try {
    const r = await fetch('/api/ecosystem/status')
    status.value = await r.json()
  } catch (e) {
    console.error('Ecosystem status failed:', e)
  } finally {
    loading.value = false
  }
}

async function runChug() {
  chugging.value = true
  chugResult.value = null
  try {
    const r = await fetch('/api/ecosystem/chug', { method: 'POST' })
    chugResult.value = await r.json()
  } catch (e) {
    chugResult.value = { success: false, error: String(e) }
  } finally {
    chugging.value = false
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.ecosystem-view {
  background: #0d1117;
  min-height: 100vh;
  padding: 2rem;
  color: #c9d1d9;
  font-family: 'Segoe UI', system-ui, sans-serif;
}

.eco-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.eco-title {
  font-size: 2rem;
  font-weight: 700;
  color: #58a6ff;
  margin: 0 0 0.25rem;
}

.eco-subtitle {
  color: #8b949e;
  margin: 0;
  font-size: 0.95rem;
}

.eco-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-refresh, .btn-chug {
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  border: 1px solid #30363d;
  font-size: 0.875rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.15s;
}

.btn-refresh {
  background: #21262d;
  color: #c9d1d9;
}

.btn-refresh:hover:not(:disabled) {
  background: #30363d;
}

.btn-chug {
  background: linear-gradient(135deg, #1f6feb, #8957e5);
  color: #fff;
  border-color: transparent;
}

.btn-chug:hover:not(:disabled) {
  opacity: 0.9;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.eco-summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.summary-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
}

.summary-pill.online { background: rgba(46, 160, 67, 0.15); border: 1px solid #2ea043; }
.summary-pill.cli { background: rgba(88, 166, 255, 0.1); border: 1px solid #1f6feb; }
.summary-pill.total { background: rgba(139, 148, 158, 0.1); border: 1px solid #30363d; }

.pill-num {
  font-size: 1.25rem;
  font-weight: 700;
  color: #e6edf3;
}

.eco-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  color: #8b949e;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #30363d;
  border-top-color: #58a6ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.service-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.service-card {
  background: #161b22;
  border-radius: 8px;
  padding: 1.2rem;
  border: 1px solid #30363d;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  transition: border-color 0.15s;
}

.service-card:hover { border-color: #58a6ff; }
.card-online { border-left: 3px solid #2ea043; }
.card-offline { border-left: 3px solid #f85149; }
.card-cli { border-left: 3px solid #58a6ff; }

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-name-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-green { background: #2ea043; box-shadow: 0 0 6px #2ea043; }
.dot-red { background: #f85149; }
.dot-blue { background: #58a6ff; }

.card-name {
  font-weight: 600;
  color: #e6edf3;
  font-size: 0.95rem;
}

.card-type-badge {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border-radius: 20px;
  background: #21262d;
  color: #8b949e;
  border: 1px solid #30363d;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card-desc {
  font-size: 0.82rem;
  color: #8b949e;
  margin: 0;
  line-height: 1.5;
}

.card-meta {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 0.25rem;
  font-size: 0.78rem;
}

.meta-label {
  color: #8b949e;
}

.meta-val {
  color: #c9d1d9;
  font-family: monospace;
}

.card-commit {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  background: #0d1117;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
}

.commit-hash {
  font-family: monospace;
  color: #58a6ff;
}

.commit-msg {
  color: #8b949e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-health {
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.health-ok { color: #2ea043; }
.health-down { color: #f85149; }
.health-cli { color: #58a6ff; }

.health-err {
  color: #8b949e;
  font-size: 0.72rem;
  font-family: monospace;
}

.card-hub details summary {
  font-size: 0.78rem;
  color: #8b949e;
  cursor: pointer;
}

.hub-snapshot {
  font-size: 0.7rem;
  color: #8b949e;
  background: #0d1117;
  padding: 0.5rem;
  border-radius: 4px;
  overflow: auto;
  max-height: 150px;
  margin-top: 0.4rem;
}

.card-actions {
  margin-top: auto;
}

.btn-open {
  display: inline-block;
  padding: 0.35rem 0.8rem;
  background: #1f6feb22;
  border: 1px solid #1f6feb;
  border-radius: 6px;
  color: #58a6ff;
  font-size: 0.8rem;
  text-decoration: none;
  transition: background 0.15s;
}

.btn-open:hover {
  background: #1f6feb44;
}

.chug-output {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.2rem;
  margin-bottom: 2rem;
}

.chug-output h3 {
  margin: 0 0 0.75rem;
  color: #e6edf3;
  font-size: 1rem;
}

.chug-status {
  padding: 0.4rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}

.chug-status.ok { background: rgba(46,160,67,0.15); color: #2ea043; }
.chug-status.fail { background: rgba(248,81,73,0.15); color: #f85149; }

.chug-pre {
  font-size: 0.75rem;
  font-family: monospace;
  background: #0d1117;
  padding: 0.75rem;
  border-radius: 4px;
  overflow: auto;
  max-height: 300px;
  color: #8b949e;
  white-space: pre-wrap;
}

.chug-pre.error { color: #f85149; }

.eco-diagram {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1rem;
}

.diagram-title {
  color: #e6edf3;
  margin: 0 0 1.5rem;
  font-size: 1rem;
}

.diagram-nodes {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.diagram-center {
  background: linear-gradient(135deg, #1f6feb, #8957e5);
  color: #fff;
  padding: 0.75rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.85rem;
  text-align: center;
  line-height: 1.4;
}

.diagram-center small {
  font-weight: 400;
  opacity: 0.8;
}

.diagram-spoke {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.diagram-spoke::before {
  content: '→';
  color: #30363d;
  font-size: 1.2rem;
}

.diagram-node {
  padding: 0.5rem 0.9rem;
  border-radius: 6px;
  font-size: 0.78rem;
  display: flex;
  flex-direction: column;
  text-align: center;
  gap: 0.15rem;
}

.node-name { font-weight: 500; }
.node-port { opacity: 0.7; font-family: monospace; font-size: 0.7rem; }

.node-fastapi { background: #0d419d22; border: 1px solid #1f6feb; color: #58a6ff; }
.node-cli     { background: #8957e522; border: 1px solid #8957e5; color: #bc8cff; }
.node-node    { background: #2ea04322; border: 1px solid #2ea043; color: #3fb950; }
.node-lib     { background: #e3b34122; border: 1px solid #e3b341; color: #e3b341; }
.node-static  { background: #f8514922; border: 1px solid #f85149; color: #ff7b72; }
</style>
