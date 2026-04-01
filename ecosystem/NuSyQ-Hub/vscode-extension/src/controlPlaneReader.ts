// controlPlaneReader.ts
// Loads control-plane structured truth in canonical order:
//   1. state/boot/rosetta_bootstrap.json   (boot capsule — primary)
//   2. state/ecosystem_registry.json       (system registry)
//   3. state/world_state_snapshot.json     (runtime probe data)
//   4. state/reports/control_plane_snapshot.json (aggregated health)
//
// Each load is independent. Missing files produce null entries rather than errors.

import * as fs from 'fs';
import * as path from 'path';

export interface RepoRole {
    role: string;
    path: string;
    entry?: string;
    status?: string;
    last_commit?: string;
}

export interface RuntimeAgent {
    online: boolean;
    latency_ms?: number | null;
}

export interface ControlPlaneData {
    /** Loaded from state/boot/rosetta_bootstrap.json */
    bootstrap: {
        repoRoles: Record<string, RepoRole>;
        cultureShipAuthority: { runtime_owner: string; control_owner: string } | null;
        runtimeState: {
            agentsOnline: string[];
            agentsOffline: string[];
            epoch?: number;
        } | null;
        knownIssues: string[];
        artifactStatus: Record<string, { status: string }>;
        loaded: boolean;
    };
    /** Loaded from state/ecosystem_registry.json */
    ecosystemRegistry: {
        systemCount: number;
        systems: Record<string, { name: string; system_type: string; status: string }>;
        repoCount: number;
        loaded: boolean;
    };
    /** Loaded from state/world_state_snapshot.json */
    runtimeSnapshot: {
        epoch: number | null;
        timestamp: string | null;
        agentsOnline: string[];
        agentsOffline: string[];
        loaded: boolean;
    };
    /** Loaded from state/reports/control_plane_snapshot.json */
    controlPlaneSnapshot: {
        overallHealth: string | null;
        healthReasons: string[];
        loaded: boolean;
    };
}

function safeReadJson(filePath: string): any | null {
    try {
        if (!fs.existsSync(filePath)) {
            return null;
        }
        const raw = fs.readFileSync(filePath, 'utf8');
        if (!raw || !raw.trim()) {
            return null;
        }
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

export function loadControlPlane(workspaceRoot: string): ControlPlaneData {
    // ── 1. Boot capsule ──────────────────────────────────────────────────────
    const bootstrapPath = path.join(workspaceRoot, 'state', 'boot', 'rosetta_bootstrap.json');
    const bootstrapRaw = safeReadJson(bootstrapPath);
    const bootstrap: ControlPlaneData['bootstrap'] = {
        repoRoles: {},
        cultureShipAuthority: null,
        runtimeState: null,
        knownIssues: [],
        artifactStatus: {},
        loaded: false,
    };

    if (bootstrapRaw) {
        bootstrap.loaded = true;
        bootstrap.repoRoles = bootstrapRaw.repo_role_map ?? {};
        bootstrap.cultureShipAuthority = bootstrapRaw.culture_ship_authority ?? null;
        const rt = bootstrapRaw.runtime_state;
        if (rt) {
            bootstrap.runtimeState = {
                agentsOnline: rt.agents_online ?? [],
                agentsOffline: rt.agents_offline ?? [],
                epoch: rt.epoch,
            };
        }
        bootstrap.knownIssues = bootstrapRaw.known_issues ?? [];
        bootstrap.artifactStatus = bootstrapRaw.control_plane_artifacts ?? {};
    }

    // ── 2. Ecosystem registry ─────────────────────────────────────────────────
    const registryPath = path.join(workspaceRoot, 'state', 'ecosystem_registry.json');
    const registryRaw = safeReadJson(registryPath);
    const ecosystemRegistry: ControlPlaneData['ecosystemRegistry'] = {
        systemCount: 0,
        systems: {},
        repoCount: 0,
        loaded: false,
    };

    if (registryRaw) {
        ecosystemRegistry.loaded = true;
        const systems = registryRaw.systems ?? {};
        ecosystemRegistry.systemCount = Object.keys(systems).length;
        ecosystemRegistry.repoCount = Object.keys(registryRaw.repo_registry ?? {}).length;
        for (const [key, val] of Object.entries(systems) as [string, any][]) {
            ecosystemRegistry.systems[key] = {
                name: val.name ?? key,
                system_type: val.system_type ?? 'unknown',
                status: val.status ?? 'unknown',
            };
        }
    }

    // ── 3. Runtime snapshot ───────────────────────────────────────────────────
    const snapshotPath = path.join(workspaceRoot, 'state', 'world_state_snapshot.json');
    const snapshotRaw = safeReadJson(snapshotPath);
    const runtimeSnapshot: ControlPlaneData['runtimeSnapshot'] = {
        epoch: null,
        timestamp: null,
        agentsOnline: [],
        agentsOffline: [],
        loaded: false,
    };

    if (snapshotRaw) {
        runtimeSnapshot.loaded = true;
        runtimeSnapshot.epoch = snapshotRaw.decision_epoch ?? null;
        runtimeSnapshot.timestamp = snapshotRaw.timestamp ?? null;
        const agents: Record<string, RuntimeAgent> = snapshotRaw.observations?.runtime_state?.agents ?? {};
        for (const [name, info] of Object.entries(agents)) {
            if ((info as RuntimeAgent).online) {
                runtimeSnapshot.agentsOnline.push(name);
            } else {
                runtimeSnapshot.agentsOffline.push(name);
            }
        }
    }

    // ── 4. Control-plane snapshot ─────────────────────────────────────────────
    const cpSnapshotPath = path.join(workspaceRoot, 'state', 'reports', 'control_plane_snapshot.json');
    const cpSnapshotRaw = safeReadJson(cpSnapshotPath);
    const controlPlaneSnapshot: ControlPlaneData['controlPlaneSnapshot'] = {
        overallHealth: null,
        healthReasons: [],
        loaded: false,
    };

    if (cpSnapshotRaw) {
        controlPlaneSnapshot.loaded = true;
        controlPlaneSnapshot.overallHealth = cpSnapshotRaw.overall_health ?? null;
        controlPlaneSnapshot.healthReasons = cpSnapshotRaw.health_reasons ?? [];
    }

    return { bootstrap, ecosystemRegistry, runtimeSnapshot, controlPlaneSnapshot };
}

/** Derive a compact status summary from the loaded control-plane data. */
export function summarizeControlPlane(data: ControlPlaneData): {
    statusIcon: string;
    statusText: string;
    tooltip: string;
    onlineCount: number;
    offlineCount: number;
    systemCount: number;
    issueCount: number;
    health: string;
} {
    // Prefer live runtime snapshot; fall back to bootstrap runtime_state
    const onlineAgents = data.runtimeSnapshot.loaded
        ? data.runtimeSnapshot.agentsOnline
        : (data.bootstrap.runtimeState?.agentsOnline ?? []);
    const offlineAgents = data.runtimeSnapshot.loaded
        ? data.runtimeSnapshot.agentsOffline
        : (data.bootstrap.runtimeState?.agentsOffline ?? []);

    const onlineCount = onlineAgents.length;
    const offlineCount = offlineAgents.length;
    const systemCount = data.ecosystemRegistry.systemCount;
    const issueCount = data.bootstrap.knownIssues.length;
    const health = data.controlPlaneSnapshot.overallHealth ?? (data.bootstrap.loaded ? 'unknown' : 'no_data');

    const healthIcon =
        health === 'healthy' ? '$(check-all)' :
        health === 'degraded' ? '$(warning)' :
        '$(question)';

    const statusText = `${healthIcon} agents ${onlineCount}↑ ${offlineCount}↓ | $(circuit-board) ${systemCount} sys | $(issues) ${issueCount}`;

    const tooltipLines = [
        `NuSyQ Control Plane — ${health}`,
        `Agents online: ${onlineAgents.slice(0, 6).join(', ')}${onlineCount > 6 ? ` +${onlineCount - 6}` : ''}`,
        offlineAgents.length > 0 ? `Offline: ${offlineAgents.join(', ')}` : '',
        data.bootstrap.cultureShipAuthority
            ? `Culture Ship: runtime=${data.bootstrap.cultureShipAuthority.runtime_owner} control=${data.bootstrap.cultureShipAuthority.control_owner}`
            : '',
        issueCount > 0 ? `Known issues: ${issueCount}` : '',
        `Registered systems: ${systemCount}`,
        `[Click to open Control Center]`,
    ].filter(Boolean).join('\n');

    const statusIcon =
        health === 'healthy' ? '$(check-all)' :
        health === 'degraded' ? '$(warning)' :
        '$(question)';

    return { statusIcon, statusText, tooltip: tooltipLines, onlineCount, offlineCount, systemCount, issueCount, health };
}

/** Build HTML for the System State webview panel. */
export function buildSystemStateHtml(data: ControlPlaneData): string {
    const summary = summarizeControlPlane(data);
    const issueItems = data.bootstrap.knownIssues
        .map(i => `<li class="issue">${escapeHtml(i)}</li>`)
        .join('');
    const repoRows = Object.entries(data.bootstrap.repoRoles)
        .map(([name, r]: [string, any]) =>
            `<tr><td><b>${escapeHtml(name)}</b></td><td>${escapeHtml(r.role ?? '')}</td><td>${escapeHtml(r.entry ?? '')}</td></tr>`
        ).join('');
    const systemRows = Object.entries(data.ecosystemRegistry.systems)
        .map(([key, s]) => {
            const statusClass = s.status === 'active' ? 'ok' : s.status === 'active_degraded' ? 'warn' : 'neutral';
            return `<tr><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.system_type)}</td><td class="${statusClass}">${escapeHtml(s.status)}</td></tr>`;
        }).join('');
    const onlineList = (data.runtimeSnapshot.loaded ? data.runtimeSnapshot.agentsOnline : data.bootstrap.runtimeState?.agentsOnline ?? [])
        .map(a => `<span class="badge ok">${escapeHtml(a)}</span>`).join(' ');
    const offlineList = (data.runtimeSnapshot.loaded ? data.runtimeSnapshot.agentsOffline : data.bootstrap.runtimeState?.agentsOffline ?? [])
        .map(a => `<span class="badge warn">${escapeHtml(a)}</span>`).join(' ');

    const csAuthority = data.bootstrap.cultureShipAuthority;

    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NuSyQ System State</title>
<style>
  body { font-family: var(--vscode-font-family); font-size: 13px; color: var(--vscode-foreground); background: var(--vscode-editor-background); padding: 12px 20px; }
  h2 { border-bottom: 1px solid var(--vscode-panel-border); padding-bottom: 4px; margin-top: 18px; }
  table { border-collapse: collapse; width: 100%; margin: 6px 0; }
  th, td { text-align: left; padding: 3px 8px; border-bottom: 1px solid var(--vscode-panel-border); }
  th { color: var(--vscode-descriptionForeground); font-weight: normal; font-size: 11px; text-transform: uppercase; }
  .ok { color: #4ec94e; }
  .warn { color: #e0a020; }
  .issue { color: var(--vscode-inputValidation-warningForeground, #e0a020); }
  .badge { display: inline-block; padding: 1px 6px; border-radius: 3px; margin: 2px; font-size: 11px; }
  .badge.ok { background: #1e3a1e; color: #4ec94e; }
  .badge.warn { background: #3a2a0a; color: #e0a020; }
  .section { margin-bottom: 16px; }
  .health { font-size: 15px; font-weight: bold; }
  .sub { color: var(--vscode-descriptionForeground); font-size: 11px; }
  ul { margin: 4px 0; padding-left: 18px; }
</style>
</head>
<body>
<p class="health ${summary.health === 'healthy' ? 'ok' : 'warn'}">
  Control Plane Health: ${escapeHtml(summary.health.toUpperCase())}
</p>
${csAuthority ? `<p class="sub">Culture Ship: runtime_owner=<b>${escapeHtml(csAuthority.runtime_owner)}</b> | control_owner=<b>${escapeHtml(csAuthority.control_owner)}</b></p>` : ''}

<div class="section">
<h2>Repo Roles</h2>
<table>
  <tr><th>Repo</th><th>Role</th><th>Entry</th></tr>
  ${repoRows || '<tr><td colspan="3">Boot capsule not loaded</td></tr>'}
</table>
</div>

<div class="section">
<h2>Runtime Agents</h2>
<p>Online: ${onlineList || '<span class="sub">none</span>'}</p>
<p>Offline: ${offlineList || '<span class="sub">none</span>'}</p>
</div>

<div class="section">
<h2>Registered Systems (${summary.systemCount})</h2>
<table>
  <tr><th>Name</th><th>Type</th><th>Status</th></tr>
  ${systemRows || '<tr><td colspan="3">Registry not loaded</td></tr>'}
</table>
</div>

${issueItems ? `<div class="section">
<h2>Known Issues (${summary.issueCount})</h2>
<ul>${issueItems}</ul>
</div>` : ''}

<p class="sub">
  Sources: ${data.bootstrap.loaded ? '✓ boot capsule' : '✗ boot capsule'} |
  ${data.ecosystemRegistry.loaded ? '✓ ecosystem registry' : '✗ ecosystem registry'} |
  ${data.runtimeSnapshot.loaded ? `✓ runtime snapshot (epoch ${data.runtimeSnapshot.epoch})` : '✗ runtime snapshot'} |
  ${data.controlPlaneSnapshot.loaded ? '✓ control-plane snapshot' : '✗ control-plane snapshot'}
</p>
</body>
</html>`;
}

function escapeHtml(str: string): string {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
