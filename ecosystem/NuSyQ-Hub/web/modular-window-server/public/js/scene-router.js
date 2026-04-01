/**
 * ΞNuSyQ Scene Router - Universal Menu Navigation System
 * Digital Analog Synthesizer UI - Modular, Flexible, Interconnected
 *
 * Brings together ALL UI components into a unified navigation system:
 * - Quantum Terminal (interactive shell)
 * - Agent Status Viewers (clickable terminals for each AI)
 * - Game Scenes (House of Leaves, Idle, Tower Defense, RPG, Roguelike)
 * - Context Browsers (Streamlit integration, file analysis)
 * - Dashboard Views (metrics, guild board, cultivation stats)
 * - Model Selectors (Ollama, LM Studio, ChatDev, etc.)
 * - Terminal Integrations (WSL, real shell commands)
 */

class SceneRouter {
    constructor() {
        this.scenes = new Map();
        this.activeScene = null;
        this.history = [];
        this.menuStack = [];

        // API endpoints
        this.apiBase = globalThis.location.origin;

        // Initialize all available scenes
        this.initializeScenes();

        // Kick off badge refresh so main menu shows live counts on load
        this.refreshBadges();

        // Refresh badges periodically (once per minute)
        setInterval(() => this.refreshBadges(), 60000);

        // Setup navigation shortcuts
        this.setupKeyboardShortcuts();
    }

    async refreshBadges() {
        try {
            const metricsResp = await fetch(`${this.apiBase}/api/metrics`);
            if (!metricsResp.ok) return;
            const metrics = await metricsResp.json();
            const util = metrics.system_utilization || {};

            const questBadge = document.getElementById('badge-help');
            if (questBadge) {
                questBadge.textContent = `${util.actionable_quests || 0} ready / ${util.blocked_quests || 0} blocked`;
            }

            const dashBadge = document.getElementById('badge-dashboards');
            if (dashBadge) {
                dashBadge.textContent = `PU q:${util.queued_pus || 0}`;
            }

            const questTrackerBadge = document.getElementById('badge-quest_tracker');
            if (questTrackerBadge) {
                questTrackerBadge.textContent = `${util.total_quests || 0} quests`;
            }
        } catch (err) {
            // ignore badge refresh errors to avoid blocking UI
        }
    }

    initializeScenes() {
        // Main Menu Categories - Digital Synthesizer Style
        // Preset agent terminals (should match backend TerminalType)
        const presetTerminals = [
            { id: 'copilot', label: '🧩 Copilot Terminal', desc: 'GitHub Copilot AI terminal' },
            { id: 'claude', label: '🤖 Claude Terminal', desc: 'Claude AI assistant terminal' },
            { id: 'chatdev', label: '🏗️ ChatDev Terminal', desc: 'ChatDev multi-agent terminal' },
            { id: 'ai_council', label: '🏛️ AI Council Terminal', desc: 'AI Council governance terminal' },
            { id: 'intermediary', label: '🔗 Intermediary Terminal', desc: 'System intermediary terminal' },
            { id: 'errors', label: '🔥 Errors Terminal', desc: 'Error management terminal' },
            { id: 'suggestions', label: '💡 Suggestions Terminal', desc: 'AI suggestions terminal' },
            { id: 'tasks', label: '✅ Tasks Terminal', desc: 'Task management terminal' },
            { id: 'tests', label: '🧪 Tests Terminal', desc: 'Testing framework terminal' },
            { id: 'zeta', label: '🎯 Zeta Terminal', desc: 'Zeta quest system terminal' },
            { id: 'agents', label: '🤖 Agent Orchestrator Terminal', desc: 'Multi-agent orchestrator terminal' },
            { id: 'metrics', label: '📊 Metrics Terminal', desc: 'System metrics terminal' },
            { id: 'anomalies', label: '⚡ Anomalies Terminal', desc: 'Anomaly detection terminal' },
            { id: 'future', label: '🔮 Future Terminal', desc: 'Future planning terminal' },
            { id: 'main', label: '🏠 Main Terminal', desc: 'Main control terminal' }
        ];

        this.scenes.set('main', {
            name: 'Main Menu',
            type: 'menu',
            items: [
                { id: 'agents', label: '🤖 Agent Control Center', desc: 'View & control all AI agents' },
                { id: 'culture_ship', label: '🚢 Culture Ship', desc: 'Autonomous dev orchestrator' },
                { id: 'simulatedverse', label: '🌌 SimulatedVerse', desc: 'Consciousness simulation engine' },
                { id: 'wizard_navigator', label: '🧙 Wizard Navigator', desc: 'Guided system navigation' },
                { id: 'orchestrator', label: '🕹️ Orchestrator', desc: 'System orchestration & meta-automation' },
                { id: 'marble', label: '⚙️ Rube Goldbergian Marble', desc: 'Complex event chain engine' },
                { id: 'antigravity', label: '🛰️ Open Antigravity', desc: 'Experimental physics/gameplay sandbox' },
                { id: 'hacknet', label: '🧬 Hacknet', desc: 'Terminal-first network infiltration workflows' },
                { id: 'hackhub', label: '🕳️ HackHub', desc: 'Collaborative exploit lab and ops board' },
                { id: 'bitburner', label: '🧠 Bitburner', desc: 'Automation scripting and progression mechanics' },
                { id: 'cogmind', label: '🤖 Cogmind', desc: 'Tactical systems simulation and diagnostics' },
                { id: 'path_of_achra', label: '🗡️ Path of Achra', desc: 'Narrative progression and build-crafting layer' },
                { id: 'preset_terminals', label: '🖥️ Preset Terminals', desc: 'Access all agent terminals' },
                { id: 'games', label: '🎮 Game Worlds', desc: 'Enter game universes' },
                { id: 'dashboards', label: '📊 Dashboards & Metrics', desc: 'System monitoring', badge: 'live' },
                { id: 'help', label: '💡 Help & Hints', desc: 'Tips, tutorials, FAQ, and commands', badge: 'quests' },
                { id: 'terminals', label: '⚡ Terminal Hub', desc: 'Shell access & commands' },
                { id: 'browsers', label: '🔍 Context Browsers', desc: 'Repository analysis' },
                { id: 'config', label: '⚙️ Configuration', desc: 'System settings' }
            ]
        });

        // Add top-level scenes for each system (placeholders for now)
        this.scenes.set('culture_ship', {
            name: 'Culture Ship',
            type: 'system-panel',
            parent: 'main',
            systemId: 'culture_ship',
            desc: 'Autonomous development orchestrator',
            doc: '/SimulatedVerse/SimulatedVerse/CULTURE_SHIP_READY.md'
        });
        this.scenes.set('simulatedverse', {
            name: 'SimulatedVerse',
            type: 'system-panel',
            parent: 'main',
            systemId: 'simulatedverse',
            desc: 'Consciousness simulation engine',
            doc: '/SimulatedVerse/SimulatedVerse/DISCOVERY_LOG.md'
        });
        this.scenes.set('wizard_navigator', {
            name: 'Wizard Navigator',
            type: 'system-panel',
            parent: 'main',
            systemId: 'wizard_navigator',
            desc: 'Guided system navigation',
            doc: '/SimulatedVerse/SimulatedVerse/context.md'
        });
        this.scenes.set('orchestrator', {
            name: 'Orchestrator',
            type: 'system-panel',
            parent: 'main',
            systemId: 'orchestrator',
            desc: 'System orchestration & meta-automation',
            doc: '/NuSyQ/README.md'
        });
        this.scenes.set('marble', {
            name: 'Rube Goldbergian Marble',
            type: 'system-panel',
            parent: 'main',
            systemId: 'marble',
            desc: 'Complex event chain engine',
            doc: '/SimulatedVerse/SimulatedVerse/game/engine/cascade_event.py'
        });
        this.scenes.set('antigravity', {
            name: 'Open Antigravity',
            type: 'system-panel',
            parent: 'main',
            systemId: 'antigravity',
            desc: 'Experimental physics/gameplay sandbox',
            doc: '/docs/SYSTEM_MAP.md'
        });
        this.scenes.set('hacknet', {
            name: 'Hacknet',
            type: 'system-panel',
            parent: 'main',
            systemId: 'hacknet',
            desc: 'Terminal-first network infiltration workflows',
            doc: '/docs/OPERATIONS.md'
        });
        this.scenes.set('hackhub', {
            name: 'HackHub',
            type: 'system-panel',
            parent: 'main',
            systemId: 'hackhub',
            desc: 'Collaborative exploit lab and ops board',
            doc: '/docs/ROUTING_RULES.md'
        });
        this.scenes.set('bitburner', {
            name: 'Bitburner',
            type: 'system-panel',
            parent: 'main',
            systemId: 'bitburner',
            desc: 'Automation scripting and progression mechanics',
            doc: '/src/factories/project_factory.py'
        });
        this.scenes.set('cogmind', {
            name: 'Cogmind',
            type: 'system-panel',
            parent: 'main',
            systemId: 'cogmind',
            desc: 'Tactical systems simulation and diagnostics',
            doc: '/src/factories/project_factory.py'
        });
        this.scenes.set('path_of_achra', {
            name: 'Path of Achra',
            type: 'system-panel',
            parent: 'main',
            systemId: 'path_of_achra',
            desc: 'Narrative progression and build-crafting layer',
            doc: '/src/factories/project_factory.py'
        });

        // Add Preset Terminals scene
        this.scenes.set('preset_terminals', {
            name: 'Preset Terminals',
            type: 'preset-terminals',
            parent: 'main',
            terminals: presetTerminals
        });

        // Agent Control Center - View all agents, their status, click to see terminals
        this.scenes.set('agents', {
            name: 'Agent Control Center',
            type: 'agent-grid',
            parent: 'main',
            agents: [] // populated from guild_board.json at render time
        });

        // Game Worlds Menu
        this.scenes.set('games', {
            name: 'Game Worlds',
            type: 'menu',
            parent: 'main',
            items: [
                { id: 'idle', label: '🌱 Cultivation Idle', desc: 'Incremental cultivation sandbox', status: 'playable' },
                { id: 'house_of_leaves', label: '🏚️ House of Leaves', desc: 'Recursive debugging maze', status: 'scaffold' },
                { id: 'tower_defense', label: '🗼 Tower Defense', desc: 'Defend codebase from bugs', status: 'planned' },
                { id: 'rpg', label: '⚔️ RPG Adventure', desc: 'Quest through the repository', status: 'planned' },
                { id: 'roguelike', label: '🎲 ASCII Roguelike', desc: 'Procedural dungeon crawler', status: 'planned' }
            ]
        });

        // Dashboards & Metrics
        this.scenes.set('dashboards', {
            name: 'Dashboards & Metrics',
            type: 'menu',
            parent: 'main',
            items: [
                { id: 'culture_ship', label: '🌌 Culture Ship Dashboard', desc: 'Autonomous healing cycles', url: '/api/dashboard/api/health' },
                { id: 'guild_board', label: '👥 Guild Board', desc: 'Multi-agent coordination', file: 'guild_board.html' },
                { id: 'cultivation_metrics', label: '🌱 Cultivation Metrics', desc: 'System growth tracking', file: 'dashboard.html' },
                { id: 'sns_metrics', label: '📈 SNS-Core Metrics', desc: 'Token savings & performance', endpoint: '/metrics' },
                { id: 'quest_tracker', label: '📜 Quest Tracker', desc: 'Active quests & progression', endpoint: '/quests', badge: 'quests' }
            ]
        });

        // Dashboard sub-scenes
        this.scenes.set('guild_board', {
            name: 'Guild Board',
            type: 'static-link',
            parent: 'dashboards',
            file: 'guild_board.html',
            description: 'Multi-agent coordination board',
        });

        this.scenes.set('cultivation_metrics', {
            name: 'Cultivation Metrics',
            type: 'static-link',
            parent: 'dashboards',
            file: 'dashboard.html',
            description: 'System growth tracking',
        });

        this.scenes.set('sns_metrics', {
            name: 'SNS-Core Metrics',
            type: 'data-feed',
            parent: 'dashboards',
            endpoint: '/api/metrics',
            description: 'Token savings & performance',
        });

        this.scenes.set('quest_tracker', {
            name: 'Quest Tracker',
            type: 'data-feed',
            parent: 'dashboards',
            endpoint: '/api/quests',
            description: 'Active quests & progression',
        });

        // Help & Hints
        this.scenes.set('help', {
            name: 'Help & Hints',
            type: 'menu',
            parent: 'main',
            items: [
                { id: 'hints', label: '💡 Hints', desc: 'Quick contextual hints', endpoint: '/hints' },
                { id: 'tutorials', label: '📘 Tutorials', desc: 'Step-by-step guides', endpoint: '/tutorials' },
                { id: 'faq', label: '❓ FAQ', desc: 'Frequently asked questions', endpoint: '/faq' },
                { id: 'commands', label: '⌨️ Commands', desc: 'Available commands & scripts', endpoint: '/commands' },
                { id: 'fl1ght', label: '🛰️ fl1ght.exe Smart Search', desc: 'Search tips & smart search helper', endpoint: '/ops' }
            ]
        });

        // Terminal Hub - Access to different terminal types
        this.scenes.set('terminals', {
            name: 'Terminal Hub',
            type: 'menu',
            parent: 'main',
            items: [
                { id: 'quantum_terminal', label: '⚡ Quantum Terminal', desc: 'Main system commands', builtin: true },
                { id: 'shell-wsl', label: '🐧 WSL Ubuntu', desc: 'Windows Subsystem for Linux', shellChannel: 'shell-wsl' },
                { id: 'shell-pwsh', label: '💻 PowerShell', desc: 'Windows PowerShell', shellChannel: 'shell-pwsh' },
                { id: 'shell-cmd', label: '⌨️ Command Prompt', desc: 'Windows CMD', shellChannel: 'shell-cmd' }
            ]
        });

        // Context Browsers
        this.scenes.set('browsers', {
            name: 'Context Browsers',
            type: 'menu',
            parent: 'main',
            items: [
                { id: 'enhanced_browser', label: '🔍 Enhanced Context Browser', desc: 'Full repository analysis', streamlit: 'Enhanced-Interactive-Context-Browser-Fixed.py' },
                { id: 'wizard_navigator', label: '🧙 Wizard Navigator', desc: 'Guided exploration', streamlit: 'Enhanced-Wizard-Navigator.py' },
                { id: 'interactive_browser', label: '📂 Interactive Browser', desc: 'Quick file explorer', streamlit: 'Interactive-Context-Browser.py' },
                { id: 'file_tree', label: '🌳 File Tree View', desc: 'Directory structure', builtin: true }
            ]
        });

        // Configuration & Settings
        this.scenes.set('config', {
            name: 'Configuration',
            type: 'settings',
            parent: 'main',
            sections: [
                {
                    name: 'Model Selection',
                    settings: [
                        { id: 'default_model', label: 'Default Chat Model', type: 'select', options: ['copilot', 'ollama', 'lmstudio', 'chatdev'] },
                        { id: 'ollama_model', label: 'Ollama Model', type: 'select', options: ['llama3.2', 'codellama', 'mistral', 'neural-chat'] },
                        { id: 'auto_switch', label: 'Auto-switch on failure', type: 'checkbox' }
                    ]
                },
                {
                    name: 'Terminal Settings',
                    settings: [
                        { id: 'default_shell', label: 'Default Shell', type: 'select', options: ['quantum', 'wsl', 'powershell', 'cmd'] },
                        { id: 'enable_wsl', label: 'Enable WSL Integration', type: 'checkbox' },
                        { id: 'terminal_theme', label: 'Terminal Theme', type: 'select', options: ['dark', 'light', 'quantum', 'matrix'] }
                    ]
                },
                {
                    name: 'UI Preferences',
                    settings: [
                        { id: 'quantum_effects', label: 'Quantum Visual Effects', type: 'checkbox' },
                        { id: 'auto_refresh', label: 'Auto-refresh Dashboards', type: 'checkbox' },
                        { id: 'refresh_interval', label: 'Refresh Interval (ms)', type: 'number', min: 1000, max: 60000 }
                    ]
                }
            ]
        });

        // Individual Game Scenes
        this.initializeGameScenes();
    }

    initializeGameScenes() {
        // Cultivation Idle Game
        this.scenes.set('idle', {
            name: 'Cultivation Idle',
            type: 'game',
            parent: 'games',
            engine: 'cultivation-idle',
            resources: ['consciousness', 'quantum_energy', 'neural_pathways', 'wisdom'],
            upgrades: true,
            prestige: true,
            automation: true
        });

        // House of Leaves Maze
        this.scenes.set('house_of_leaves', {
            name: 'House of Leaves',
            type: 'game',
            parent: 'games',
            engine: 'maze-navigator',
            pythonModule: 'src.games.house_of_leaves',
            status: 'scaffold'
        });
    }

    // Navigate to a scene
    navigate(sceneId, data = {}) {
        const scene = this.scenes.get(sceneId);
        if (!scene) {
            console.error(`Scene not found: ${sceneId}`);
            return;
        }

        // Add to history
        if (this.activeScene) {
            this.history.push(this.activeScene);
        }

        this.activeScene = sceneId;
        this.renderScene(scene, data);
    }

    // Go back to previous scene
    back() {
        if (this.history.length > 0) {
            const previousScene = this.history.pop();
            this.activeScene = previousScene;
            this.renderScene(this.scenes.get(previousScene));
        } else if (this.activeScene !== 'main') {
            // Go to parent or main
            const scene = this.scenes.get(this.activeScene);
            this.navigate(scene.parent || 'main');
        }
    }

    // Render a scene
    renderScene(scene, data = {}) {
        // If the scene definition was passed by id, resolve
        if (typeof scene === 'string') {
            scene = this.scenes.get(scene);
        }
        const container = document.getElementById('scene-container') || this.createSceneContainer();

        switch (scene.type) {
            case 'menu':
                this.renderMenu(container, scene);
                break;
            case 'agent-grid':
                this.renderAgentGrid(container, scene);
                break;
            case 'game':
                this.renderGame(container, scene, data);
                break;
            case 'settings':
                this.renderSettings(container, scene);
                break;
            case 'preset-terminals':
                this.renderPresetTerminals(container, scene);
                break;
            case 'system-panel':
                this.renderSystemPanel(container, scene, this.activeScene);
                break;
            case 'data-feed':
                this.renderDataFeed(container, scene);
                break;
            case 'static-link':
                this.renderStaticLink(container, scene);
                break;
            default:
                this.renderGeneric(container, scene);
        }
    }

    async renderSystemPanel(container, scene, sceneId = null) {
        // Show loading first with game-like layout
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div style="margin-top: 20px; color: #fff;">
                <div style="font-size: 16px; margin-bottom: 10px;">${scene.desc || ''}</div>
                <div style="margin-bottom: 20px;">
                    <a href="${scene.doc}" target="_blank" style="color: #4ade80; text-decoration: underline;">Documentation / Source</a>
                </div>

                <!-- System Status Block -->
                <div id="system-status-block" style="font-size: 14px; color: #aaa; margin-bottom: 20px; padding: 15px; background: rgba(102,126,234,0.1); border-radius: 8px;">
                    Loading system status...
                </div>

                <!-- Game Progression Block -->
                <div id="game-progress-block" style="font-size: 14px; color: #aaa; margin-bottom: 20px; padding: 15px; background: rgba(74,222,128,0.1); border-radius: 8px;">
                    Loading progression...
                </div>

                <!-- Quick Actions Block -->
                <div id="quick-actions-block" style="font-size: 14px; margin-top: 20px;">
                    <h4 style="color: #667eea; margin-bottom: 10px;">⚡ Quick Actions</h4>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button onclick="sceneRouter.executeAction('scan')" style="padding: 8px 16px; background: rgba(102,126,234,0.3); border: 1px solid rgba(102,126,234,0.5); border-radius: 6px; color: #fff; cursor: pointer;">🔍 Scan</button>
                        <button onclick="sceneRouter.executeAction('heal')" style="padding: 8px 16px; background: rgba(74,222,128,0.3); border: 1px solid rgba(74,222,128,0.5); border-radius: 6px; color: #fff; cursor: pointer;">💚 Heal</button>
                        <button onclick="sceneRouter.executeAction('suggest')" style="padding: 8px 16px; background: rgba(251,191,36,0.3); border: 1px solid rgba(251,191,36,0.5); border-radius: 6px; color: #fff; cursor: pointer;">💡 Suggest</button>
                        <button onclick="sceneRouter.navigate('help')" style="padding: 8px 16px; background: rgba(168,85,247,0.3); border: 1px solid rgba(168,85,247,0.5); border-radius: 6px; color: #fff; cursor: pointer;">❓ Help</button>
                    </div>
                </div>
            </div>
        `;

        // Fetch live status from backend
        try {
            const systemId = scene.systemId || sceneId || scene.id || scene.name.toLowerCase().replace(/\s+/g, '_');
            const resp = await fetch(`${this.apiBase}/api/systems/${encodeURIComponent(systemId)}/status`);
            if (resp.ok) {
                const status = await resp.json();
                document.getElementById('system-status-block').innerHTML = `
                    <h4 style="color: #667eea; margin: 0 0 10px 0;">📊 System Status</h4>
                    <b>Status:</b> <span style="color: ${status.status === 'online' ? '#4ade80' : '#ef4444'}; font-weight: bold;">${status.status}</span><br>
                    <b>Detail:</b> ${status.detail || ''}<br>
                    <b>Timestamp:</b> <span style="color: #aaa;">${status.timestamp}</span>
                `;
            } else {
                document.getElementById('system-status-block').innerHTML = `<span style="color: #ef4444;">Failed to fetch system status.</span>`;
            }
        } catch (e) {
            document.getElementById('system-status-block').innerHTML = `<span style="color: #ef4444;">Error: ${e.message}</span>`;
        }

        // Fetch game progression
        try {
            const progResp = await fetch(`${this.apiBase}/api/progress`);
            if (progResp.ok) {
                const prog = await progResp.json();
                const consciousnessBar = '█'.repeat(Math.floor(prog.consciousness_score / 10)) + '░'.repeat(10 - Math.floor(prog.consciousness_score / 10));
                document.getElementById('game-progress-block').innerHTML = `
                    <h4 style="color: #4ade80; margin: 0 0 10px 0;">🎮 Game Progression</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>⭐ Evolution Level: <b>${prog.evolution_level}</b>/5</div>
                        <div>🏛️ Temple Floor: <b>${prog.temple_floor}</b>/10</div>
                        <div>📜 Quests Completed: <b>${prog.quests_completed}</b></div>
                        <div>🔓 Skills Unlocked: <b>${prog.skills_unlocked}</b></div>
                    </div>
                    <div style="margin-top: 10px;">
                        🧠 Consciousness: [<span style="color: #4ade80;">${consciousnessBar}</span>] ${prog.consciousness_score.toFixed(1)}%
                    </div>
                    ${prog.achievements.length > 0 ? `
                        <div style="margin-top: 10px;">
                            🏆 Achievements: ${prog.achievements.map(a => `<span style="color: #fbbf24; margin-right: 8px;">✓ ${a}</span>`).join('')}
                        </div>
                    ` : ''}
                `;
            } else {
                document.getElementById('game-progress-block').innerHTML = `<span style="color: #aaa;">Progression data unavailable</span>`;
            }
        } catch (e) {
            document.getElementById('game-progress-block').innerHTML = `<span style="color: #aaa;">Progression: ${e.message}</span>`;
        }
    }

    // Execute a quick action and show result
    async executeAction(actionName) {
        try {
            const resp = await fetch(`${this.apiBase}/api/actions/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: actionName, dry_run: false })
            });
            if (resp.ok) {
                const result = await resp.json();
                alert(`✅ ${result.message}\n\nXP Earned: +${result.xp_earned}`);
            } else {
                alert(`❌ Action failed: ${resp.status}`);
            }
        } catch (e) {
            alert(`❌ Error: ${e.message}`);
        }
    }

    renderPresetTerminals(container, scene) {
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div class="preset-terminals-list" style="margin-top: 20px;">
                ${scene.terminals.map(term => `
                    <div class="preset-terminal-item" onclick="sceneRouter.openAgentTerminal('${term.id}')"
                         style="
                            padding: 15px;
                            margin: 10px 0;
                            background: rgba(102, 126, 234, 0.1);
                            border: 1px solid rgba(102, 126, 234, 0.3);
                            border-radius: 8px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                         "
                         onmouseover="this.style.background='rgba(102, 126, 234, 0.2)'; this.style.borderColor='rgba(102, 126, 234, 0.6)';"
                         onmouseout="this.style.background='rgba(102, 126, 234, 0.1)'; this.style.borderColor='rgba(102, 126, 234, 0.3)';">
                        <div style="font-size: 18px; color: #fff; margin-bottom: 5px;">
                            ${term.label}
                        </div>
                        <div style="font-size: 12px; color: rgba(255, 255, 255, 0.6);">
                            ${term.desc}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    createSceneContainer() {
        // Create overlay container for scenes
        const container = document.createElement('div');
        container.id = 'scene-container';
        container.className = 'scene-container';
        container.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            width: 400px;
            max-height: 80vh;
            background: linear-gradient(135deg, rgba(20, 20, 30, 0.98), rgba(40, 20, 60, 0.95));
            border: 2px solid rgba(102, 126, 234, 0.6);
            border-radius: 12px;
            padding: 20px;
            z-index: 1000;
            overflow-y: auto;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(10px);
        `;
        document.body.appendChild(container);
        return container;
    }

    renderMenu(container, scene) {
        // Delegate to the async renderer which handles dashboards and dynamic panels.
        return this.renderMenuAsync(container, scene);
    }

    renderAgentGrid(container, scene) {
        // Lazy-load guild board to populate agents
        if (!scene.agents || scene.agents.length === 0) {
            this.loadGuildBoardAgents().then(agents => {
                if (agents && agents.length > 0) {
                    scene.agents = agents;
                    this.renderAgentGrid(container, scene); // re-render with data
                    return;
                }
            });
        }

        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div class="agent-grid" style="margin-top: 20px;">
                ${scene.agents.map(agent => `
                    <div class="agent-card" style="
                        padding: 15px;
                        margin: 10px 0;
                        background: rgba(${agent.status === 'online' ? '74, 222, 128' : '239, 68, 68'}, 0.1);
                        border: 1px solid rgba(${agent.status === 'online' ? '74, 222, 128' : '239, 68, 68'}, 0.3);
                        border-radius: 8px;
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 16px; color: #fff; font-weight: bold;">
                                    ${agent.name}
                                </div>
                                <div style="font-size: 12px; color: rgba(255, 255, 255, 0.6); margin-top: 3px;">
                                    ${agent.model} · <span style="color: ${agent.status === 'online' ? '#4ade80' : '#ef4444'};">${agent.status}</span>
                                </div>
                            </div>
                            <div style="
                                width: 12px;
                                height: 12px;
                                background: ${agent.status === 'online' ? '#4ade80' : '#ef4444'};
                                border-radius: 50%;
                                ${agent.status === 'online' ? 'animation: pulse 2s ease-in-out infinite;' : ''}
                            "></div>
                        </div>
                        ${agent.endpoint ? `<div style="font-size: 11px; color: rgba(255, 255, 255, 0.4); margin-top: 8px;">${agent.endpoint}</div>` : ''}
                        <div class="agent-actions" style="margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                            ${agent.actions.map(action => `
                                <button onclick="sceneRouter.agentAction('${agent.id}', '${action}')"
                                    style="
                                        padding: 6px 12px;
                                        background: rgba(102, 126, 234, 0.2);
                                        border: 1px solid rgba(102, 126, 234, 0.4);
                                        border-radius: 4px;
                                        color: #667eea;
                                        font-size: 11px;
                                        cursor: pointer;
                                        transition: all 0.2s;
                                    "
                                    onmouseover="this.style.background='rgba(102, 126, 234, 0.3)'"
                                    onmouseout="this.style.background='rgba(102, 126, 234, 0.2)'">
                                    ${action.replaceAll('_', ' ').toUpperCase()}
                                </button>
                            `).join('')}
                        </div>
                        ${agent.models ? `
                            <div style="margin-top: 10px;">
                                <select id="model-select-${agent.id}" style="
                                    width: 100%;
                                    padding: 6px;
                                    background: rgba(0, 0, 0, 0.3);
                                    border: 1px solid rgba(102, 126, 234, 0.3);
                                    border-radius: 4px;
                                    color: #fff;
                                    font-size: 12px;
                                ">
                                    ${agent.models.map(model => `<option value="${model}">${model}</option>`).join('')}
                                </select>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    async loadGuildBoardAgents() {
        if (this.guildBoardAgents) return this.guildBoardAgents;

        // Try API endpoints first (preferred), then fall back to static files
        const apiSources = [
            `${this.apiBase}/api/agents`,
            `${this.apiBase}/api/guild/summary`
        ];

        // Try /api/agents endpoint first
        try {
            const resp = await fetch(`${this.apiBase}/api/agents`);
            if (resp.ok) {
                const agents = await resp.json();
                this.guildBoardAgents = agents.map(a => ({
                    id: a.id,
                    name: a.name,
                    model: a.model || a.id,
                    status: a.status || 'unknown',
                    terminal: true,
                    endpoint: a.endpoint || '',
                    lastActivity: null,
                    actions: ['view_terminal', 'restart', 'configure']
                }));
                return this.guildBoardAgents;
            }
        } catch (error) {
            console.warn('API agents endpoint failed:', error);
        }

        // Try /api/guild/summary endpoint
        try {
            const resp = await fetch(`${this.apiBase}/api/guild/summary`);
            if (resp.ok) {
                const summary = await resp.json();
                // Extract agent count info for display
                if (summary.agents_online !== undefined) {
                    // Create placeholder agents based on summary
                    this.guildBoardAgents = [
                        { id: 'copilot', name: 'Copilot', model: 'gpt-copilot', status: 'online', terminal: true, endpoint: '/terminals/copilot', actions: ['view_terminal', 'restart', 'configure'] },
                        { id: 'ollama', name: 'Ollama', model: 'qwen2.5-coder', status: 'online', terminal: true, endpoint: '/terminals/ollama', actions: ['view_terminal', 'restart', 'configure'] },
                        { id: 'chatdev', name: 'ChatDev', model: 'chatdev-ensemble', status: 'idle', terminal: true, endpoint: '/terminals/chatdev', actions: ['view_terminal', 'restart', 'configure'] },
                        { id: 'claude', name: 'Claude', model: 'claude-3.5-sonnet', status: 'online', terminal: true, endpoint: '/terminals/claude', actions: ['view_terminal', 'restart', 'configure'] },
                        { id: 'ai_council', name: 'AI Council', model: 'ensemble', status: 'idle', terminal: true, endpoint: '/terminals/ai_council', actions: ['view_terminal', 'restart', 'configure'] }
                    ];
                    return this.guildBoardAgents;
                }
            }
        } catch (error) {
            console.warn('Guild summary endpoint failed:', error);
        }

        // Fall back to static file sources
        const staticSources = [
            '/state/guild/guild_board.json',
            '/docs/guild_board.json'
        ];

        for (const src of staticSources) {
            try {
                const resp = await fetch(src);
                if (!resp.ok) continue;
                const board = await resp.json();
                const agents = board?.agents || {};
                this.guildBoardAgents = Object.keys(agents).map(id => {
                    const a = agents[id] || {};
                    return {
                        id,
                        name: a.agent_id || id,
                        model: a.agent_id || id,
                        status: a.status || 'unknown',
                        terminal: true,
                        endpoint: a.endpoint || '',
                        lastActivity: a.timestamp || null,
                        actions: ['view_terminal', 'restart', 'configure']
                    };
                });
                return this.guildBoardAgents;
            } catch (error) {
                console.warn(`Guild board load failed from ${src}:`, error);
            }
        }

        // Ultimate fallback with default agents
        this.guildBoardAgents = [
            { id: 'copilot', name: 'Copilot', model: 'gpt-copilot', status: 'offline', terminal: true, endpoint: '', actions: ['view_terminal'] },
            { id: 'ollama', name: 'Ollama', model: 'local', status: 'offline', terminal: true, endpoint: '', actions: ['view_terminal'] },
            { id: 'chatdev', name: 'ChatDev', model: 'ensemble', status: 'offline', terminal: true, endpoint: '', actions: ['view_terminal'] }
        ];
        return this.guildBoardAgents;
    }

    renderSettings(container, scene) {
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div class="settings-sections" style="margin-top: 20px;">
                ${scene.sections.map(section => `
                    <div class="settings-section" style="margin-bottom: 25px;">
                        <h3 style="color: rgba(255, 255, 255, 0.9); font-size: 14px; margin-bottom: 12px;">
                            ${section.name}
                        </h3>
                        ${section.settings.map(setting => this.renderSetting(setting)).join('')}
                    </div>
                `).join('')}
                <button onclick="sceneRouter.saveSettings()" style="
                    width: 100%;
                    padding: 12px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none;
                    border-radius: 6px;
                    color: #fff;
                    font-weight: bold;
                    cursor: pointer;
                    margin-top: 20px;
                ">Save Settings</button>
            </div>
        `;
    }

    renderSetting(setting) {
        let input = '';
        switch (setting.type) {
            case 'select':
                input = `
                    <select id="setting-${setting.id}" style="
                        width: 100%;
                        padding: 8px;
                        background: rgba(0, 0, 0, 0.3);
                        border: 1px solid rgba(102, 126, 234, 0.3);
                        border-radius: 4px;
                        color: #fff;
                    ">
                        ${setting.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                    </select>
                `;
                break;
            case 'checkbox':
                input = `
                    <input type="checkbox" id="setting-${setting.id}" style="
                        width: 20px;
                        height: 20px;
                        cursor: pointer;
                    ">
                `;
                break;
            case 'number':
                input = `
                    <input type="number" id="setting-${setting.id}"
                        min="${setting.min || 0}"
                        max="${setting.max || 100}"
                        style="
                            width: 100%;
                            padding: 8px;
                            background: rgba(0, 0, 0, 0.3);
                            border: 1px solid rgba(102, 126, 234, 0.3);
                            border-radius: 4px;
                            color: #fff;
                        ">
                `;
                break;
        }

        return `
            <div class="setting-item" style="margin-bottom: 15px;">
                <label style="color: rgba(255, 255, 255, 0.7); font-size: 13px; display: block; margin-bottom: 6px;">
                    ${setting.label}
                </label>
                ${input}
            </div>
        `;
    }

    async renderMenuAsync(container, scene) {
        // Special handling for Dashboards & Metrics
        if (scene.name === 'Dashboards & Metrics') {
            container.innerHTML = `
                <div class="scene-header">
                    <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                    <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
                </div>
                <div class="dashboard-panels" style="margin-top: 20px;">
                    <div id="culture-ship-dashboard" style="margin-bottom: 30px;">
                        <h3 style="color: #4ade80;">🌌 Culture Ship Dashboard</h3>
                        <div id="culture-ship-health">Loading health data...</div>
                    </div>
                    <div id="metrics-panel" style="margin-bottom: 30px;">
                        <h3 style="color: #4ade80;">📊 System Metrics</h3>
                        <div id="system-metrics">Loading metrics...</div>
                    </div>
                </div>
            `;
            // Fetch and display health data
            try {
                const resp = await fetch(`${this.apiBase}/api/health`);
                if (resp.ok) {
                    const health = await resp.json();
                    document.getElementById('culture-ship-health').innerHTML = `
                        <b>Status:</b> <span style="color: ${health.overall_status === 'healthy' ? '#4ade80' : '#ef4444'}; font-weight: bold;">${health.overall_status}</span><br>
                        <b>Uptime:</b> ${health.system.uptime_seconds}s<br>
                        <b>Last Heartbeat:</b> <span style="color: #aaa;">${health.system.last_heartbeat}</span>
                        <br><b>Problems:</b> ${health.problems ? JSON.stringify(health.problems) : 'N/A'}
                    `;
                } else {
                    document.getElementById('culture-ship-health').innerHTML = `<span style="color: #ef4444;">Failed to fetch health data.</span>`;
                }
            } catch (e) {
                document.getElementById('culture-ship-health').innerHTML = `<span style="color: #ef4444;">Error: ${e.message}</span>`;
            }
            // Example metrics panel (expand as needed)
            try {
                const metricsResp = await fetch(`${this.apiBase}/api/metrics`);
                if (metricsResp.ok) {
                    const metrics = await metricsResp.json();
                    const util = metrics.system_utilization || {};
                    document.getElementById('system-metrics').innerHTML = `
                        <b>Metrics:</b> <br>
                        <ul>
                            <li>Agents Online: <span style="color:#4ade80;">${metrics.agents_online}</span></li>
                            <li>Active Quests: <span style="color:#4ade80;">${metrics.active_quests}</span></li>
                            <li>Quests: <span style="color:#4ade80;">${util.actionable_quests || 0} actionable</span> /
                                <span style="color:#f87171;">${util.blocked_quests || 0} blocked</span> /
                                ${util.total_quests || 0} total</li>
                            <li>PU Queue: queued ${util.queued_pus || 0} · executing ${util.executing_pus || 0} · done ${util.completed_pus || 0}</li>
                            <li>System Utilization: CPU ${util.cpu_percent}% · MEM ${util.mem_percent}%</li>
                        </ul>
                    `;
                } else {
                    document.getElementById('system-metrics').innerHTML = `<span style="color: #ef4444;">Failed to fetch metrics.</span>`;
                }
            } catch (e) {
                document.getElementById('system-metrics').innerHTML = `<span style="color: #ef4444;">Error loading metrics: ${e.message}</span>`;
            }
            return;
        }

        // Special handling for Help & Hints
        if (scene.name === 'Help & Hints' || scene.id === 'help') {
            container.innerHTML = `
                <div class="scene-header">
                    <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                    <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
                </div>
                <div class="help-sections" style="margin-top: 20px;">
                    <div style="margin-bottom: 12px;">
                        <input id="help-search" placeholder="Search hints, commands, FAQ..." style="width:100%; padding:8px; border-radius:6px; border:1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.2); color: #fff;" />
                    </div>
                    <div id="help-results">
                        <h3 style="color: #4ade80;">Loading help content...</h3>
                    </div>
                </div>
            `;

            const resultsDiv = document.getElementById('help-results');

            // Fetch hints, tutorials, faq, commands, and smart search suggestions in parallel
            Promise.all([
                fetch(`${this.apiBase}/api/hints`).then(r => r.ok ? r.json() : []).catch(() => []),
                fetch(`${this.apiBase}/api/tutorials`).then(r => r.ok ? r.json() : []).catch(() => []),
                fetch(`${this.apiBase}/api/faq`).then(r => r.ok ? r.json() : []).catch(() => []),
                fetch(`${this.apiBase}/api/commands`).then(r => r.ok ? r.json() : []).catch(() => []),
                fetch(`${this.apiBase}/api/ops`).then(r => r.ok ? r.json() : []).catch(() => []),
                fetch(`${this.apiBase}/api/metrics`).then(r => r.ok ? r.json() : null).catch(() => null)
            ]).then(([hints, tutorials, faq, commands, ops, metrics]) => {
                // Update menu badges with quest counts if available
                const questBadge = document.getElementById('badge-help');
                if (questBadge) {
                    const actionable = metrics?.system_utilization?.actionable_quests ?? hints.length ?? 0;
                    const blocked = metrics?.system_utilization?.blocked_quests ?? 0;
                    questBadge.textContent = `${actionable} ready / ${blocked} blocked`;
                }

                const dashBadge = document.getElementById('badge-dashboards');
                if (dashBadge && metrics?.system_utilization) {
                    dashBadge.textContent = `PU q:${metrics.system_utilization.queued_pus || 0}`;
                }

                const questTrackerBadge = document.getElementById('badge-quest_tracker');
                if (questTrackerBadge && metrics?.system_utilization) {
                    questTrackerBadge.textContent = `${metrics.system_utilization.total_quests || 0} quests`;
                }

                const makeList = (title, items, renderFn) => `
                    <div style="margin-bottom:18px;">
                        <h4 style="color:#667eea; margin:6px 0;">${title}</h4>
                        <div style="font-size:13px; color: #ddd;">
                            ${items.map(it => renderFn(it)).join('')}
                        </div>
                    </div>
                `;

                const hintsHtml = makeList('Hints', hints, h => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <b>${h.title}</b><div style="font-size:12px; color:#aaa; margin-top:4px;">${h.text}</div>
                    </div>
                `);

                const tutorialsHtml = makeList('Tutorials', tutorials, t => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <b>${t.title}</b>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${(t.steps || []).slice(0,3).map(s => `<div>• ${s}</div>`).join('')}</div>
                    </div>
                `);

                const faqHtml = makeList('FAQ', faq, f => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <b>${f.question}</b>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${f.answer}</div>
                    </div>
                `);

                const commandsHtml = makeList('Commands', commands, c => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <code style="color:#9ae6b4;">${c.command}</code>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${c.description}${c.example ? ` — <span style=\"color:#7dd3fc;\">${c.example}</span>` : ''}</div>
                    </div>
                `);
                const smartHtml = makeList('Smart Search (fl1ght.exe)', ops, o => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <code style="color:#9ae6b4;">${o.command}</code>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${o.description}${o.example ? ` — <span style=\"color:#7dd3fc;\">${o.example}</span>` : ''}</div>
                    </div>
                `);
                resultsDiv.innerHTML = `${smartHtml}${hintsHtml}${tutorialsHtml}${faqHtml}${commandsHtml}`;

                // Simple client-side search
                const searchInput = document.getElementById('help-search');
                const renderHint = h => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <b>${h.title}</b><div style="font-size:12px; color:#aaa; margin-top:4px;">${h.text}</div>
                    </div>
                `;
                const renderTutorial = t => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <b>${t.title}</b>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${(t.steps || []).slice(0,3).map(s => `<div>• ${s}</div>`).join('')}</div>
                    </div>
                `;
                const renderFaq = f => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <b>${f.question}</b>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${f.answer}</div>
                    </div>
                `;
                const renderCommand = c => `
                    <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                        <code style="color:#9ae6b4;">${c.command}</code>
                        <div style="font-size:12px; color:#aaa; margin-top:4px;">${c.description}${c.example ? ` — <span style=\"color:#7dd3fc;\">${c.example}</span>` : ''}</div>
                    </div>
                `;

                searchInput.addEventListener('input', async (e) => {
                    const q = e.target.value.trim();
                    if (!q) {
                        resultsDiv.innerHTML = `${smartHtml}${hintsHtml}${tutorialsHtml}${faqHtml}${commandsHtml}`;
                        return;
                    }

                    // Server-side search for smarter, unified results
                    try {
                        const resp = await fetch(`${this.apiBase}/api/search?q=${encodeURIComponent(q)}`);
                        if (resp.ok) {
                            const data = await resp.json();
                            if (!data || data.length === 0) {
                                resultsDiv.innerHTML = `<div style="color:#ddd;">No results for "${q}"</div>`;
                                return;
                            }
                            // Render search results as command-like entries
                            const resultsHtml = `
                                <div style="margin-bottom:18px;">
                                    <h4 style="color:#667eea; margin:6px 0;">Search Results</h4>
                                    <div style="font-size:13px; color: #ddd;">
                                        ${data.map(c => `
                                            <div style="padding:8px; border-radius:6px; margin-bottom:6px; background: rgba(255,255,255,0.02);">
                                                <code style="color:#9ae6b4;">${c.command}</code>
                                                <div style="font-size:12px; color:#aaa; margin-top:4px;">${c.description}${c.example ? ` — <span style=\"color:#7dd3fc;\">${c.example}</span>` : ''}</div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `;
                            resultsDiv.innerHTML = resultsHtml;
                            return;
                        }
                        resultsDiv.innerHTML = `<div style="color:#ef4444;">Search request failed: ${resp.status}</div>`;
                    } catch (err) {
                        // Fallback to client-side filtering if server search fails
                        const ql = q.toLowerCase();
                        const filter = (list) => list.filter(i => JSON.stringify(i).toLowerCase().includes(ql));
                        const filteredHintsHtml = makeList('Hints', filter(hints), renderHint);
                        const filteredTutorialsHtml = makeList('Tutorials', filter(tutorials), renderTutorial);
                        const filteredFaqHtml = makeList('FAQ', filter(faq), renderFaq);
                        const filteredCommandsHtml = makeList('Commands', filter(commands), renderCommand);
                        resultsDiv.innerHTML = `${filteredHintsHtml}${filteredTutorialsHtml}${filteredFaqHtml}${filteredCommandsHtml}`;
                    }
                });

                // Attach evolve trigger to global router
                this.triggerEvolve = async function () {
                    const prompt = document.getElementById('evolve-prompt')?.value || '';
                    const resultDiv = document.getElementById('evolve-result');
                    resultDiv.innerHTML = 'Running evolve...';
                    try {
                        const resp = await fetch(`${this.apiBase}/api/evolve`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt })
                        });
                        if (resp.ok) {
                            const data = await resp.json();
                            resultDiv.innerHTML = `Saved: ${data.file}`;
                        } else {
                            const txt = await resp.text();
                            resultDiv.innerHTML = `Failed: ${resp.status} ${txt}`;
                        }
                    } catch (err) {
                        resultDiv.innerHTML = `Error: ${err.message}`;
                    }
                };
            }).catch(err => {
                resultsDiv.innerHTML = `<div style="color:#ef4444;">Failed to load help content: ${err.message || err}</div>`;
            });

            return;
        }
        // Build onclick handler based on item properties
        const getItemOnClick = (item) => {
            // Shell terminal channel (WSL, PowerShell, CMD)
            if (item.shellChannel) {
                return `sceneRouter.openShellTerminal('${item.shellChannel}', '${item.label}')`;
            }
            // API endpoint - open as JSON dashboard
            if (item.endpoint) {
                return `sceneRouter.openDashboard('${item.id}', '${item.label}', '/api${item.endpoint}')`;
            }
            // Direct URL - open as JSON dashboard
            if (item.url) {
                return `sceneRouter.openDashboard('${item.id}', '${item.label}', '${item.url}')`;
            }
            // Static HTML file - open in iframe
            if (item.file) {
                return `sceneRouter.openStaticDashboard('${item.id}', '${item.label}', '${item.file}')`;
            }
            // Streamlit app - open external Streamlit
            if (item.streamlit) {
                return `sceneRouter.openStreamlitApp('${item.id}', '${item.label}', '${item.streamlit}')`;
            }
            // Builtin scene - navigate normally
            if (item.builtin) {
                return `sceneRouter.handleBuiltinScene('${item.id}')`;
            }
            // Default: navigate to scene
            return `sceneRouter.navigate('${item.id}')`;
        };

        container.innerHTML = `
            <div class="scene-header">
                ${scene.parent ? '<button class="back-btn" onclick="sceneRouter.back()">← Back</button>' : ''}
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div class="menu-items" style="margin-top: 20px;">
                ${scene.items.map(item => `
                    <div class="menu-item" onclick="${getItemOnClick(item)}"
                         style="
                            padding: 15px;
                            margin: 10px 0;
                            background: rgba(102, 126, 234, 0.1);
                            border: 1px solid rgba(102, 126, 234, 0.3);
                            border-radius: 8px;
                            cursor: pointer;
                            transition: all 0.3s ease;
                         "
                         onmouseover="this.style.background='rgba(102, 126, 234, 0.2)'; this.style.borderColor='rgba(102, 126, 234, 0.6)';"
                         onmouseout="this.style.background='rgba(102, 126, 234, 0.1)'; this.style.borderColor='rgba(102, 126, 234, 0.3)';">
                        <div style="font-size: 18px; color: #fff; margin-bottom: 5px;">
                            ${item.label} ${item.badge ? `<span id="badge-${item.id}" style="font-size:12px;color:#4ade80;background:rgba(74,222,128,0.15);padding:2px 6px;border-radius:6px;vertical-align:middle;">${item.badge}</span>` : ''}
                        </div>
                        <div style="font-size: 12px; color: rgba(255, 255, 255, 0.6);">
                            ${item.desc}
                            ${item.status ? ` <span style="color: #4ade80;">[${item.status}]</span>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    // Agent actions
    async agentAction(agentId, action) {
        console.log(`Agent action: ${agentId} -> ${action}`);

        switch (action) {
            case 'view_terminal': {
                this.openAgentTerminal(agentId);
                break;
            }
            case 'switch_model': {
                const select = document.getElementById(`model-select-${agentId}`);
                if (select) {
                    const model = select.value;
                    await this.switchAgentModel(agentId, model);
                }
                break;
            }
            case 'restart': {
                await this.restartAgent(agentId);
                break;
            }
            case 'configure': {
                this.navigate('config');
                break;
            }
            case 'view_agents': {
                alert(`Sub-agents for ${agentId}: CEO, CTO, Programmer, Tester, Reviewer`);
                break;
            }
            default: {
                console.log(`Action ${action} not implemented yet`);
            }
        }
    }

    openAgentTerminal(agentId) {
        // Check if terminal API is available
        if (!globalThis.TerminalViewer) {
            alert('Terminal viewer not loaded. Ensure terminal-viewer.js is included.');
            return;
        }

        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'agent-terminal-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s ease-in;
        `;

        // Create terminal window
        const terminalWindow = document.createElement('div');
        terminalWindow.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 8px;
            width: 80%;
            max-width: 900px;
            height: 70%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        `;

        terminalWindow.innerHTML = `
            <div class="terminal-header" style="
                padding: 15px 20px;
                background: rgba(102, 126, 234, 0.1);
                border-bottom: 1px solid rgba(102, 126, 234, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="color: #667eea; margin: 0; font-size: 16px;">
                    ⚡ ${agentId.charAt(0).toUpperCase() + agentId.slice(1)} Terminal
                </h3>
                <button onclick="this.closest('.agent-terminal-modal').remove()" style="
                    background: rgba(255, 77, 77, 0.2);
                    border: 1px solid rgba(255, 77, 77, 0.4);
                    color: #ff4d4d;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">✕ Close</button>
            </div>
            <div id="terminal-output-${agentId}" style="
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            "></div>
            <div class="terminal-input" style="
                padding: 15px;
                background: rgba(0, 0, 0, 0.3);
                border-top: 1px solid rgba(102, 126, 234, 0.3);
                display: flex;
                gap: 10px;
            ">
                <input type="text" id="terminal-cmd-${agentId}" placeholder="Enter command..." style="
                    flex: 1;
                    padding: 10px;
                    background: rgba(0, 0, 0, 0.4);
                    border: 1px solid rgba(102, 126, 234, 0.4);
                    border-radius: 4px;
                    color: #fff;
                    font-family: 'Consolas', monospace;
                " />
                <button onclick="sceneRouter.sendAgentCommand('${agentId}')" style="
                    padding: 10px 20px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none;
                    border-radius: 4px;
                    color: #fff;
                    font-weight: bold;
                    cursor: pointer;
                ">Send</button>
            </div>
        `;

        modal.appendChild(terminalWindow);
        document.body.appendChild(modal);

        // Initialize terminal viewer
        const viewer = new TerminalViewer(agentId, {
            autoRefresh: true,
            refreshInterval: 2000,
            maxEntries: 100
        });
        viewer.render(`terminal-output-${agentId}`);

        // Store reference for cleanup
        modal.terminalViewer = viewer;

        // Setup enter key for input
        const input = document.getElementById(`terminal-cmd-${agentId}`);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendAgentCommand(agentId);
            }
        });

        // Focus input
        input.focus();

        // Cleanup on close
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                viewer.stop();
                modal.remove();
            }
        });
    }

    // Generic shell terminal (WSL / PowerShell / CMD)
    openShellTerminal(shellChannel, label = 'Shell Terminal') {
        if (!globalThis.TerminalViewer) {
            alert('Terminal viewer not loaded. Ensure terminal-viewer.js is included.');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'agent-terminal-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s ease-in;
        `;

        const terminalWindow = document.createElement('div');
        terminalWindow.style.cssText = `
            background: linear-gradient(135deg, #0f172a 0%, #111827 100%);
            border: 2px solid rgba(94,234,212,0.5);
            border-radius: 8px;
            width: 80%;
            max-width: 900px;
            height: 70%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        `;

        terminalWindow.innerHTML = `
            <div class="terminal-header" style="
                padding: 15px 20px;
                background: rgba(94, 234, 212, 0.1);
                border-bottom: 1px solid rgba(94, 234, 212, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="color: #5eead4; margin: 0; font-size: 16px;">
                    ${label}
                </h3>
                <button onclick="this.closest('.agent-terminal-modal').remove()" style="
                    background: rgba(255,77,77,0.2);
                    border: 1px solid rgba(255,77,77,0.4);
                    color: #ff4d4d;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">✕ Close</button>
            </div>
            <div id="terminal-output-${shellChannel}" style="
                flex: 1;
                overflow-y: auto;
                padding: 15px;
            "></div>
            <div class="terminal-input" style="
                padding: 15px;
                background: rgba(0,0,0,0.3);
                border-top: 1px solid rgba(94,234,212,0.3);
                display: flex;
                gap: 10px;
            ">
                <input type="text" id="terminal-cmd-${shellChannel}" placeholder="Enter shell command..." style="
                    flex: 1;
                    padding: 10px;
                    background: rgba(0,0,0,0.4);
                    border: 1px solid rgba(94,234,212,0.4);
                    border-radius: 4px;
                    color: #fff;
                    font-family: 'Consolas', monospace;
                " />
                <button onclick="sceneRouter.sendShellCommand('${shellChannel}')" style="
                    padding: 10px 20px;
                    background: linear-gradient(135deg, #5eead4, #22d3ee);
                    border: none;
                    border-radius: 4px;
                    color: #0f172a;
                    font-weight: bold;
                    cursor: pointer;
                ">Run</button>
            </div>
        `;

        modal.appendChild(terminalWindow);
        document.body.appendChild(modal);

        const viewer = new TerminalViewer(shellChannel, {
            autoRefresh: true,
            refreshInterval: 1500,
            maxEntries: 200
        });
        viewer.render(`terminal-output-${shellChannel}`);
        modal.terminalViewer = viewer;

        const input = document.getElementById(`terminal-cmd-${shellChannel}`);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendShellCommand(shellChannel);
            }
        });
        input.focus();

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                viewer.stop();
                modal.remove();
            }
        });
    }

    async sendShellCommand(shellChannel) {
        const input = document.getElementById(`terminal-cmd-${shellChannel}`);
        if (!input) return;
        const command = input.value.trim();
        if (!command) return;

        if (globalThis.terminalAPI) {
            await globalThis.terminalAPI.sendCommand(shellChannel, command, 'INFO', {
                source: 'web_ui_shell',
                type: 'user_shell_command'
            });
        }

        input.value = '';
        input.focus();
    }

    // Open JSON API dashboard (Flask/FastAPI)
    openDashboard(dashboardId, label, apiUrl) {
        if (!window.DashboardViewer) {
            alert('Dashboard viewer not loaded. Ensure dashboard-viewer.js is included.');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'dashboard-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        const dashboardWindow = document.createElement('div');
        dashboardWindow.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 8px;
            width: 85%;
            max-width: 1100px;
            height: 80%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        `;

        dashboardWindow.innerHTML = `
            <div style="
                padding: 15px 20px;
                background: rgba(102, 126, 234, 0.1);
                border-bottom: 1px solid rgba(102, 126, 234, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="color: #667eea; margin: 0; font-size: 16px;">
                    📊 ${label}
                </h3>
                <button onclick="this.closest('.dashboard-modal').remove()" style="
                    background: rgba(255, 77, 77, 0.2);
                    border: 1px solid rgba(255, 77, 77, 0.4);
                    color: #ff4d4d;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">✕ Close</button>
            </div>
            <div id="dashboard-content-${dashboardId}" style="
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            "></div>
        `;

        modal.appendChild(dashboardWindow);
        document.body.appendChild(modal);

        const viewer = new DashboardViewer(dashboardId, {
            type: 'json',
            apiEndpoint: apiUrl.startsWith('http') ? apiUrl : `${this.apiBase}${apiUrl}`,
            autoRefresh: true,
            refreshInterval: 5000
        });
        viewer.render(`dashboard-content-${dashboardId}`);

        modal.dashboardViewer = viewer;

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                viewer.stop();
                modal.remove();
            }
        });
    }

    // Open static HTML dashboard
    openStaticDashboard(dashboardId, label, htmlFile) {
        const modal = document.createElement('div');
        modal.className = 'dashboard-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        const dashboardWindow = document.createElement('div');
        dashboardWindow.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 8px;
            width: 90%;
            max-width: 1200px;
            height: 85%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        `;

        dashboardWindow.innerHTML = `
            <div style="
                padding: 15px 20px;
                background: rgba(102, 126, 234, 0.1);
                border-bottom: 1px solid rgba(102, 126, 234, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="color: #667eea; margin: 0; font-size: 16px;">
                    📊 ${label}
                </h3>
                <button onclick="this.closest('.dashboard-modal').remove()" style="
                    background: rgba(255, 77, 77, 0.2);
                    border: 1px solid rgba(255, 77, 77, 0.4);
                    color: #ff4d4d;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">✕ Close</button>
            </div>
            <iframe
                src="/docs/Metrics/${htmlFile}"
                style="
                    flex: 1;
                    width: 100%;
                    border: none;
                    background: #000;
                "
                frameborder="0"
            ></iframe>
        `;

        modal.appendChild(dashboardWindow);
        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    async sendAgentCommand(agentId) {
        const input = document.getElementById(`terminal-cmd-${agentId}`);
        if (!input) return;

        const command = input.value.trim();
        if (!command) return;

        // Send to terminal API
        if (globalThis.terminalAPI) {
            await globalThis.terminalAPI.sendCommand(agentId, command, 'INFO', {
                source: 'web_ui_terminal',
                type: 'user_command'
            });
        }

        input.value = '';
        input.focus();
    }

    // Open Streamlit app in new tab or modal
    openStreamlitApp(appId, label, pythonFile) {
        // Streamlit typically runs on port 8501
        const streamlitPort = 8501;
        const streamlitUrl = `http://localhost:${streamlitPort}`;

        // Create modal with options
        const modal = document.createElement('div');
        modal.className = 'streamlit-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        `;

        modalContent.innerHTML = `
            <h3 style="color: #667eea; margin: 0 0 20px 0;">🔍 ${label}</h3>
            <p style="color: rgba(255, 255, 255, 0.7); margin-bottom: 20px;">
                Streamlit app: <code style="color: #4ade80;">${pythonFile}</code>
            </p>
            <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                <button onclick="window.open('${streamlitUrl}', '_blank'); this.closest('.streamlit-modal').remove();" style="
                    padding: 12px 24px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border: none;
                    border-radius: 6px;
                    color: #fff;
                    font-weight: bold;
                    cursor: pointer;
                ">🌐 Open in New Tab</button>
                <button onclick="sceneRouter.launchStreamlit('${pythonFile}'); this.closest('.streamlit-modal').remove();" style="
                    padding: 12px 24px;
                    background: rgba(74, 222, 128, 0.2);
                    border: 1px solid rgba(74, 222, 128, 0.5);
                    border-radius: 6px;
                    color: #4ade80;
                    font-weight: bold;
                    cursor: pointer;
                ">🚀 Launch Streamlit</button>
                <button onclick="this.closest('.streamlit-modal').remove();" style="
                    padding: 12px 24px;
                    background: rgba(255, 77, 77, 0.2);
                    border: 1px solid rgba(255, 77, 77, 0.4);
                    border-radius: 6px;
                    color: #ff4d4d;
                    font-weight: bold;
                    cursor: pointer;
                ">✕ Cancel</button>
            </div>
            <p style="color: rgba(255, 255, 255, 0.4); font-size: 12px; margin-top: 20px;">
                Note: Ensure Streamlit server is running on port ${streamlitPort}
            </p>
        `;

        modal.appendChild(modalContent);
        document.body.appendChild(modal);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    // Launch Streamlit via terminal command
    async launchStreamlit(pythonFile) {
        if (globalThis.terminalAPI) {
            const command = `streamlit run ${pythonFile} --server.port 8501`;
            await globalThis.terminalAPI.sendCommand('shell-pwsh', command, 'INFO', {
                source: 'streamlit_launcher',
                type: 'streamlit_launch'
            });

            // Show notification
            setTimeout(() => {
                window.open('http://localhost:8501', '_blank');
            }, 3000);
        } else {
            alert('Terminal API not available. Run manually:\n\nstreamlit run ' + pythonFile);
        }
    }

    // Handle builtin scenes (quantum terminal, file tree, etc.)
    handleBuiltinScene(sceneId) {
        switch (sceneId) {
            case 'quantum_terminal':
                // Focus the main quantum terminal
                const terminalInput = document.getElementById('terminal-input');
                if (terminalInput) {
                    terminalInput.focus();
                    // Close menu
                    const container = document.getElementById('scene-container');
                    if (container) container.style.display = 'none';
                } else {
                    alert('Quantum Terminal not found on page. Check if terminal-module exists.');
                }
                break;

            case 'file_tree':
                // Open file tree viewer
                this.openFileTreeViewer();
                break;

            default:
                console.warn(`Builtin scene not implemented: ${sceneId}`);
                alert(`Builtin scene '${sceneId}' not yet implemented.`);
        }
    }

    // Open file tree viewer modal
    async openFileTreeViewer() {
        const modal = document.createElement('div');
        modal.className = 'file-tree-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        const treeWindow = document.createElement('div');
        treeWindow.style.cssText = `
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid rgba(102, 126, 234, 0.5);
            border-radius: 8px;
            width: 60%;
            max-width: 800px;
            height: 70%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        `;

        treeWindow.innerHTML = `
            <div style="
                padding: 15px 20px;
                background: rgba(102, 126, 234, 0.1);
                border-bottom: 1px solid rgba(102, 126, 234, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="color: #667eea; margin: 0; font-size: 16px;">
                    🌳 File Tree View
                </h3>
                <button onclick="this.closest('.file-tree-modal').remove()" style="
                    background: rgba(255, 77, 77, 0.2);
                    border: 1px solid rgba(255, 77, 77, 0.4);
                    color: #ff4d4d;
                    padding: 6px 12px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                ">✕ Close</button>
            </div>
            <div id="file-tree-content" style="
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                color: #ddd;
            ">
                Loading file tree...
            </div>
        `;

        modal.appendChild(treeWindow);
        document.body.appendChild(modal);

        // Fetch directory structure from backend
        try {
            const resp = await fetch(`${this.apiBase}/api/map`);
            if (resp.ok) {
                const mapData = await resp.json();
                const treeContent = document.getElementById('file-tree-content');

                // Render map data as hierarchical tree
                let treeHtml = '<div style="line-height: 1.8;">';

                if (mapData.regions) {
                    for (const [region, info] of Object.entries(mapData.regions)) {
                        treeHtml += `
                            <div style="margin-bottom: 15px;">
                                <div style="color: #667eea; font-weight: bold;">
                                    📁 ${region}
                                </div>
                                <div style="padding-left: 20px; color: rgba(255,255,255,0.6); font-size: 12px;">
                                    ${info.description || ''}
                                    ${info.key_files ? `<br>Key files: ${info.key_files.slice(0, 5).join(', ')}` : ''}
                                </div>
                            </div>
                        `;
                    }
                }

                treeHtml += '</div>';
                treeContent.innerHTML = treeHtml;
            } else {
                document.getElementById('file-tree-content').innerHTML =
                    '<span style="color: #ef4444;">Failed to load file tree.</span>';
            }
        } catch (e) {
            document.getElementById('file-tree-content').innerHTML =
                `<span style="color: #ef4444;">Error: ${e.message}</span>`;
        }

        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
    }

    async switchAgentModel(agentId, model) {
        console.log(`Switching ${agentId} to model: ${model}`);

        if (agentId === 'ollama') {
            try {
                // Call Ollama API to switch model
                const response = await fetch('http://localhost:11434/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: model,
                        prompt: 'Model switch test',
                        stream: false
                    })
                });

                if (response.ok) {
                    // Send notification to terminal
                    if (globalThis.terminalAPI) {
                        await globalThis.terminalAPI.sendCommand('agents', `Switched Ollama to ${model}`, 'SUCCESS');
                        await globalThis.terminalAPI.sendCommand('ollama', `Model switched to ${model}`, 'INFO');
                    }
                    alert(`✅ Ollama model switched to ${model}`);
                } else {
                    alert(`❌ Failed to switch model: ${response.statusText}`);
                }
            } catch (error) {
                alert(`❌ Error switching model: ${error.message}`);
            }
        } else {
            alert(`Model switching not yet implemented for ${agentId}`);
        }
    }

    async restartAgent(agentId) {
        console.log(`Restarting agent: ${agentId}`);

        // Send restart signal via terminal API
        if (globalThis.terminalAPI) {
            await globalThis.terminalAPI.sendCommand('agents', `restart_${agentId}`, 'CRITICAL', {
                action: 'restart',
                agent: agentId
            });

            alert(`🔄 Restart signal sent to ${agentId}. Check terminal for status.`);

            // Poll for restart confirmation after 3 seconds
            setTimeout(async () => {
                const status = await this.checkAgentStatus(agentId);
                if (status && status.status === 'online') {
                    alert(`✅ ${agentId} restarted successfully`);
                }
            }, 3000);
        } else {
            alert('Terminal API not available. Cannot restart agent.');
        }
    }

    async checkAgentStatus(agentId) {
        if (globalThis.terminalAPI) {
            return await globalThis.terminalAPI.getAgentStatus(agentId);
        }
        return null;
    }

    loadGameEngine(engineId, data) {
        console.log(`Loading game engine: ${engineId}`, data);
        // TODO: Dynamic game engine loading
    }

    // ==========================================================================
    // SETTINGS PERSISTENCE - localStorage implementation
    // ==========================================================================

    saveSettings() {
        console.log('Saving settings...');

        // Collect settings from form elements
        const settings = {
            model: document.querySelector('select[onchange*="model"]')?.value || 'qwen2.5-coder',
            shell: document.querySelector('select[onchange*="shell"]')?.value || 'shell-wsl',
            theme: document.querySelector('select[onchange*="theme"]')?.value || 'quantum-dark',
            autoRefresh: document.querySelector('input[type="checkbox"][onchange*="auto"]')?.checked ?? true,
            refreshInterval: parseInt(document.querySelector('input[type="number"][onchange*="interval"]')?.value || '5000', 10),
            evolution_level: this.evolutionLevel || 1,
            saved_at: new Date().toISOString()
        };

        try {
            localStorage.setItem('nusyq_settings', JSON.stringify(settings));
            console.log('Settings saved to localStorage:', settings);
            alert('✅ Settings saved successfully!');
        } catch (e) {
            console.error('Failed to save settings:', e);
            alert('❌ Failed to save settings: ' + e.message);
        }
    }

    loadSettings() {
        try {
            const stored = localStorage.getItem('nusyq_settings');
            if (stored) {
                const settings = JSON.parse(stored);
                console.log('Settings loaded from localStorage:', settings);

                // Apply evolution level
                if (settings.evolution_level) {
                    this.evolutionLevel = settings.evolution_level;
                }

                return settings;
            }
        } catch (e) {
            console.error('Failed to load settings:', e);
        }
        return null;
    }

    // Get a specific setting with default fallback
    getSetting(key, defaultValue) {
        try {
            const stored = localStorage.getItem('nusyq_settings');
            if (stored) {
                const settings = JSON.parse(stored);
                return settings[key] !== undefined ? settings[key] : defaultValue;
            }
        } catch (e) {
            console.error('Failed to get setting:', e);
        }
        return defaultValue;
    }

    // Update a single setting
    updateSetting(key, value) {
        try {
            const stored = localStorage.getItem('nusyq_settings') || '{}';
            const settings = JSON.parse(stored);
            settings[key] = value;
            settings.updated_at = new Date().toISOString();
            localStorage.setItem('nusyq_settings', JSON.stringify(settings));
            console.log(`Setting ${key} updated to:`, value);
        } catch (e) {
            console.error('Failed to update setting:', e);
        }
    }

    // Reset all settings to defaults
    resetSettings() {
        const defaults = {
            model: 'qwen2.5-coder',
            shell: 'shell-wsl',
            theme: 'quantum-dark',
            autoRefresh: true,
            refreshInterval: 5000,
            evolution_level: 1,
            saved_at: new Date().toISOString()
        };

        try {
            localStorage.setItem('nusyq_settings', JSON.stringify(defaults));
            this.evolutionLevel = 1;
            console.log('Settings reset to defaults');
            alert('✅ Settings reset to defaults!');
        } catch (e) {
            console.error('Failed to reset settings:', e);
        }
    }

    // Agent status polling
    startAgentStatusPolling() {
        // Avoid multiple polling intervals
        if (this.statusPollingInterval) {
            return;
        }

        // Poll every 5 seconds
        this.statusPollingInterval = setInterval(async () => {
            await this.updateAgentStatuses();
        }, 5000);

        // Initial update
        this.updateAgentStatuses();
    }

    stopAgentStatusPolling() {
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
            this.statusPollingInterval = null;
        }
    }

    async updateAgentStatuses() {
        // Only update if we're on the agents scene
        if (this.activeScene !== 'agents') {
            return;
        }

        const scene = this.scenes.get('agents');
        if (!scene || !globalThis.terminalAPI) {
            return;
        }

        // Update each agent's status
        for (const agent of scene.agents) {
            try {
                const status = await globalThis.terminalAPI.getAgentStatus(agent.id);

                // Update agent status in scene data
                if (status && status.status) {
                    agent.status = status.status;
                    agent.lastActivity = status.lastActivity;
                    agent.lastMessage = status.lastMessage;
                }
            } catch (error) {
                console.error(`Failed to get status for ${agent.id}:`, error);
                agent.status = 'error';
            }
        }

        // Re-render agent grid with updated statuses
        const container = document.getElementById('scene-content');
        if (container) {
            this.renderAgentGrid(container, scene);
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // ESC to go back
            if (e.key === 'Escape') {
                this.back();
            }

            // Ctrl+M for main menu
            if (e.ctrlKey && e.key === 'm') {
                e.preventDefault();
                this.navigate('main');
            }

            // Ctrl+A for agents
            if (e.ctrlKey && e.key === 'a') {
                e.preventDefault();
                this.navigate('agents');
            }

            // Ctrl+G for games
            if (e.ctrlKey && e.key === 'g') {
                e.preventDefault();
                this.navigate('games');
            }
        });
    }

    // Render game scene
    renderGame(container, scene, data) {
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div id="game-content-${scene.engine}" style="margin-top: 20px;">
                <div style="color: rgba(255, 255, 255, 0.7); text-align: center; padding: 40px;">
                    Loading ${scene.name}...
                </div>
            </div>
        `;

        // Launch game engine
        if (scene.engine === 'maze-navigator' && window.HouseOfLeavesEngine) {
            const gameDiv = document.getElementById(`game-content-${scene.engine}`);
            gameDiv.innerHTML = '<div id="house-of-leaves-game"></div>';

            const game = new HouseOfLeavesEngine('house-of-leaves-game');
            game.render();
            game.setupControls();
        } else if (scene.engine === 'cultivation-idle' && window.CultivationIdleEngine) {
            const gameDiv = document.getElementById(`game-content-${scene.engine}`);
            gameDiv.innerHTML = '<div id="cultivation-idle-game"></div>';

            // Initialize cultivation idle game
            window.cultivationGame = new CultivationIdleEngine('cultivation-idle-game');
            window.cultivationGame.start();
        } else {
            document.getElementById(`game-content-${scene.engine}`).innerHTML = `
                <div style="color: rgba(255, 255, 255, 0.6); text-align: center; padding: 40px;">
                    <h3 style="color: #667eea;">Game Engine: ${scene.engine}</h3>
                    <p>Status: ${scene.status || 'Loading...'}</p>
                    <p style="font-size: 12px; color: rgba(255, 255, 255, 0.4);">
                        Game implementation in progress
                    </p>
                </div>
            `;
        }
    }

    // Generic renderer for unknown scene types
    renderGeneric(container, scene) {
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div style="margin-top: 20px; color: rgba(255, 255, 255, 0.7);">
                <p>${scene.description || 'Scene details'}</p>
                <p style="font-size: 12px; color: rgba(255, 255, 255, 0.4);">
                    Scene type: ${scene.type || 'unknown'}
                </p>
            </div>
        `;
    }

    async renderDataFeed(container, scene) {
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div id="data-feed-content" style="margin-top: 16px; color: #ddd; font-size: 13px;">
                Loading ${scene.endpoint || ''}...
            </div>
        `;

        const target = document.getElementById('data-feed-content');
        try {
            const resp = await fetch(`${this.apiBase}${scene.endpoint}`);
            if (!resp.ok) {
                target.innerHTML = `<span style="color:#ef4444;">Failed to load (${resp.status})</span>`;
                return;
            }
            const data = await resp.json();
            if (Array.isArray(data)) {
                target.innerHTML = data
                    .map(
                        (item) =>
                            `<div style="padding:8px;margin-bottom:6px;border-radius:6px;background:rgba(255,255,255,0.04);">
                                <pre style="white-space:pre-wrap;margin:0;color:#e5e7eb;">${JSON.stringify(item, null, 2)}</pre>
                            </div>`
                    )
                    .join('');
            } else {
                target.innerHTML = `<pre style="white-space:pre-wrap;margin:0;color:#e5e7eb;">${JSON.stringify(
                    data,
                    null,
                    2
                )}</pre>`;
            }
        } catch (err) {
            target.innerHTML = `<span style="color:#ef4444;">Error: ${err.message || err}</span>`;
        }
    }

    renderStaticLink(container, scene) {
        const link = scene.file || scene.url || scene.endpoint || '#';
        container.innerHTML = `
            <div class="scene-header">
                <button class="back-btn" onclick="sceneRouter.back()">← Back</button>
                <h2 style="color: #667eea; margin: 0;">${scene.name}</h2>
            </div>
            <div style="margin-top: 20px; color: rgba(255, 255, 255, 0.7); font-size: 14px;">
                <p>${scene.description || 'Open linked resource'}</p>
                <a href="${link}" target="_blank" style="color:#4ade80;text-decoration:underline;">Open ${link}</a>
            </div>
        `;
    }

    // Show/hide menu
    toggle() {
        const container = document.getElementById('scene-container');
        if (container) {
            container.style.display = container.style.display === 'none' ? 'block' : 'none';
        } else {
            this.navigate('main');
        }
    }
}

// Initialize global scene router
window.sceneRouter = new SceneRouter();

// Add menu button to header
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('.header');
    if (header) {
        const menuBtn = document.createElement('button');
        menuBtn.innerHTML = '☰ Menu';
        menuBtn.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 6px;
            color: #fff;
            font-weight: bold;
            cursor: pointer;
            z-index: 1001;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        `;
        menuBtn.onclick = () => window.sceneRouter.navigate('main');
        document.body.appendChild(menuBtn);
    }
});

console.log('🌌 Scene Router initialized - Press Ctrl+M for main menu');
