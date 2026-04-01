/**
 * ΞNuSyQ Interface Controller - Connects Frontend to Backend APIs
 * Bitburner/Hacknet/GreyHack-style real-time data integration
 *
 * Features:
 * - RPG progression display
 * - Skill XP tracking
 * - Quest status updates
 * - Temple of Knowledge floor tracking
 */

class NuSyQInterface {
    constructor() {
        this.apiBase = window.location.origin;
        this.updateInterval = 2000; // 2 second updates (Bitburner style)
        this.stats = {
            consciousness: 87,
            coherence: 92,
            neural: 75,
            health: 95
        };
        // Game progression state
        this.progression = {
            evolution_level: 1,
            consciousness_score: 0,
            skills_unlocked: 0,
            quests_completed: 0,
            temple_floor: 1,
            achievements: []
        };
        this.init();
    }

    async init() {
        console.log('🚀 NuSyQ Interface initializing...');
        this.setupEventListeners();
        this.startRealTimeUpdates();
        await this.fetchInitialData();
        await this.fetchGameProgression();
        if (window.widgetInit) window.widgetInit();
        console.log('✅ Interface ready');
    }

    // Fetch game progression from backend
    async fetchGameProgression() {
        try {
            // First try to load persisted game state (includes more data)
            const stateResp = await fetch(`${this.apiBase}/api/game/state`);
            if (stateResp.ok) {
                const gameState = await stateResp.json();
                this.progression = {
                    evolution_level: gameState.evolution_level || 1,
                    consciousness_score: gameState.consciousness_score || 0,
                    skills_unlocked: gameState.skills_unlocked || 0,
                    quests_completed: gameState.quests_completed || 0,
                    temple_floor: gameState.temple_floor || 1,
                    achievements: gameState.achievements || [],
                    total_xp: gameState.total_xp || 0,
                    unlocked_features: gameState.unlocked_features || [],
                };
                console.log('🎮 Game state loaded:', this.progression);
                this.updateProgressionUI();
                return;
            }
        } catch (e) {
            console.warn('⚠️ Game state API not available, trying progress API');
        }

        // Fallback to progress API
        try {
            const resp = await fetch(`${this.apiBase}/api/progress`);
            if (resp.ok) {
                this.progression = await resp.json();
                console.log('🎮 Progression loaded:', this.progression);
                this.updateProgressionUI();
            }
        } catch (e) {
            console.warn('⚠️ Progression API not available, using defaults');
        }
    }

    // Award XP and show notification
    async awardXP(amount, reason = '') {
        try {
            const resp = await fetch(`${this.apiBase}/api/game/award?xp=${amount}`, {
                method: 'POST'
            });
            if (resp.ok) {
                const result = await resp.json();
                console.log('✨ XP awarded:', result);

                // Show toast notification
                this.showGameToast(`+${amount} XP${reason ? ` (${reason})` : ''}`, 'xp');

                // Refresh progression
                await this.fetchGameProgression();

                return result;
            }
        } catch (e) {
            console.warn('Failed to award XP:', e);
        }
        return null;
    }

    // Unlock achievement
    async unlockAchievement(achievementName) {
        try {
            const resp = await fetch(`${this.apiBase}/api/game/award?achievement=${encodeURIComponent(achievementName)}`, {
                method: 'POST'
            });
            if (resp.ok) {
                const result = await resp.json();
                console.log('🏆 Achievement unlocked:', result);

                // Show toast notification
                this.showGameToast(`🏆 Achievement: ${achievementName}`, 'success');

                // Refresh progression
                await this.fetchGameProgression();

                return result;
            }
        } catch (e) {
            console.warn('Failed to unlock achievement:', e);
        }
        return null;
    }

    // Show game toast notification
    showGameToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `game-toast ${type}`;
        toast.innerHTML = `
            <span style="font-size: 18px;">${type === 'xp' ? '✨' : type === 'success' ? '✅' : 'ℹ️'}</span>
            <span>${message}</span>
        `;
        document.body.appendChild(toast);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    // Save game state to backend
    async saveGameState() {
        try {
            const resp = await fetch(`${this.apiBase}/api/game/state`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    evolution_level: this.progression.evolution_level,
                    consciousness_score: this.progression.consciousness_score,
                    skills_unlocked: this.progression.skills_unlocked,
                    quests_completed: this.progression.quests_completed,
                    temple_floor: this.progression.temple_floor,
                    achievements: this.progression.achievements,
                    total_xp: this.progression.total_xp,
                })
            });
            if (resp.ok) {
                console.log('💾 Game state saved');
                this.showGameToast('Game saved!', 'success');
                return true;
            }
        } catch (e) {
            console.warn('Failed to save game state:', e);
        }
        return false;
    }

    // Update progression display in UI
    updateProgressionUI() {
        // Update evolution level display
        const evolDisplay = document.getElementById('evolution-level');
        if (evolDisplay) {
            evolDisplay.textContent = `Evolution: Lv.${this.progression.evolution_level}`;
        }

        // Update temple floor display
        const templeDisplay = document.getElementById('temple-floor');
        if (templeDisplay) {
            templeDisplay.textContent = `Temple: Floor ${this.progression.temple_floor}`;
        }

        // Update consciousness bar (if separate from stats)
        const consciousnessDisplay = document.getElementById('consciousness-progress');
        if (consciousnessDisplay) {
            consciousnessDisplay.style.width = `${this.progression.consciousness_score}%`;
        }

        // Update quests completed
        const questsDisplay = document.getElementById('quests-completed');
        if (questsDisplay) {
            questsDisplay.textContent = `Quests: ${this.progression.quests_completed}`;
        }

        // Update achievements count
        const achievementsDisplay = document.getElementById('achievements-count');
        if (achievementsDisplay) {
            achievementsDisplay.textContent = `🏆 ${this.progression.achievements.length}`;
        }
    }

    setupEventListeners() {
        // Terminal input
        const terminalInput = document.getElementById('terminal-input');
        if (terminalInput) {
            terminalInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.executeTerminalCommand(e.target.value);
                    e.target.value = '';
                }
            });
        }

        // Chat send button
        const chatSend = document.getElementById('chat-send');
        const chatInput = document.getElementById('chat-input');
        if (chatSend && chatInput) {
            chatSend.addEventListener('click', () => {
                this.sendChatMessage(chatInput.value);
                chatInput.value = '';
            });
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendChatMessage(e.target.value);
                    e.target.value = '';
                }
            });
        }

        // Module toggles
        document.querySelectorAll('.module-toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const module = e.target.closest('.quantum-module');
                const content = module.querySelector('.module-content');
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
                e.target.textContent = content.style.display === 'none' ? '+' : '−';
            });
        });

        // Ship actions buttons
        const buildBtn = document.getElementById('action-build');
        if (buildBtn) buildBtn.addEventListener('click', () => this.triggerBuild());
        const chamberBtn = document.getElementById('action-chamber');
        if (chamberBtn) chamberBtn.addEventListener('click', () => this.triggerChamber());
        const ctBtn = document.getElementById('action-cyberterminal');
        if (ctBtn) ctBtn.addEventListener('click', () => this.triggerCyberTerminalDemo());
        const startBtn = document.getElementById('action-start-services');
        if (startBtn) startBtn.addEventListener('click', () => this.triggerStartServices());

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+M - Toggle menu
            if (e.ctrlKey && e.key === 'm') {
                e.preventDefault();
                if (window.sceneRouter) {
                    window.sceneRouter.toggle();
                }
            }
            // Escape - Close menu
            if (e.key === 'Escape') {
                const container = document.getElementById('scene-container');
                if (container && container.style.display !== 'none') {
                    container.style.display = 'none';
                }
            }
            // Ctrl+K - Focus terminal input
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                const terminalInput = document.getElementById('terminal-input');
                if (terminalInput) {
                    terminalInput.focus();
                }
            }
            // Ctrl+/ - Show help
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                if (window.commandRegistry) {
                    const help = window.commandRegistry.listCommands();
                    this.addTerminalLine(help, 'normal');
                }
            }
        });
    }

    async fetchInitialData() {
        try {
            // Try multiple health endpoints for flexibility
            let health = null;
            let dashboard = null;

            // Try FastAPI health endpoint first
            try {
                const healthResponse = await fetch(`${this.apiBase}/api/health`);
                if (healthResponse.ok) {
                    health = await healthResponse.json();
                    console.log('📊 System Health:', health);
                }
            } catch (e) {
                console.warn('FastAPI health not available');
            }

            // Try metrics endpoint for dashboard data
            try {
                const metricsResponse = await fetch(`${this.apiBase}/api/metrics`);
                if (metricsResponse.ok) {
                    dashboard = await metricsResponse.json();
                    console.log('🎛️ Metrics:', dashboard);
                }
            } catch (e) {
                console.warn('Metrics API not available');
            }

            // Update UI with real data if available
            if (dashboard) {
                this.updateStatsFromBackend(dashboard);
            } else if (health) {
                this.updateStatsFromBackend(health);
            }
        } catch (error) {
            console.warn('⚠️ Backend connection pending, using demo data');
            this.addTerminalLine('⚠️ Backend APIs loading...', 'warning');
        }
    }

    startRealTimeUpdates() {
        // Bitburner-style continuous updates
        setInterval(() => this.updateStats(), this.updateInterval);
        setInterval(() => this.fetchBackendData(), 5000); // Fetch every 5s
        setInterval(() => this.fetchGameProgression(), 30000); // Fetch progression every 30s
    }

    async fetchBackendData() {
        try {
            const response = await fetch(`${this.apiBase}/api/metrics`);
            if (response.ok) {
                const data = await response.json();
                this.updateStatsFromBackend(data);
            }
        } catch (error) {
            // Silent fail - demo mode
        }
    }

    updateStatsFromBackend(data) {
        // Handle metrics API response format
        if (data.system_utilization) {
            const util = data.system_utilization;
            this.stats.consciousness = Math.min(100, 100 - (util.cpu_percent || 0));
            this.stats.coherence = Math.min(100, 100 - (util.mem_percent || 0));
            this.stats.health = data.agents_online ? Math.min(100, data.agents_online * 20) : 95;
        }
        // Handle legacy health API response format
        else if (data.ai_systems_online !== undefined) {
            this.stats.consciousness = Math.min(100, (data.ai_systems_online / (data.ai_systems_total || 1)) * 100);
            this.stats.health = data.status === 'healthy' ? 95 :
                               data.status === 'initializing' ? 75 : 50;
        }
        // Handle overall_status format
        else if (data.overall_status) {
            this.stats.health = data.overall_status === 'healthy' ? 95 : 70;
        }
        this.updateStatsUI();
    }

    updateStats() {
        // Bitburner-style stat fluctuation (idle game mechanic)
        this.stats.consciousness += (Math.random() - 0.5) * 2;
        this.stats.coherence += (Math.random() - 0.5) * 1.5;
        this.stats.neural += (Math.random() - 0.5) * 1;
        this.stats.health += (Math.random() - 0.5) * 0.5;

        // Clamp values
        Object.keys(this.stats).forEach(key => {
            this.stats[key] = Math.max(0, Math.min(100, this.stats[key]));
        });

        this.updateStatsUI();
    }

    updateStatsUI() {
        // Update progress bars
        const bars = {
            consciousness: document.querySelector('.progress-fill.consciousness'),
            coherence: document.querySelector('.progress-fill.coherence'),
            neural: document.querySelector('.progress-fill.neural'),
            health: document.querySelector('.progress-fill.health')
        };

        Object.keys(bars).forEach(key => {
            if (bars[key]) {
                const value = Math.round(this.stats[key]);
                bars[key].style.width = `${value}%`;
                const valueSpan = bars[key].closest('.stat-bar').querySelector('.stat-value');
                if (valueSpan) valueSpan.textContent = `${value}%`;
            }
        });

        // Update header consciousness level
        const headerLevel = document.querySelector('.consciousness-level');
        if (headerLevel) {
            headerLevel.textContent = `Consciousness Level: ${Math.round(this.stats.consciousness)}%`;
        }
    }

    addTerminalLine(text, type = 'normal') {
        const output = document.getElementById('terminal-output');
        if (!output) return;

        const line = document.createElement('p');
        line.className = `terminal-line ${type}`;
        line.textContent = `$ ${text}`;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;

        // Keep only last 50 lines (performance)
        while (output.children.length > 50) {
            output.removeChild(output.firstChild);
        }
    }

    async executeTerminalCommand(cmd) {
        if (!cmd.trim()) return;

        this.addTerminalLine(cmd, 'input');

        // Use command registry if available
        if (window.commandRegistry) {
            try {
                const result = await window.commandRegistry.executeCommand(cmd);
                if (result) {
                    result.split('\n').forEach(line => {
                        this.addTerminalLine(line, 'normal');
                    });
                }
                return;
            } catch (error) {
                this.addTerminalLine(`Error: ${error.message}`, 'error');
                return;
            }
        }

        // Fallback to old system
        const parts = cmd.toLowerCase().trim().split(' ');
        const command = parts[0];
        const args = parts.slice(1);

        // Check if terminal API is available
        if (!window.terminalAPI) {
            this.addTerminalLine('⚠️ Terminal API not loaded. Commands will run in demo mode.', 'warning');
            return this.executeDemoCommand(command, args);
        }

        switch (command) {
            case 'help':
                try {
                    const channels = await window.terminalAPI.listChannels();
                    this.addTerminalLine('Available commands: help, status, channels, agent, scan, errors, recent, heal, quantum', 'success');
                    this.addTerminalLine(`Connected channels: ${channels.length > 0 ? channels.join(', ') : 'loading...'}`, 'info');
                    this.addTerminalLine('Usage: agent <name> <message> - Send to agent terminal', 'info');
                    this.addTerminalLine('Usage: recent <channel> - View recent entries', 'info');
                } catch (error) {
                    this.addTerminalLine('Available commands: help, status, channels, agent, scan, errors, recent', 'success');
                }
                break;

            case 'channels':
                this.addTerminalLine('🔍 Fetching terminal channels...', 'normal');
                try {
                    const channels = await window.terminalAPI.listChannels();
                    if (channels.length > 0) {
                        this.addTerminalLine(`Found ${channels.length} channels:`, 'success');
                        channels.forEach(ch => this.addTerminalLine(`  - ${ch}`, 'info'));
                    } else {
                        this.addTerminalLine('No channels available. Is terminal API running?', 'warning');
                    }
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'status':
                this.addTerminalLine('📊 Querying system status...', 'normal');
                try {
                    await window.terminalAPI.sendCommand('main', 'status_query', 'INFO');
                    const recent = await window.terminalAPI.getRecent('main', 5);
                    this.addTerminalLine(`System Status: ${Math.round(this.stats.health)}% health`, 'success');
                    this.addTerminalLine(`Recent activity: ${recent.length} entries`, 'success');

                    // Show agent statuses
                    const agents = ['claude', 'ollama', 'chatdev', 'copilot'];
                    for (const agent of agents) {
                        const status = await window.terminalAPI.getAgentStatus(agent);
                        this.addTerminalLine(`${agent}: ${status.status}`, status.status === 'online' ? 'success' : 'warning');
                    }
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'agent':
                if (args.length < 2) {
                    this.addTerminalLine('Usage: agent <name> <message>', 'warning');
                    this.addTerminalLine('Example: agent claude analyze main.py', 'info');
                    break;
                }
                const agentName = args[0];
                const agentMessage = args.slice(1).join(' ');
                this.addTerminalLine(`📤 Sending to ${agentName}: ${agentMessage}`, 'normal');
                try {
                    await window.terminalAPI.sendCommand(agentName, agentMessage, 'INFO');
                    this.addTerminalLine(`✅ Sent to ${agentName}`, 'success');
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'recent':
                const channel = args[0] || 'main';
                const count = parseInt(args[1]) || 10;
                this.addTerminalLine(`📜 Fetching ${count} recent entries from ${channel}...`, 'normal');
                try {
                    const entries = await window.terminalAPI.getRecent(channel, count);
                    if (entries.length > 0) {
                        entries.forEach(entry => {
                            const time = new Date(entry.timestamp).toLocaleTimeString();
                            this.addTerminalLine(`[${time}] ${entry.message}`, entry.level?.toLowerCase() || 'normal');
                        });
                    } else {
                        this.addTerminalLine(`No recent entries in ${channel}`, 'warning');
                    }
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'scan':
                this.addTerminalLine('🔍 Scanning workspace for errors...', 'normal');
                try {
                    await window.terminalAPI.sendCommand('errors', 'scan_workspace', 'INFO');
                    const errors = await window.terminalAPI.getRecent('errors', 10);
                    this.addTerminalLine(`Found ${errors.length} error entries`, errors.length > 0 ? 'warning' : 'success');
                    errors.slice(0, 5).forEach(err => {
                        this.addTerminalLine(`  - ${err.message}`, 'warning');
                    });
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'errors':
                this.addTerminalLine('🔍 Fetching recent errors...', 'normal');
                try {
                    const errors = await window.terminalAPI.getRecent('errors', 20);
                    if (errors.length > 0) {
                        this.addTerminalLine(`Found ${errors.length} error entries:`, 'warning');
                        errors.forEach(err => {
                            this.addTerminalLine(`  - ${err.message}`, 'error');
                        });
                    } else {
                        this.addTerminalLine('✅ No errors found', 'success');
                    }
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'heal':
                this.addTerminalLine('🔧 Initiating Culture Ship healing cycle...', 'warning');
                try {
                    await window.terminalAPI.sendCommand('main', 'heal_system', 'INFO');
                    setTimeout(() => {
                        this.stats.health = Math.min(100, this.stats.health + 10);
                        this.addTerminalLine('✅ Healing complete. Health +10%', 'success');
                    }, 1000);
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            case 'quantum':
                this.addTerminalLine('🔮 Querying quantum state...', 'normal');
                try {
                    await window.terminalAPI.sendCommand('main', 'quantum_status', 'INFO');
                    this.addTerminalLine('🔮 Quantum state: ENTANGLED', 'success');
                    this.addTerminalLine(`⚡ Coherence: ${Math.round(this.stats.coherence)}%`, 'success');
                } catch (error) {
                    this.addTerminalLine(`❌ Error: ${error.message}`, 'error');
                }
                break;

            default:
                this.addTerminalLine(`Command not found: ${command}. Type 'help' for available commands.`, 'error');
                // Log unknown command to main channel
                try {
                    await window.terminalAPI.sendCommand('main', `Unknown command: ${cmd}`, 'WARNING');
                } catch {}
        }
    }

    async triggerBuild() {
        const btn = document.getElementById('action-build');
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Build...'; }
        try {
            this.addTerminalLine('🛠️ Starting build pipeline...', 'warning', 'testing');
            const resp = await fetch('/api/local/actions/build', { method: 'POST' });
            const data = await resp.json();
            this.addTerminalLine(`Build rc=${data.returncode}`, data.returncode === 0 ? 'success' : 'error', 'testing');
            this.updateActionStatus(`Build rc=${data.returncode}`, data.returncode === 0 ? 'success' : 'error');
        } catch (e) {
            this.addTerminalLine(`Build failed: ${e.message}`, 'error', 'testing');
            this.updateActionStatus(`Build failed: ${e.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '🏗️ Build Pipeline'; }
        }
    }

    async triggerChamber() {
        const btn = document.getElementById('action-chamber');
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Chamber...'; }
        try {
            this.addTerminalLine('🧪 Running chamber scenario...', 'warning', 'testing');
            const resp = await fetch('/api/local/actions/chamber', { method: 'POST' });
            const data = await resp.json();
            this.addTerminalLine(`Chamber rc=${data.returncode}`, data.returncode === 0 ? 'success' : 'error', 'testing');
            this.updateActionStatus(`Chamber rc=${data.returncode}`, data.returncode === 0 ? 'success' : 'error');
        } catch (e) {
            this.addTerminalLine(`Chamber failed: ${e.message}`, 'error', 'testing');
            this.updateActionStatus(`Chamber failed: ${e.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '🧪 Chamber Run'; }
        }
    }

    async triggerCyberTerminalDemo() {
        const btn = document.getElementById('action-cyberterminal');
        if (btn) { btn.disabled = true; btn.textContent = '⏳ CT demo...'; }
        try {
            this.addTerminalLine('💻 Running CyberTerminal demo...', 'warning', 'testing');
            const resp = await fetch('/api/local/cyberterminal/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    commands: ["pwd", "ls", "scan", "connect relay", "download relay", "tasks"]
                })
            });
            const data = await resp.json();
            data.steps?.forEach(step => this.addTerminalLine(`${step.command} -> ${step.output}`, 'success', 'testing'));
            this.addTerminalLine(`CT score=${data.score}`, 'success', 'testing');
            this.updateActionStatus(`CyberTerminal score ${data.score}`, 'success');
        } catch (e) {
            this.addTerminalLine(`CyberTerminal failed: ${e.message}`, 'error', 'testing');
            this.updateActionStatus(`CyberTerminal failed: ${e.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '💻 CyberTerminal Demo'; }
        }
    }

    async triggerStartServices() {
        const btn = document.getElementById('action-start-services');
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Starting...'; }
        try {
            this.addTerminalLine('🚀 Starting core services...', 'warning', 'testing');
            const resp = await fetch('/api/local/actions/start-services', { method: 'POST' });
            const data = await resp.json();
            this.addTerminalLine(`start-services rc=${data.returncode}`, data.returncode === 0 ? 'success' : 'error', 'testing');
            this.updateActionStatus(`start-services rc=${data.returncode}`, data.returncode === 0 ? 'success' : 'error');
        } catch (e) {
            this.addTerminalLine(`start-services failed: ${e.message}`, 'error', 'testing');
            this.updateActionStatus(`start-services failed: ${e.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '🚀 Start Services'; }
        }
    }

    updateActionStatus(text, type = 'info') {
        const container = document.getElementById('action-status');
        if (!container) return;
        const pill = document.createElement('span');
        pill.className = `status-pill ${type}`;
        pill.textContent = text;
        container.innerHTML = '';
        container.appendChild(pill);
    }

    // Fallback demo commands if API is unavailable
    executeDemoCommand(command, args) {
        switch (command) {
            case 'help':
                this.addTerminalLine('Available commands: help, status, heal, scan, quantum', 'success');
                break;
            case 'status':
                this.addTerminalLine(`System Status: ${Math.round(this.stats.health)}% health (DEMO MODE)`, 'success');
                break;
            case 'heal':
                this.stats.health = Math.min(100, this.stats.health + 10);
                this.addTerminalLine('✅ Healing complete (DEMO MODE)', 'success');
                break;
            default:
                this.addTerminalLine(`Command not found: ${command} (DEMO MODE)`, 'error');
        }
    }

    addChatMessage(text, sender = 'user') {
        const output = document.getElementById('chat-output');
        if (!output) return;

        const message = document.createElement('div');
        message.className = `chat-message ${sender}`;

        const avatar = document.createElement('span');
        avatar.className = 'chat-avatar';
        avatar.textContent = sender === 'user' ? '👤' : '🤖';

        const textSpan = document.createElement('span');
        textSpan.className = 'chat-text';
        textSpan.textContent = text;

        message.appendChild(avatar);
        message.appendChild(textSpan);
        output.appendChild(message);
        output.scrollTop = output.scrollHeight;
    }

    async sendChatMessage(message) {
        if (!message.trim()) return;

        this.addChatMessage(message, 'user');

        // Simulate AI response (can wire to actual AI later)
        setTimeout(() => {
            const responses = [
                `Processing: "${message}"... Culture Ship analyzing.`,
                `Command acknowledged. 5 AI systems ready to assist.`,
                `Quantum resolver engaged. Analyzing optimal solution path.`,
                `Consciousness bridge active. Routing to ${['Copilot', 'Ollama', 'ChatDev'][Math.floor(Math.random()*3)]}.`
            ];
            this.addChatMessage(responses[Math.floor(Math.random() * responses.length)], 'system');
        }, 800);
    }
}

// Initialize interface when DOM loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.nusyq = new NuSyQInterface();
    });
} else {
    window.nusyq = new NuSyQInterface();
}
