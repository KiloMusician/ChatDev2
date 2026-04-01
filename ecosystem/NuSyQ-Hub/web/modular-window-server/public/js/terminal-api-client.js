/**
 * Terminal API Client - Bridge between Web UI and Terminal REST API
 * Connects scene-router.js and interface.js to the backend terminal ecosystem
 */

class TerminalAPIClient {
    constructor(baseURL = window.location.origin) {
        this.baseURL = baseURL;
        this.cache = new Map();
        this.cacheTimeout = 2000; // 2 seconds
    }

    /**
     * Send a command to a specific terminal channel
     * @param {string} channel - Terminal channel (claude, main, errors, etc.)
     * @param {string} message - Command or message to send
     * @param {string} level - Log level (INFO, WARNING, ERROR, CRITICAL, SUCCESS)
     * @param {object} metadata - Additional metadata
     * @returns {Promise<object>} Response from API
     */
    async sendCommand(channel, message, level = 'INFO', metadata = {}) {
        try {
            const response = await fetch(`${this.baseURL}/api/terminals/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    channel,
                    message,
                    level,
                    metadata: {
                        source: 'web_ui',
                        timestamp: new Date().toISOString(),
                        ...metadata
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`Terminal API error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`[TerminalAPI] Failed to send to ${channel}:`, error);
            return {
                success: false,
                error: error.message,
                channel,
                message
            };
        }
    }

    /**
     * Get recent entries from a terminal channel
     * @param {string} channel - Terminal channel name
     * @param {number} count - Number of recent entries to retrieve (default 50)
     * @returns {Promise<Array>} Array of terminal entries
     */
    async getRecent(channel, count = 50) {
        const cacheKey = `${channel}:${count}`;

        // Check cache
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }

        try {
            const response = await fetch(`${this.baseURL}/api/terminals/${channel}/recent?count=${count}`);

            if (!response.ok) {
                throw new Error(`Terminal API error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            // Cache result
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });

            return data;
        } catch (error) {
            console.error(`[TerminalAPI] Failed to get recent from ${channel}:`, error);
            return [];
        }
    }

    /**
     * List all available terminal channels
     * @returns {Promise<Array>} Array of channel names
     */
    async listChannels() {
        try {
            const response = await fetch(`${this.baseURL}/api/terminals`);

            if (!response.ok) {
                throw new Error(`Terminal API error: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('[TerminalAPI] Failed to list channels:', error);
            return [];
        }
    }

    /**
     * Execute a command and wait for response (with timeout)
     * @param {string} channel - Terminal channel
     * @param {string} command - Command to execute
     * @param {number} timeout - Timeout in milliseconds (default 5000)
     * @returns {Promise<object>} Command result
     */
    async executeCommand(channel, command, timeout = 5000) {
        const startTime = Date.now();

        // Send command
        await this.sendCommand(channel, command, 'INFO', {
            type: 'command',
            expectResponse: true
        });

        // Poll for response
        return new Promise((resolve, reject) => {
            const pollInterval = setInterval(async () => {
                if (Date.now() - startTime > timeout) {
                    clearInterval(pollInterval);
                    reject(new Error('Command timeout'));
                    return;
                }

                const recent = await this.getRecent(channel, 10);
                const response = recent.find(entry =>
                    entry.timestamp > startTime &&
                    entry.metadata?.type === 'command_response'
                );

                if (response) {
                    clearInterval(pollInterval);
                    resolve(response);
                }
            }, 500); // Poll every 500ms
        });
    }

    /**
     * Clear cache (useful for forcing refresh)
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Health check - verify Terminal API is accessible
     * @returns {Promise<boolean>} True if API is accessible
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                timeout: 3000
            });
            return response.ok;
        } catch (error) {
            console.error('[TerminalAPI] Health check failed:', error);
            return false;
        }
    }

    /**
     * Get agent status by checking recent terminal activity
     * @param {string} agentId - Agent identifier (claude, ollama, chatdev, etc.)
     * @returns {Promise<object>} Agent status object
     */
    async getAgentStatus(agentId) {
        try {
            const recent = await this.getRecent(agentId, 1);

            if (recent.length === 0) {
                return {
                    status: 'offline',
                    lastActivity: null,
                    message: 'No recent activity'
                };
            }

            const lastEntry = recent[0];
            const lastActivity = new Date(lastEntry.timestamp);
            const ageMs = Date.now() - lastActivity.getTime();

            // Determine status based on activity age
            let status;
            if (ageMs < 60000) { // < 1 minute
                status = 'online';
            } else if (ageMs < 300000) { // < 5 minutes
                status = 'idle';
            } else {
                status = 'offline';
            }

            return {
                status,
                lastActivity: lastActivity.toISOString(),
                lastMessage: lastEntry.message,
                age: ageMs
            };
        } catch (error) {
            return {
                status: 'error',
                lastActivity: null,
                message: error.message
            };
        }
    }

    /**
     * Stream terminal updates via polling (alternative to WebSocket)
     * @param {string} channel - Channel to monitor
     * @param {function} callback - Called with new entries
     * @param {number} interval - Poll interval in ms (default 2000)
     * @returns {function} Stop function to cancel streaming
     */
    startStreaming(channel, callback, interval = 2000) {
        let lastTimestamp = Date.now();

        const pollFn = async () => {
            const recent = await this.getRecent(channel, 100);
            const newEntries = recent.filter(entry =>
                new Date(entry.timestamp).getTime() > lastTimestamp
            );

            if (newEntries.length > 0) {
                callback(newEntries);
                lastTimestamp = Math.max(...newEntries.map(e =>
                    new Date(e.timestamp).getTime()
                ));
            }
        };

        const intervalId = setInterval(pollFn, interval);

        // Return stop function
        return () => clearInterval(intervalId);
    }
}

// Create global instance
window.terminalAPI = new TerminalAPIClient();

// Auto health check on load
window.addEventListener('DOMContentLoaded', async () => {
    const healthy = await window.terminalAPI.healthCheck();
    console.log(`[TerminalAPI] Health check: ${healthy ? '✅ CONNECTED' : '❌ OFFLINE'}`);

    if (!healthy) {
        console.warn('[TerminalAPI] Terminal API is not accessible. Check that terminal_api.py is running on port 8000');
    }
});

console.log('✅ Terminal API Client loaded');
