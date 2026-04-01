/**
 * Terminal Viewer - Live terminal display component with auto-refresh
 * Displays streaming terminal output from backend channels
 */

class TerminalViewer {
    constructor(channel, options = {}) {
        this.channel = channel;
        this.container = null;
        this.autoRefresh = options.autoRefresh !== false; // Default true
        this.refreshInterval = options.refreshInterval || 2000; // 2 seconds
        this.maxEntries = options.maxEntries || 100;
        this.showTimestamps = options.showTimestamps !== false; // Default true
        this.showLevels = options.showLevels !== false; // Default true
        this.autoScroll = options.autoScroll !== false; // Default true
        this.filterLevel = options.filterLevel || null; // Filter by log level

        this.intervalId = null;
        this.stopStreamingFn = null;
        this.lastEntryCount = 0;
    }

    /**
     * Render the terminal viewer in a container
     * @param {string} containerId - DOM element ID to render into
     */
    async render(containerId) {
        this.container = document.getElementById(containerId);

        if (!this.container) {
            console.error(`[TerminalViewer] Container ${containerId} not found`);
            return;
        }

        // Add terminal viewer class for styling
        this.container.classList.add('terminal-viewer');
        this.container.innerHTML = `
            <div class="terminal-header">
                <span class="terminal-channel">${this.channel}</span>
                <div class="terminal-controls">
                    <button class="terminal-btn" onclick="terminalViewers['${containerId}'].refresh()">🔄</button>
                    <button class="terminal-btn" onclick="terminalViewers['${containerId}'].clear()">🗑️</button>
                    <button class="terminal-btn" onclick="terminalViewers['${containerId}'].toggleAutoScroll()">
                        ${this.autoScroll ? '📜' : '📍'}
                    </button>
                </div>
            </div>
            <div class="terminal-output" id="${containerId}-output"></div>
            <div class="terminal-footer">
                <span class="terminal-status">Loading...</span>
            </div>
        `;

        // Initial load
        await this.refresh();

        // Start auto-refresh or streaming
        if (this.autoRefresh) {
            this.startAutoRefresh();
        }

        // Store reference for button callbacks
        if (!window.terminalViewers) {
            window.terminalViewers = {};
        }
        window.terminalViewers[containerId] = this;
    }

    /**
     * Refresh terminal output from API
     */
    async refresh() {
        try {
            const entries = await window.terminalAPI.getRecent(this.channel, this.maxEntries);

            // Filter by level if specified
            const filteredEntries = this.filterLevel
                ? entries.filter(e => e.level === this.filterLevel)
                : entries;

            this.displayEntries(filteredEntries);
            this.updateStatus(`${filteredEntries.length} entries`);
            this.lastEntryCount = filteredEntries.length;
        } catch (error) {
            console.error(`[TerminalViewer] Refresh failed for ${this.channel}:`, error);
            this.updateStatus(`Error: ${error.message}`);
        }
    }

    /**
     * Display terminal entries
     * @param {Array} entries - Terminal entries to display
     */
    displayEntries(entries) {
        const outputDiv = this.container.querySelector('.terminal-output');

        if (!outputDiv) return;

        // Clear and rebuild (more reliable than incremental updates)
        outputDiv.innerHTML = entries.map(entry => this.formatEntry(entry)).join('');

        // Auto-scroll to bottom
        if (this.autoScroll) {
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    }

    /**
     * Format a single terminal entry as HTML
     * @param {object} entry - Terminal entry object
     * @returns {string} HTML string
     */
    formatEntry(entry) {
        const level = (entry.level || 'INFO').toLowerCase();
        const timestamp = this.showTimestamps
            ? `<span class="terminal-timestamp">${this.formatTimestamp(entry.timestamp)}</span>`
            : '';
        const levelBadge = this.showLevels
            ? `<span class="terminal-level terminal-level-${level}">${entry.level}</span>`
            : '';
        const message = this.escapeHtml(entry.message || '');

        return `
            <div class="terminal-entry terminal-entry-${level}" data-timestamp="${entry.timestamp}">
                ${timestamp}
                ${levelBadge}
                <span class="terminal-message">${message}</span>
            </div>
        `;
    }

    /**
     * Format timestamp for display
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted time string
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Raw text
     * @returns {string} Escaped HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Update status bar
     * @param {string} status - Status message
     */
    updateStatus(status) {
        const statusSpan = this.container.querySelector('.terminal-status');
        if (statusSpan) {
            statusSpan.textContent = status;
        }
    }

    /**
     * Clear terminal output
     */
    clear() {
        const outputDiv = this.container.querySelector('.terminal-output');
        if (outputDiv) {
            outputDiv.innerHTML = '<div class="terminal-entry terminal-entry-info">Terminal cleared</div>';
        }
    }

    /**
     * Toggle auto-scroll
     */
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        const btn = this.container.querySelector('.terminal-controls button:last-child');
        if (btn) {
            btn.textContent = this.autoScroll ? '📜' : '📍';
        }
    }

    /**
     * Start auto-refresh polling
     */
    startAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }

        this.intervalId = setInterval(() => this.refresh(), this.refreshInterval);
    }

    /**
     * Start streaming via terminal API
     */
    startStreaming() {
        if (this.stopStreamingFn) {
            this.stopStreamingFn();
        }

        this.stopStreamingFn = window.terminalAPI.startStreaming(
            this.channel,
            (newEntries) => {
                // Append new entries incrementally
                const outputDiv = this.container.querySelector('.terminal-output');
                if (outputDiv) {
                    const newHtml = newEntries.map(e => this.formatEntry(e)).join('');
                    outputDiv.insertAdjacentHTML('beforeend', newHtml);

                    // Trim if exceeds max entries
                    const allEntries = outputDiv.querySelectorAll('.terminal-entry');
                    if (allEntries.length > this.maxEntries) {
                        const toRemove = allEntries.length - this.maxEntries;
                        for (let i = 0; i < toRemove; i++) {
                            allEntries[i].remove();
                        }
                    }

                    // Auto-scroll
                    if (this.autoScroll) {
                        outputDiv.scrollTop = outputDiv.scrollHeight;
                    }

                    this.updateStatus(`${allEntries.length} entries (+${newEntries.length} new)`);
                }
            },
            this.refreshInterval
        );
    }

    /**
     * Stop auto-refresh/streaming
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        if (this.stopStreamingFn) {
            this.stopStreamingFn();
            this.stopStreamingFn = null;
        }
    }

    /**
     * Destroy viewer and cleanup
     */
    destroy() {
        this.stop();
        if (this.container) {
            this.container.innerHTML = '';
            this.container.classList.remove('terminal-viewer');
        }
    }

    /**
     * Filter entries by log level
     * @param {string|null} level - Log level to filter by (or null for all)
     */
    setFilterLevel(level) {
        this.filterLevel = level;
        this.refresh();
    }

    /**
     * Send command to this terminal channel
     * @param {string} message - Command message
     * @param {string} level - Log level
     */
    async sendCommand(message, level = 'INFO') {
        const result = await window.terminalAPI.sendCommand(this.channel, message, level);

        if (result.success !== false) {
            // Force refresh to show the command
            setTimeout(() => this.refresh(), 500);
        }

        return result;
    }
}

/**
 * Create and render a terminal viewer in one step
 * @param {string} channel - Terminal channel
 * @param {string} containerId - DOM element ID
 * @param {object} options - Viewer options
 * @returns {TerminalViewer} Created viewer instance
 */
function createTerminalViewer(channel, containerId, options = {}) {
    const viewer = new TerminalViewer(channel, options);
    viewer.render(containerId);
    return viewer;
}

// Global viewer registry
window.TerminalViewer = TerminalViewer;
window.createTerminalViewer = createTerminalViewer;

console.log('✅ Terminal Viewer loaded');
