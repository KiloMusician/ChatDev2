/**
 * Dashboard Viewer - Universal dashboard embedding and visualization
 * Supports Flask, FastAPI, static HTML, and custom JSON dashboards
 */

class DashboardViewer {
    constructor(dashboardId, options = {}) {
        this.dashboardId = dashboardId;
        this.type = options.type || 'json'; // json, iframe, custom
        this.apiEndpoint = options.apiEndpoint || null;
        this.refreshInterval = options.refreshInterval || 5000; // 5 seconds
        this.autoRefresh = options.autoRefresh !== false;
        this.container = null;
        this.intervalId = null;
        this.socketConnection = null;
    }

    /**
     * Render dashboard in container
     * @param {string} containerId - DOM element ID
     */
    async render(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`[DashboardViewer] Container ${containerId} not found`);
            return;
        }

        this.container.classList.add('dashboard-viewer');

        switch (this.type) {
            case 'iframe':
                this.renderIframe();
                break;
            case 'json':
                await this.renderJSON();
                break;
            case 'custom':
                await this.renderCustom();
                break;
            default:
                console.error(`[DashboardViewer] Unknown type: ${this.type}`);
        }

        if (this.autoRefresh && this.type !== 'iframe') {
            this.startAutoRefresh();
        }
    }

    /**
     * Render iframe-based dashboard
     */
    renderIframe() {
        this.container.innerHTML = `
            <iframe
                src="${this.apiEndpoint}"
                style="
                    width: 100%;
                    height: 100%;
                    border: none;
                    border-radius: 8px;
                    background: rgba(0, 0, 0, 0.3);
                "
                frameborder="0"
            ></iframe>
        `;
    }

    /**
     * Render JSON-based dashboard (Flask/FastAPI)
     */
    async renderJSON() {
        try {
            const response = await fetch(this.apiEndpoint);
            const data = await response.json();

            this.displayDashboardData(data);
        } catch (error) {
            console.error(`[DashboardViewer] Failed to fetch dashboard:`, error);
            this.container.innerHTML = `
                <div style="color: #ef4444; padding: 20px; text-align: center;">
                    ❌ Failed to load dashboard<br>
                    <small>${error.message}</small>
                </div>
            `;
        }
    }

    /**
     * Display dashboard data
     * @param {object} data - Dashboard data
     */
    displayDashboardData(data) {
        let html = `
            <div class="dashboard-header" style="
                padding: 15px;
                background: rgba(102, 126, 234, 0.1);
                border-bottom: 1px solid rgba(102, 126, 234, 0.3);
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <h3 style="color: #667eea; margin: 0;">${this.dashboardId}</h3>
                <button onclick="dashboardViewers['${this.container.id}'].refresh()" style="
                    padding: 6px 12px;
                    background: rgba(102, 126, 234, 0.2);
                    border: 1px solid rgba(102, 126, 234, 0.4);
                    border-radius: 4px;
                    color: #667eea;
                    cursor: pointer;
                ">🔄 Refresh</button>
            </div>
            <div class="dashboard-content" style="padding: 20px;">
        `;

        // Health Status
        if (data.status) {
            const statusColor = this.getStatusColor(data.status);
            html += `
                <div class="dashboard-stat" style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: rgba(255, 255, 255, 0.7); font-size: 14px;">System Status</span>
                        <span style="
                            padding: 4px 12px;
                            background: rgba(${statusColor}, 0.2);
                            border: 1px solid rgba(${statusColor}, 0.4);
                            border-radius: 4px;
                            color: rgb(${statusColor});
                            font-weight: bold;
                            font-size: 13px;
                        ">${data.status.toUpperCase()}</span>
                    </div>
                </div>
            `;
        }

        // AI Systems
        if (data.ai_systems_online !== undefined && data.ai_systems_total !== undefined) {
            const percentage = (data.ai_systems_online / data.ai_systems_total) * 100;
            html += this.renderProgressBar(
                'AI Systems Online',
                data.ai_systems_online,
                data.ai_systems_total,
                percentage,
                '74, 222, 128'
            );
        }

        // Healing Cycles
        if (data.healing_cycles !== undefined) {
            html += `
                <div class="dashboard-stat" style="margin-bottom: 20px;">
                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 14px; margin-bottom: 8px;">
                        Healing Cycles Completed
                    </div>
                    <div style="color: #fff; font-size: 24px; font-weight: bold;">
                        ${data.healing_cycles}
                    </div>
                </div>
            `;
        }

        // Issues
        if (data.issues !== undefined) {
            html += `
                <div class="dashboard-stat" style="margin-bottom: 20px;">
                    <div style="color: rgba(255, 255, 255, 0.7); font-size: 14px; margin-bottom: 8px;">
                        Active Issues
                    </div>
                    <div style="color: ${data.issues > 0 ? '#ef4444' : '#4ade80'}; font-size: 24px; font-weight: bold;">
                        ${data.issues}
                    </div>
                </div>
            `;
        }

        // Metrics (generic)
        if (data.metrics) {
            html += '<h4 style="color: rgba(255, 255, 255, 0.9); margin: 20px 0 10px 0;">Metrics</h4>';
            for (const [key, value] of Object.entries(data.metrics)) {
                html += `
                    <div class="metric-item" style="
                        display: flex;
                        justify-content: space-between;
                        padding: 10px;
                        margin-bottom: 8px;
                        background: rgba(0, 0, 0, 0.3);
                        border-radius: 4px;
                    ">
                        <span style="color: rgba(255, 255, 255, 0.7);">${this.formatLabel(key)}</span>
                        <span style="color: #fff; font-weight: bold;">${value}</span>
                    </div>
                `;
            }
        }

        // Timestamp
        if (data.timestamp) {
            html += `
                <div style="
                    margin-top: 20px;
                    padding-top: 15px;
                    border-top: 1px solid rgba(102, 126, 234, 0.2);
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 12px;
                ">
                    Last updated: ${new Date(data.timestamp).toLocaleString()}
                </div>
            `;
        }

        html += '</div>'; // Close dashboard-content

        this.container.innerHTML = html;

        // Store reference for refresh button
        if (!window.dashboardViewers) {
            window.dashboardViewers = {};
        }
        window.dashboardViewers[this.container.id] = this;
    }

    /**
     * Render progress bar
     */
    renderProgressBar(label, current, total, percentage, color) {
        return `
            <div class="dashboard-stat" style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: rgba(255, 255, 255, 0.7); font-size: 14px;">${label}</span>
                    <span style="color: rgba(255, 255, 255, 0.7); font-size: 13px;">${current}/${total}</span>
                </div>
                <div style="
                    width: 100%;
                    height: 20px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 10px;
                    overflow: hidden;
                    position: relative;
                ">
                    <div style="
                        width: ${percentage}%;
                        height: 100%;
                        background: linear-gradient(90deg, rgba(${color}, 0.6), rgba(${color}, 0.9));
                        transition: width 0.3s ease;
                    "></div>
                    <span style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        color: #fff;
                        font-weight: bold;
                        font-size: 11px;
                        text-shadow: 0 0 3px rgba(0, 0, 0, 0.8);
                    ">${Math.round(percentage)}%</span>
                </div>
            </div>
        `;
    }

    /**
     * Get status color RGB
     */
    getStatusColor(status) {
        switch (status.toLowerCase()) {
            case 'healthy':
            case 'operational':
            case 'ok':
                return '74, 222, 128'; // Green
            case 'initializing':
            case 'warning':
                return '251, 191, 36'; // Yellow
            case 'error':
            case 'critical':
                return '239, 68, 68'; // Red
            default:
                return '102, 126, 234'; // Blue
        }
    }

    /**
     * Format label (snake_case to Title Case)
     */
    formatLabel(key) {
        return key
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Refresh dashboard data
     */
    async refresh() {
        if (this.type === 'json') {
            await this.renderJSON();
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.intervalId = setInterval(() => this.refresh(), this.refreshInterval);
    }

    /**
     * Stop auto-refresh
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        if (this.socketConnection) {
            this.socketConnection.disconnect();
            this.socketConnection = null;
        }
    }

    /**
     * Connect via WebSocket for real-time updates
     */
    connectWebSocket(socketUrl) {
        if (typeof io === 'undefined') {
            console.warn('[DashboardViewer] Socket.IO not loaded, falling back to polling');
            return;
        }

        this.socketConnection = io(socketUrl);

        this.socketConnection.on('dashboard_update', (data) => {
            console.log('[DashboardViewer] Received WebSocket update:', data);
            this.displayDashboardData(data);
        });

        this.socketConnection.on('connect', () => {
            console.log('[DashboardViewer] WebSocket connected');
        });

        this.socketConnection.on('disconnect', () => {
            console.log('[DashboardViewer] WebSocket disconnected');
        });
    }

    /**
     * Custom renderer (override in subclass)
     */
    async renderCustom() {
        console.warn('[DashboardViewer] Custom render not implemented');
        this.container.innerHTML = '<div style="padding: 20px; color: #fff;">Custom dashboard renderer not implemented</div>';
    }

    /**
     * Destroy viewer
     */
    destroy() {
        this.stop();
        if (this.container) {
            this.container.innerHTML = '';
            this.container.classList.remove('dashboard-viewer');
        }
    }
}

/**
 * Create dashboard viewer helper
 */
function createDashboardViewer(dashboardId, containerId, options = {}) {
    const viewer = new DashboardViewer(dashboardId, options);
    viewer.render(containerId);
    return viewer;
}

// Global exports
window.DashboardViewer = DashboardViewer;
window.createDashboardViewer = createDashboardViewer;

console.log('✅ Dashboard Viewer loaded');
