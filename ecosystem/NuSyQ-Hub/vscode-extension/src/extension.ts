// @ts-nocheck
import * as vscode from 'vscode';
import { execFile } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { loadControlPlane, summarizeControlPlane, buildSystemStateHtml } from './controlPlaneReader';

let systemStatusBarItem: vscode.StatusBarItem;
let focusStatusBarItem: vscode.StatusBarItem;
let statusUpdateInterval: NodeJS.Timeout;
let documentChangeTimer: NodeJS.Timeout | undefined;

const outputChannels = new Map<string, vscode.OutputChannel>();
const ROUTER_OUTPUT = 'NuSyQ Router';
const SERVICES_OUTPUT = 'NuSyQ Services';
const DIAGNOSTICS_OUTPUT = 'NuSyQ Diagnostics';

const TERMINAL_NAMES = [
    'Claude',
    'Copilot',
    'Codex',
    'ChatDev',
    'AI Council',
    'Intermediary',
    'Errors',
    'Suggestions',
    'Tasks',
    'Tests',
    'Zeta',
    'Agents',
    'Metrics',
    'Anomalies',
    'Future',
    'Main',
    'Culture Ship',
    'Moderator',
    'System',
    'ChatGPT Bridge',
    'SimulatedVerse',
    'Ollama',
    'LM Studio',
] as const;

const TERMINAL_COMMAND_ROUTES: Array<{ command: string; title: string; terminal: string; level?: string }> = [
    { command: 'nusyq.claude.query', title: 'NuSyQ: Claude Query', terminal: 'Claude' },
    { command: 'nusyq.copilot.query', title: 'NuSyQ: Copilot Query', terminal: 'Copilot' },
    { command: 'nusyq.codex.query', title: 'NuSyQ: Codex Query', terminal: 'Codex' },
    { command: 'nusyq.chatdev.generate', title: 'NuSyQ: ChatDev Generate', terminal: 'ChatDev' },
    { command: 'nusyq.council.propose', title: 'NuSyQ: AI Council Propose', terminal: 'AI Council' },
    { command: 'nusyq.chatgpt.bridge', title: 'NuSyQ: ChatGPT Bridge', terminal: 'ChatGPT Bridge' },
    { command: 'nusyq.ollama.query', title: 'NuSyQ: Ollama Query', terminal: 'Ollama' },
    { command: 'nusyq.lmstudio.query', title: 'NuSyQ: LM Studio Query', terminal: 'LM Studio' },
    { command: 'nusyq.future.predictions', title: 'NuSyQ: Future Predictions', terminal: 'Future' },
    { command: 'nusyq.moderator.review', title: 'NuSyQ: Moderator Review', terminal: 'Moderator' },
    { command: 'nusyq.cultureShip.audit', title: 'NuSyQ: Culture Ship Audit', terminal: 'Culture Ship' },
    { command: 'nusyq.intermediary.send', title: 'NuSyQ: Intermediary Send', terminal: 'Intermediary' },
];

const routeContext: {
    activeFile: string;
    activeTerminal: string;
    lastSelection: string;
    diagnosticsCount: number;
} = {
    activeFile: 'none',
    activeTerminal: 'Main',
    lastSelection: 'none',
    diagnosticsCount: 0,
};

export function activate(context: vscode.ExtensionContext) {
    logRouter('NuSyQ Extension activating...');

    systemStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    systemStatusBarItem.command = 'nusyq.controlCenter';
    focusStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    focusStatusBarItem.command = 'nusyq.routeToTerminal';

    context.subscriptions.push(systemStatusBarItem, focusStatusBarItem);
    systemStatusBarItem.show();
    focusStatusBarItem.show();

    registerCommands(context);
    registerEventHooks(context);

    updateFocusStatus();
    updateStatusBar();
    statusUpdateInterval = setInterval(updateStatusBar, 30000);

    const cfg = vscode.workspace.getConfiguration('nusyq');
    if (cfg.get<boolean>('autoStartOnOpen', false)) {
        const mode = cfg.get<string>('autoStartMode', 'terminals');
        if (mode === 'ignition') {
            runStartNusyqCommand(['ignition', '--json'], ROUTER_OUTPUT, false);
        } else {
            runStartNusyqCommand(['terminals', 'activate'], ROUTER_OUTPUT, false);
        }
    }

    logRouter('NuSyQ Extension activated.');
}

export function deactivate() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    if (documentChangeTimer) {
        clearTimeout(documentChangeTimer);
    }
}

function registerCommands(context: vscode.ExtensionContext) {
    const disposables: vscode.Disposable[] = [
        vscode.commands.registerCommand('enhanceCopilotContext', enhanceCopilotContext),
        vscode.commands.registerCommand('nusyq.showQuickMenu', showQuickMenu),
        vscode.commands.registerCommand('nusyq.showGuildBoard', showGuildBoard),
        vscode.commands.registerCommand('nusyq.refreshStatus', updateStatusBar),
        vscode.commands.registerCommand('nusyq.tripartiteStatus', showTripartiteStatus),
        vscode.commands.registerCommand('nusyq.startServices', startAllServices),
        vscode.commands.registerCommand('nusyq.serviceStatus', showServiceStatus),
        vscode.commands.registerCommand('nusyq.controlCenter', showControlCenter),
        vscode.commands.registerCommand('nusyq.ignition', () => runStartNusyqCommand(['ignition', '--json'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.ignitionThorough', () => runStartNusyqCommand(['ignition', '--thorough', '--json'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.terminalsActivate', () => runStartNusyqCommand(['terminals', 'activate'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.terminalsSnapshot', () => runStartNusyqCommand(['terminal_snapshot', '--json'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.openclaw.status', () => runStartNusyqCommand(['openclaw_status', '--json'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.antigravity.health', () => runStartNusyqCommand(['antigravity_health', '--json'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.simVerse.sync', () => runStartNusyqCommand(['simverse_bridge'], ROUTER_OUTPUT, true)),
        vscode.commands.registerCommand('nusyq.routeToTerminal', routeToTerminalPrompt),
        vscode.commands.registerCommand('nusyq.tasks.run', () => vscode.commands.executeCommand('workbench.action.tasks.runTask')),
        vscode.commands.registerCommand('nusyq.tests.run', () => vscode.commands.executeCommand('workbench.action.tasks.test')),
        vscode.commands.registerCommand('nusyq.showSystemState', showSystemStatePanel),
    ];

    for (const route of TERMINAL_COMMAND_ROUTES) {
        disposables.push(
            vscode.commands.registerCommand(route.command, async () => {
                const prompt = await vscode.window.showInputBox({
                    prompt: `Message for ${route.terminal}`,
                    placeHolder: 'Enter message payload',
                });
                if (!prompt) {
                    return;
                }
                await routeToTerminal(route.terminal, route.level || 'INFO', prompt, {
                    command: route.command,
                    activeFile: routeContext.activeFile,
                    selection: routeContext.lastSelection,
                });

                if (route.command === 'nusyq.intermediary.send') {
                    await dispatchIntermediaryPrompt(prompt, 'code_analysis_helper');
                }
            })
        );
    }

    context.subscriptions.push(...disposables);
}

function registerEventHooks(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.workspace.onDidChangeWorkspaceFolders(async () => {
            logRouter('Workspace folders changed; refreshing snapshot.');
            await runStartNusyqCommand(['snapshot'], ROUTER_OUTPUT, false);
            updateStatusBar();
        }),
        vscode.workspace.onDidChangeConfiguration((event) => {
            if (event.affectsConfiguration('nusyq')) {
                logRouter('NuSyQ configuration changed; refreshing status.');
                updateStatusBar();
            }
        }),
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            routeContext.activeFile = editor?.document.fileName ? path.basename(editor.document.fileName) : 'none';
            updateFocusStatus();
        }),
        vscode.workspace.onDidChangeTextDocument((event) => {
            queueDocumentChangeRouting(event.document);
        }),
        vscode.window.onDidChangeTextEditorSelection((event) => {
            const selected = event.textEditor.document.getText(event.selections[0]) || '';
            routeContext.lastSelection = selected.trim().slice(0, 120) || 'none';
            updateFocusStatus();
        }),
        vscode.workspace.onDidSaveTextDocument(async (document) => {
            const cfg = vscode.workspace.getConfiguration('nusyq');
            if (cfg.get<boolean>('autoRouteOnSave', true)) {
                await routeToTerminal('Tasks', 'INFO', `Saved ${path.basename(document.fileName)}`, {
                    event: 'onDidSaveTextDocument',
                    languageId: document.languageId,
                });
            }
            updateStatusBar();
        }),
        vscode.languages.onDidChangeDiagnostics(async () => {
            await routeDiagnostics();
        }),
        vscode.window.onDidOpenTerminal(async (terminal) => {
            await routeToTerminal('System', 'INFO', `Terminal opened: ${terminal.name}`, {
                event: 'onDidOpenTerminal',
            });
        }),
        vscode.window.onDidCloseTerminal(async (terminal) => {
            await routeToTerminal('System', 'WARNING', `Terminal closed: ${terminal.name}`, {
                event: 'onDidCloseTerminal',
            });
        }),
        vscode.window.onDidChangeActiveTerminal(async (terminal) => {
            routeContext.activeTerminal = terminal?.name || 'Main';
            updateFocusStatus();
            await routeToTerminal('Agents', 'INFO', `Active terminal focus: ${routeContext.activeTerminal}`, {
                event: 'onDidChangeActiveTerminal',
            });
        })
    );
}

async function routeDiagnostics() {
    const cfg = vscode.workspace.getConfiguration('nusyq');
    if (!cfg.get<boolean>('autoRouteDiagnostics', true)) {
        return;
    }

    let total = 0;
    for (const diagnosticTuple of vscode.languages.getDiagnostics()) {
        total += diagnosticTuple[1].length;
    }

    const previous = routeContext.diagnosticsCount;
    routeContext.diagnosticsCount = total;

    const diagnosticsChannel = getOutputChannel(DIAGNOSTICS_OUTPUT);
    diagnosticsChannel.appendLine(`[${new Date().toISOString()}] diagnostics=${total}`);

    await routeToTerminal('Errors', 'INFO', `Diagnostics updated: ${total}`, {
        event: 'onDidChangeDiagnostics',
        previous,
    });

    const spikeThreshold = cfg.get<number>('diagnosticsSpikeThreshold', 25);
    if (total - previous >= spikeThreshold) {
        vscode.window.showWarningMessage(`NuSyQ diagnostics spike detected: ${previous} -> ${total}`);
        await routeToTerminal('Anomalies', 'WARNING', `Diagnostics spike: ${previous} -> ${total}`, {
            event: 'diagnostics_spike',
        });
    }

    updateStatusBar();
}

function queueDocumentChangeRouting(document: vscode.TextDocument) {
    if (documentChangeTimer) {
        clearTimeout(documentChangeTimer);
    }

    documentChangeTimer = setTimeout(async () => {
        await routeToTerminal('Suggestions', 'DEBUG', `Edited ${path.basename(document.fileName)}`, {
            event: 'onDidChangeTextDocument',
            languageId: document.languageId,
        });
    }, 900);
}

async function showControlCenter() {
    const items = [
        { label: '$(circuit-board) System State', command: 'nusyq.showSystemState' },
        { label: '$(rocket) Run Ignition', command: 'nusyq.ignition' },
        { label: '$(flame) Run Ignition (Thorough)', command: 'nusyq.ignitionThorough' },
        { label: '$(terminal) Activate Specialized Terminals', command: 'nusyq.terminalsActivate' },
        { label: '$(pulse) Service Status', command: 'nusyq.serviceStatus' },
        { label: '$(output) Terminal Snapshot', command: 'nusyq.terminalsSnapshot' },
        { label: '$(broadcast) Route Message To Terminal', command: 'nusyq.routeToTerminal' },
        { label: '$(zap) OpenClaw Status', command: 'nusyq.openclaw.status' },
        { label: '$(beaker) Antigravity Health', command: 'nusyq.antigravity.health' },
        { label: '$(game) SimulatedVerse Sync', command: 'nusyq.simVerse.sync' },
        { label: '$(organization) Tripartite Status', command: 'nusyq.tripartiteStatus' },
    ];

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'NuSyQ Control Center',
        matchOnDescription: true,
    });

    if (selected) {
        await vscode.commands.executeCommand(selected.command);
    }
}

async function routeToTerminalPrompt() {
    const terminal = await vscode.window.showQuickPick([...TERMINAL_NAMES], {
        placeHolder: 'Select terminal channel',
    });
    if (!terminal) {
        return;
    }

    const message = await vscode.window.showInputBox({
        prompt: `Message for ${terminal}`,
        placeHolder: 'Enter message',
    });
    if (!message) {
        return;
    }

    await routeToTerminal(terminal, 'INFO', message, {
        command: 'nusyq.routeToTerminal',
        activeFile: routeContext.activeFile,
        activeTerminal: routeContext.activeTerminal,
    });
}

async function routeToTerminal(channel: string, level: string, message: string, metadata: Record<string, unknown> = {}) {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        return;
    }

    const output = getOutputChannel(ROUTER_OUTPUT);
    const metaJson = JSON.stringify({
        ...metadata,
        source: 'vscode-extension',
        ts: new Date().toISOString(),
    });

    const result = await runPythonScript(
        workspaceFolder,
        ['scripts/emit_terminal.py', channel, level.toLowerCase(), message, metaJson],
        output,
        false
    );

    if (!result.ok) {
        output.appendLine(`route_to_terminal failed for ${channel}: ${result.stderr || result.stdout}`);
    }
}

async function dispatchIntermediaryPrompt(prompt: string, moduleName: string) {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        return;
    }
    const output = getOutputChannel(ROUTER_OUTPUT);
    await runPythonScript(
        workspaceFolder,
        ['scripts/intermediary_client.py', '--prompt', prompt, '--module', moduleName],
        output,
        true
    );
}

async function runStartNusyqCommand(args: string[], outputName: string, reveal = true) {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return { ok: false, stdout: '', stderr: 'No workspace folder found' };
    }

    const output = getOutputChannel(outputName);
    if (reveal) {
        output.show(true);
    }
    output.appendLine(`$ ${resolvePythonBinary()} scripts/start_nusyq.py ${args.join(' ')}`);

    return runPythonScript(workspaceFolder, ['scripts/start_nusyq.py', ...args], output, false);
}

function runPythonScript(
    workspaceFolder: string,
    scriptArgs: string[],
    output: vscode.OutputChannel,
    revealOutputOnFinish: boolean
): Promise<{ ok: boolean; stdout: string; stderr: string }> {
    const pythonBin = resolvePythonBinary();
    return new Promise((resolve) => {
        execFile(
            pythonBin,
            scriptArgs,
            { cwd: workspaceFolder, maxBuffer: 1024 * 1024 * 10 },
            (error, stdout, stderr) => {
                if (stdout) {
                    output.appendLine(stdout.trimEnd());
                }
                if (stderr) {
                    output.appendLine(stderr.trimEnd());
                }
                if (revealOutputOnFinish) {
                    output.show(true);
                }

                if (error) {
                    resolve({ ok: false, stdout, stderr: stderr || error.message });
                    return;
                }
                resolve({ ok: true, stdout, stderr });
            }
        );
    });
}

function resolvePythonBinary(): string {
    return vscode.workspace.getConfiguration('nusyq').get<string>('pythonPath', 'python');
}

function getOutputChannel(name: string): vscode.OutputChannel {
    const existing = outputChannels.get(name);
    if (existing) {
        return existing;
    }
    const channel = vscode.window.createOutputChannel(name);
    outputChannels.set(name, channel);
    return channel;
}

function logRouter(message: string) {
    const output = getOutputChannel(ROUTER_OUTPUT);
    output.appendLine(`[${new Date().toISOString()}] ${message}`);
}

async function updateStatusBar() {
    try {
        const workspaceFolder = getWorkspaceRoot();
        if (!workspaceFolder) {
            systemStatusBarItem.text = '$(warning) NuSyQ: No workspace';
            return;
        }

        // ── Primary: structured artifact load order ────────────────────────
        // 1. state/boot/rosetta_bootstrap.json
        // 2. state/ecosystem_registry.json
        // 3. state/world_state_snapshot.json
        // 4. state/reports/control_plane_snapshot.json
        const cpData = loadControlPlane(workspaceFolder);

        if (cpData.bootstrap.loaded || cpData.runtimeSnapshot.loaded) {
            const summary = summarizeControlPlane(cpData);
            systemStatusBarItem.text = summary.statusText;
            systemStatusBarItem.tooltip = summary.tooltip + '\nClick to open Control Center';
            return;
        }

        // ── Fallback: legacy file-based status (critical_services + guild board) ──
        const serviceStatePath = path.join(workspaceFolder, 'state', 'services', 'critical_services.json');
        const guildBoardPath = path.join(workspaceFolder, 'docs', 'GUILD_BOARD.md');
        const ignitionPath = path.join(workspaceFolder, 'state', 'reports', 'ignition_latest.json');

        let serviceCount = 0;
        let runningServices = 0;
        let questCount = 0;
        let ignitionStatus = 'unknown';

        if (fs.existsSync(serviceStatePath)) {
            try {
                const serviceState = JSON.parse(fs.readFileSync(serviceStatePath, 'utf8'));
                const services = serviceState.services || {};
                serviceCount = Object.keys(services).length;
                runningServices = Object.values(services).filter((s: any) => s.status === 'running').length;
            } catch { /* ignore parse errors */ }
        }

        if (fs.existsSync(guildBoardPath)) {
            const guildBoard = fs.readFileSync(guildBoardPath, 'utf8');
            const questMatches = guildBoard.match(/##\s+\[/g);
            questCount = questMatches ? questMatches.length : 0;
        }

        if (fs.existsSync(ignitionPath)) {
            try {
                const ignition = JSON.parse(fs.readFileSync(ignitionPath, 'utf8'));
                ignitionStatus = ignition.status || 'unknown';
            } catch { /* ignore parse errors */ }
        }

        const serviceIcon =
            runningServices === serviceCount && serviceCount > 0 ? '$(check)'
            : runningServices > 0 ? '$(warning)'
            : '$(x)';

        systemStatusBarItem.text =
            `${serviceIcon} svc ${runningServices}/${serviceCount} | $(checklist) ${questCount} | $(pulse) ${ignitionStatus}`;
        systemStatusBarItem.tooltip = 'NuSyQ Status (fallback)\nClick to open Control Center';
    } catch (error: any) {
        systemStatusBarItem.text = '$(warning) NuSyQ: Error';
        systemStatusBarItem.tooltip = `Error: ${error.message}`;
    }
}

let systemStatePanel: vscode.WebviewPanel | undefined;

async function showSystemStatePanel() {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const cpData = loadControlPlane(workspaceFolder);
    const html = buildSystemStateHtml(cpData);

    if (systemStatePanel) {
        systemStatePanel.reveal(vscode.ViewColumn.Two);
        systemStatePanel.webview.html = html;
        return;
    }

    systemStatePanel = vscode.window.createWebviewPanel(
        'nusyqSystemState',
        'NuSyQ System State',
        vscode.ViewColumn.Two,
        { enableScripts: false }
    );
    systemStatePanel.webview.html = html;
    systemStatePanel.onDidDispose(() => { systemStatePanel = undefined; });
}

function updateFocusStatus() {
    focusStatusBarItem.text =
        `$(symbol-event) ${routeContext.activeTerminal} | $(file-code) ${routeContext.activeFile} | $(issue-opened) ${routeContext.diagnosticsCount}`;
    focusStatusBarItem.tooltip = 'NuSyQ Focus Context\nClick to route message to a terminal';
}

async function showQuickMenu() {
    const items = [
        {
            label: '$(dashboard) Control Center',
            description: 'Open NuSyQ Control Center',
            command: 'nusyq.controlCenter',
        },
        {
            label: '$(book) Guild Board',
            description: 'View active quests and guild status',
            command: 'nusyq.showGuildBoard',
        },
        {
            label: '$(pulse) Service Status',
            description: 'Check running services and health',
            command: 'nusyq.serviceStatus',
        },
        {
            label: '$(refresh) Refresh Status',
            description: 'Update status bar now',
            command: 'nusyq.refreshStatus',
        },
        {
            label: '$(rocket) Run Ignition',
            description: 'Activate orchestrator stack',
            command: 'nusyq.ignition',
        },
    ];

    const selected = await vscode.window.showQuickPick(items, {
        placeHolder: 'NuSyQ Quick Actions',
        matchOnDescription: true,
    });

    if (selected) {
        await vscode.commands.executeCommand(selected.command);
    }
}

async function showGuildBoard() {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const guildBoardPath = path.join(workspaceFolder, 'docs', 'GUILD_BOARD.md');

    if (!fs.existsSync(guildBoardPath)) {
        vscode.window.showErrorMessage('Guild Board not found at docs/GUILD_BOARD.md');
        return;
    }

    const doc = await vscode.workspace.openTextDocument(guildBoardPath);
    await vscode.window.showTextDocument(doc, { preview: false });
}

async function showServiceStatus() {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const output = getOutputChannel(SERVICES_OUTPUT);
    output.show(true);
    output.appendLine('='.repeat(70));
    output.appendLine('NuSyQ Service Status');
    output.appendLine('='.repeat(70));

    await runPythonScript(
        workspaceFolder,
        ['scripts/start_all_critical_services.py', 'status'],
        output,
        false
    );
}

async function startAllServices() {
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const output = getOutputChannel(SERVICES_OUTPUT);
    output.show(true);
    output.appendLine('Starting all critical services...');

    const result = await runPythonScript(
        workspaceFolder,
        ['scripts/start_all_critical_services.py', 'start', '--no-monitor'],
        output,
        false
    );

    if (!result.ok) {
        vscode.window.showErrorMessage('Failed to start services');
        return;
    }

    setTimeout(updateStatusBar, 1500);
    vscode.window.showInformationMessage('Services started successfully');
}

async function showTripartiteStatus() {
    await runStartNusyqCommand(['snapshot'], ROUTER_OUTPUT, true);
}

async function enhanceCopilotContext() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showInformationMessage('No active editor');
        return;
    }

    const filePath = editor.document.fileName;
    const workspaceFolder = getWorkspaceRoot();
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const output = getOutputChannel('Copilot Enhancement');
    output.show(true);
    output.appendLine(`Enhancing context for ${filePath}`);

    await runPythonScript(
        workspaceFolder,
        ['scripts/enhance_copilot_context.py', filePath, '--compact'],
        output,
        false
    );
}

function getWorkspaceRoot(): string | undefined {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        return undefined;
    }

    for (const folder of workspaceFolders) {
        if (folder.name.includes('NuSyQ-Hub') || folder.name.includes('Main')) {
            return folder.uri.fsPath;
        }
    }

    return workspaceFolders[0].uri.fsPath;
}
