/**
 * Lightweight widget switcher for the Culture Ship bridge.
 * Widgets are simple renderers that write HTML into #widget-container.
 */

const widgetRegistry = {
    hub: {
        title: 'Main Hub',
        render: (el) => {
            el.innerHTML = `
                <h3>🛰️ Culture Ship Hub</h3>
                <p>Choose a widget from the switcher to display contextual tools.</p>
                <ul>
                    <li>Shop Index (mock)</li>
                    <li>Status Peek</li>
                    <li>Log Tail</li>
                </ul>
            `;
        },
    },
    shop: {
        title: 'Shop Index',
        render: (el) => {
            el.innerHTML = `
                <h3>🛒 Ship Shop Index</h3>
                <div class="widget-list">
                    <button class="widget-btn" data-item="terminal-upgrade">Terminal Upgrade Mk.II</button>
                    <button class="widget-btn" data-item="synth-module">Modular Synth Patch Pack</button>
                    <button class="widget-btn" data-item="ct-mission-pack">CyberTerminal Mission Pack</button>
                </div>
                <p class="widget-hint">Click an item to log it to the testing channel.</p>
            `;
            el.querySelectorAll('.widget-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const item = btn.dataset.item;
                    window.nusyq?.addTerminalLine(`🛒 Selected ${item}`, 'success', 'testing');
                    window.nusyq?.updateActionStatus(`Selected ${item}`, 'info');
                });
            });
        },
    },
    status: {
        title: 'Status Peek',
        render: (() => {
            let intervalId;
            let lastPorts = {};
            let lastReceipt = '';
            let lastArtifact = '';

            const formatMessage = (prefix, text) => {
                window.nusyq?.addTerminalLine(`${prefix} ${text}`, 'info', 'service-status');
            };

            const greetChange = (label, ok) => {
                const verb = ok ? 'back online' : 'now offline';
                formatMessage('⚙️ Status', `${label} ${verb}`);
            };

            const renderPorts = (ports) => {
                return Object.entries(ports)
                    .map(([label, ok]) => {
                        const emoji = ok ? '🟢' : '⚠️';
                        return `<div class="status-row">
                            <span>${emoji}</span>
                            <strong>${label}</strong>
                            <span>${ok ? 'up' : 'down'}</span>
                        </div>`;
                    })
                    .join('');
            };

            const renderDuplicates = (duplicates) => {
                return Object.entries(duplicates)
                    .map(([label, count]) => {
                        const emoji = count <= 1 ? '🟢' : '🟡';
                        return `<div class="status-row">
                            <span>${emoji}</span>
                            <strong>${label}</strong>
                            <span>${count} instance${count === 1 ? '' : 's'}</span>
                        </div>`;
                    })
                    .join('');
            };

            const parseArtifact = (splitPath) => {
                if (!splitPath) return 'n/a';
                const parts = splitPath.split(/[\\/]/).filter(Boolean);
                return parts.slice(-2).join('/');
            };

            const updateView = (el, data) => {
                const overall = Object.values(data.ports).every(Boolean);
                const statusLabel = overall ? 'All systems nominal' : 'Attention required';
                el.innerHTML = `
                    <h3>📡 Status Peek</h3>
                    <p class="status-overview">${statusLabel}</p>
                    <div class="status-chunk">
                        <h4>Ports</h4>
                        <div class="status-grid">${renderPorts(data.ports)}</div>
                    </div>
                    <div class="status-chunk">
                        <h4>Flagged Launchers</h4>
                        <div class="status-grid">${renderDuplicates(data.duplicates)}</div>
                    </div>
                    <div class="status-chunk">
                        <h4>ChatDev</h4>
                        <p><strong>Latest receipt:</strong> ${data.chatdev_receipt}</p>
                        <p><strong>WareHouse:</strong> ${parseArtifact(data.warehouse_artifact)}</p>
                    </div>
                `;
            };

            const logChanges = (data) => {
                Object.entries(data.ports).forEach(([label, ok]) => {
                    if (Object.prototype.hasOwnProperty.call(lastPorts, label) && lastPorts[label] !== ok) {
                        greetChange(label, ok);
                    }
                    lastPorts[label] = ok;
                });
                if (data.chatdev_receipt && data.chatdev_receipt !== lastReceipt) {
                    formatMessage('🧾 ChatDev', `New artifact: ${data.chatdev_receipt}`);
                    lastReceipt = data.chatdev_receipt;
                }
                if (data.warehouse_artifact && data.warehouse_artifact !== lastArtifact) {
                    lastArtifact = data.warehouse_artifact;
                }
            };

            const fetchStatus = async (el) => {
                try {
                    const resp = await fetch('/api/status/ship');
                    if (!resp.ok) throw new Error('status fetch failed');
                    const data = await resp.json();
                    logChanges(data);
                    updateView(el, data);
                } catch (error) {
                    el.innerHTML = `<h3>📡 Status Peek</h3><p>Error fetching status</p>`;
                }
            };

            return async (el) => {
                if (intervalId) {
                    clearInterval(intervalId);
                }
                await fetchStatus(el);
                intervalId = setInterval(() => fetchStatus(el), 6000);
            };
        })(),
    },
    logs: {
        title: 'Log Tail (testing)',
        render: async (el) => {
            el.innerHTML = `<h3>📜 Log Tail</h3><pre class="widget-log" id="widget-log"></pre>`;
            const target = el.querySelector('#widget-log');
            try {
                const resp = await fetch('/api/logs/testing');
                if (resp.ok) {
                    const data = await resp.json();
                    target.textContent = data.lines.map(l => l.message || JSON.stringify(l)).slice(-10).join('\n');
                }
            } catch (e) {
                target.textContent = 'Error loading logs';
            }
        },
    },
};

export function initWidgetSwitcher() {
    const select = document.getElementById('widget-switcher');
    const container = document.getElementById('widget-container');
    const backBtn = document.getElementById('widget-back');
    if (!select || !container || !backBtn) return;

    const render = (key) => {
        const widget = widgetRegistry[key] || widgetRegistry.hub;
        container.innerHTML = '';
        const title = document.getElementById('widget-title');
        if (title) title.textContent = widget.title;
        widget.render(container);
    };

    select.addEventListener('change', (e) => {
        render(e.target.value);
    });

    backBtn.addEventListener('click', () => {
        select.value = 'hub';
        render('hub');
        window.nusyq?.addTerminalLine('🔙 Back to hub widget', 'info', 'testing');
    });

    window.widgetInit = () => render(select.value || 'hub');
    render('hub');
}
