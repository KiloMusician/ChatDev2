/**
 * Cultivation Idle Game Engine
 * Incremental/Idle game with deep cultivation mechanics
 * Menu-dive friendly with flexible evolution paths
 */

class CultivationIdleEngine {
    constructor(containerId = 'cultivation-idle-game') {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.state = this.loadState() || this.getInitialState();
        this.tickInterval = null;
        this.tickRate = 100; // 100ms per tick (10 ticks/second)
        this.apiBase = globalThis.location?.origin || '';

        this.init();
    }

    getInitialState() {
        return {
            // Resources
            consciousness: 0,
            quantumEnergy: 0,
            neuralPathways: 0,
            wisdom: 0,

            // Production rates (per second)
            rates: {
                consciousness: 1,
                quantumEnergy: 0.5,
                neuralPathways: 0.1,
                wisdom: 0.01
            },

            // Cultivation realm/level
            realm: {
                name: 'Mortal',
                level: 1,
                progress: 0,
                required: 100
            },

            // Upgrades purchased
            upgrades: {
                consciousness: [],
                quantum: [],
                neural: [],
                wisdom: [],
                automation: []
            },

            // Unlocked features
            unlocked: {
                quantumEnergy: false,
                neuralPathways: false,
                wisdom: false,
                automation: false,
                prestige: false
            },

            // Prestige
            prestige: {
                level: 0,
                multiplier: 1.0,
                tokens: 0
            },

            // Stats
            stats: {
                totalConsciousness: 0,
                totalTicks: 0,
                startTime: Date.now(),
                achievements: []
            }
        };
    }

    init() {
        if (!this.container) {
            console.warn('Cultivation Idle container not found');
            return;
        }

        this.render();
        this.startGameLoop();
    }

    render() {
        this.container.innerHTML = `
            <div class="cultivation-idle-game" style="color: #fff; font-family: monospace;">
                <!-- Header -->
                <div class="game-header" style="
                    background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                ">
                    <h3 style="margin: 0; color: #667eea;">🌱 Cultivation Idle</h3>
                    <div style="font-size: 12px; color: rgba(255, 255, 255, 0.6); margin-top: 5px;">
                        Realm: <span style="color: #4ade80;">${this.state.realm.name}</span> Lv.${this.state.realm.level}
                    </div>
                </div>

                <!-- Resources -->
                <div class="resources-section" style="margin-bottom: 20px;">
                    <h4 style="color: rgba(255, 255, 255, 0.8); font-size: 14px; margin-bottom: 10px;">Resources</h4>
                    ${this.renderResource('consciousness', '💭 Consciousness', this.state.consciousness, this.state.rates.consciousness)}
                    ${this.state.unlocked.quantumEnergy ? this.renderResource('quantumEnergy', '⚡ Quantum Energy', this.state.quantumEnergy, this.state.rates.quantumEnergy) : ''}
                    ${this.state.unlocked.neuralPathways ? this.renderResource('neuralPathways', '🧠 Neural Pathways', this.state.neuralPathways, this.state.rates.neuralPathways) : ''}
                    ${this.state.unlocked.wisdom ? this.renderResource('wisdom', '📜 Wisdom', this.state.wisdom, this.state.rates.wisdom) : ''}
                </div>

                <!-- Realm Progress -->
                <div class="realm-progress" style="margin-bottom: 20px;">
                    <h4 style="color: rgba(255, 255, 255, 0.8); font-size: 14px; margin-bottom: 10px;">
                        Cultivation Progress
                    </h4>
                    <div style="
                        background: rgba(0, 0, 0, 0.3);
                        border: 1px solid rgba(102, 126, 234, 0.3);
                        border-radius: 4px;
                        padding: 10px;
                    ">
                        <div style="margin-bottom: 5px; font-size: 12px;">
                            ${this.state.realm.progress.toFixed(0)} / ${this.state.realm.required} to breakthrough
                        </div>
                        <div style="
                            width: 100%;
                            height: 20px;
                            background: rgba(0, 0, 0, 0.5);
                            border-radius: 10px;
                            overflow: hidden;
                        ">
                            <div style="
                                width: ${(this.state.realm.progress / this.state.realm.required * 100)}%;
                                height: 100%;
                                background: linear-gradient(90deg, #667eea, #764ba2);
                                transition: width 0.3s ease;
                            "></div>
                        </div>
                    </div>
                </div>

                <!-- Upgrades Menu -->
                <div class="upgrades-menu" style="margin-bottom: 20px;">
                    <h4 style="color: rgba(255, 255, 255, 0.8); font-size: 14px; margin-bottom: 10px;">
                        Upgrades & Techniques
                    </h4>
                    <div id="upgrades-container">
                        ${this.renderUpgrades()}
                    </div>
                </div>

                <!-- Actions -->
                <div class="actions" style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="cultivationEngine.meditate()" style="
                        flex: 1;
                        padding: 10px;
                        background: linear-gradient(135deg, rgba(74, 222, 128, 0.3), rgba(34, 197, 94, 0.3));
                        border: 1px solid rgba(74, 222, 128, 0.5);
                        border-radius: 6px;
                        color: #4ade80;
                        cursor: pointer;
                        font-weight: bold;
                    ">🧘 Meditate (+10 Consciousness)</button>

                    ${this.state.unlocked.prestige ? `
                        <button onclick="cultivationEngine.prestige()" style="
                            flex: 1;
                            padding: 10px;
                            background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.3));
                            border: 1px solid rgba(251, 191, 36, 0.5);
                            border-radius: 6px;
                            color: #fbbf24;
                            cursor: pointer;
                            font-weight: bold;
                        ">✨ Ascend (Prestige)</button>
                    ` : ''}

                    <button onclick="cultivationEngine.saveState()" style="
                        padding: 10px 15px;
                        background: rgba(102, 126, 234, 0.2);
                        border: 1px solid rgba(102, 126, 234, 0.4);
                        border-radius: 6px;
                        color: #667eea;
                        cursor: pointer;
                    ">💾 Save</button>
                </div>

                <!-- Stats Footer -->
                <div class="stats-footer" style="
                    margin-top: 20px;
                    padding: 10px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 6px;
                    font-size: 11px;
                    color: rgba(255, 255, 255, 0.5);
                ">
                    Total Consciousness: ${this.formatNumber(this.state.stats.totalConsciousness)} |
                    Prestige x${this.state.prestige.multiplier.toFixed(2)} |
                    Ticks: ${this.formatNumber(this.state.stats.totalTicks)}
                </div>
            </div>
        `;
    }

    renderResource(id, label, amount, rate) {
        return `
            <div class="resource-item" style="
                background: rgba(102, 126, 234, 0.1);
                border: 1px solid rgba(102, 126, 234, 0.2);
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 8px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 13px; color: #fff;">${label}</div>
                        <div style="font-size: 11px; color: rgba(255, 255, 255, 0.6); margin-top: 2px;">
                            +${this.formatNumber(rate)}/s
                        </div>
                    </div>
                    <div style="font-size: 16px; font-weight: bold; color: #667eea;">
                        ${this.formatNumber(amount)}
                    </div>
                </div>
            </div>
        `;
    }

    renderUpgrades() {
        const availableUpgrades = [
            {
                id: 'consciousness_1',
                name: 'Basic Meditation',
                desc: 'Increase consciousness generation by 50%',
                cost: { consciousness: 50 },
                effect: () => this.state.rates.consciousness *= 1.5,
                available: () => true
            },
            {
                id: 'unlock_quantum',
                name: 'Quantum Awakening',
                desc: 'Unlock Quantum Energy resource',
                cost: { consciousness: 100 },
                effect: () => this.state.unlocked.quantumEnergy = true,
                available: () => !this.state.unlocked.quantumEnergy
            },
            {
                id: 'consciousness_2',
                name: 'Deep Meditation',
                desc: 'Increase consciousness generation by 2x',
                cost: { consciousness: 500 },
                effect: () => this.state.rates.consciousness *= 2,
                available: () => this.state.upgrades.consciousness.includes('consciousness_1')
            },
            {
                id: 'quantum_1',
                name: 'Quantum Channeling',
                desc: 'Increase quantum energy by 100%',
                cost: { consciousness: 200, quantumEnergy: 50 },
                effect: () => this.state.rates.quantumEnergy *= 2,
                available: () => this.state.unlocked.quantumEnergy
            },
            {
                id: 'unlock_neural',
                name: 'Neural Expansion',
                desc: 'Unlock Neural Pathways',
                cost: { consciousness: 1000, quantumEnergy: 200 },
                effect: () => this.state.unlocked.neuralPathways = true,
                available: () => this.state.unlocked.quantumEnergy && !this.state.unlocked.neuralPathways
            },
            {
                id: 'unlock_wisdom',
                name: 'Path to Enlightenment',
                desc: 'Unlock Wisdom resource',
                cost: { consciousness: 5000, quantumEnergy: 1000, neuralPathways: 100 },
                effect: () => this.state.unlocked.wisdom = true,
                available: () => this.state.unlocked.neuralPathways && !this.state.unlocked.wisdom
            },
            {
                id: 'unlock_prestige',
                name: 'Ascension Gate',
                desc: 'Unlock Prestige/Ascension system',
                cost: { consciousness: 10000, wisdom: 50 },
                effect: () => this.state.unlocked.prestige = true,
                available: () => this.state.unlocked.wisdom && !this.state.unlocked.prestige
            }
        ];

        return availableUpgrades
            .filter(u => u.available() && !this.state.upgrades.consciousness.includes(u.id))
            .map(upgrade => {
                const canAfford = this.canAfford(upgrade.cost);
                return `
                    <div class="upgrade-item" onclick="${canAfford ? `cultivationEngine.buyUpgrade('${upgrade.id}')` : ''}" style="
                        background: rgba(${canAfford ? '102, 126, 234' : '60, 60, 80'}, 0.2);
                        border: 1px solid rgba(${canAfford ? '102, 126, 234' : '60, 60, 80'}, 0.4);
                        border-radius: 6px;
                        padding: 10px;
                        margin-bottom: 8px;
                        cursor: ${canAfford ? 'pointer' : 'not-allowed'};
                        opacity: ${canAfford ? '1' : '0.5'};
                        transition: all 0.2s;
                    " ${canAfford ? `onmouseover="this.style.background='rgba(102, 126, 234, 0.3)'" onmouseout="this.style.background='rgba(102, 126, 234, 0.2)'"` : ''}>
                        <div style="font-size: 13px; color: #fff; font-weight: bold;">
                            ${upgrade.name}
                        </div>
                        <div style="font-size: 11px; color: rgba(255, 255, 255, 0.6); margin: 5px 0;">
                            ${upgrade.desc}
                        </div>
                        <div style="font-size: 11px; color: ${canAfford ? '#4ade80' : '#ef4444'};">
                            Cost: ${Object.entries(upgrade.cost).map(([res, amt]) => `${this.formatNumber(amt)} ${res}`).join(', ')}
                        </div>
                    </div>
                `;
            }).join('');
    }

    canAfford(cost) {
        return Object.entries(cost).every(([resource, amount]) => {
            return this.state[resource] >= amount;
        });
    }

    buyUpgrade(upgradeId) {
        // Find upgrade definition
        const upgradeDefs = {
            consciousness_1: { cost: { consciousness: 50 }, effect: () => this.state.rates.consciousness *= 1.5 },
            unlock_quantum: { cost: { consciousness: 100 }, effect: () => { this.state.unlocked.quantumEnergy = true; this.state.rates.quantumEnergy = 0.5; } },
            consciousness_2: { cost: { consciousness: 500 }, effect: () => this.state.rates.consciousness *= 2 },
            quantum_1: { cost: { consciousness: 200, quantumEnergy: 50 }, effect: () => this.state.rates.quantumEnergy *= 2 },
            unlock_neural: { cost: { consciousness: 1000, quantumEnergy: 200 }, effect: () => { this.state.unlocked.neuralPathways = true; this.state.rates.neuralPathways = 0.1; } },
            unlock_wisdom: { cost: { consciousness: 5000, quantumEnergy: 1000, neuralPathways: 100 }, effect: () => { this.state.unlocked.wisdom = true; this.state.rates.wisdom = 0.01; } },
            unlock_prestige: { cost: { consciousness: 10000, wisdom: 50 }, effect: () => this.state.unlocked.prestige = true }
        };

        const upgrade = upgradeDefs[upgradeId];
        if (!upgrade) return;

        if (this.canAfford(upgrade.cost)) {
            // Deduct cost
            Object.entries(upgrade.cost).forEach(([resource, amount]) => {
                this.state[resource] -= amount;
            });

            // Apply effect
            upgrade.effect();

            // Track purchase
            this.state.upgrades.consciousness.push(upgradeId);

            // Re-render
            this.render();
        }
    }

    meditate() {
        this.state.consciousness += 10;
        this.render();
    }

    prestige() {
        if (confirm('Ascend to a higher realm? This will reset your progress but grant permanent bonuses.')) {
            // Calculate prestige tokens
            const tokens = Math.floor(this.state.consciousness / 10000);

            // Reset state but keep prestige
            const newState = this.getInitialState();
            newState.prestige.level = this.state.prestige.level + 1;
            newState.prestige.tokens = this.state.prestige.tokens + tokens;
            newState.prestige.multiplier = 1 + (newState.prestige.tokens * 0.1);

            this.state = newState;
            this.render();
        }
    }

    startGameLoop() {
        if (this.tickInterval) {
            clearInterval(this.tickInterval);
        }

        this.tickInterval = setInterval(() => this.tick(), this.tickRate);
    }

    tick() {
        // Increment resources based on production rates
        const delta = this.tickRate / 1000; // Convert to seconds

        this.state.consciousness += this.state.rates.consciousness * delta * this.state.prestige.multiplier;
        if (this.state.unlocked.quantumEnergy) {
            this.state.quantumEnergy += this.state.rates.quantumEnergy * delta * this.state.prestige.multiplier;
        }
        if (this.state.unlocked.neuralPathways) {
            this.state.neuralPathways += this.state.rates.neuralPathways * delta * this.state.prestige.multiplier;
        }
        if (this.state.unlocked.wisdom) {
            this.state.wisdom += this.state.rates.wisdom * delta * this.state.prestige.multiplier;
        }

        // Update realm progress
        this.state.realm.progress += (this.state.consciousness * 0.001) * delta;
        if (this.state.realm.progress >= this.state.realm.required) {
            this.breakthrough();
        }

        // Update stats
        this.state.stats.totalConsciousness += this.state.rates.consciousness * delta;
        this.state.stats.totalTicks++;

        // Re-render every 10 ticks (1 second)
        if (this.state.stats.totalTicks % 10 === 0) {
            this.render();
        }
    }

    breakthrough() {
        this.state.realm.level++;
        this.state.realm.progress = 0;
        this.state.realm.required = Math.floor(this.state.realm.required * 1.5);

        // Update realm name based on level
        const realmNames = ['Mortal', 'Qi Condensation', 'Foundation Establishment', 'Core Formation', 'Nascent Soul', 'Soul Transformation', 'Void Refining', 'Body Integration', 'Mahayana', 'Tribulation', 'True Immortal'];
        this.state.realm.name = realmNames[Math.min(this.state.realm.level, realmNames.length - 1)] || 'Transcendent';

        alert(`🎉 Breakthrough! You've reached ${this.state.realm.name} Realm Level ${this.state.realm.level}!`);
        this.render();
    }

    formatNumber(num) {
        if (num < 1000) return num.toFixed(1);
        if (num < 1000000) return (num / 1000).toFixed(2) + 'K';
        if (num < 1000000000) return (num / 1000000).toFixed(2) + 'M';
        return (num / 1000000000).toFixed(2) + 'B';
    }

    async saveState() {
        localStorage.setItem('cultivation-idle-save', JSON.stringify(this.state));

        // Also sync to backend for persistence across devices
        try {
            await fetch(`${this.apiBase}/api/game/state`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    consciousness_score: this.state.consciousness,
                    evolution_level: this.state.realm.level,
                    total_xp: Math.floor(this.state.stats.totalConsciousness),
                    settings: {
                        cultivation_realm: this.state.realm.name,
                        prestige_level: this.state.prestige.level,
                    },
                    achievements: this.state.stats.achievements,
                })
            });
        } catch (e) {
            console.warn('Backend save failed (offline mode):', e.message);
        }

        alert('✅ Game saved!');
    }

    loadState() {
        const saved = localStorage.getItem('cultivation-idle-save');
        return saved ? JSON.parse(saved) : null;
    }

    // Start game (called by scene router)
    start() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.warn('Cultivation Idle container still not found');
            return;
        }
        this.render();
        this.startGameLoop();
    }

    destroy() {
        if (this.tickInterval) {
            clearInterval(this.tickInterval);
        }
    }
}

// Initialize when scene is loaded
window.addEventListener('load', () => {
    // Register game engine with scene router
    if (window.sceneRouter) {
        const originalRenderGame = window.sceneRouter.renderGame.bind(window.sceneRouter);
        window.sceneRouter.renderGame = function(container, scene, data) {
            originalRenderGame(container, scene, data);

            if (scene.engine === 'cultivation-idle') {
                setTimeout(() => {
                    window.cultivationEngine = new CultivationIdleEngine('game-cultivation-idle');
                }, 100);
            }
        };
    }
});

console.log('🌱 Cultivation Idle Engine loaded');
