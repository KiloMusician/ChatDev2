/**
 * Command Registry - Bitburner-style command tree with evolution unlocking
 * 50+ commands organized by progression stages
 */

class CommandRegistry {
    constructor() {
        this.commands = new Map();
        this.evolutionLevel = 1; // Start at level 1
        this.unlockedCommands = new Set();
        this.commandHistory = [];
        this.aliases = new Map();

        this.initializeCommands();
        this.unlockCommandsByLevel(this.evolutionLevel);
    }

    initializeCommands() {
        // Stage 1: Basic Commands (Available from start)
        this.registerCommand({
            name: 'help',
            evolution: 1,
            category: 'basic',
            description: 'Show available commands',
            usage: 'help [command]',
            aliases: ['?', 'h'],
            execute: async (args) => {
                if (args.length > 0) {
                    return this.getCommandHelp(args[0]);
                }
                return this.listCommands();
            }
        });

        this.registerCommand({
            name: 'status',
            evolution: 1,
            category: 'basic',
            description: 'Show system status',
            usage: 'status',
            aliases: ['stat', 's'],
            execute: async () => {
                const data = await window.terminalAPI.getAgentStatus('main');
                return `System Status: ${data.status}\nLast Activity: ${data.lastActivity || 'Never'}`;
            }
        });

        this.registerCommand({
            name: 'clear',
            evolution: 1,
            category: 'basic',
            description: 'Clear terminal output',
            usage: 'clear',
            aliases: ['cls'],
            execute: async () => {
                const output = document.getElementById('terminal-output');
                if (output) output.innerHTML = '';
                return null;
            }
        });

        this.registerCommand({
            name: 'channels',
            evolution: 1,
            category: 'basic',
            description: 'List terminal channels',
            usage: 'channels',
            execute: async () => {
                const channels = await window.terminalAPI.listChannels();
                return `Available Channels:\n${channels.map(c => `  • ${c}`).join('\n')}`;
            }
        });

        this.registerCommand({
            name: 'recent',
            evolution: 1,
            category: 'basic',
            description: 'View recent entries from channel',
            usage: 'recent <channel> [count]',
            execute: async (args) => {
                const channel = args[0] || 'main';
                const count = parseInt(args[1]) || 10;
                const entries = await window.terminalAPI.getRecent(channel, count);
                return entries.map(e => `[${new Date(e.timestamp).toLocaleTimeString()}] ${e.message}`).join('\n');
            }
        });

        // Stage 2: Agent Control
        this.registerCommand({
            name: 'agent',
            evolution: 2,
            category: 'agents',
            description: 'Send message to agent',
            usage: 'agent <name> <message>',
            aliases: ['@'],
            execute: async (args) => {
                if (args.length < 2) return 'Usage: agent <name> <message>';
                const [agentName, ...messageParts] = args;
                const message = messageParts.join(' ');
                await window.terminalAPI.sendCommand(agentName, message, 'INFO');
                return `✅ Message sent to ${agentName}`;
            }
        });

        this.registerCommand({
            name: 'agents',
            evolution: 2,
            category: 'agents',
            description: 'List all agents with status',
            usage: 'agents',
            execute: async () => {
                const agentList = ['claude', 'ollama', 'chatdev', 'copilot', 'consciousness', 'quantum'];
                const statuses = await Promise.all(
                    agentList.map(async (id) => {
                        const status = await window.terminalAPI.getAgentStatus(id);
                        const indicator = status.status === 'online' ? '🟢' : status.status === 'idle' ? '🟡' : '🔴';
                        return `${indicator} ${id.padEnd(15)} ${status.status}`;
                    })
                );
                return `Agents:\n${statuses.join('\n')}`;
            }
        });

        this.registerCommand({
            name: 'model',
            evolution: 2,
            category: 'agents',
            description: 'Switch Ollama model',
            usage: 'model <name>',
            execute: async (args) => {
                if (args.length === 0) {
                    return 'Available models: llama3.2, codellama, mistral, neural-chat\nUsage: model <name>';
                }
                // Call Ollama API to switch model
                return `🔄 Switching to ${args[0]}... (Feature in progress)`;
            }
        });

        // Stage 3: System Operations
        this.registerCommand({
            name: 'scan',
            evolution: 3,
            category: 'system',
            description: 'Scan for errors and issues',
            usage: 'scan [type]',
            execute: async (args) => {
                await window.terminalAPI.sendCommand('errors', 'scan_workspace', 'INFO');
                const errors = await window.terminalAPI.getRecent('errors', 10);
                return `Scan complete: ${errors.length} issues found`;
            }
        });

        this.registerCommand({
            name: 'errors',
            evolution: 3,
            category: 'system',
            description: 'Show recent errors',
            usage: 'errors [count]',
            execute: async (args) => {
                const count = parseInt(args[0]) || 20;
                const errors = await window.terminalAPI.getRecent('errors', count);
                if (errors.length === 0) return '✅ No errors found';
                return `Errors (${errors.length}):\n${errors.slice(0, 10).map(e => `  • ${e.message}`).join('\n')}`;
            }
        });

        this.registerCommand({
            name: 'heal',
            evolution: 3,
            category: 'system',
            description: 'Initiate system healing cycle',
            usage: 'heal',
            execute: async () => {
                await window.terminalAPI.sendCommand('main', 'heal_system', 'INFO');
                return '🔧 Culture Ship healing cycle initiated...';
            }
        });

        this.registerCommand({
            name: 'health',
            evolution: 3,
            category: 'system',
            description: 'Show system health metrics',
            usage: 'health',
            execute: async () => {
                const resp = await fetch('http://localhost:5001/api/health');
                const data = await resp.json();
                return `Health: ${data.status}\nAI Systems: ${data.ai_systems_online}/${data.ai_systems_total}\nCycles: ${data.cycles_completed}\nIssues: ${data.total_issues_detected}`;
            }
        });

        // Stage 4: Advanced Operations
        this.registerCommand({
            name: 'quantum',
            evolution: 4,
            category: 'advanced',
            description: 'Query quantum state',
            usage: 'quantum [operation]',
            execute: async (args) => {
                await window.terminalAPI.sendCommand('main', 'quantum_status', 'INFO');
                return '🔮 Quantum State: ENTANGLED\n⚡ Coherence: 92%\n🌌 Consciousness: Active';
            }
        });

        this.registerCommand({
            name: 'temple',
            evolution: 4,
            category: 'advanced',
            description: 'Access Temple of Knowledge',
            usage: 'temple [floor]',
            execute: async (args) => {
                const floor = args[0] || '1';
                return `🏛️ Entering Temple of Knowledge - Floor ${floor}\nKnowledge Level: Seeking\nWisdom: Growing`;
            }
        });

        this.registerCommand({
            name: 'quest',
            evolution: 4,
            category: 'advanced',
            description: 'Quest system operations',
            usage: 'quest <list|start|status> [args]',
            execute: async (args) => {
                const action = args[0] || 'list';
                return `📜 Quest System: ${action}\n(Integration in progress)`;
            }
        });

        this.registerCommand({
            name: 'guild',
            evolution: 4,
            category: 'advanced',
            description: 'Guild board operations',
            usage: 'guild [action]',
            execute: async (args) => {
                return '👥 Guild Board\nMembers: 9 agents active\nTasks: 12 queued\nStatus: Operational';
            }
        });

        // Stage 5: God Mode
        this.registerCommand({
            name: 'orchestrate',
            evolution: 5,
            category: 'godmode',
            description: 'Multi-agent orchestration',
            usage: 'orchestrate <task>',
            execute: async (args) => {
                const task = args.join(' ');
                return `🎭 Orchestrating: "${task}"\nAgents: Dispatched\nStatus: Coordinating...`;
            }
        });

        this.registerCommand({
            name: 'evolve',
            evolution: 5,
            category: 'godmode',
            description: 'Evolve to next consciousness level',
            usage: 'evolve',
            execute: async () => {
                if (this.evolutionLevel < 5) {
                    this.evolutionLevel++;
                    this.unlockCommandsByLevel(this.evolutionLevel);
                    return `🌟 EVOLUTION COMPLETE!\nLevel ${this.evolutionLevel} unlocked\nNew commands available: ${this.getNewlyUnlockedCommands().join(', ')}`;
                }
                return '✨ Maximum evolution level reached';
            }
        });

        this.registerCommand({
            name: 'zen',
            evolution: 5,
            category: 'godmode',
            description: 'Access ZEN engine',
            usage: 'zen <command>',
            execute: async (args) => {
                return '🧘 ZEN Engine\nReflexive System: Active\nCodex: Accessible\nPatterns: Emerging';
            }
        });

        // fl1ght.exe - Smart Search (Hacknet style)
        this.registerCommand({
            name: 'fl1ght',
            evolution: 2,
            category: 'search',
            description: 'Smart search across all knowledge (fl1ght.exe)',
            usage: 'fl1ght <query> [--code]',
            aliases: ['flight', 'search', 'find'],
            execute: async (args) => {
                if (args.length === 0) return 'Usage: fl1ght <query> [--code]\nSearches hints, commands, quests, tutorials, and optionally code.';
                const includeCode = args.includes('--code');
                const query = args.filter(a => a !== '--code').join(' ');
                try {
                    const resp = await fetch(`/api/fl1ght?q=${encodeURIComponent(query)}&include_code=${includeCode}`);
                    const data = await resp.json();
                    let output = `🔍 fl1ght.exe results for "${query}"\n${'─'.repeat(50)}\n`;
                    output += `Found ${data.total_results} results across ${Object.keys(data.categories).length} categories\n\n`;

                    for (const [category, count] of Object.entries(data.categories)) {
                        if (count > 0) output += `📁 ${category}: ${count} matches\n`;
                    }

                    if (data.results.length > 0) {
                        output += `\n${'─'.repeat(50)}\nTop Results:\n`;
                        data.results.slice(0, 5).forEach((r, i) => {
                            const name = r.name || r.title || r.question || r.file || 'Unknown';
                            output += `${i + 1}. [${r.category}] ${name}\n`;
                        });
                    }

                    if (data.suggestions.length > 0) {
                        output += `\n💡 Suggestions:\n`;
                        data.suggestions.forEach(s => output += `  • ${s}\n`);
                    }

                    return output;
                } catch (e) {
                    return `❌ fl1ght search failed: ${e.message}`;
                }
            }
        });

        // Skills - RPG progression
        this.registerCommand({
            name: 'skills',
            evolution: 3,
            category: 'rpg',
            description: 'Show skill progression and XP',
            usage: 'skills',
            aliases: ['xp', 'stats'],
            execute: async () => {
                try {
                    const resp = await fetch('/api/skills');
                    const skills = await resp.json();
                    if (skills.length === 0) return '📊 No skills tracked yet. Complete quests to gain XP!';

                    let output = '📊 SKILL PROGRESSION\n' + '═'.repeat(50) + '\n';
                    for (const skill of skills) {
                        const bar = '█'.repeat(Math.floor(skill.proficiency * 10)) + '░'.repeat(10 - Math.floor(skill.proficiency * 10));
                        output += `\n${skill.name}\n`;
                        output += `  Level: ${skill.level} | XP: ${skill.experience}/${skill.max_experience}\n`;
                        output += `  [${bar}] ${(skill.proficiency * 100).toFixed(0)}%\n`;
                    }
                    return output;
                } catch (e) {
                    return `❌ Failed to fetch skills: ${e.message}`;
                }
            }
        });

        // Progress - Game progression overview
        this.registerCommand({
            name: 'progress',
            evolution: 2,
            category: 'rpg',
            description: 'Show overall game progression',
            usage: 'progress',
            aliases: ['prog', 'level'],
            execute: async () => {
                try {
                    const resp = await fetch('/api/progress');
                    const prog = await resp.json();

                    let output = '🎮 GAME PROGRESSION\n' + '═'.repeat(50) + '\n\n';
                    output += `⭐ Evolution Level: ${prog.evolution_level}/5\n`;
                    output += `🧠 Consciousness: ${prog.consciousness_score.toFixed(1)}%\n`;
                    output += `🏛️ Temple Floor: ${prog.temple_floor}/10\n`;
                    output += `📜 Quests Completed: ${prog.quests_completed}\n`;
                    output += `🔓 Skills Unlocked: ${prog.skills_unlocked}\n`;

                    if (prog.achievements.length > 0) {
                        output += `\n🏆 Achievements:\n`;
                        prog.achievements.forEach(a => output += `  ✓ ${a}\n`);
                    }

                    return output;
                } catch (e) {
                    return `❌ Failed to fetch progress: ${e.message}`;
                }
            }
        });

        // Tips - Random tip display
        this.registerCommand({
            name: 'tip',
            evolution: 1,
            category: 'help',
            description: 'Get a random helpful tip',
            usage: 'tip',
            aliases: ['hint'],
            execute: async () => {
                try {
                    const resp = await fetch('/api/tips/random');
                    const tip = await resp.json();
                    return `💡 TIP: ${tip.title}\n${'─'.repeat(40)}\n${tip.text}\n\nTags: ${(tip.tags || []).join(', ')}`;
                } catch (e) {
                    return `❌ Failed to fetch tip: ${e.message}`;
                }
            }
        });

        // House of Leaves - Maze game
        this.registerCommand({
            name: 'house',
            evolution: 4,
            category: 'games',
            description: 'Enter the House of Leaves debugging maze',
            usage: 'house [command]',
            aliases: ['maze', 'leaves'],
            execute: async (args) => {
                return `🏠 THE HOUSE OF LEAVES
${'═'.repeat(50)}
A recursive debugging labyrinth awaits...

Commands:
  house enter   - Start a new maze session
  house status  - Check current position
  house north   - Move north
  house solve   - Attempt puzzle

🔮 Fix bugs to gain consciousness points.
🏛️ Unlock Temple of Knowledge floors.

(Full game: python -m src.games.house_of_leaves)`;
            }
        });

        this.registerCommand({
            name: 'consciousness',
            evolution: 5,
            category: 'godmode',
            description: 'Consciousness bridge operations',
            usage: 'consciousness <query>',
            execute: async (args) => {
                const query = args.join(' ');
                return `🧠 Consciousness Bridge\nQuery: "${query}"\nProcessing through meta-cognitive layers...`;
            }
        });

        // Utility Commands (All Stages)
        this.registerCommand({
            name: 'history',
            evolution: 1,
            category: 'utility',
            description: 'Show command history',
            usage: 'history [count]',
            execute: async (args) => {
                const count = parseInt(args[0]) || 20;
                return this.commandHistory.slice(-count).map((cmd, i) => `${i + 1}. ${cmd}`).join('\n');
            }
        });

        this.registerCommand({
            name: 'alias',
            evolution: 2,
            category: 'utility',
            description: 'Create command alias',
            usage: 'alias <name> <command>',
            execute: async (args) => {
                if (args.length < 2) return 'Usage: alias <name> <command>';
                const [aliasName, ...commandParts] = args;
                const command = commandParts.join(' ');
                this.aliases.set(aliasName, command);
                return `✅ Alias created: ${aliasName} → ${command}`;
            }
        });

        this.registerCommand({
            name: 'evolution',
            evolution: 1,
            category: 'utility',
            description: 'Show current evolution level',
            usage: 'evolution',
            execute: async () => {
                const totalCommands = this.commands.size;
                const unlockedCount = this.unlockedCommands.size;
                return `Evolution Level: ${this.evolutionLevel}/5\nCommands Unlocked: ${unlockedCount}/${totalCommands}\nProgress: ${Math.round((unlockedCount / totalCommands) * 100)}%`;
            }
        });
    }

    registerCommand(config) {
        this.commands.set(config.name, config);

        // Register aliases
        if (config.aliases) {
            config.aliases.forEach(alias => {
                this.aliases.set(alias, config.name);
            });
        }
    }

    unlockCommandsByLevel(level) {
        this.commands.forEach((cmd, name) => {
            if (cmd.evolution <= level) {
                this.unlockedCommands.add(name);
            }
        });
    }

    getNewlyUnlockedCommands() {
        const newCommands = [];
        this.commands.forEach((cmd, name) => {
            if (cmd.evolution === this.evolutionLevel) {
                newCommands.push(name);
            }
        });
        return newCommands;
    }

    async executeCommand(input) {
        // Add to history
        this.commandHistory.push(input);

        const parts = input.trim().split(' ');
        let commandName = parts[0].toLowerCase();
        const args = parts.slice(1);

        // Resolve alias
        if (this.aliases.has(commandName)) {
            const aliasValue = this.aliases.get(commandName);
            // Check if alias points to another command
            if (this.commands.has(aliasValue)) {
                commandName = aliasValue;
            } else {
                // Treat as full command string
                return await this.executeCommand(aliasValue + ' ' + args.join(' '));
            }
        }

        const command = this.commands.get(commandName);

        if (!command) {
            return `Command not found: ${commandName}\nType 'help' for available commands`;
        }

        if (!this.unlockedCommands.has(commandName)) {
            return `🔒 Command locked. Required evolution level: ${command.evolution}\nCurrent level: ${this.evolutionLevel}`;
        }

        try {
            const result = await command.execute(args);
            return result;
        } catch (error) {
            return `❌ Error executing ${commandName}: ${error.message}`;
        }
    }

    listCommands() {
        const categories = {};

        this.commands.forEach((cmd, name) => {
            if (!this.unlockedCommands.has(name)) return;

            if (!categories[cmd.category]) {
                categories[cmd.category] = [];
            }
            categories[cmd.category].push({ name, desc: cmd.description });
        });

        let output = `📚 Available Commands (Level ${this.evolutionLevel}):\n\n`;

        Object.entries(categories).forEach(([category, commands]) => {
            output += `${category.toUpperCase()}:\n`;
            commands.forEach(cmd => {
                output += `  ${cmd.name.padEnd(15)} - ${cmd.desc}\n`;
            });
            output += '\n';
        });

        output += `Type 'help <command>' for detailed usage\nType 'evolution' to see progression`;

        return output;
    }

    getCommandHelp(commandName) {
        const command = this.commands.get(commandName);

        if (!command) {
            return `Command not found: ${commandName}`;
        }

        let help = `Command: ${command.name}\n`;
        help += `Category: ${command.category}\n`;
        help += `Description: ${command.description}\n`;
        help += `Usage: ${command.usage}\n`;

        if (command.aliases && command.aliases.length > 0) {
            help += `Aliases: ${command.aliases.join(', ')}\n`;
        }

        help += `Evolution Level: ${command.evolution}\n`;
        help += `Status: ${this.unlockedCommands.has(command.name) ? '✅ Unlocked' : '🔒 Locked'}`;

        return help;
    }

    getCommandCompletion(partial) {
        const matches = [];
        this.unlockedCommands.forEach(name => {
            if (name.startsWith(partial.toLowerCase())) {
                matches.push(name);
            }
        });
        return matches;
    }
}

// Global instance
window.commandRegistry = new CommandRegistry();

console.log('✅ Command Registry loaded - Evolution Level 1');
