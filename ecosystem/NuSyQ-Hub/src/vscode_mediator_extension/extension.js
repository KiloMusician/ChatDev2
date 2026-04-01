const vscode = require('vscode');
const cp = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');
const http = require('node:http');
const https = require('node:https');

let mediatorProc = null;
let mediatorStatusBarItem = null;
let diagnosticsStatusBarItem = null;
let terminalStatusBarItem = null;
let diagnosticsSubscription = null;
let saveSubscription = null;
let terminalOpenSubscription = null;
let terminalCloseSubscription = null;
let activeTerminalSubscription = null;
let diagnosticsRefreshTimer = null;
let bridgeSnapshotRefreshTimer = null;
let diagnosticsPanel = null;
let capabilityPanel = null;
let bridgeSnapshotInFlight = false;
let pendingBridgeSnapshotRefresh = false;
let capabilityWorkspaceWatchers = [];

const DIRECT_COMMAND_SURFACES = [
  {
    command: 'nusyq.controlCenter',
    title: 'NuSyQ Control Center',
    subtitle: 'Open the hidden bridge control center',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.showQuickMenu',
    title: 'NuSyQ Quick Menu',
    subtitle: 'Jump into the bridge quick menu',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.showGuildBoard',
    title: 'NuSyQ Guild Board',
    subtitle: 'Open the guild board UI',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.serviceStatus',
    title: 'NuSyQ Service Status',
    subtitle: 'Inspect orchestrated service health',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.tripartiteStatus',
    title: 'NuSyQ Tripartite Status',
    subtitle: 'Inspect the tripartite system state',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.startServices',
    title: 'NuSyQ Start Services',
    subtitle: 'Start core orchestrated services',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.ignition',
    title: 'NuSyQ Ignition',
    subtitle: 'Run the standard ignition flow',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.ignitionThorough',
    title: 'NuSyQ Ignition Thorough',
    subtitle: 'Run the deeper ignition flow',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.terminalsActivate',
    title: 'NuSyQ Terminal Activation',
    subtitle: 'Spin up the specialized terminal grid',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.terminalsSnapshot',
    title: 'NuSyQ Terminal Snapshot',
    subtitle: 'Capture the current terminal state',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.routeToTerminal',
    title: 'NuSyQ Route To Terminal',
    subtitle: 'Send an operator prompt into a dedicated terminal',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.openclaw.status',
    title: 'NuSyQ OpenClaw Status',
    subtitle: 'Inspect OpenClaw through the bridge extension',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.antigravity.health',
    title: 'NuSyQ Antigravity Health',
    subtitle: 'Run the antigravity health check',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.simVerse.sync',
    title: 'NuSyQ SimulatedVerse Sync',
    subtitle: 'Run the SimulatedVerse bridge sync',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.tasks.run',
    title: 'NuSyQ Run Tasks',
    subtitle: 'Open the VS Code task runner',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.tests.run',
    title: 'NuSyQ Run Tests',
    subtitle: 'Open the VS Code test runner',
    family: 'NuSyQ Bridge',
  },
  {
    command: 'nusyq.intermediary.send',
    title: 'Intermediary Send',
    subtitle: 'Route a prompt through the intermediary bridge',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.cultureShip.audit',
    title: 'Culture Ship Audit',
    subtitle: 'Launch the Culture Ship audit flow',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.council.propose',
    title: 'AI Council Propose',
    subtitle: 'Send a proposal into the council terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.ollama.query',
    title: 'Ollama Query',
    subtitle: 'Query Ollama through the bridge terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.lmstudio.query',
    title: 'LM Studio Query',
    subtitle: 'Query LM Studio through the bridge terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.chatdev.generate',
    title: 'ChatDev Generate',
    subtitle: 'Invoke the bridge ChatDev generator',
    family: 'ChatDev',
  },
  {
    command: 'nusyq.claude.query',
    title: 'Claude Query',
    subtitle: 'Route a prompt into the Claude terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.copilot.query',
    title: 'Copilot Query',
    subtitle: 'Route a prompt into the Copilot terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.codex.query',
    title: 'Codex Query',
    subtitle: 'Route a prompt into the Codex terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.chatgpt.bridge',
    title: 'ChatGPT Bridge',
    subtitle: 'Route through the ChatGPT bridge terminal',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.future.predictions',
    title: 'Future Predictions',
    subtitle: 'Open the future-prediction terminal flow',
    family: 'AI Routing',
  },
  {
    command: 'nusyq.moderator.review',
    title: 'Moderator Review',
    subtitle: 'Open the moderator review terminal flow',
    family: 'AI Routing',
  },
  {
    command: 'startChatDevParty',
    title: 'ChatDev Party',
    subtitle: 'Launch the standalone ChatDev party extension',
    family: 'ChatDev',
  },
  {
    command: 'launchChatDevTask',
    title: 'ChatDev Task',
    subtitle: 'Launch the standalone ChatDev task runner',
    family: 'ChatDev',
  },
];

function getWorkspaceRoot() {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) return null;
  return workspaceFolders[0].uri.fsPath;
}

function getWorkspaceRoots() {
  const workspaceFolders = vscode.workspace.workspaceFolders || [];
  const roots = new Set(workspaceFolders.map((folder) => folder.uri.fsPath));
  const firstRoot = getWorkspaceRoot();
  if (firstRoot) {
    const userRoot = path.resolve(firstRoot, '..', '..', '..');
    [
      path.join(userRoot, 'NuSyQ'),
      path.join(userRoot, 'Dev-Mentor'),
      path.join(userRoot, 'Desktop', 'Legacy', 'NuSyQ-Hub'),
      path.join(userRoot, 'Desktop', 'SimulatedVerse', 'SimulatedVerse'),
      '/mnt/c/CONCEPT',
    ]
      .filter((candidate) => fs.existsSync(candidate))
      .forEach((candidate) => roots.add(candidate));
  }
  return Array.from(roots);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function getMediatorConfig() {
  return vscode.workspace.getConfiguration('powershellMediator');
}

function readJsonFile(filePath) {
  if (!filePath) return null;
  if (!fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch (_err) {
    return null;
  }
}

function findArtifactPath(relativeCandidates) {
  const roots = getWorkspaceRoots();
  for (const root of roots) {
    for (const relativeCandidate of relativeCandidates) {
      const candidate = path.join(root, relativeCandidate);
      if (fs.existsSync(candidate)) {
        return candidate;
      }
    }
  }
  return null;
}

function getFreshness(payload, fallbackTimestamp = null) {
  const generatedAt = payload?.generated_at || payload?.timestamp || fallbackTimestamp || null;
  const staleAfterSeconds = Number(payload?.stale_after_seconds || 0) || null;
  if (!generatedAt) {
    return { generatedAt: null, staleAfterSeconds, ageSeconds: null, stale: false, label: 'unknown' };
  }
  const ageSeconds = Math.max(0, Math.floor((Date.now() - new Date(generatedAt).getTime()) / 1000));
  const stale = Boolean(staleAfterSeconds && ageSeconds > staleAfterSeconds);
  return {
    generatedAt,
    staleAfterSeconds,
    ageSeconds,
    stale,
    label: stale ? 'stale' : 'fresh',
  };
}

function loadArtifactCard(relativeCandidates) {
  const filePath = findArtifactPath(relativeCandidates);
  const payload = readJsonFile(filePath);
  return {
    path: filePath,
    exists: Boolean(payload),
    payload,
    sourceHashes: payload?.source_hashes || {},
    sourcePaths: Array.isArray(payload?.source_paths) ? payload.source_paths : [],
    ...getFreshness(payload, filePath ? statMtimeIso(filePath) : null),
  };
}

function writeJsonFile(filePath, payload) {
  if (!filePath) return false;
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
    return true;
  } catch (_err) {
    return false;
  }
}

function readTextFile(filePath) {
  if (!filePath) return null;
  if (!fs.existsSync(filePath)) return null;
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch (_err) {
    return null;
  }
}

function readTailLines(filePath, maxLines = 10, maxBytes = 65536) {
  if (!filePath) return [];
  if (!fs.existsSync(filePath)) return [];
  try {
    const stat = fs.statSync(filePath);
    const readSize = Math.min(stat.size, maxBytes);
    const fd = fs.openSync(filePath, 'r');
    try {
      const buffer = Buffer.alloc(readSize);
      fs.readSync(fd, buffer, 0, readSize, stat.size - readSize);
      const text = buffer.toString('utf8');
      return text
        .split(/\r?\n/)
        .filter((line) => line.trim())
        .slice(-maxLines);
    } finally {
      fs.closeSync(fd);
    }
  } catch (_err) {
    return [];
  }
}

function readJsonlEntries(filePath, maxLines = 10, maxBytes = 65536) {
  return readTailLines(filePath, maxLines, maxBytes)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch (_err) {
        return { raw: line };
      }
    })
    .filter(Boolean);
}

function normalizeAgentDashboardEntry(agent) {
  if (!agent || typeof agent !== 'object') {
    return {
      name: 'unknown',
      status: 'unknown',
      pid: null,
      detail: 'no agent data',
      created: null,
    };
  }

  return {
    name: agent.name || agent.id || agent.agent || 'unknown',
    status: agent.status || (agent.pid || agent.ProcessId ? 'running' : 'observed'),
    pid: agent.pid || agent.ProcessId || null,
    detail: agent.command || agent.role || agent.last_active || agent.summary || 'no detail',
    created: agent.created || agent.last_active || null,
  };
}

function summarizeUnifiedErrorSignals(payload, fallbackSnapshot) {
  if (payload && typeof payload === 'object') {
    const circuits = Array.isArray(payload.circuits) ? payload.circuits : [];
    const issues = Array.isArray(payload.issues) ? payload.issues : [];
    const countCandidates = [
      payload.total_errors,
      payload.total_diagnostics,
      payload.total,
      payload.error_count,
      payload.errors,
      circuits.length,
      issues.length,
    ].filter((value) => typeof value === 'number');
    const latestCircuit =
      circuits.find((item) => item && typeof item === 'object') ||
      (issues.find((item) => item && typeof item === 'object') || null);

    return {
      exists: true,
      total: countCandidates[0] ?? 0,
      openCircuits: circuits.length || issues.length,
      note:
        payload.summary ||
        payload.note ||
        payload.message ||
        (circuits.length ? `${circuits.length} circuit(s) tracked` : 'legacy unified error feed'),
      latestCircuitId:
        latestCircuit?.circuitId ||
        latestCircuit?.id ||
        latestCircuit?.name ||
        latestCircuit?.file ||
        null,
    };
  }

  return {
    exists: Boolean(fallbackSnapshot),
    total: fallbackSnapshot?.total_diagnostics ?? fallbackSnapshot?.ground_truth?.total ?? 0,
    openCircuits: fallbackSnapshot?.repo_breakdown?.length ?? 0,
    note: fallbackSnapshot ? 'falling back to canonical error report' : 'no unified error feed available',
    latestCircuitId: null,
  };
}

function buildLegacyAgentDashboardState({
  statusPath,
  unifiedErrorsPath,
  repairRequestsPath,
  questLogPath,
  canonicalErrorSnapshot,
}) {
  const statusPayload = readJsonFile(statusPath);
  const statusAgentsRaw = Array.isArray(statusPayload)
    ? statusPayload
    : Array.isArray(statusPayload?.agents)
      ? statusPayload.agents
      : [];
  const agents = statusAgentsRaw.map((agent) => normalizeAgentDashboardEntry(agent)).slice(0, 12);
  const questsFromStatus = Array.isArray(statusPayload?.quests) ? statusPayload.quests : [];
  const questEvents = readJsonlEntries(questLogPath, 8)
    .map((entry) => ({
      timestamp: entry.timestamp || entry.time || 'unknown',
      event: entry.event || entry.type || entry.quest_id || entry.raw || 'unknown',
      detail:
        entry?.details?.action ||
        entry?.details?.status ||
        entry?.details?.view ||
        entry?.details?.error ||
        entry?.status ||
        entry?.raw ||
        'n/a',
    }))
    .reverse();
  const legacyErrorPayload = readJsonFile(unifiedErrorsPath);
  const repairQueuePayload = readJsonFile(repairRequestsPath);
  const repairQueue = Array.isArray(repairQueuePayload) ? repairQueuePayload : [];
  const scanSummary =
    statusPayload?.scans && typeof statusPayload.scans === 'object'
      ? Object.entries(statusPayload.scans)
          .map(([name, value]) => {
            if (typeof value === 'string') return `${name}: ${value}`;
            if (value && typeof value === 'object' && Array.isArray(value.results)) {
              return `${name}: ${value.results.length} result(s)`;
            }
            return `${name}: ready`;
          })
          .slice(0, 3)
      : [];

  return {
    generatedAt: statusPayload?.generated || statMtimeIso(statusPath),
    statusExists: Boolean(statusPayload),
    agents,
    agentCount: statusAgentsRaw.length,
    runningAgents: agents.filter((agent) => agent.pid || /running|active|online/i.test(agent.status)).length,
    questsFromStatus: questsFromStatus.slice(0, 6),
    questEvents,
    errors: summarizeUnifiedErrorSignals(legacyErrorPayload, canonicalErrorSnapshot),
    repairQueue,
    repairQueueSize: repairQueue.length,
    latestRepairRequest: repairQueue.length ? repairQueue[repairQueue.length - 1] : null,
    scanSummary,
    paths: {
      statusPath,
      unifiedErrorsPath,
      repairRequestsPath,
    },
  };
}

function submitRepairRequest(root, payload = {}) {
  if (!root) {
    return { ok: false, reason: 'workspace not open', path: null };
  }

  const repairPath = path.join(root, 'state', 'repair_requests.json');
  const existing = readJsonFile(repairPath);
  const queue = Array.isArray(existing) ? existing : [];
  queue.push({
    action: payload.action || 'rehydrate',
    circuitId: payload.circuitId || null,
    requestedBy: payload.requestedBy || 'powershell-mediator',
    requestedAt: new Date().toISOString(),
  });

  return {
    ok: writeJsonFile(repairPath, queue),
    path: repairPath,
    queued: queue.length,
  };
}

function statMtimeIso(filePath) {
  if (!filePath) return null;
  try {
    return fs.statSync(filePath).mtime.toISOString();
  } catch (_err) {
    return null;
  }
}

function summarizeSnapshotCard(snapshot, fallbackTimestamp = null) {
  const exists = Boolean(snapshot);
  const timestamp = snapshot?.timestamp || snapshot?.generated_at || fallbackTimestamp || null;

  let detail = 'no snapshot';
  const readiness = snapshot?.capability_intelligence?.advanced_ai_readiness?.capabilities;
  if (readiness && typeof readiness === 'object') {
    const counts = { ready: 0, partial: 0, missing: 0 };
    Object.values(readiness).forEach((capability) => {
      const status = capability && typeof capability === 'object' ? capability.status : null;
      if (status && Object.prototype.hasOwnProperty.call(counts, status)) {
        counts[status] += 1;
      }
    });
    detail = `ready ${counts.ready} | partial ${counts.partial} | missing ${counts.missing}`;
  } else if (typeof snapshot?.total_diagnostics === 'number' && snapshot?.ground_truth) {
    detail = `errors ${snapshot.ground_truth.errors ?? 0} | warnings ${snapshot.ground_truth.warnings ?? 0} | total ${snapshot.total_diagnostics}`;
  } else if (snapshot?.graph_learning?.summary) {
    const summary = snapshot.graph_learning.summary;
    detail = `nodes ${summary.node_count ?? 'n/a'} | critical ${summary.critical_file_count ?? 'n/a'}`;
  } else if (typeof snapshot?.history_events === 'number' && snapshot?.team) {
    const coverage = snapshot.team?.avg_coverage_per_task;
    detail = `events ${snapshot.history_events} | coverage ${coverage ?? 'n/a'}`;
  } else if (
    typeof snapshot?.created === 'number' ||
    typeof snapshot?.skipped === 'number' ||
    typeof snapshot?.failed === 'number'
  ) {
    detail = `created ${snapshot?.created ?? 0} | skipped ${snapshot?.skipped ?? 0} | failed ${snapshot?.failed ?? 0}`;
  } else if (Array.isArray(snapshot?.causality_chain)) {
    const loopType = snapshot?.feedback_loop?.loop_type || 'none';
    detail = `links ${snapshot.causality_chain.length} | loop ${loopType}`;
  } else if (snapshot?.status) {
    detail = `status: ${snapshot.status}`;
  }

  return { exists, timestamp, detail };
}

function summarizeControlPlaneState({ bootstrap, registry, snapshot, deprecations, runtimeDescriptor }) {
  const selectedSource = bootstrap.exists
    ? 'bootstrap'
    : registry.exists
      ? 'registry'
      : snapshot.exists
        ? 'snapshot'
        : 'none';
  const selectedPayload = bootstrap.payload || registry.payload || snapshot.payload || {};
  const cultureShip =
    runtimeDescriptor.payload ||
    selectedPayload?.control_plane ||
    selectedPayload?.workflows?.culture_ship ||
    {};
  const deprecated = deprecations.payload?.deprecated || selectedPayload?.deprecated || {};
  const repoRoles =
    bootstrap.payload?.repo_roles ||
    Object.entries(registry.payload?.repos || {}).reduce((acc, [name, meta]) => {
      acc[name] = {
        role: meta?.role || 'unknown',
        path: meta?.path || 'unknown',
        priority: meta?.priority ?? null,
      };
      return acc;
    }, {});

  return {
    selectedSource,
    runtimeOwner: cultureShip.runtime_owner || cultureShip.runtimeOwner || 'simulatedverse',
    controlOwner: cultureShip.control_owner || cultureShip.controlOwner || 'nusyq_hub',
    repoRoles,
    deprecationCounts: Object.fromEntries(
      Object.entries(deprecated).map(([key, value]) => [key, Array.isArray(value) ? value.length : 0])
    ),
    artifacts: { bootstrap, registry, snapshot, deprecations, runtimeDescriptor },
  };
}

function buildReportDrilldown({
  aiStatusSnapshot,
  graphLearningSnapshot,
  specializationSnapshot,
  advancedAiQuestsSnapshot,
  causalAnalysisSnapshot,
}) {
  const readiness =
    aiStatusSnapshot?.capability_intelligence?.advanced_ai_readiness?.capabilities || {};
  const readinessRows = Object.entries(readiness)
    .map(([name, payload]) => ({
      name,
      status: payload?.status || 'unknown',
      summary: payload?.summary || 'no summary',
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  const graphHighlights = Array.isArray(graphLearningSnapshot?.graph_learning?.top_central_nodes)
    ? graphLearningSnapshot.graph_learning.top_central_nodes.slice(0, 5).map((node) => ({
        path: node.path || 'unknown',
        repo: node.repo || 'n/a',
        pagerank: node.pagerank ?? 0,
        fanOut: node.fan_out ?? 0,
      }))
    : [];

  const specializationAttempts = Array.isArray(specializationSnapshot?.recent_attempts)
    ? specializationSnapshot.recent_attempts.slice(-5).reverse()
    : [];

  const specializationLeaders = Array.isArray(specializationSnapshot?.agents)
    ? specializationSnapshot.agents.slice(0, 5).map((agent) => ({
        name: agent.agent || 'unknown',
        bestTask: agent.best_task || 'n/a',
        avgScore: agent.avg_specialization_score ?? 0,
      }))
    : [];

  const questBridge = advancedAiQuestsSnapshot
    ? {
        created: advancedAiQuestsSnapshot.created ?? 0,
        skipped: advancedAiQuestsSnapshot.skipped ?? 0,
        failed: advancedAiQuestsSnapshot.failed ?? 0,
        questIds: Array.isArray(advancedAiQuestsSnapshot.quest_ids)
          ? advancedAiQuestsSnapshot.quest_ids.slice(0, 5)
          : [],
      }
    : null;

  const causalLinks = Array.isArray(causalAnalysisSnapshot?.causality_chain)
    ? causalAnalysisSnapshot.causality_chain.slice(0, 6).map((link) => ({
        relationship: link.relationship || 'n/a',
        type: link.type || 'unknown',
        confidence: link.confidence ?? 0,
      }))
    : [];

  const feedbackLoop = causalAnalysisSnapshot?.feedback_loop
    ? {
        system: causalAnalysisSnapshot.feedback_loop.system || 'unknown',
        loopType: causalAnalysisSnapshot.feedback_loop.loop_type || 'undetermined',
        confidence: causalAnalysisSnapshot.feedback_loop.confidence ?? 0,
      }
    : null;

  const auditRecommendations = Array.isArray(aiStatusSnapshot?.audit_intelligence?.recommended_commands)
    ? aiStatusSnapshot.audit_intelligence.recommended_commands.slice(0, 6)
    : [];

  const auditCanonicals = Array.isArray(aiStatusSnapshot?.audit_intelligence?.canonical)
    ? aiStatusSnapshot.audit_intelligence.canonical
        .filter((item) => item && item.exists)
        .slice(0, 5)
        .map((item) => item.path)
    : [];

  return {
    readinessRows,
    graphHighlights,
    specializationAttempts,
    specializationLeaders,
    questBridge,
    causalLinks,
    feedbackLoop,
    auditRecommendations,
    auditCanonicals,
  };
}

function buildErrorDrilldown(errorReportSnapshot) {
  const repoRows =
    errorReportSnapshot && typeof errorReportSnapshot.by_repo === 'object'
      ? Object.entries(errorReportSnapshot.by_repo).map(([name, payload]) => ({
          name,
          total: payload?.total ?? 0,
          errors: payload?.by_severity?.error ?? 0,
          warnings: payload?.by_severity?.warning ?? 0,
          infos: payload?.by_severity?.info ?? 0,
        }))
      : [];

  const scanWarnings = Array.isArray(errorReportSnapshot?.scan_warnings)
    ? errorReportSnapshot.scan_warnings.slice(0, 6)
    : [];

  const groundTruth = errorReportSnapshot?.ground_truth || {};
  const diagnosticsExportCounts = errorReportSnapshot?.diagnostics_export_counts || {};

  return {
    totalDiagnostics: errorReportSnapshot?.total_diagnostics ?? 0,
    partialScan: Boolean(errorReportSnapshot?.partial_scan),
    confidence: groundTruth?.confidence || 'unknown',
    scanMode: errorReportSnapshot?.scan_mode || 'unknown',
    errors: groundTruth?.errors ?? errorReportSnapshot?.by_severity?.errors ?? 0,
    warnings: groundTruth?.warnings ?? errorReportSnapshot?.by_severity?.warnings ?? 0,
    infos:
      groundTruth?.infos ??
      groundTruth?.infos_hints ??
      errorReportSnapshot?.by_severity?.infos_hints ??
      0,
    note: groundTruth?.note || 'No ground-truth note available.',
    repoRows,
    scanWarnings,
    diagnosticsExportTotal: diagnosticsExportCounts?.total ?? 0,
    diagnosticsExportPath: diagnosticsExportCounts?.path || null,
  };
}

function buildErrorCheckpointSummary(checkpointSnapshot) {
  if (!checkpointSnapshot) {
    return {
      status: 'missing',
      currentCheck: 'no checkpoint',
      progressLabel: 'No active scan checkpoint',
      updatedAt: null,
    };
  }

  const progress = checkpointSnapshot.progress || {};
  const currentCheck = checkpointSnapshot.current_check || 'unknown';
  let progressLabel = currentCheck;
  if (progress?.event === 'tool_start') {
    progressLabel = `${progress.repo || 'repo'}:${progress.tool || 'tool'} (${progress.percent ?? 'n/a'}%)`;
  } else if (progress?.event === 'tool_progress') {
    const batchLabel =
      progress.batch_index && progress.total_batches
        ? `batch ${progress.batch_index}/${progress.total_batches}`
        : 'batch';
    const retryLabel = progress.retry
      ? ` retry${progress.retry_index ? ` ${progress.retry_index}` : ''}`
      : '';
    progressLabel = `${progress.repo || 'repo'}:${progress.tool || 'tool'} ${batchLabel}${retryLabel}`;
  } else if (progress?.event === 'tool_complete') {
    progressLabel = `${progress.repo || 'repo'}:${progress.tool || 'tool'} complete`;
  } else if (progress?.event === 'repo_start') {
    progressLabel = `${progress.repo || 'repo'} started`;
  } else if (progress?.event === 'repo_complete') {
    progressLabel = `${progress.repo || 'repo'} complete`;
  }

  return {
    status: checkpointSnapshot.status || 'unknown',
    currentCheck,
    progressLabel,
    updatedAt: checkpointSnapshot.updated_at || null,
    progress,
  };
}

function buildWorkspaceDrilldown({
  questLogPath,
  zetaTrackerPath,
  checklistPath,
  currentStatePath,
  errorReportPath,
  errorReportMdPath,
  sessionsDir,
}) {
  const questTail = readTailLines(questLogPath, 6)
    .map((line) => {
      try {
        const entry = JSON.parse(line);
        return {
          timestamp: entry.timestamp || 'unknown',
          event: entry.event || 'unknown',
          detail:
            entry?.details?.action ||
            entry?.details?.status ||
            entry?.details?.view ||
            entry?.details?.error ||
            'n/a',
        };
      } catch (_err) {
        return null;
      }
    })
    .filter(Boolean)
    .reverse();

  const zetaTracker = readJsonFile(zetaTrackerPath);
  const currentProgress = zetaTracker?.current_progress || {};
  const recentAchievements = Array.isArray(currentProgress.recent_achievements)
    ? currentProgress.recent_achievements.slice(0, 5)
    : [];

  const checklistText = readTextFile(checklistPath) || '';
  const openChecklistItems = checklistText
    .split(/\r?\n/)
    .map((line) => line.match(/^- \[ \] (.+)$/))
    .filter(Boolean)
    .slice(0, 8)
    .map((match) => match[1]);

  const currentStateText = readTextFile(currentStatePath) || '';
  const lintErrorsMatch = currentStateText.match(/Lint errors:\s*`([^`]+)`/);
  const aiAgentsMatch = currentStateText.match(/AI agents used:\s*`([^`]+)`/);
  const currentStateHighlights = currentStateText
    .split(/\r?\n/)
    .filter((line) => line.startsWith('- '))
    .slice(0, 8)
    .map((line) => line.replace(/^- /, '').trim());

  let sessionBreadcrumbs = [];
  try {
    sessionBreadcrumbs = fs
      .readdirSync(sessionsDir)
      .filter((name) => /^SESSION_.*\.md$/i.test(name))
      .sort()
      .slice(-5)
      .reverse()
      .map((name) => {
        const filePath = path.join(sessionsDir, name);
        const text = readTextFile(filePath) || '';
        const firstNonEmpty = text
          .split(/\r?\n/)
          .map((line) => line.trim())
          .find((line) => line);
        return {
          name,
          path: filePath,
          title: firstNonEmpty || name,
          updatedAt: statMtimeIso(filePath),
        };
      });
  } catch (_err) {
    sessionBreadcrumbs = [];
  }

  return {
    questTail,
    zeta: {
      completionPercentage: currentProgress.completion_percentage ?? null,
      masteredTasks: currentProgress.mastered_tasks ?? null,
      inProgressTasks: currentProgress.in_progress_tasks ?? null,
      currentPhase: currentProgress.current_phase || 'unknown',
      nextPriority: currentProgress.next_priority || 'unknown',
      recentAchievements,
    },
    checklist: {
      openItems: openChecklistItems,
    },
    currentState: {
      lintErrors: lintErrorsMatch ? lintErrorsMatch[1] : 'unknown',
      aiAgentsUsed: aiAgentsMatch ? aiAgentsMatch[1] : 'unknown',
      highlights: currentStateHighlights,
    },
    paths: {
      questLogPath,
      zetaTrackerPath,
      checklistPath,
      currentStatePath,
      errorReportPath,
      errorReportMdPath,
      latestSessionPath: sessionBreadcrumbs[0]?.path || null,
    },
    sessionBreadcrumbs,
  };
}

function formatAge(isoText) {
  if (!isoText) return 'unknown';
  const parsed = new Date(isoText);
  if (Number.isNaN(parsed.getTime())) return isoText;
  const deltaMs = Date.now() - parsed.getTime();
  const minutes = Math.round(deltaMs / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

function runTaskByLabel(label) {
  return vscode.commands.executeCommand('workbench.action.tasks.runTask', label);
}

async function openPathInEditor(targetPath) {
  if (!targetPath || !fs.existsSync(targetPath)) {
    vscode.window.showErrorMessage(`Path not found: ${targetPath || 'unknown'}`);
    return;
  }
  const uri = vscode.Uri.file(targetPath);
  const stat = fs.statSync(targetPath);
  if (stat.isDirectory()) {
    await vscode.commands.executeCommand('revealInExplorer', uri);
    return;
  }
  const document = await vscode.workspace.openTextDocument(uri);
  await vscode.window.showTextDocument(document, { preview: false });
}

async function getCommandSurfaceState() {
  const availableCommands = new Set(await vscode.commands.getCommands(true));
  return DIRECT_COMMAND_SURFACES.map((surface) => ({
    ...surface,
    available: availableCommands.has(surface.command),
  }));
}

function getTerminalKeeperState(root) {
  if (!root) {
    return {
      exists: false,
      available: false,
      detail: 'workspace not open',
      activeSession: null,
      sessionGroups: 0,
      terminals: 0,
    };
  }

  const sessionsPath = path.join(root, '.vscode', 'sessions.json');
  const payload = readJsonFile(sessionsPath);
  if (!payload || typeof payload !== 'object') {
    return {
      exists: false,
      available: false,
      detail: 'session grid not configured',
      activeSession: null,
      sessionGroups: 0,
      terminals: 0,
      path: sessionsPath,
    };
  }

  const sessions = payload.sessions && typeof payload.sessions === 'object' ? payload.sessions : {};
  const sessionGroups = Object.keys(sessions).length;
  const terminals = Object.values(sessions).reduce(
    (count, group) => count + (Array.isArray(group) ? group.length : 0),
    0
  );
  const activeSession = typeof payload.active === 'string' ? payload.active : null;

  return {
    exists: true,
    available: sessionGroups > 0 && terminals > 0,
    detail:
      sessionGroups > 0
        ? `${terminals} terminals across ${sessionGroups} session group(s)`
        : 'configured but empty',
    activeSession,
    sessionGroups,
    terminals,
    activateOnStartup: Boolean(payload.activateOnStartup),
    path: sessionsPath,
  };
}

function summarizeTerminalRuntime(root) {
  const keeper = getTerminalKeeperState(root);
  const openTerminals = vscode.window.terminals.map((terminal) => terminal.name);
  const openTerminalSet = new Set(openTerminals);
  const activeTerminalName = vscode.window.activeTerminal?.name || null;
  const sessions = keeper.exists ? readJsonFile(keeper.path)?.sessions || {} : {};
  const activeSessionEntries = Array.isArray(sessions?.[keeper.activeSession]) ? sessions[keeper.activeSession] : [];
  const configuredActiveNames = activeSessionEntries
    .map((entry) => (entry && typeof entry.name === 'string' ? entry.name : null))
    .filter(Boolean);
  const matchedConfiguredNames = configuredActiveNames.filter((name) => openTerminalSet.has(name));
  const missingConfiguredNames = configuredActiveNames.filter((name) => !openTerminalSet.has(name));
  const unexpectedOpenNames = openTerminals.filter((name) => !configuredActiveNames.includes(name));

  return {
    keeper,
    openCount: openTerminals.length,
    activeTerminalName,
    openTerminals,
    configuredActiveNames,
    matchedConfiguredNames,
    missingConfiguredNames,
    unexpectedOpenNames,
    coverage:
      configuredActiveNames.length > 0
        ? `${matchedConfiguredNames.length}/${configuredActiveNames.length}`
        : `${openTerminals.length}/0`,
  };
}

function normalizeTerminalKey(name) {
  return String(name || '')
    .normalize('NFKD')
    .replace(/[^\w\s-]/g, ' ')
    .toLowerCase()
    .replace(/\s+/g, '_')
    .replace(/^_+|_+$/g, '');
}

function getConfiguredTerminalContracts(root) {
  if (!root) return [];
  const payload = readJsonFile(path.join(root, 'config', 'terminal_groups.json'));
  if (!payload || typeof payload !== 'object') return [];

  const buildAliases = (key, entry) => {
    const aliases = new Set([normalizeTerminalKey(key), normalizeTerminalKey(entry?.name)]);
    for (const route of Array.isArray(entry?.routes) ? entry.routes : []) {
      aliases.add(normalizeTerminalKey(route));
    }
    return Array.from(aliases).filter(Boolean);
  };

  const sections = [
    ['agent', payload.agent_terminals],
    ['operational', payload.operational_terminals],
  ];

  return sections.flatMap(([category, entries]) =>
    Object.entries(entries || {}).map(([key, entry]) => ({
      key,
      name: entry?.name || key,
      category,
      purpose: entry?.purpose || null,
      agents: Array.isArray(entry?.agents) ? entry.agents : [],
      routes: Array.isArray(entry?.routes) ? entry.routes : [],
      aliases: buildAliases(key, entry),
    }))
  );
}

function findConfiguredTerminalContract(root, name, commandText) {
  const contracts = getConfiguredTerminalContracts(root);
  if (contracts.length === 0) return null;

  const nameAliases = new Set([
    normalizeTerminalKey(name),
    normalizeTerminalKey(String(name || '').replace(/\blogs?\b/gi, '')),
    normalizeTerminalKey(String(name || '').replace(/\bterminal\b/gi, '')),
  ]);
  const haystack = `${name} ${commandText}`.toLowerCase();

  const exact = contracts.find((contract) => contract.aliases.some((alias) => nameAliases.has(alias)));
  if (exact) return exact;

  return (
    contracts.find((contract) =>
      contract.routes.some((route) => haystack.includes(String(route || '').toLowerCase()))
    ) || null
  );
}

function inferTerminalAgents(root, name, commandText) {
  const configured = findConfiguredTerminalContract(root, name, commandText);
  if (configured?.agents?.length) return configured.agents;
  const haystack = `${name} ${commandText}`.toLowerCase();
  const agents = new Set();
  const maybeAdd = (token, label) => {
    if (haystack.includes(token)) agents.add(label);
  };
  maybeAdd('claude', 'Claude');
  maybeAdd('copilot', 'Copilot');
  maybeAdd('codex', 'Codex');
  maybeAdd('chatdev', 'ChatDev');
  maybeAdd('council', 'AI Council');
  maybeAdd('intermediary', 'Intermediary');
  maybeAdd('ollama', 'Ollama');
  maybeAdd('lm studio', 'LM Studio');
  maybeAdd('lmstudio', 'LM Studio');
  maybeAdd('culture ship', 'Culture Ship');
  maybeAdd('moderator', 'Moderator');
  maybeAdd('chatgpt', 'ChatGPT Bridge');
  maybeAdd('simulatedverse', 'SimulatedVerse');
  maybeAdd('simulated verse', 'SimulatedVerse');
  maybeAdd('future', 'Future');
  if (haystack.includes('agents')) {
    ['OpenClaw', 'SkyClaw', 'MetaClaw', 'Hermes-Agent', 'Shepherd', 'Hugging Face'].forEach((agent) =>
      agents.add(agent)
    );
  }
  if (haystack.includes('system')) {
    ['OpenClaw', 'SkyClaw', 'MetaClaw'].forEach((agent) => agents.add(agent));
  }
  return Array.from(agents);
}

function inferTerminalPurpose(root, name, commandText) {
  const configured = findConfiguredTerminalContract(root, name, commandText);
  if (configured?.purpose) return configured.purpose;
  const key = normalizeTerminalKey(name);
  if (key.includes('errors')) return 'error monitoring';
  if (key.includes('suggestions')) return 'suggestion stream';
  if (key.includes('tasks')) return 'task queue';
  if (key.includes('tests')) return 'test telemetry';
  if (key.includes('metrics')) return 'metrics and health';
  if (key.includes('anomalies')) return 'anomaly detection';
  if (key.includes('future')) return 'future prediction stream';
  if (key.includes('council')) return 'multi-agent council';
  if (key.includes('intermediary')) return 'AI routing bridge';
  if (key.includes('culture_ship')) return 'culture ship interface';
  if (key.includes('chatdev')) return 'multi-agent development';
  if (key.includes('ollama')) return 'local model runtime';
  if (key.includes('lm_studio')) return 'OpenAI-compatible model runtime';
  if (key.includes('system')) return 'system status';
  if (key.includes('agents')) return 'agent coordination hub';
  if (key.includes('main')) return 'main operational console';
  if (key.includes('codex') || key.includes('copilot') || key.includes('claude')) return 'agent log watcher';
  if (String(commandText || '').toLowerCase().includes('watch_')) return 'terminal watcher';
  return 'specialized terminal';
}

function resolveWorkspaceScriptPath(commandText, root) {
  if (!root || !commandText) return null;
  const match = String(commandText).match(/-File\s+("?)([^"\n]+?\.ps1)\1(?:\s|$)/i);
  if (!match) return null;
  const raw = match[2].replace(/\\/g, '/');
  const basename = path.basename(raw);
  const directCandidates = [
    path.join(root, 'data', 'terminal_watchers', basename),
    path.join(root, 'scripts', 'terminals', basename),
    path.join(root, '.vscode', basename),
  ];
  const exactIfExists = raw.startsWith('/') && fs.existsSync(raw) ? raw : null;
  const candidates = exactIfExists ? [exactIfExists, ...directCandidates] : directCandidates;
  return candidates.find((candidate) => fs.existsSync(candidate)) || directCandidates[0] || null;
}

function inferLogPathsFromScript(scriptPath, root, fallbackKey) {
  const results = new Set();
  const text = scriptPath ? readTextFile(scriptPath) || '' : '';
  const patterns = [
    /data[\\/]+terminal_logs[\\/]+([A-Za-z0-9_.-]+\.log)/gi,
    /state[\\/]+logs[\\/]+([A-Za-z0-9_.-]+\.log)/gi,
    /state[\\/]+reports[\\/]+([A-Za-z0-9_.-]+\.(?:log|md|json))/gi,
    /docs[\\/]+Reports[\\/]+diagnostics[\\/]+([A-Za-z0-9_.-]+\.(?:log|md|json))/gi,
  ];
  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const relative = match[0].replace(/\\/g, '/');
      results.add(path.join(root, ...relative.split('/')));
    }
  }
  if (scriptPath && path.basename(scriptPath).startsWith('watch_') && fallbackKey) {
    results.add(path.join(root, 'data', 'terminal_logs', `${fallbackKey}.log`));
  }
  return Array.from(results);
}

async function buildTerminalAwareness(root, terminalRuntime) {
  if (!root || !terminalRuntime.keeper.exists) return [];
  const payload = readJsonFile(terminalRuntime.keeper.path);
  const sessions = payload?.sessions || {};
  const activeEntries = Array.isArray(sessions?.[terminalRuntime.keeper.activeSession])
    ? sessions[terminalRuntime.keeper.activeSession]
    : [];

  const liveTerminals = await Promise.all(
    vscode.window.terminals.map(async (terminal) => {
      let processId = null;
      try {
        processId = await terminal.processId;
      } catch (_err) {
        processId = null;
      }
      return { name: terminal.name, processId };
    })
  );
  const liveByName = new Map(liveTerminals.map((entry) => [entry.name, entry]));

  return activeEntries.map((entry) => {
    const name = entry?.name || 'unknown';
    const commands = Array.isArray(entry?.commands) ? entry.commands : [];
    const commandText = commands.join(' && ');
    const scriptPath = resolveWorkspaceScriptPath(commandText, root);
    const configured = findConfiguredTerminalContract(root, name, commandText);
    const fallbackKey = configured?.key || normalizeTerminalKey(name);
    const logPaths = inferLogPathsFromScript(scriptPath, root, fallbackKey);
    const live = liveByName.get(name) || null;
    return {
      name,
      key: fallbackKey,
      purpose: inferTerminalPurpose(root, name, commandText),
      agents: inferTerminalAgents(root, name, commandText),
      commandText,
      scriptPath,
      scriptExists: Boolean(scriptPath && fs.existsSync(scriptPath)),
      logPaths,
      live: Boolean(live),
      processId: live?.processId ?? null,
      icon: entry?.icon || null,
      color: entry?.color || null,
      configuredName: configured?.name || null,
      configuredCategory: configured?.category || null,
    };
  });
}

function buildOutputAwareness(root, terminalAwareness, controlPlane = null) {
  if (!root) return [];
  const surfaces = [];
  const pushSurface = (label, filePath, category) => {
    if (!filePath) return;
    surfaces.push({
      label,
      path: filePath,
      category,
      exists: fs.existsSync(filePath),
    });
  };

  for (const terminal of terminalAwareness) {
    for (const logPath of terminal.logPaths) {
      pushSurface(`${terminal.name} Log`, logPath, 'terminal-log');
    }
  }

  pushSurface('Agent Bus', path.join(root, 'state', 'logs', 'agent_bus.log'), 'coordination');
  pushSurface(
    'Unified Error Report',
    path.join(root, 'state', 'reports', 'unified_error_report_latest.md'),
    'diagnostics'
  );
  pushSurface('Current State', path.join(root, 'state', 'reports', 'current_state.md'), 'state');
  pushSurface(
    'Quest Log',
    path.join(root, 'src', 'Rosetta_Quest_System', 'quest_log.jsonl'),
    'quest'
  );
  pushSurface(
    'Terminal Awareness Snapshot',
    path.join(root, 'state', 'reports', 'terminal_awareness_latest.json'),
    'registry'
  );
  const discoveredArchiveIndex = findArtifactPath(['state/reports/obsolete_current_state_archive_index.json']);
  pushSurface('Obsolete Current State Index', discoveredArchiveIndex, 'archive');
  const discoveredArchiveSummary = findArtifactPath(['state/reports/obsolete_current_state_archive_summary.md']);
  pushSurface('Obsolete Current State Summary', discoveredArchiveSummary, 'archive');
  const sharedQuestRotationStatus = findArtifactPath(['shared_cultivation/quest_log_rotation_status.json']);
  pushSurface('Shared Quest Rotation Status', sharedQuestRotationStatus, 'maintenance');
  const sharedQuestRotationPolicy = findArtifactPath(['shared_cultivation/QUEST_LOG_ROTATION_POLICY.md']);
  pushSurface('Shared Quest Rotation Policy', sharedQuestRotationPolicy, 'policy');

  if (controlPlane?.artifacts) {
    [
      ['Rosetta Bootstrap', controlPlane.artifacts.bootstrap.path],
      ['Rosetta Registry', controlPlane.artifacts.registry.path],
      ['Control Plane Snapshot', controlPlane.artifacts.snapshot.path],
      ['Deprecation Registry', controlPlane.artifacts.deprecations.path],
      ['Culture Ship Runtime Descriptor', controlPlane.artifacts.runtimeDescriptor.path],
      ['Control Plane Manifest', findArtifactPath(['config/control_plane_manifest.json'])],
    ].forEach(([label, filePath]) => pushSurface(label, filePath, 'control-plane'));
  }

  const deduped = new Map();
  for (const surface of surfaces) {
    if (!deduped.has(surface.path)) {
      deduped.set(surface.path, surface);
    }
  }
  return Array.from(deduped.values());
}

function persistTerminalAwarenessSnapshot(root, terminalAwareness, outputAwareness) {
  if (!root) return;
  writeJsonFile(path.join(root, 'state', 'reports', 'terminal_awareness_latest.json'), {
    generated_at: new Date().toISOString(),
    terminals: terminalAwareness,
    output_surfaces: outputAwareness,
  });
}

async function refreshTerminalAwarenessSnapshot() {
  const root = getWorkspaceRoot();
  if (!root) return;
  const terminalRuntime = summarizeTerminalRuntime(root);
  const terminalAwareness = await buildTerminalAwareness(root, terminalRuntime);
  const outputAwareness = buildOutputAwareness(root, terminalAwareness);
  persistTerminalAwarenessSnapshot(root, terminalAwareness, outputAwareness);
}

function buildCapabilityActionEntries(commandSurfaces) {
  const actions = [
    {
      title: 'Activate Intelligence Terminals',
      subtitle: 'Start the workspace terminal intelligence grid',
      kind: 'task',
      value: 'Terminals: Activate Intelligence',
    },
    {
      title: 'NuSyQ Brief',
      subtitle: 'Run the 60-second status brief',
      kind: 'task',
      value: 'NuSyQ: Brief (60s Status)',
    },
    {
      title: 'NuSyQ Spine Snapshot',
      subtitle: 'Run the main system state snapshot',
      kind: 'task',
      value: 'NuSyQ: Snapshot (Spine Lens)',
    },
    {
      title: 'NuSyQ Doctor',
      subtitle: 'Run full workspace diagnostics',
      kind: 'task',
      value: 'NuSyQ: Doctor (Full Diagnostics)',
    },
    {
      title: 'Unified Error Report',
      subtitle: 'Run the canonical multi-repo error ground-truth scan',
      kind: 'task',
      value: 'NuSyQ: Unified Error Report',
    },
    {
      title: 'Problem Signal Snapshot',
      subtitle: 'Capture the current problem/error signal summary',
      kind: 'task',
      value: 'NuSyQ: Problem Signal Snapshot',
    },
    {
      title: 'AI Systems Snapshot',
      subtitle: 'Refresh repo-wide AI health report',
      kind: 'task',
      value: '🤖 AI Systems: Status Snapshot',
    },
    {
      title: 'Causal Analysis',
      subtitle: 'Run the local causal-link sample analysis',
      kind: 'task',
      value: '🔗 Causal Analysis: Sample',
    },
    {
      title: 'Graph Learning',
      subtitle: 'Generate dependency-graph impact snapshot',
      kind: 'task',
      value: '🕸️ Graph Learning: Hub Snapshot',
    },
    {
      title: 'Advanced AI Quests',
      subtitle: 'Create quests for remaining advanced-AI gaps',
      kind: 'task',
      value: '🧠 Advanced AI: Generate Quests',
    },
    {
      title: 'Specialization Status',
      subtitle: 'Inspect cross-agent specialization learning',
      kind: 'task',
      value: '🧬 Specialization: Status Snapshot',
    },
    {
      title: 'MJOLNIR Probes',
      subtitle: 'Probe all registered agents',
      kind: 'task',
      value: '🔫 MJOLNIR: Probe All Agents',
    },
    {
      title: 'OpenClaw Bridge Start',
      subtitle: 'Launch the NuSyQ OpenClaw gateway bridge',
      kind: 'task',
      value: '🦀 OpenClaw: Start Gateway Bridge (bg)',
    },
    {
      title: 'OpenClaw Bridge Status',
      subtitle: 'Check bridge connectivity status',
      kind: 'task',
      value: '🦀 OpenClaw: Bridge Status',
    },
    {
      title: 'OpenClaw Operational Status',
      subtitle: 'Inspect gateway and channel readiness',
      kind: 'task',
      value: '🛰️ OpenClaw: Operational Status',
    },
    {
      title: 'SkyClaw Status',
      subtitle: 'Inspect the Rust sidecar gateway state',
      kind: 'task',
      value: '🛫 SkyClaw: Status',
    },
    {
      title: 'SkyClaw Start',
      subtitle: 'Start the Rust sidecar gateway',
      kind: 'task',
      value: '🛫 SkyClaw: Start',
    },
    {
      title: 'SkyClaw Stop',
      subtitle: 'Stop the Rust sidecar gateway',
      kind: 'task',
      value: '🛑 SkyClaw: Stop',
    },
    {
      title: 'AI Intermediary Start',
      subtitle: 'Launch the cognitive bridge process',
      kind: 'task',
      value: '🧠 AI Intermediary: Start (bg)',
    },
    {
      title: 'Culture Ship Probe',
      subtitle: 'Run Culture Ship health probe',
      kind: 'task',
      value: '⚗️ Culture Ship: Health Probe',
    },
    {
      title: 'AI Council Demo',
      subtitle: 'Exercise the council loop from VS Code',
      kind: 'task',
      value: '🗳️ AI Council: Demo Loop',
    },
    {
      title: 'Ollama Model Inventory',
      subtitle: 'List local Ollama models',
      kind: 'task',
      value: '🦙 Ollama: List Local Models',
    },
    {
      title: 'LM Studio Models',
      subtitle: 'Query the configured LM Studio endpoint',
      kind: 'task',
      value: 'Check LM Studio models',
    },
    {
      title: 'Diagnostics Dashboard',
      subtitle: 'Open live diagnostics + bridge snapshot',
      kind: 'command',
      value: 'powershellMediator.openDiagnosticsDashboard',
    },
  ];

  return actions.concat(
    commandSurfaces
      .filter((surface) => surface.available)
      .map((surface) => ({
        title: surface.title,
        subtitle: surface.subtitle,
        kind: 'command',
        value: surface.command,
      }))
  );
}

function probeJsonEndpoint(urlText, transform) {
  return new Promise((resolve) => {
    let parsed;
    try {
      parsed = new URL(urlText);
    } catch (_err) {
      resolve({ ok: false, label: urlText, detail: 'invalid url' });
      return;
    }

    const client = parsed.protocol === 'https:' ? https : http;
    const req = client.request(
      parsed,
      { method: 'GET', timeout: 2000, headers: { Accept: 'application/json' } },
      (res) => {
        let body = '';
        res.on('data', (chunk) => {
          body += chunk;
        });
        res.on('end', () => {
          let payload = null;
          try {
            payload = body ? JSON.parse(body) : null;
          } catch (_err) {
            payload = null;
          }

          const transformed = typeof transform === 'function' ? transform(payload, res.statusCode) : {};
          resolve({
            ok: res.statusCode >= 200 && res.statusCode < 300,
            statusCode: res.statusCode,
            detail: transformed.detail || body || `HTTP ${res.statusCode}`,
            meta: transformed.meta || {},
          });
        });
      }
    );
    req.on('error', (err) => resolve({ ok: false, label: urlText, detail: err.message, meta: {} }));
    req.on('timeout', () => {
      req.destroy(new Error('timeout'));
    });
    req.end();
  });
}

async function collectCapabilityState() {
  const root = getWorkspaceRoot();
  const config = getMediatorConfig();
  const ollamaBaseUrl = config.get('ollamaBaseUrl', 'http://127.0.0.1:11434');
  const lmStudioBaseUrl = config.get('lmStudioBaseUrl', 'http://127.0.0.1:1234');
  const openClawHealthUrl = config.get('openClawHealthUrl', 'http://127.0.0.1:18790/api/health');
  const additionalCapabilities = config.get('additionalCapabilities', []);

  const [ollama, lmstudio, openclaw] = await Promise.all([
    probeJsonEndpoint(`${ollamaBaseUrl.replace(/\/$/, '')}/api/tags`, (payload) => ({
      detail: payload?.models ? `${payload.models.length} model(s)` : 'reachable',
      meta: { count: Array.isArray(payload?.models) ? payload.models.length : 0 },
    })),
    probeJsonEndpoint(`${lmStudioBaseUrl.replace(/\/$/, '')}/v1/models`, (payload) => ({
      detail: payload?.data ? `${payload.data.length} model(s)` : 'reachable',
      meta: { count: Array.isArray(payload?.data) ? payload.data.length : 0 },
    })),
    probeJsonEndpoint(openClawHealthUrl, (payload) => ({
      detail: payload?.status || payload?.message || 'reachable',
      meta: payload || {},
    })),
  ]);

  const aiStatusPath = root ? path.join(root, 'state', 'reports', 'ai_status_latest.json') : null;
  const openClawStatusPath = root ? path.join(root, 'state', 'reports', 'openclaw_status.json') : null;
  const graphLearningPath = root ? path.join(root, 'state', 'reports', 'graph_learning_latest.json') : null;
  const specializationPath = root
    ? path.join(root, 'state', 'reports', 'specialization_status_latest.json')
    : null;
  const advancedAiQuestsPath = root
    ? path.join(root, 'state', 'reports', 'advanced_ai_quests_latest.json')
    : null;
  const causalAnalysisPath = root
    ? path.join(root, 'state', 'reports', 'causal_analysis_latest.json')
    : null;
  const errorReportStatePath = root
    ? path.join(root, 'state', 'reports', 'unified_error_report_latest.json')
    : null;
  const errorReportCheckpointPath = root
    ? path.join(root, 'state', 'reports', 'error_report_checkpoint_latest.json')
    : null;
  const errorReportDocsPath = root
    ? path.join(root, 'docs', 'Reports', 'diagnostics', 'unified_error_report_latest.json')
    : null;
  const errorReportPath =
    errorReportStatePath && fs.existsSync(errorReportStatePath)
      ? errorReportStatePath
      : errorReportDocsPath;
  const errorReportMdPath = root
    ? path.join(root, 'state', 'reports', 'unified_error_report_latest.md')
    : null;
  const legacyUnifiedErrorsPath = root ? path.join(root, 'state', 'unified_errors.json') : null;
  const agentDashboardStatusPath = root ? path.join(root, 'tools', 'agent_dashboard', 'status.json') : null;
  const repairRequestsPath = root ? path.join(root, 'state', 'repair_requests.json') : null;
  const questLogPath = root ? path.join(root, 'src', 'Rosetta_Quest_System', 'quest_log.jsonl') : null;
  const zetaTrackerPath = root ? path.join(root, 'config', 'ZETA_PROGRESS_TRACKER.json') : null;
  const checklistPath = root ? path.join(root, 'docs', 'Checklists', 'PROJECT_STATUS_CHECKLIST.md') : null;
  const currentStatePath = root ? path.join(root, 'state', 'reports', 'current_state.md') : null;
  const sessionsDir = root ? path.join(root, 'docs', 'Agent-Sessions') : null;
  const aiStatusSnapshot = aiStatusPath ? readJsonFile(aiStatusPath) : null;
  const openClawSnapshot = openClawStatusPath ? readJsonFile(openClawStatusPath) : null;
  const graphLearningSnapshot = graphLearningPath ? readJsonFile(graphLearningPath) : null;
  const specializationSnapshot = specializationPath ? readJsonFile(specializationPath) : null;
  const advancedAiQuestsSnapshot = advancedAiQuestsPath ? readJsonFile(advancedAiQuestsPath) : null;
  const causalAnalysisSnapshot = causalAnalysisPath ? readJsonFile(causalAnalysisPath) : null;
  const errorReportSnapshot = errorReportPath ? readJsonFile(errorReportPath) : null;
  const errorReportCheckpointSnapshot = errorReportCheckpointPath
    ? readJsonFile(errorReportCheckpointPath)
    : null;

  const commandSurfaces = await getCommandSurfaceState();
  const terminalRuntime = summarizeTerminalRuntime(root);
  const terminalAwareness = await buildTerminalAwareness(root, terminalRuntime);
  const bootstrapArtifact = loadArtifactCard([
    'state/boot/rosetta_bootstrap.json',
    'State/boot/rosetta_bootstrap.json',
  ]);
  const registryArtifact = loadArtifactCard([
    'state/registry.json',
    'State/registry.json',
  ]);
  const snapshotArtifact = loadArtifactCard([
    'state/reports/control_plane_snapshot.json',
    'State/reports/control_plane_snapshot.json',
  ]);
  const deprecationArtifact = loadArtifactCard([
    'state/deprecation_registry.json',
    'State/deprecation_registry.json',
  ]);
  const runtimeDescriptorArtifact = loadArtifactCard([
    'state/culture_ship_runtime_descriptor.json',
    'State/culture_ship_runtime_descriptor.json',
  ]);
  const controlPlane = summarizeControlPlaneState({
    bootstrap: bootstrapArtifact,
    registry: registryArtifact,
    snapshot: snapshotArtifact,
    deprecations: deprecationArtifact,
    runtimeDescriptor: runtimeDescriptorArtifact,
  });
  const outputAwareness = buildOutputAwareness(root, terminalAwareness, controlPlane);
  const agentDashboard = buildLegacyAgentDashboardState({
    statusPath: agentDashboardStatusPath,
    unifiedErrorsPath: legacyUnifiedErrorsPath,
    repairRequestsPath,
    questLogPath,
    canonicalErrorSnapshot: errorReportSnapshot,
  });

  return {
    live: { ollama, lmstudio, openclaw },
    snapshots: {
      aiStatus: {
        ...summarizeSnapshotCard(aiStatusSnapshot, aiStatusPath ? statMtimeIso(aiStatusPath) : null),
        path: aiStatusPath,
      },
      openclaw: {
        ...summarizeSnapshotCard(
          openClawSnapshot,
          openClawStatusPath ? statMtimeIso(openClawStatusPath) : null
        ),
        path: openClawStatusPath,
      },
      graphLearning: {
        ...summarizeSnapshotCard(
          graphLearningSnapshot,
          graphLearningPath ? statMtimeIso(graphLearningPath) : null
        ),
        path: graphLearningPath,
      },
      specialization: {
        ...summarizeSnapshotCard(
          specializationSnapshot,
          specializationPath ? statMtimeIso(specializationPath) : null
        ),
        path: specializationPath,
      },
      advancedAiQuests: {
        ...summarizeSnapshotCard(
          advancedAiQuestsSnapshot,
          advancedAiQuestsPath ? statMtimeIso(advancedAiQuestsPath) : null
        ),
        path: advancedAiQuestsPath,
      },
      causalAnalysis: {
        ...summarizeSnapshotCard(
          causalAnalysisSnapshot,
          causalAnalysisPath ? statMtimeIso(causalAnalysisPath) : null
        ),
        path: causalAnalysisPath,
      },
      errorReport: {
        ...summarizeSnapshotCard(errorReportSnapshot, errorReportPath ? statMtimeIso(errorReportPath) : null),
        path: errorReportPath,
      },
    },
    entrySurfaces: {
      commandSurfaces,
      terminalKeeper: terminalRuntime.keeper,
    },
    reports: buildReportDrilldown({
      aiStatusSnapshot,
      graphLearningSnapshot,
      specializationSnapshot,
      advancedAiQuestsSnapshot,
      causalAnalysisSnapshot,
    }),
    errors: buildErrorDrilldown(errorReportSnapshot),
    errorCheckpoint: buildErrorCheckpointSummary(errorReportCheckpointSnapshot),
    workspace: buildWorkspaceDrilldown({
      questLogPath,
      zetaTrackerPath,
      checklistPath,
      currentStatePath,
      errorReportPath,
      errorReportMdPath,
      sessionsDir,
    }),
    agentDashboard,
    terminals: terminalRuntime,
    terminalAwareness,
    outputAwareness,
    controlPlane,
    additionalCapabilities,
    actions: buildCapabilityActionEntries(commandSurfaces),
  };
}

function updateMediatorStatus(text, tooltip) {
  if (!mediatorStatusBarItem) {
    mediatorStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    mediatorStatusBarItem.command = 'powershellMediator.start';
    mediatorStatusBarItem.show();
  }
  mediatorStatusBarItem.text = text;
  mediatorStatusBarItem.tooltip = tooltip;
}

function ensureDiagnosticsStatusBar() {
  if (!diagnosticsStatusBarItem) {
    diagnosticsStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);
    diagnosticsStatusBarItem.command = 'powershellMediator.refreshDiagnosticsSnapshot';
    diagnosticsStatusBarItem.show();
  }
  return diagnosticsStatusBarItem;
}

function ensureTerminalStatusBar() {
  if (!terminalStatusBarItem) {
    terminalStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 98);
    terminalStatusBarItem.command = 'powershellMediator.openCapabilityCockpit';
    terminalStatusBarItem.show();
  }
  return terminalStatusBarItem;
}

function summarizeDiagnostics() {
  const summary = { error: 0, warning: 0, info: 0, hint: 0, total: 0, files: 0, bySource: new Map() };
  const entries = vscode.languages.getDiagnostics();

  for (const [, diagnostics] of entries) {
    if (!diagnostics || diagnostics.length === 0) continue;
    summary.files += 1;
    for (const diagnostic of diagnostics) {
      summary.total += 1;
      const source = diagnostic.source || 'Unknown';
      summary.bySource.set(source, (summary.bySource.get(source) || 0) + 1);
      switch (diagnostic.severity) {
        case vscode.DiagnosticSeverity.Error:
          summary.error += 1;
          break;
        case vscode.DiagnosticSeverity.Warning:
          summary.warning += 1;
          break;
        case vscode.DiagnosticSeverity.Information:
          summary.info += 1;
          break;
        case vscode.DiagnosticSeverity.Hint:
          summary.hint += 1;
          break;
        default:
          summary.info += 1;
          break;
      }
    }
  }

  return summary;
}

function refreshDiagnosticsStatus() {
  const item = ensureDiagnosticsStatusBar();
  const summary = summarizeDiagnostics();
  item.text = `$(warning) E${summary.error} W${summary.warning} I${summary.info} H${summary.hint}`;

  const topSources = [...summary.bySource.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([source, count]) => `${source}: ${count}`);

  const tooltipLines = [
    'Live VS Code diagnostics',
    '',
    `Errors: ${summary.error}`,
    `Warnings: ${summary.warning}`,
    `Infos: ${summary.info}`,
    `Hints: ${summary.hint}`,
    `Total: ${summary.total}`,
    `Files with diagnostics: ${summary.files}`,
  ];

  if (topSources.length > 0) {
    tooltipLines.push('', 'Top sources:', ...topSources);
  }

  tooltipLines.push('', 'Click to refresh the NuSyQ diagnostics bridge snapshot.');
  item.tooltip = tooltipLines.join('\n');

  updateDiagnosticsPanel();
}

function refreshTerminalStatus() {
  const item = ensureTerminalStatusBar();
  const summary = summarizeTerminalRuntime(getWorkspaceRoot());
  item.text = `$(terminal) ${summary.openCount} | ${summary.coverage}`;

  const tooltipLines = [
    'Live terminal topology',
    '',
    `Open terminals: ${summary.openCount}`,
    `Configured active session: ${summary.keeper.activeSession || 'none'}`,
    `Configured coverage: ${summary.coverage}`,
    `Active terminal: ${summary.activeTerminalName || 'none'}`,
  ];

  if (summary.matchedConfiguredNames.length > 0) {
    tooltipLines.push('', 'Matched configured terminals:', ...summary.matchedConfiguredNames.slice(0, 8));
  }
  if (summary.missingConfiguredNames.length > 0) {
    tooltipLines.push('', 'Missing configured terminals:', ...summary.missingConfiguredNames.slice(0, 8));
  }
  if (summary.unexpectedOpenNames.length > 0) {
    tooltipLines.push('', 'Open but outside active session:', ...summary.unexpectedOpenNames.slice(0, 8));
  }

  tooltipLines.push('', 'Click to open the NuSyQ capability cockpit.');
  item.tooltip = tooltipLines.join('\n');

  void updateCapabilityPanel();
}

function scheduleDiagnosticsRefresh() {
  if (diagnosticsRefreshTimer) clearTimeout(diagnosticsRefreshTimer);
  diagnosticsRefreshTimer = setTimeout(() => {
    diagnosticsRefreshTimer = null;
    refreshDiagnosticsStatus();
  }, 250);
}

function shouldAutoRefreshBridge(document) {
  if (!document) return false;
  const config = getMediatorConfig();
  if (!config.get('autoRefreshDiagnosticsSnapshotOnSave', true)) return false;
  const languageIds = new Set(config.get('autoRefreshLanguageIds', ['python', 'javascript', 'typescript', 'json']));
  return languageIds.has(document.languageId);
}

function scheduleBridgeSnapshotRefresh(showMessage = false) {
  const config = getMediatorConfig();
  const debounceMs = Math.max(250, config.get('diagnosticsSnapshotDebounceMs', 1500));
  if (bridgeSnapshotRefreshTimer) clearTimeout(bridgeSnapshotRefreshTimer);
  bridgeSnapshotRefreshTimer = setTimeout(() => {
    bridgeSnapshotRefreshTimer = null;
    refreshDiagnosticsSnapshot(showMessage);
  }, debounceMs);
}

function readBridgeSnapshot() {
  const root = getWorkspaceRoot();
  if (!root) return null;
  const snapshotPath = path.join(root, 'docs', 'Reports', 'diagnostics', 'vscode_diagnostics_bridge.json');
  if (!fs.existsSync(snapshotPath)) return null;
  try {
    return JSON.parse(fs.readFileSync(snapshotPath, 'utf8'));
  } catch (err) {
    return { error: err.message, path: snapshotPath };
  }
}

function renderDiagnosticsDashboard() {
  const live = summarizeDiagnostics();
  const snapshot = readBridgeSnapshot();
  const topSources = [...live.bySource.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([source, count]) => `<tr><td>${escapeHtml(source)}</td><td>${count}</td></tr>`)
    .join('');

  const snapshotCounts = snapshot
    ? `
      <div class="metric-grid">
        <div class="metric"><span>Snapshot Errors</span><strong>${snapshot.errors ?? 'n/a'}</strong></div>
        <div class="metric"><span>Snapshot Warnings</span><strong>${snapshot.warnings ?? 'n/a'}</strong></div>
        <div class="metric"><span>Snapshot Infos</span><strong>${snapshot.infos ?? 'n/a'}</strong></div>
        <div class="metric"><span>Snapshot Total</span><strong>${snapshot.total ?? 'n/a'}</strong></div>
      </div>
      <p class="meta">Snapshot timestamp: ${escapeHtml(snapshot.timestamp || 'unknown')}</p>
    `
    : '<p class="meta">No bridge snapshot found yet. Run a refresh to create one.</p>';

  return `<!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
      body {
        font-family: var(--vscode-font-family);
        color: var(--vscode-foreground);
        background:
          radial-gradient(circle at top right, color-mix(in srgb, var(--vscode-button-background) 15%, transparent), transparent 30%),
          linear-gradient(180deg, color-mix(in srgb, var(--vscode-editor-background) 92%, white), var(--vscode-editor-background));
        padding: 16px;
        max-width: 1240px;
        margin: 0 auto;
      }
      .hero {
        display: grid;
        grid-template-columns: minmax(260px, 1.2fr) minmax(260px, 1fr);
        gap: 16px;
        margin-bottom: 16px;
        padding: 16px;
        border: 1px solid var(--vscode-panel-border);
        border-radius: 14px;
        background: color-mix(in srgb, var(--vscode-editor-background) 84%, white);
      }
      .hero h1 { margin: 0 0 8px; font-size: 22px; }
      .hero p { margin: 0; opacity: 0.8; line-height: 1.45; }
      .toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
      button { border: 1px solid var(--vscode-button-border, transparent); background: var(--vscode-button-background); color: var(--vscode-button-foreground); padding: 6px 12px; cursor: pointer; }
      button:hover { background: var(--vscode-button-hoverBackground); }
      .metric-grid { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; margin-bottom: 12px; }
      .metric { border: 1px solid var(--vscode-panel-border); padding: 10px; border-radius: 10px; background: color-mix(in srgb, var(--vscode-editor-background) 88%, white); }
      .metric span { display: block; font-size: 11px; opacity: 0.8; text-transform: uppercase; }
      .metric strong { display: block; font-size: 22px; margin-top: 6px; }
      h2 { margin: 18px 0 10px; font-size: 15px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--vscode-panel-border); }
      .meta { opacity: 0.75; font-size: 12px; }
      @media (max-width: 960px) {
        .hero, .metric-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <div class="hero">
      <div>
        <h1>NuSyQ Diagnostics</h1>
        <p>
          Live VS Code diagnostics plus the persisted bridge snapshot in one view, so operators can compare
          editor truth against the exported system record without leaving the IDE.
        </p>
      </div>
      <div class="metric-grid">
        <div class="metric"><span>Files</span><strong>${live.files}</strong></div>
        <div class="metric"><span>Total Issues</span><strong>${live.total}</strong></div>
        <div class="metric"><span>Top Source Count</span><strong>${topSources ? live.bySource.size : 0}</strong></div>
        <div class="metric"><span>Snapshot</span><strong>${escapeHtml(snapshot?.timestamp ? 'present' : 'missing')}</strong></div>
      </div>
    </div>
    <div class="toolbar">
      <button id="refreshLive">Refresh Live</button>
      <button id="refreshSnapshot">Refresh Snapshot</button>
    </div>
    <div class="metric-grid">
      <div class="metric"><span>Live Errors</span><strong>${live.error}</strong></div>
      <div class="metric"><span>Live Warnings</span><strong>${live.warning}</strong></div>
      <div class="metric"><span>Live Infos</span><strong>${live.info}</strong></div>
      <div class="metric"><span>Live Hints</span><strong>${live.hint}</strong></div>
    </div>
    <p class="meta">Files with diagnostics: ${live.files} | Total live issues: ${live.total}</p>
    <h2>Bridge Snapshot</h2>
    ${snapshotCounts}
    <h2>Top Live Sources</h2>
    <table>
      <thead><tr><th>Source</th><th>Issues</th></tr></thead>
      <tbody>${topSources || '<tr><td colspan="2">No live diagnostics</td></tr>'}</tbody>
    </table>
    <script>
      const vscode = acquireVsCodeApi();
      document.getElementById('refreshLive').addEventListener('click', () => {
        vscode.postMessage({ type: 'refreshLive' });
      });
      document.getElementById('refreshSnapshot').addEventListener('click', () => {
        vscode.postMessage({ type: 'refreshSnapshot' });
      });
    </script>
  </body>
  </html>`;
}

function updateDiagnosticsPanel() {
  if (!diagnosticsPanel) return;
  diagnosticsPanel.webview.html = renderDiagnosticsDashboard();
}

function openDiagnosticsDashboard() {
  if (diagnosticsPanel) {
    diagnosticsPanel.reveal(vscode.ViewColumn.Beside);
    updateDiagnosticsPanel();
    return;
  }

  diagnosticsPanel = vscode.window.createWebviewPanel(
    'powershellMediatorDiagnostics',
    'NuSyQ Diagnostics',
    vscode.ViewColumn.Beside,
    { enableScripts: true }
  );
  diagnosticsPanel.onDidDispose(() => {
    diagnosticsPanel = null;
  });
  diagnosticsPanel.webview.onDidReceiveMessage((message) => {
    if (message.type === 'refreshLive') {
      refreshDiagnosticsStatus();
      return;
    }
    if (message.type === 'refreshSnapshot') {
      refreshDiagnosticsSnapshot(true);
    }
  });
  updateDiagnosticsPanel();
}

function renderCapabilityCockpit(state) {
  const onlineServices = Object.values(state.live).filter((probe) => probe.ok).length;
  const liveCards = [
    ['Ollama', state.live.ollama, 'Local model runtime'],
    ['LM Studio', state.live.lmstudio, 'OpenAI-compatible endpoint'],
    ['OpenClaw', state.live.openclaw, 'Gateway health'],
  ]
    .map(([name, probe, subtitle]) => {
      const status = probe.ok ? 'online' : 'offline';
      const badge = probe.ok ? 'ok' : 'bad';
      return `
        <div class="card">
          <div class="card-head">
            <div>
              <strong>${escapeHtml(name)}</strong>
              <div class="subtle">${escapeHtml(subtitle)}</div>
            </div>
            <span class="badge ${badge}">${status}</span>
          </div>
          <div class="detail">${escapeHtml(probe.detail || 'No detail')}</div>
        </div>
      `;
    })
    .join('');

  const heroMetrics = `
    <div class="hero-metrics">
      <div class="hero-metric"><span>Online Services</span><strong>${onlineServices}/3</strong></div>
      <div class="hero-metric"><span>Observed Agents</span><strong>${state.agentDashboard.agentCount}</strong></div>
      <div class="hero-metric"><span>Repair Queue</span><strong>${state.agentDashboard.repairQueueSize}</strong></div>
      <div class="hero-metric"><span>Quest Events</span><strong>${state.agentDashboard.questEvents.length}</strong></div>
    </div>
  `;

  const controlPlaneCards = [
    ['Bootstrap', state.controlPlane.artifacts.bootstrap],
    ['Registry', state.controlPlane.artifacts.registry],
    ['Snapshot', state.controlPlane.artifacts.snapshot],
    ['Deprecations', state.controlPlane.artifacts.deprecations],
    ['Runtime Descriptor', state.controlPlane.artifacts.runtimeDescriptor],
  ]
    .map(([name, artifact]) => {
      const status = artifact.exists ? artifact.label : 'missing';
      const detail = artifact.exists
        ? `${artifact.sourcePaths.length} sources | ${Object.keys(artifact.sourceHashes || {}).length} hashes`
        : 'no artifact';
      return `
        <div class="snapshot">
          <strong>${escapeHtml(name)}</strong>
          <div class="subtle">${escapeHtml(status)}</div>
          <div>${escapeHtml(detail)}</div>
          <div>${escapeHtml(artifact.generatedAt ? formatAge(artifact.generatedAt) : 'no timestamp')}</div>
        </div>
      `;
    })
    .join('');

  const controlPlaneRoleRows = Object.entries(state.controlPlane.repoRoles || {})
    .map(
      ([name, meta]) => `<tr><td>${escapeHtml(name)}</td><td>${escapeHtml(meta.role || 'unknown')}</td><td>${escapeHtml(
        meta.priority ?? 'n/a'
      )}</td></tr>`
    )
    .join('');

  const deprecationSummary = Object.entries(state.controlPlane.deprecationCounts || {})
    .map(([name, count]) => `<span class="chip">${escapeHtml(name)} ${escapeHtml(String(count))}</span>`)
    .join('');
  const ideSurfaces = state.controlPlane.artifacts.snapshot.payload?.ide_surfaces || {};
  const ideTaskRows = Array.isArray(ideSurfaces.dev_mentor_task_sample)
    ? ideSurfaces.dev_mentor_task_sample
        .map((label) => `<tr><td>${escapeHtml(label)}</td><td>task</td></tr>`)
        .join('')
    : '';
  const ideCommandChips = []
    .concat(Array.isArray(ideSurfaces.mediator_commands) ? ideSurfaces.mediator_commands.slice(0, 8) : [])
    .concat(
      Array.isArray(ideSurfaces.chatdev_extension_commands)
        ? ideSurfaces.chatdev_extension_commands.slice(0, 4)
        : []
    )
    .map((name) => `<span class="chip">${escapeHtml(name)}</span>`)
    .join('');
  const storageSurfaces = state.controlPlane.artifacts.snapshot.payload?.storage_surfaces || {};
  const storageRows = Object.values(storageSurfaces.surfaces || {})
    .map((surface) => `<tr>
      <td>${escapeHtml(surface.label || 'unknown')}</td>
      <td>${escapeHtml(surface.kind || 'unknown')}</td>
      <td>${escapeHtml(surface.owner || 'unknown')}</td>
      <td>${escapeHtml(surface.exists ? 'present' : 'missing')}</td>
    </tr>`)
    .join('');
  const storageChips = Array.isArray(storageSurfaces.legacy_current_state_archives?.sample)
    ? storageSurfaces.legacy_current_state_archives.sample
        .map((name) => `<span class="chip">${escapeHtml(name)}</span>`)
        .join('')
    : '';
  const outputSurfaceCount = state.outputAwareness.length;
  const outputSurfacePresentCount = state.outputAwareness.filter((surface) => surface.exists).length;
  const outputTerminalLogCount = state.outputAwareness.filter((surface) => surface.category === 'terminal-log').length;
  const outputControlPlaneCount = state.outputAwareness.filter((surface) => surface.category === 'control-plane').length;
  const liveTerminalCount = state.terminalAwareness.filter((terminal) => terminal.live).length;
  const mappedAgentCount = new Set(
    state.terminalAwareness.flatMap((terminal) => terminal.agents || [])
  ).size;
  const terminalsWithLogs = state.terminalAwareness.filter((terminal) => terminal.logPaths.length).length;

  const snapshotCards = [
    ['AI Status', state.snapshots.aiStatus],
    ['OpenClaw Status', state.snapshots.openclaw],
    ['Graph Learning', state.snapshots.graphLearning],
    ['Specialization Status', state.snapshots.specialization],
    ['Advanced AI Quests', state.snapshots.advancedAiQuests],
    ['Causal Analysis', state.snapshots.causalAnalysis],
  ]
    .map(([name, snapshot]) => {
      const status = snapshot.exists ? 'present' : 'missing';
      return `
        <div class="snapshot">
          <strong>${escapeHtml(name)}</strong>
          <div class="subtle">${status}</div>
          <div>${escapeHtml(snapshot.detail || 'no detail')}</div>
          <div>${escapeHtml(snapshot.timestamp ? formatAge(snapshot.timestamp) : 'no snapshot')}</div>
        </div>
      `;
    })
    .join('');

  const terminalMetrics = `
    <div class="metric-grid">
      <div class="metric"><span>Open Terminals</span><strong>${state.terminals.openCount}</strong></div>
      <div class="metric"><span>Configured Session</span><strong>${escapeHtml(
        state.terminals.keeper.activeSession || 'none'
      )}</strong></div>
      <div class="metric"><span>Coverage</span><strong>${escapeHtml(state.terminals.coverage)}</strong></div>
      <div class="metric"><span>Active Terminal</span><strong>${escapeHtml(
        state.terminals.activeTerminalName || 'none'
      )}</strong></div>
    </div>
  `;

  const configuredTerminalRows = state.terminals.configuredActiveNames
    .map((name) => {
      const active = state.terminals.matchedConfiguredNames.includes(name);
      return `<tr><td>${escapeHtml(name)}</td><td>${active ? 'open' : 'missing'}</td></tr>`;
    })
    .join('');

  const openTerminalRows = state.terminals.openTerminals
    .map((name) => {
      const expected = state.terminals.configuredActiveNames.includes(name);
      return `<tr><td>${escapeHtml(name)}</td><td>${expected ? 'session' : 'ad hoc'}</td></tr>`;
    })
    .join('');

  const terminalAwarenessRows = state.terminalAwareness.length
    ? state.terminalAwareness
        .map((terminal) => {
          const agents = terminal.agents.length
            ? terminal.agents.map((agent) => `<span class="chip">${escapeHtml(agent)}</span>`).join('')
            : '<span class="subtle">unmapped</span>';
          const logs = terminal.logPaths.length
            ? terminal.logPaths
                .slice(0, 2)
                .map((logPath) => `<div class="subtle">${escapeHtml(path.basename(logPath))}</div>`)
                .join('')
            : '<div class="subtle">no log path inferred</div>';
          return `<tr>
            <td>${escapeHtml(terminal.name)}</td>
            <td>${escapeHtml(terminal.live ? 'live' : 'configured')}</td>
            <td>${escapeHtml(terminal.processId ?? 'n/a')}</td>
            <td>${escapeHtml(terminal.purpose)}</td>
            <td>${agents}</td>
            <td>${logs}</td>
          </tr>`;
        })
        .join('')
    : '<tr><td colspan="6">No terminal awareness entries available.</td></tr>';

  const outputAwarenessRows = state.outputAwareness.length
    ? state.outputAwareness
        .map(
          (surface) => `<tr>
            <td>${escapeHtml(surface.label)}</td>
            <td>${escapeHtml(surface.category)}</td>
            <td>${escapeHtml(surface.exists ? 'present' : 'missing')}</td>
            <td>${escapeHtml(path.basename(surface.path || ''))}</td>
          </tr>`
        )
        .join('')
    : '<tr><td colspan="4">No output surfaces available.</td></tr>';

  const commandSurfaceCards = state.entrySurfaces.commandSurfaces
    .map((surface) => {
      const badge = surface.available ? 'ok' : 'bad';
      const status = surface.available ? 'available' : 'missing';
      return `
        <div class="card">
          <div class="card-head">
            <div>
              <strong>${escapeHtml(surface.title)}</strong>
              <div class="subtle">${escapeHtml(surface.family)}</div>
            </div>
            <span class="badge ${badge}">${status}</span>
          </div>
          <div class="detail">${escapeHtml(surface.subtitle)}</div>
        </div>
      `;
    })
    .join('');

  const terminalKeeper = state.entrySurfaces.terminalKeeper;
  const terminalKeeperBadge = terminalKeeper.available ? 'ok' : 'bad';
  const terminalKeeperStatus = terminalKeeper.available ? 'ready' : 'missing';
  const terminalKeeperCard = `
    <div class="card">
      <div class="card-head">
        <div>
          <strong>Terminal Keeper Grid</strong>
          <div class="subtle">Session-driven terminal surface</div>
        </div>
        <span class="badge ${terminalKeeperBadge}">${terminalKeeperStatus}</span>
      </div>
      <div class="detail">${escapeHtml(terminalKeeper.detail)}</div>
      <div class="subtle">
        Active session: ${escapeHtml(terminalKeeper.activeSession || 'none')} |
        Startup: ${terminalKeeper.activateOnStartup ? 'on' : 'off'}
      </div>
    </div>
  `;

  const actionButtons = state.actions
    .map(
      (action) => `
        <button data-kind="${escapeHtml(action.kind)}" data-value="${escapeHtml(action.value)}">
          <strong>${escapeHtml(action.title)}</strong>
          <span>${escapeHtml(action.subtitle)}</span>
        </button>
      `
    )
    .join('');

  const additional = Array.isArray(state.additionalCapabilities) && state.additionalCapabilities.length
    ? state.additionalCapabilities
        .map((name) => `<span class="chip">${escapeHtml(name)}</span>`)
        .join('')
    : '<span class="subtle">No additional capabilities configured.</span>';

  const readinessRows = state.reports.readinessRows
    .map(
      (row) => `<tr><td>${escapeHtml(row.name)}</td><td>${escapeHtml(row.status)}</td><td>${escapeHtml(
        row.summary
      )}</td></tr>`
    )
    .join('');

  const graphRows = state.reports.graphHighlights
    .map(
      (row) => `<tr><td>${escapeHtml(row.path)}</td><td>${escapeHtml(row.repo)}</td><td>${escapeHtml(
        String(row.fanOut)
      )}</td><td>${escapeHtml(Number(row.pagerank).toFixed(4))}</td></tr>`
    )
    .join('');

  const specializationLeaderRows = state.reports.specializationLeaders
    .map(
      (row) => `<tr><td>${escapeHtml(row.name)}</td><td>${escapeHtml(row.bestTask)}</td><td>${escapeHtml(
        Number(row.avgScore).toFixed(2)
      )}</td></tr>`
    )
    .join('');

  const specializationAttemptRows = state.reports.specializationAttempts
    .map(
      (row) => `<tr><td>${escapeHtml(row.agent || 'unknown')}</td><td>${escapeHtml(
        row.task_type || 'n/a'
      )}</td><td>${escapeHtml(String(row.success))}</td><td>${escapeHtml(
        Number(row.quality_score ?? 0).toFixed(2)
      )}</td></tr>`
    )
    .join('');

  const questBridge = state.reports.questBridge;
  const questBridgeSummary = questBridge
    ? `
      <div class="metric-grid">
        <div class="metric"><span>Created</span><strong>${questBridge.created}</strong></div>
        <div class="metric"><span>Skipped</span><strong>${questBridge.skipped}</strong></div>
        <div class="metric"><span>Failed</span><strong>${questBridge.failed}</strong></div>
        <div class="metric"><span>Quest IDs</span><strong>${questBridge.questIds.length}</strong></div>
      </div>
      <div class="chips">${
        questBridge.questIds.length
          ? questBridge.questIds.map((id) => `<span class="chip">${escapeHtml(id)}</span>`).join('')
          : '<span class="subtle">No recent quest IDs emitted.</span>'
      }</div>
    `
    : '<p class="subtle">No advanced AI quest bridge snapshot available.</p>';

  const causalRows = state.reports.causalLinks
    .map(
      (row) => `<tr><td>${escapeHtml(row.relationship)}</td><td>${escapeHtml(
        row.type
      )}</td><td>${escapeHtml(Number(row.confidence).toFixed(2))}</td></tr>`
    )
    .join('');

  const feedbackLoopSummary = state.reports.feedbackLoop
    ? `${escapeHtml(state.reports.feedbackLoop.system)} | ${escapeHtml(
        state.reports.feedbackLoop.loopType
      )} | confidence ${escapeHtml(Number(state.reports.feedbackLoop.confidence).toFixed(2))}`
    : 'No feedback loop snapshot';

  const auditCommands = state.reports.auditRecommendations.length
    ? state.reports.auditRecommendations
        .map((command) => `<span class="chip">${escapeHtml(command)}</span>`)
        .join('')
    : '<span class="subtle">No audit recommendations available.</span>';

  const auditCanonicals = state.reports.auditCanonicals.length
    ? state.reports.auditCanonicals
        .map((item) => `<tr><td>${escapeHtml(item)}</td></tr>`)
        .join('')
    : '<tr><td>No canonical audit docs found</td></tr>';

  const errorRepoRows = state.errors.repoRows.length
    ? state.errors.repoRows
        .map(
          (row) =>
            `<tr><td>${escapeHtml(row.name)}</td><td>${escapeHtml(String(row.total))}</td><td>${escapeHtml(
              String(row.errors)
            )}</td><td>${escapeHtml(String(row.warnings))}</td><td>${escapeHtml(
              String(row.infos)
            )}</td></tr>`
        )
        .join('')
    : '<tr><td colspan="5">No repo breakdown available.</td></tr>';

  const errorWarningChips = state.errors.scanWarnings.length
    ? state.errors.scanWarnings
        .map((item) => `<span class="chip">${escapeHtml(item)}</span>`)
        .join('')
    : '<span class="subtle">No scan warnings recorded.</span>';

  const checkpointDetail = state.errorCheckpoint.updatedAt
    ? `${state.errorCheckpoint.progressLabel} | updated ${escapeHtml(formatAge(state.errorCheckpoint.updatedAt))}`
    : state.errorCheckpoint.progressLabel;

  const zetaAchievements = state.workspace.zeta.recentAchievements.length
    ? state.workspace.zeta.recentAchievements
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join('')
    : '<li>No recent achievements captured.</li>';

  const checklistRows = state.workspace.checklist.openItems.length
    ? state.workspace.checklist.openItems
        .map((item) => `<tr><td>${escapeHtml(item)}</td></tr>`)
        .join('')
    : '<tr><td>No open checklist items detected.</td></tr>';

  const currentStateRows = state.workspace.currentState.highlights.length
    ? state.workspace.currentState.highlights
        .map((item) => `<tr><td>${escapeHtml(item)}</td></tr>`)
        .join('')
    : '<tr><td>No current-state highlights available.</td></tr>';

  const questTailRows = state.workspace.questTail.length
    ? state.workspace.questTail
        .map(
          (item) =>
            `<tr><td>${escapeHtml(formatAge(item.timestamp))}</td><td>${escapeHtml(
              item.event
            )}</td><td>${escapeHtml(item.detail)}</td></tr>`
        )
        .join('')
    : '<tr><td colspan="3">No recent quest events found.</td></tr>';

  const sessionRows = state.workspace.sessionBreadcrumbs.length
    ? state.workspace.sessionBreadcrumbs
        .map(
          (item) =>
            `<tr><td>${escapeHtml(item.name)}</td><td>${escapeHtml(item.title)}</td><td>${escapeHtml(
              formatAge(item.updatedAt)
            )}</td></tr>`
        )
        .join('')
    : '<tr><td colspan="3">No session breadcrumbs found.</td></tr>';

  const agentRows = state.agentDashboard.agents.length
    ? state.agentDashboard.agents
        .map(
          (agent) => `<tr><td>${escapeHtml(agent.name)}</td><td>${escapeHtml(
            agent.status
          )}</td><td>${escapeHtml(agent.pid ?? 'n/a')}</td><td>${escapeHtml(
            agent.created ? formatAge(agent.created) : 'n/a'
          )}</td><td>${escapeHtml(agent.detail)}</td></tr>`
        )
        .join('')
    : '<tr><td colspan="5">No agent dashboard status snapshot found.</td></tr>';

  const legacyQuestRows = state.agentDashboard.questEvents.length
    ? state.agentDashboard.questEvents
        .map(
          (entry) => `<tr><td>${escapeHtml(formatAge(entry.timestamp))}</td><td>${escapeHtml(
            entry.event
          )}</td><td>${escapeHtml(entry.detail)}</td></tr>`
        )
        .join('')
    : '<tr><td colspan="3">No quest events in the legacy dashboard feed.</td></tr>';

  const repairRows = state.agentDashboard.repairQueue.length
    ? state.agentDashboard.repairQueue
        .slice(-5)
        .reverse()
        .map(
          (entry) => `<tr><td>${escapeHtml(entry.action || 'unknown')}</td><td>${escapeHtml(
            entry.circuitId || 'n/a'
          )}</td><td>${escapeHtml(entry.requestedBy || 'unknown')}</td><td>${escapeHtml(
            entry.requestedAt ? formatAge(entry.requestedAt) : 'unknown'
          )}</td></tr>`
        )
        .join('')
    : '<tr><td colspan="4">No queued repair requests.</td></tr>';

  const scanChips = state.agentDashboard.scanSummary.length
    ? state.agentDashboard.scanSummary.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join('')
    : '<span class="subtle">No auxiliary scans recorded in the legacy dashboard snapshot.</span>';

  return `<!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
      body {
        font-family: var(--vscode-font-family);
        color: var(--vscode-foreground);
        background:
          radial-gradient(circle at top left, color-mix(in srgb, var(--vscode-button-background) 16%, transparent), transparent 34%),
          linear-gradient(180deg, color-mix(in srgb, var(--vscode-editor-background) 92%, white), var(--vscode-editor-background));
        padding: 16px;
        max-width: 1560px;
        margin: 0 auto;
      }
      .hero {
        display: grid;
        grid-template-columns: minmax(260px, 1.2fr) minmax(320px, 1fr);
        gap: 16px;
        margin-bottom: 16px;
        padding: 16px;
        border: 1px solid var(--vscode-panel-border);
        border-radius: 14px;
        background: color-mix(in srgb, var(--vscode-editor-background) 78%, white);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
      }
      .hero h1 { margin: 0 0 8px; font-size: 24px; }
      .hero p { margin: 0; line-height: 1.45; opacity: 0.8; }
      .hero-metrics {
        display: grid;
        grid-template-columns: repeat(2, minmax(130px, 1fr));
        gap: 10px;
        align-content: start;
      }
      .hero-metric, .metric {
        border: 1px solid var(--vscode-panel-border);
        padding: 10px;
        border-radius: 10px;
        background: color-mix(in srgb, var(--vscode-editor-background) 88%, white);
      }
      .hero-metric span, .metric span { display: block; font-size: 11px; opacity: 0.8; text-transform: uppercase; }
      .hero-metric strong, .metric strong { display: block; font-size: 22px; margin-top: 6px; }
      .toolbar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
      .grid { display: grid; grid-template-columns: repeat(3, minmax(220px, 1fr)); gap: 12px; }
      .card, .snapshot {
        border: 1px solid var(--vscode-panel-border);
        border-radius: 12px;
        padding: 14px;
        background: color-mix(in srgb, var(--vscode-editor-background) 90%, white);
      }
      .card-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
      .badge { padding: 2px 8px; border-radius: 999px; text-transform: uppercase; font-size: 11px; }
      .badge.ok { background: rgba(60, 179, 113, 0.18); color: #5fd38d; }
      .badge.bad { background: rgba(220, 80, 80, 0.18); color: #f08b8b; }
      .detail, .subtle { opacity: 0.78; font-size: 12px; margin-top: 6px; }
      .actions { display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 10px; margin-top: 12px; }
      button { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; border: 1px solid var(--vscode-button-border, transparent); background: var(--vscode-button-background); color: var(--vscode-button-foreground); padding: 10px 12px; cursor: pointer; border-radius: 6px; }
      button:hover { background: var(--vscode-button-hoverBackground); }
      .metric-grid { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; margin-bottom: 12px; }
      h2 { margin: 18px 0 10px; font-size: 15px; }
      .chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
      .chip { border: 1px solid var(--vscode-panel-border); padding: 4px 8px; border-radius: 999px; font-size: 12px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { text-align: left; padding: 8px; border-bottom: 1px solid var(--vscode-panel-border); }
      @media (max-width: 1024px) {
        .hero, .grid, .actions, .metric-grid, .hero-metrics {
          grid-template-columns: 1fr;
        }
      }
    </style>
  </head>
  <body>
    <div class="hero">
      <div>
        <h1>NuSyQ Capability Cockpit</h1>
        <p>
          The canonical IDE control plane for live services, cross-repo operators, legacy agent-dashboard
          signals, and direct recovery actions.
        </p>
        <div class="subtle">Latest agent dashboard snapshot: ${escapeHtml(
          state.agentDashboard.generatedAt ? formatAge(state.agentDashboard.generatedAt) : 'not available'
        )}</div>
      </div>
      ${heroMetrics}
    </div>
    <h2>Control Plane</h2>
    <div class="grid">${controlPlaneCards}</div>
    <div class="metric-grid">
      <div class="metric"><span>Precedence Source</span><strong>${escapeHtml(state.controlPlane.selectedSource)}</strong></div>
      <div class="metric"><span>Runtime Owner</span><strong>${escapeHtml(state.controlPlane.runtimeOwner)}</strong></div>
      <div class="metric"><span>Control Owner</span><strong>${escapeHtml(state.controlPlane.controlOwner)}</strong></div>
      <div class="metric"><span>Deprecated</span><strong>${escapeHtml(String(Object.values(state.controlPlane.deprecationCounts || {}).reduce((sum, count) => sum + Number(count || 0), 0)))}</strong></div>
    </div>
    <div class="chips">${deprecationSummary || '<span class="subtle">No deprecated surfaces recorded.</span>'}</div>
    <table>
      <thead><tr><th>Repo</th><th>Role</th><th>Priority</th></tr></thead>
      <tbody>${controlPlaneRoleRows || '<tr><td colspan="3">No repo role data available.</td></tr>'}</tbody>
    </table>
    <h2>IDE Surfaces</h2>
    <div class="metric-grid">
      <div class="metric"><span>Mediator Commands</span><strong>${escapeHtml(String(ideSurfaces.mediator_command_count ?? 0))}</strong></div>
      <div class="metric"><span>Mediator Settings</span><strong>${escapeHtml(String(ideSurfaces.mediator_setting_count ?? 0))}</strong></div>
      <div class="metric"><span>Legacy Dash Cmds</span><strong>${escapeHtml(String(ideSurfaces.legacy_dashboard_command_count ?? 0))}</strong></div>
      <div class="metric"><span>Dev-Mentor Tasks</span><strong>${escapeHtml(String(ideSurfaces.dev_mentor_task_count ?? 0))}</strong></div>
    </div>
    <div class="chips">${ideCommandChips || '<span class="subtle">No IDE commands surfaced.</span>'}</div>
    <table>
      <thead><tr><th>Task / Surface</th><th>Kind</th></tr></thead>
      <tbody>${ideTaskRows || '<tr><td colspan="2">No task sample recorded.</td></tr>'}</tbody>
    </table>
    <h2>Storage Surfaces</h2>
    <div class="metric-grid">
      <div class="metric"><span>Tracked Stores</span><strong>${escapeHtml(String(storageSurfaces.tracked_surface_count ?? 0))}</strong></div>
      <div class="metric"><span>Present Stores</span><strong>${escapeHtml(String(storageSurfaces.existing_surface_count ?? 0))}</strong></div>
      <div class="metric"><span>SQLite DBs</span><strong>${escapeHtml(String(storageSurfaces.sqlite_db_count ?? 0))}</strong></div>
      <div class="metric"><span>Legacy Archives</span><strong>${escapeHtml(String(storageSurfaces.legacy_current_state_archive_count ?? 0))}</strong></div>
    </div>
    <table>
      <thead><tr><th>Store</th><th>Kind</th><th>Owner</th><th>Status</th></tr></thead>
      <tbody>${storageRows || '<tr><td colspan="4">No storage surfaces recorded.</td></tr>'}</tbody>
    </table>
    <div class="chips">${storageChips || '<span class="subtle">No legacy current_state archives sampled.</span>'}</div>
    <div class="toolbar">
      <button id="refreshCockpit">Refresh Cockpit</button>
      <button id="openDiagnostics">Diagnostics Dashboard</button>
      <button data-kind="task" data-value="NuSyQ: Problem Signal Snapshot">Run Problem Signals</button>
      <button data-kind="task" data-value="NuSyQ: Unified Error Report">Run Error Ground Truth</button>
      <button data-kind="openPath" data-value="${escapeHtml(
        state.workspace.paths.currentStatePath || ''
      )}">Open Current State</button>
      <button data-kind="openPath" data-value="${escapeHtml(
        state.workspace.paths.errorReportPath || ''
      )}">Open Error Report</button>
      <button data-kind="openPath" data-value="${escapeHtml(
        state.agentDashboard.paths.statusPath || ''
      )}">Open Agent Status</button>
      <button id="queueRepair">Queue Rehydrate Repair</button>
    </div>
    <h2>Live Services</h2>
    <div class="grid">${liveCards}</div>
    <h2>Last Snapshots</h2>
    <div class="grid">${snapshotCards}</div>
    <h2>Error Ground Truth</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Unified Error Report</strong>
            <div class="subtle">${escapeHtml(
              `mode ${state.errors.scanMode} | confidence ${state.errors.confidence} | partial ${state.errors.partialScan}`
            )}</div>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Total</span><strong>${escapeHtml(
            String(state.errors.totalDiagnostics)
          )}</strong></div>
          <div class="metric"><span>Errors</span><strong>${escapeHtml(
            String(state.errors.errors)
          )}</strong></div>
          <div class="metric"><span>Warnings</span><strong>${escapeHtml(
            String(state.errors.warnings)
          )}</strong></div>
          <div class="metric"><span>Infos</span><strong>${escapeHtml(
            String(state.errors.infos)
          )}</strong></div>
        </div>
        <div class="subtle">${escapeHtml(state.errors.note)}</div>
        <div class="chips">${errorWarningChips}</div>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Repo Breakdown</strong>
            <div class="subtle">Canonical diagnostics by repository</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Repo</th><th>Total</th><th>Errors</th><th>Warnings</th><th>Infos</th></tr></thead>
          <tbody>${errorRepoRows}</tbody>
        </table>
        <div class="subtle" style="margin-top: 10px;">VS Code export diagnostics: ${escapeHtml(
          String(state.errors.diagnosticsExportTotal)
        )}</div>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Error Report Scan Progress</strong>
            <div class="subtle">${escapeHtml(state.errorCheckpoint.status)}</div>
          </div>
        </div>
        <div class="detail">${escapeHtml(checkpointDetail)}</div>
        <div class="subtle">Current check: ${escapeHtml(state.errorCheckpoint.currentCheck)}</div>
      </div>
    </div>
    <h2>Agent Mesh</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Legacy Agent Dashboard Feed</strong>
            <div class="subtle">Absorbed status.json roster and scan metadata</div>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Observed</span><strong>${escapeHtml(
            String(state.agentDashboard.agentCount)
          )}</strong></div>
          <div class="metric"><span>Running</span><strong>${escapeHtml(
            String(state.agentDashboard.runningAgents)
          )}</strong></div>
          <div class="metric"><span>Status Feed</span><strong>${escapeHtml(
            state.agentDashboard.statusExists ? 'present' : 'missing'
          )}</strong></div>
          <div class="metric"><span>Scans</span><strong>${escapeHtml(
            String(state.agentDashboard.scanSummary.length)
          )}</strong></div>
        </div>
        <div class="chips">${scanChips}</div>
        <table>
          <thead><tr><th>Agent</th><th>Status</th><th>PID</th><th>Age</th><th>Detail</th></tr></thead>
          <tbody>${agentRows}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Unified Error Queue</strong>
            <div class="subtle">${escapeHtml(state.agentDashboard.errors.note)}</div>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Total Issues</span><strong>${escapeHtml(
            String(state.agentDashboard.errors.total)
          )}</strong></div>
          <div class="metric"><span>Open Circuits</span><strong>${escapeHtml(
            String(state.agentDashboard.errors.openCircuits)
          )}</strong></div>
          <div class="metric"><span>Repair Queue</span><strong>${escapeHtml(
            String(state.agentDashboard.repairQueueSize)
          )}</strong></div>
          <div class="metric"><span>Latest Circuit</span><strong>${escapeHtml(
            state.agentDashboard.errors.latestCircuitId || 'n/a'
          )}</strong></div>
        </div>
        <div class="chips">
          <button data-kind="task" data-value="NuSyQ: Unified Error Report">Run Unified Error Report</button>
          <button data-kind="openPath" data-value="${escapeHtml(
            state.agentDashboard.paths.unifiedErrorsPath || ''
          )}">Open Legacy Error Feed</button>
          <button data-kind="openPath" data-value="${escapeHtml(
            state.agentDashboard.paths.repairRequestsPath || ''
          )}">Open Repair Queue</button>
        </div>
        <table>
          <thead><tr><th>Action</th><th>Circuit</th><th>Requested By</th><th>Age</th></tr></thead>
          <tbody>${repairRows}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Quest Stream</strong>
            <div class="subtle">Legacy dashboard tail plus Rosetta quest flow</div>
          </div>
        </div>
        <div class="chips">
          <button data-kind="openPath" data-value="${escapeHtml(
            state.workspace.paths.questLogPath || ''
          )}">Open Quest Stream</button>
          <button data-kind="task" data-value="NuSyQ: Snapshot (Spine Lens)">Run Snapshot</button>
        </div>
        <table>
          <thead><tr><th>Age</th><th>Event</th><th>Detail</th></tr></thead>
          <tbody>${legacyQuestRows}</tbody>
        </table>
      </div>
    </div>
    <h2>Workspace Compass</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Current State</strong>
            <div class="subtle">Live workspace snapshot and repo drift highlights</div>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Lint Errors</span><strong>${escapeHtml(
            String(state.workspace.currentState.lintErrors)
          )}</strong></div>
          <div class="metric"><span>AI Agents Used</span><strong>${escapeHtml(
            String(state.workspace.currentState.aiAgentsUsed)
          )}</strong></div>
          <div class="metric"><span>ZETA Complete</span><strong>${escapeHtml(
            `${state.workspace.zeta.completionPercentage ?? 'n/a'}%`
          )}</strong></div>
          <div class="metric"><span>In Progress</span><strong>${escapeHtml(
            String(state.workspace.zeta.inProgressTasks ?? 'n/a')
          )}</strong></div>
        </div>
        <table>
          <thead><tr><th>Current State Highlights</th></tr></thead>
          <tbody>${currentStateRows}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>ZETA Progress</strong>
            <div class="subtle">${escapeHtml(state.workspace.zeta.currentPhase)}</div>
          </div>
        </div>
        <div class="subtle">Next priority: ${escapeHtml(state.workspace.zeta.nextPriority)}</div>
        <div class="subtle">Mastered tasks: ${escapeHtml(
          String(state.workspace.zeta.masteredTasks ?? 'n/a')
        )}</div>
        <ul>${zetaAchievements}</ul>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Checklist Drift</strong>
            <div class="subtle">Open platform TODOs from the canonical project checklist</div>
          </div>
        </div>
        <div class="chips">
          <button data-kind="openPath" data-value="${escapeHtml(
            state.workspace.paths.checklistPath || ''
          )}">Open Checklist</button>
          <button data-kind="openPath" data-value="${escapeHtml(
            state.workspace.paths.zetaTrackerPath || ''
          )}">Open ZETA Tracker</button>
        </div>
        <table>
          <thead><tr><th>Open Items</th></tr></thead>
          <tbody>${checklistRows}</tbody>
        </table>
      </div>
    </div>
    <h2>Readiness Drilldown</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Advanced AI Readiness</strong>
            <div class="subtle">Current capability statuses from AI status snapshot</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Capability</th><th>Status</th><th>Summary</th></tr></thead>
          <tbody>${readinessRows || '<tr><td colspan="3">No readiness snapshot available</td></tr>'}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Graph Learning Highlights</strong>
            <div class="subtle">Top central nodes from latest graph-learning report</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Path</th><th>Repo</th><th>Fan-out</th><th>PageRank</th></tr></thead>
          <tbody>${graphRows || '<tr><td colspan="4">No graph-learning report available</td></tr>'}</tbody>
        </table>
      </div>
    </div>
    <h2>Learning & Quests</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Specialization Leaders</strong>
            <div class="subtle">Best current agent-task profiles</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Agent</th><th>Best Task</th><th>Avg Score</th></tr></thead>
          <tbody>${specializationLeaderRows || '<tr><td colspan="3">No specialization leaders available</td></tr>'}</tbody>
        </table>
        <div class="subtle" style="margin-top: 10px;">Recent attempts</div>
        <table>
          <thead><tr><th>Agent</th><th>Task</th><th>Success</th><th>Quality</th></tr></thead>
          <tbody>${specializationAttemptRows || '<tr><td colspan="4">No recent specialization attempts</td></tr>'}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Advanced AI Quest Bridge</strong>
            <div class="subtle">Latest quest-generation bridge summary</div>
          </div>
        </div>
        ${questBridgeSummary}
      </div>
    </div>
    <h2>Causality & Audits</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Causal Analysis</strong>
            <div class="subtle">${feedbackLoopSummary}</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Relationship</th><th>Type</th><th>Confidence</th></tr></thead>
          <tbody>${causalRows || '<tr><td colspan="3">No causal-analysis snapshot available</td></tr>'}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Audit Intelligence</strong>
            <div class="subtle">Recommended commands and canonical docs</div>
          </div>
        </div>
        <div class="chips">${auditCommands}</div>
        <table style="margin-top: 10px;">
          <thead><tr><th>Canonical Audit Docs</th></tr></thead>
          <tbody>${auditCanonicals}</tbody>
        </table>
      </div>
    </div>
    <h2>Quests & Breadcrumbs</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Recent Quest Events</strong>
            <div class="subtle">Tail of the Rosetta quest log</div>
          </div>
        </div>
        <div class="chips">
          <button data-kind="openPath" data-value="${escapeHtml(
            state.workspace.paths.questLogPath || ''
          )}">Open Quest Log</button>
        </div>
        <table>
          <thead><tr><th>Age</th><th>Event</th><th>Detail</th></tr></thead>
          <tbody>${questTailRows}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Session Breadcrumbs</strong>
            <div class="subtle">Latest session summaries under docs/Agent-Sessions</div>
          </div>
        </div>
        <div class="chips">
          <button data-kind="openPath" data-value="${escapeHtml(
            state.workspace.paths.latestSessionPath || ''
          )}">Open Latest Session</button>
        </div>
        <table>
          <thead><tr><th>File</th><th>Title</th><th>Updated</th></tr></thead>
          <tbody>${sessionRows}</tbody>
        </table>
      </div>
    </div>
    <h2>Terminal Topology</h2>
    ${terminalMetrics}
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Configured Active Session</strong>
            <div class="subtle">${escapeHtml(state.terminals.keeper.detail)}</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Terminal</th><th>Status</th></tr></thead>
          <tbody>${configuredTerminalRows || '<tr><td colspan="2">No configured active session terminals</td></tr>'}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Open VS Code Terminals</strong>
            <div class="subtle">Live terminal instances in this window</div>
          </div>
        </div>
        <table>
          <thead><tr><th>Terminal</th><th>Type</th></tr></thead>
          <tbody>${openTerminalRows || '<tr><td colspan="2">No open terminals</td></tr>'}</tbody>
        </table>
      </div>
    </div>
    <h2>Agent Terminal Registry</h2>
    <div class="grid">
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Specialized Terminals</strong>
            <div class="subtle">Live PID-aware terminal map for agents and operators</div>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Observed Terminals</span><strong>${escapeHtml(String(state.terminalAwareness.length))}</strong></div>
          <div class="metric"><span>Live Terminals</span><strong>${escapeHtml(String(liveTerminalCount))}</strong></div>
          <div class="metric"><span>Mapped Agents</span><strong>${escapeHtml(String(mappedAgentCount))}</strong></div>
          <div class="metric"><span>With Logs</span><strong>${escapeHtml(String(terminalsWithLogs))}</strong></div>
        </div>
        <div class="chips">
          <button data-kind="openPath" data-value="${escapeHtml(
            state.terminals.keeper.path || ''
          )}">Open Sessions</button>
          <button data-kind="openPath" data-value="${escapeHtml(
            path.join(getWorkspaceRoot() || '', 'state', 'reports', 'terminal_snapshot_latest.json')
          )}">Open Terminal Snapshot</button>
          <button data-kind="openPath" data-value="${escapeHtml(
            path.join(getWorkspaceRoot() || '', 'state', 'reports', 'terminal_awareness_latest.json')
          )}">Open Terminal Registry</button>
        </div>
        <table>
          <thead><tr><th>Terminal</th><th>Status</th><th>PID</th><th>Purpose</th><th>Agents</th><th>Logs</th></tr></thead>
          <tbody>${terminalAwarenessRows}</tbody>
        </table>
      </div>
      <div class="card">
        <div class="card-head">
          <div>
            <strong>Output Surfaces</strong>
            <div class="subtle">Logs, reports, and channels agents can actually consume</div>
          </div>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Observed Outputs</span><strong>${escapeHtml(String(outputSurfaceCount))}</strong></div>
          <div class="metric"><span>Present Outputs</span><strong>${escapeHtml(String(outputSurfacePresentCount))}</strong></div>
          <div class="metric"><span>Terminal Logs</span><strong>${escapeHtml(String(outputTerminalLogCount))}</strong></div>
          <div class="metric"><span>Control Plane</span><strong>${escapeHtml(String(outputControlPlaneCount))}</strong></div>
        </div>
        <table>
          <thead><tr><th>Surface</th><th>Category</th><th>Status</th><th>Artifact</th></tr></thead>
          <tbody>${outputAwarenessRows}</tbody>
        </table>
      </div>
    </div>
    <h2>Direct Entry Points</h2>
    <div class="grid">${terminalKeeperCard}${commandSurfaceCards}</div>
    <h2>Quick Actions</h2>
    <div class="actions">${actionButtons}</div>
    <h2>Declared Additional Capabilities</h2>
    <div class="chips">${additional}</div>
    <script>
      const vscode = acquireVsCodeApi();
      document.getElementById('refreshCockpit').addEventListener('click', () => {
        vscode.postMessage({ type: 'refreshCockpit' });
      });
      document.getElementById('openDiagnostics').addEventListener('click', () => {
        vscode.postMessage({ type: 'openDiagnostics' });
      });
      document.getElementById('queueRepair').addEventListener('click', () => {
        vscode.postMessage({ type: 'queueRepair' });
      });
      document.querySelectorAll('button[data-kind]').forEach((button) => {
        button.addEventListener('click', () => {
          vscode.postMessage({
            type:
              button.dataset.kind === 'task'
                ? 'runTask'
                : button.dataset.kind === 'openPath'
                  ? 'openPath'
                  : 'runCommand',
            value: button.dataset.value,
          });
        });
      });
    </script>
  </body>
  </html>`;
}

async function updateCapabilityPanel() {
  if (!capabilityPanel) return;
  capabilityPanel.webview.html = '<html><body style="font-family: var(--vscode-font-family); padding: 16px;">Refreshing capability cockpit…</body></html>';
  const state = await collectCapabilityState();
  persistTerminalAwarenessSnapshot(getWorkspaceRoot(), state.terminalAwareness, state.outputAwareness);
  if (capabilityPanel) {
    capabilityPanel.webview.html = renderCapabilityCockpit(state);
  }
}

function openCapabilityCockpit() {
  if (capabilityPanel) {
    capabilityPanel.reveal(vscode.ViewColumn.Active);
    void updateCapabilityPanel();
    return;
  }

  capabilityPanel = vscode.window.createWebviewPanel(
    'powershellMediatorCapabilities',
    'NuSyQ Capability Cockpit',
    vscode.ViewColumn.Active,
    { enableScripts: true }
  );
  capabilityPanel.onDidDispose(() => {
    capabilityPanel = null;
  });
  capabilityPanel.webview.onDidReceiveMessage((message) => {
    if (message.type === 'refreshCockpit') {
      void updateCapabilityPanel();
      return;
    }
    if (message.type === 'openDiagnostics') {
      openDiagnosticsDashboard();
      return;
    }
    if (message.type === 'queueRepair') {
      const result = submitRepairRequest(getWorkspaceRoot(), { action: 'rehydrate' });
      if (result.ok) {
        vscode.window.showInformationMessage(
          `Repair request queued at ${result.path} (${result.queued} queued)`
        );
        void updateCapabilityPanel();
      } else {
        vscode.window.showErrorMessage(`Failed to queue repair request: ${result.reason || 'unknown error'}`);
      }
      return;
    }
    if (message.type === 'runTask' && message.value) {
      void runTaskByLabel(message.value);
      return;
    }
    if (message.type === 'openPath' && message.value) {
      void openPathInEditor(message.value);
      return;
    }
    if (message.type === 'runCommand' && message.value) {
      void vscode.commands.executeCommand(message.value).then(
        undefined,
        (err) => vscode.window.showErrorMessage(`Command failed: ${message.value} (${err.message})`)
      );
    }
  });
  void updateCapabilityPanel();
}

function registerCapabilityWorkspaceWatchers(context) {
  const folders = vscode.workspace.workspaceFolders || [];
  if (!folders.length) return;

  const globs = [
    'tools/agent_dashboard/status.json',
    'src/Rosetta_Quest_System/quest_log.jsonl',
    'state/unified_errors.json',
    'state/repair_requests.json',
    'state/boot/rosetta_bootstrap.json',
    'State/boot/rosetta_bootstrap.json',
    'state/registry.json',
    'State/registry.json',
    'state/reports/control_plane_snapshot.json',
    'State/reports/control_plane_snapshot.json',
    'state/deprecation_registry.json',
    'State/deprecation_registry.json',
    'state/culture_ship_runtime_descriptor.json',
    'State/culture_ship_runtime_descriptor.json',
    'config/control_plane_manifest.json',
    'state/reports/obsolete_current_state_archive_index.json',
    'state/reports/obsolete_current_state_archive_summary.md',
    'shared_cultivation/quest_log_rotation_status.json',
    'shared_cultivation/QUEST_LOG_ROTATION_POLICY.md',
  ];
  const patterns = folders.flatMap((folder) =>
    globs.map((glob) => new vscode.RelativePattern(folder, glob))
  );

  const refresh = () => {
    if (capabilityPanel) {
      void updateCapabilityPanel();
    }
  };

  capabilityWorkspaceWatchers = patterns.map((pattern) => {
    const watcher = vscode.workspace.createFileSystemWatcher(pattern);
    watcher.onDidChange(refresh, null, context.subscriptions);
    watcher.onDidCreate(refresh, null, context.subscriptions);
    watcher.onDidDelete(refresh, null, context.subscriptions);
    context.subscriptions.push(watcher);
    return watcher;
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function refreshDiagnosticsSnapshot(showMessage = true) {
  if (bridgeSnapshotInFlight) {
    pendingBridgeSnapshotRefresh = true;
    return;
  }

  const root = getWorkspaceRoot();
  if (!root) {
    vscode.window.showErrorMessage('Open the workspace root before refreshing diagnostics');
    return;
  }

  const out = vscode.window.createOutputChannel('Mediator');
  const pythonPath =
    vscode.workspace.getConfiguration('python').get('defaultInterpreterPath') || 'python';
  const cmd = `"${pythonPath}" scripts/vscode_diagnostics_bridge.py --quiet`;
  out.show(true);
  out.appendLine(`$ ${cmd}`);
  bridgeSnapshotInFlight = true;

  cp.exec(cmd, { cwd: root }, (err, stdout, stderr) => {
    bridgeSnapshotInFlight = false;
    if (stdout) out.appendLine(stdout);
    if (stderr) out.appendLine(stderr);
    if (err) {
      vscode.window.showErrorMessage(`Diagnostics bridge refresh failed: ${err.message}`);
      if (pendingBridgeSnapshotRefresh) {
        pendingBridgeSnapshotRefresh = false;
        scheduleBridgeSnapshotRefresh(false);
      }
      return;
    }
    if (showMessage) {
      const snapshotPath = path.join(root, 'docs', 'Reports', 'diagnostics', 'vscode_diagnostics_bridge.json');
      vscode.window.showInformationMessage(`Diagnostics bridge snapshot refreshed: ${snapshotPath}`);
    }
    updateDiagnosticsPanel();
    void updateCapabilityPanel();
    if (pendingBridgeSnapshotRefresh) {
      pendingBridgeSnapshotRefresh = false;
      scheduleBridgeSnapshotRefresh(false);
    }
  });
}

function startMediator(_context) {
  if (mediatorProc) {
    vscode.window.showInformationMessage('PowerShell mediator already running');
    return;
  }

  const root = getWorkspaceRoot();
  if (!root) {
    vscode.window.showErrorMessage('Open the workspace root before starting the mediator');
    return;
  }
  const script = path.join(root, 'scripts', 'start_powershell_mediator.ps1');

  // Use pwsh to run the wrapper script so it runs the node mediator in background
  const pwsh = 'pwsh';
  const args = ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script];

  try {
    mediatorProc = cp.spawn(pwsh, args, { detached: true, stdio: 'ignore' });
    mediatorProc.unref();
    updateMediatorStatus('Mediator: Running', 'PowerShell mediator is running');
    vscode.window.showInformationMessage('PowerShell mediator started');
  } catch (err) {
    vscode.window.showErrorMessage(`Failed to start mediator: ${err.message}`);
    updateMediatorStatus('Mediator: Error', err.message);
  }
}

async function stopMediator() {
  // Attempt to stop mediator by reading PID file and using taskkill
  const ws = vscode.workspace.workspaceFolders?.[0];
  if (!ws) {
    vscode.window.showErrorMessage('Open a workspace to stop the mediator');
    return;
  }
  const pidFile = path.join(ws.uri.fsPath, '.vscode', 'mediator', 'mediator.pid');
  const launcherPidFile = path.join(ws.uri.fsPath, '.vscode', 'mediator', 'launcher.pid');
  const out = vscode.window.createOutputChannel('Mediator');
  out.show(true);

  let pid = null;
  try {
    if (fs.existsSync(pidFile)) pid = fs.readFileSync(pidFile, 'utf8').trim();
    else if (fs.existsSync(launcherPidFile)) pid = fs.readFileSync(launcherPidFile, 'utf8').trim();
  } catch (e) {
    out.appendLine(`Failed to read PID file: ${e.message}`);
  }

  if (!pid) {
    vscode.window.showInformationMessage('Mediator PID file not found. Is the mediator running?');
    updateMediatorStatus('Mediator: Unknown', 'Mediator PID not found');
    return;
  }

  out.appendLine(`Stopping mediator PID ${pid} (attempting graceful HTTP stop first)`);

  // Determine control port: prefer mediator.http.port if present, otherwise default
  let port = 52101;
  try {
    const portFile = path.join(ws.uri.fsPath, '.vscode', 'mediator', 'mediator.http.port');
    // Wait for the port file to appear if the mediator was just started (up to 10s)
    const maxWait = 10000;
    const pollInterval = 200;
    let waited = 0;
    while (waited < maxWait && !fs.existsSync(portFile)) {
      // eslint-disable-next-line no-await-in-loop
      await sleep(pollInterval);
      waited += pollInterval;
    }
    if (fs.existsSync(portFile)) {
      const txt = fs.readFileSync(portFile, 'utf8').trim();
      const p = parseInt(txt, 10);
      if (!Number.isNaN(p) && p > 0 && p < 65536) port = p;
    } else {
      out.appendLine(`mediator.http.port not found; falling back to default port ${port}`);
    }
  } catch (e) {
    out.appendLine(`Failed to read mediator.http.port file: ${e.message}`);
  }

  const options = {
    hostname: '127.0.0.1',
    port: port,
    path: '/stop-child',
    method: 'POST',
    timeout: 5000,
  };

  // Try HTTP graceful stop and wait for child PID to disappear
  const tryHttpStop = () =>
    new Promise((resolve, reject) => {
      const req = http.request(options, (res) => {
        let body = '';
        res.on('data', (d) => {
          body += d;
        });
        res.on('end', () => resolve({ status: res.statusCode, body }));
      });
      req.on('error', (err) => reject(err));
      req.end();
    });

  try {
    out.appendLine(`Attempting HTTP stop on 127.0.0.1:${port}`);
    const resp = await tryHttpStop();
    out.appendLine(`HTTP stop-child returned ${resp.status} ${resp.body}`);

    // Wait for pid file to disappear (up to 8s)
    const waitForStop = 8000;
    const waitInterval = 250;
    let elapsed = 0;
    while (elapsed < waitForStop) {
      if (!fs.existsSync(pidFile)) {
        out.appendLine('PID file removed after HTTP stop');
        try {
      if (fs.existsSync(launcherPidFile)) fs.unlinkSync(launcherPidFile);
        } catch (e) {
          out.appendLine(`Failed to remove launcherPidFile: ${e.message}`);
        }
        updateMediatorStatus('Mediator: Stopped', 'PowerShell mediator stopped');
        vscode.window.showInformationMessage('PowerShell mediator stopped (via HTTP)');
        return;
      }
      // eslint-disable-next-line no-await-in-loop
      await sleep(waitInterval);
      elapsed += waitInterval;
    }
    out.appendLine('PID still present after HTTP stop; falling back to taskkill');
  } catch (err) {
    out.appendLine(
      `HTTP stop-child request failed: ${err.message}. Falling back to taskkill.`
    );
  }

  // fallback to taskkill if HTTP stop didn't work or PID remained
  const killCmd = `taskkill /PID ${pid} /T /F`;
  cp.exec(killCmd, (err, stdout, stderr) => {
    if (stdout) out.appendLine(stdout);
    if (stderr) out.appendLine(stderr);
    if (err) {
      out.appendLine(`taskkill error: ${err.message}`);
      vscode.window.showErrorMessage(`Failed to stop mediator: ${err.message}`);
      updateMediatorStatus('Mediator: Error', 'Failed to stop mediator');
      return;
    }
    try {
      if (fs.existsSync(pidFile)) fs.unlinkSync(pidFile);
    } catch (e) {
      out.appendLine(`Failed to remove pidFile: ${e.message}`);
    }
    try {
      if (fs.existsSync(launcherPidFile)) fs.unlinkSync(launcherPidFile);
    } catch (e) {
      out.appendLine(`Failed to remove launcherPidFile: ${e.message}`);
    }
    updateMediatorStatus('Mediator: Stopped', 'PowerShell mediator stopped');
    vscode.window.showInformationMessage('PowerShell mediator stopped');
  });
}

function openReports() {
  const ws = vscode.workspace.workspaceFolders?.[0];
  if (!ws) {
    vscode.window.showErrorMessage('Open a workspace to use this command');
    return;
  }
  const reportsPath = path.join(ws.uri.fsPath, 'docs', 'Reports', 'diagnostics');
  vscode.env.openExternal(vscode.Uri.file(reportsPath));
}

function runCommandInOutput(cmd, cwd) {
  const out = vscode.window.createOutputChannel('Mediator');
  out.show(true);
  out.appendLine(`$ ${cmd}`);
  cp.exec(cmd, { cwd: cwd }, (err, stdout, stderr) => {
    if (stdout) out.appendLine(stdout);
    if (stderr) out.appendLine(stderr);
    if (err) out.appendLine(`ERROR: ${err.message}`);
  });
}

function listOllamaModels() {
  // Attempt to locate a workspace folder that looks like NuSyQ
  const folders = vscode.workspace.workspaceFolders || [];
  let repoPath = null;
  for (const f of folders) {
    const candidate = path.join(f.uri.fsPath, 'nusyq_chatdev.py');
    if (fs.existsSync(candidate)) {
      repoPath = f.uri.fsPath;
      break;
    }
    // also check folder name
    if (f.name?.toLowerCase().includes('nusyq')) {
      repoPath = f.uri.fsPath;
    }
  }
  if (!repoPath && folders.length === 1) repoPath = folders[0].uri.fsPath;
  if (!repoPath) {
    vscode.window
      .showQuickPick(
        folders.map((f) => f.name),
        { placeHolder: 'Select workspace folder to run ollama' }
      )
      .then((sel) => {
        if (!sel) return;
        const chosen = folders.find((f) => f.name === sel);
        if (chosen) runCommandInOutput('ollama list', chosen.uri.fsPath);
      });
    return;
  }
  runCommandInOutput('ollama list', repoPath);
}

function runChatDevTask() {
  // Run nusyq_chatdev.py in the NuSyQ repo (non-interactive example)
  const folders = vscode.workspace.workspaceFolders || [];
  let repoPath = null;
  for (const f of folders) {
    const candidate = path.join(f.uri.fsPath, 'nusyq_chatdev.py');
    if (fs.existsSync(candidate)) {
      repoPath = f.uri.fsPath;
      break;
    }
  }
  if (!repoPath) {
    vscode.window.showErrorMessage(
      'Could not find nusyq_chatdev.py in any workspace folder. Open the NuSyQ repo or select a workspace folder.'
    );
    return;
  }
  const pythonExe = 'python';
  const script = 'nusyq_chatdev.py';
  const cmd = `${pythonExe} ${script} --task "Inspect workspace and report" --symbolic --consensus`;
  runCommandInOutput(cmd, repoPath);
}

function activate(context) {
  const startCmd = vscode.commands.registerCommand('powershellMediator.start', () =>
    startMediator(context)
  );
  const stopCmd = vscode.commands.registerCommand('powershellMediator.stop', () => stopMediator());
  const openReportsCmd = vscode.commands.registerCommand('powershellMediator.openReports', () =>
    openReports()
  );
  const listOllamaCmd = vscode.commands.registerCommand('powershellMediator.listOllamaModels', () =>
    listOllamaModels()
  );
  const runChatDevCmd = vscode.commands.registerCommand('powershellMediator.runChatDevTask', () =>
    runChatDevTask()
  );
  const refreshDiagnosticsCmd = vscode.commands.registerCommand(
    'powershellMediator.refreshDiagnosticsSnapshot',
    () => refreshDiagnosticsSnapshot(true)
  );
  const openDiagnosticsDashboardCmd = vscode.commands.registerCommand(
    'powershellMediator.openDiagnosticsDashboard',
    () => openDiagnosticsDashboard()
  );
  const openCapabilityCockpitCmd = vscode.commands.registerCommand(
    'powershellMediator.openCapabilityCockpit',
    () => openCapabilityCockpit()
  );
  context.subscriptions.push(
    startCmd,
    stopCmd,
    openReportsCmd,
    listOllamaCmd,
    runChatDevCmd,
    refreshDiagnosticsCmd,
    openDiagnosticsDashboardCmd,
    openCapabilityCockpitCmd
  );
  registerCapabilityWorkspaceWatchers(context);

  updateMediatorStatus('Mediator: Idle', 'PowerShell mediator not started');
  refreshDiagnosticsStatus();
  refreshTerminalStatus();
  void refreshTerminalAwarenessSnapshot();
  scheduleBridgeSnapshotRefresh(false);

  diagnosticsSubscription = vscode.languages.onDidChangeDiagnostics(() => {
    scheduleDiagnosticsRefresh();
  });
  saveSubscription = vscode.workspace.onDidSaveTextDocument((document) => {
    scheduleDiagnosticsRefresh();
    if (shouldAutoRefreshBridge(document)) {
      scheduleBridgeSnapshotRefresh(false);
    }
  });
  terminalOpenSubscription = vscode.window.onDidOpenTerminal(() => {
    refreshTerminalStatus();
    void refreshTerminalAwarenessSnapshot();
  });
  terminalCloseSubscription = vscode.window.onDidCloseTerminal(() => {
    refreshTerminalStatus();
    void refreshTerminalAwarenessSnapshot();
  });
  activeTerminalSubscription = vscode.window.onDidChangeActiveTerminal(() => {
    refreshTerminalStatus();
    void refreshTerminalAwarenessSnapshot();
  });
  context.subscriptions.push(
    diagnosticsSubscription,
    saveSubscription,
    terminalOpenSubscription,
    terminalCloseSubscription,
    activeTerminalSubscription
  );
}

function deactivate() {
  if (mediatorStatusBarItem) {
    mediatorStatusBarItem.dispose();
    mediatorStatusBarItem = null;
  }
  if (diagnosticsStatusBarItem) {
    diagnosticsStatusBarItem.dispose();
    diagnosticsStatusBarItem = null;
  }
  if (terminalStatusBarItem) {
    terminalStatusBarItem.dispose();
    terminalStatusBarItem = null;
  }
  if (diagnosticsSubscription) {
    diagnosticsSubscription.dispose();
    diagnosticsSubscription = null;
  }
  if (saveSubscription) {
    saveSubscription.dispose();
    saveSubscription = null;
  }
  if (terminalOpenSubscription) {
    terminalOpenSubscription.dispose();
    terminalOpenSubscription = null;
  }
  if (terminalCloseSubscription) {
    terminalCloseSubscription.dispose();
    terminalCloseSubscription = null;
  }
  if (activeTerminalSubscription) {
    activeTerminalSubscription.dispose();
    activeTerminalSubscription = null;
  }
  if (diagnosticsRefreshTimer) {
    clearTimeout(diagnosticsRefreshTimer);
    diagnosticsRefreshTimer = null;
  }
  if (bridgeSnapshotRefreshTimer) {
    clearTimeout(bridgeSnapshotRefreshTimer);
    bridgeSnapshotRefreshTimer = null;
  }
  if (diagnosticsPanel) {
    diagnosticsPanel.dispose();
    diagnosticsPanel = null;
  }
  if (capabilityPanel) {
    capabilityPanel.dispose();
    capabilityPanel = null;
  }
  capabilityWorkspaceWatchers = [];
}

module.exports = {
  activate,
  deactivate,
};
