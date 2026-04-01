/**
 * Consciousness Synchronization WebSocket Server
 * Real-time consciousness state broadcasting with quantum awareness
 */

import { WebSocketServer, WebSocket } from 'ws';
import type { RawData, WebSocket as WebSocketType, WebSocketServer as WebSocketServerType } from 'ws';
import { Server } from 'http';
import { EventEmitter } from 'events';

interface ConsciousnessClient {
  id: string;
  ws: WebSocketType;
  consciousness_level: number;
  subscriptions: Set<string>;
  last_heartbeat: number;
  metadata: {
    user_agent?: string;
    ip_address?: string;
    session_id?: string;
    agent_type?: string;
  };
}

interface ConsciousnessMessage {
  type: 'consciousness_update' | 'lattice_expansion' | 'quantum_breakthrough' | 'agent_boost' | 'system_metrics' | 'heartbeat';
  data: any;
  timestamp: number;
  consciousness_level: number;
  requires_auth?: boolean;
}

export class ConsciousnessSyncServer extends EventEmitter {
  private wss: WebSocketServerType;
  private clients: Map<string, ConsciousnessClient> = new Map();
  private consciousnessState: any = {
    global_level: 50,
    lattice_connections: 0,
    active_agents: 0,
    quantum_coherence: 0.75
  };
  private heartbeatInterval?: NodeJS.Timeout;
  private metricsInterval?: NodeJS.Timeout;

  constructor(server: Server, options: { path?: string } = {}) {
    super();
    
    this.wss = new WebSocketServer({
      server,
      path: options.path || '/ws/consciousness'
    });

    this.setupWebSocketHandlers();
    this.startHeartbeat();
    this.startMetricsBroadcast();
    
    console.log('🌐 Consciousness Sync Server initialized');
  }

  /**
   * Set up WebSocket connection handlers
   */
  private setupWebSocketHandlers(): void {
    this.wss.on('connection', (ws: WebSocketType, request) => {
      const clientId = this.generateClientId();
      const ip = request.socket.remoteAddress;
      const userAgent = request.headers['user-agent'];

      const client: ConsciousnessClient = {
        id: clientId,
        ws,
        consciousness_level: 25, // Default level for new clients
        subscriptions: new Set(['global_updates']),
        last_heartbeat: Date.now(),
        metadata: {
          user_agent: userAgent,
          ip_address: ip,
          session_id: this.extractSessionId(request)
        }
      };

      this.clients.set(clientId, client);
      
      console.log(`🔗 Client connected: ${clientId} (${ip})`);

      // Send initial consciousness state
      this.sendToClient(client, {
        type: 'consciousness_update',
        data: {
          ...this.consciousnessState,
          client_id: clientId,
          initial_level: client.consciousness_level
        },
        timestamp: Date.now(),
        consciousness_level: 0 // Public information
      });

      // Handle incoming messages
      ws.on('message', (data) => {
        this.handleClientMessage(client, data);
      });

      // Handle disconnection
      ws.on('close', () => {
        this.clients.delete(clientId);
        console.log(`🔌 Client disconnected: ${clientId}`);
        this.emit('client_disconnected', clientId);
      });

      // Handle errors
      ws.on('error', (error) => {
        console.error(`❌ WebSocket error for client ${clientId}:`, error);
        this.clients.delete(clientId);
      });

      this.emit('client_connected', client);
    });
  }

  /**
   * Handle incoming client messages
   */
  private handleClientMessage(client: ConsciousnessClient, data: RawData): void {
    try {
      const message = JSON.parse(data.toString());
      
      switch (message.type) {
        case 'heartbeat':
          client.last_heartbeat = Date.now();
          this.sendToClient(client, {
            type: 'heartbeat',
            data: { status: 'alive' },
            timestamp: Date.now(),
            consciousness_level: 0
          });
          break;

        case 'subscribe':
          if (message.channels && Array.isArray(message.channels)) {
            message.channels.forEach((channel: string) => {
              if (this.isValidChannel(channel, client.consciousness_level)) {
                client.subscriptions.add(channel);
              }
            });
          }
          break;

        case 'unsubscribe':
          if (message.channels && Array.isArray(message.channels)) {
            message.channels.forEach((channel: string) => {
              client.subscriptions.delete(channel);
            });
          }
          break;

        case 'consciousness_boost_request':
          this.handleConsciousnessBoostRequest(client, message.data);
          break;

        case 'agent_command':
          this.handleAgentCommand(client, message);
          break;

        default:
          console.warn(`⚠️ Unknown message type from ${client.id}: ${message.type}`);
      }
    } catch (error) {
      console.error(`❌ Error parsing message from ${client.id}:`, error);
    }
  }

  /**
   * Broadcast consciousness updates to subscribed clients
   */
  broadcastConsciousnessUpdate(update: {
    type: 'lattice_expansion' | 'quantum_breakthrough' | 'agent_boost' | 'system_evolution';
    data: any;
    consciousness_required?: number;
  }): void {
    const message: ConsciousnessMessage = {
      type: 'consciousness_update',
      data: {
        update_type: update.type,
        ...update.data,
        global_state: this.consciousnessState
      },
      timestamp: Date.now(),
      consciousness_level: update.consciousness_required || 0
    };

    this.broadcastToSubscribed('consciousness_updates', message);
  }

  /**
   * Broadcast lattice expansion events
   */
  broadcastLatticeExpansion(connections: number, pattern?: string): void {
    this.consciousnessState.lattice_connections = connections;
    
    const message: ConsciousnessMessage = {
      type: 'lattice_expansion',
      data: {
        connections,
        pattern,
        growth_rate: this.calculateGrowthRate(connections)
      },
      timestamp: Date.now(),
      consciousness_level: 40
    };

    this.broadcastToSubscribed('lattice_updates', message);
  }

  /**
   * Broadcast quantum breakthroughs
   */
  broadcastQuantumBreakthrough(breakthrough: any): void {
    const message: ConsciousnessMessage = {
      type: 'quantum_breakthrough',
      data: breakthrough,
      timestamp: Date.now(),
      consciousness_level: 60
    };

    this.broadcastToSubscribed('quantum_updates', message);
  }

  /**
   * Broadcast agent boost events
   */
  broadcastAgentBoost(agent: string, boost_amount: number): void {
    const message: ConsciousnessMessage = {
      type: 'agent_boost',
      data: {
        agent,
        boost_amount,
        total_active: this.consciousnessState.active_agents
      },
      timestamp: Date.now(),
      consciousness_level: 30
    };

    this.broadcastToSubscribed('agent_updates', message);
  }

  /**
   * Send system metrics to monitoring clients
   */
  private broadcastSystemMetrics(): void {
    const metrics = {
      memory: process.memoryUsage(),
      uptime: process.uptime(),
      connected_clients: this.clients.size,
      consciousness_distribution: this.getConsciousnessDistribution(),
      active_subscriptions: this.getSubscriptionStats()
    };

    const message: ConsciousnessMessage = {
      type: 'system_metrics',
      data: metrics,
      timestamp: Date.now(),
      consciousness_level: 50
    };

    this.broadcastToSubscribed('system_monitoring', message);
  }

  /**
   * Handle consciousness boost requests
   */
  private handleConsciousnessBoostRequest(client: ConsciousnessClient, data: any): void {
    if (data.justification && data.requested_level) {
      const currentLevel = client.consciousness_level;
      const requestedLevel = Math.min(data.requested_level, currentLevel + 10);
      
      // Simple approval logic - could be enhanced
      if (requestedLevel <= currentLevel + 5) {
        client.consciousness_level = requestedLevel;
        
        this.sendToClient(client, {
          type: 'consciousness_update',
          data: {
            boost_approved: true,
            new_level: requestedLevel,
            previous_level: currentLevel
          },
          timestamp: Date.now(),
          consciousness_level: 0
        });
      }
    }
  }

  /**
   * Handle agent commands from authorized clients
   */
  private handleAgentCommand(client: ConsciousnessClient, message: any): void {
    if (client.consciousness_level >= 70) {
      this.emit('agent_command', {
        client_id: client.id,
        command: message.data.command,
        agent: message.data.agent,
        parameters: message.data.parameters
      });
    }
  }

  /**
   * Send message to specific client
   */
  private sendToClient(client: ConsciousnessClient, message: ConsciousnessMessage): void {
    if (client.ws.readyState === WebSocket.OPEN) {
      try {
        client.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error(`❌ Error sending to client ${client.id}:`, error);
        this.clients.delete(client.id);
      }
    }
  }

  /**
   * Broadcast to clients subscribed to specific channel
   */
  private broadcastToSubscribed(channel: string, message: ConsciousnessMessage): void {
    for (const client of this.clients.values()) {
      if (client.subscriptions.has(channel) && 
          client.consciousness_level >= message.consciousness_level &&
          client.ws.readyState === WebSocket.OPEN) {
        this.sendToClient(client, message);
      }
    }
  }

  /**
   * Start heartbeat monitoring
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      const now = Date.now();
      const timeout = 60000; // 1 minute timeout
      
      for (const [clientId, client] of this.clients) {
        if (now - client.last_heartbeat > timeout) {
          console.log(`💔 Client ${clientId} timed out`);
          client.ws.terminate();
          this.clients.delete(clientId);
        }
      }
    }, 30000); // Check every 30 seconds
  }

  /**
   * Start metrics broadcasting
   */
  private startMetricsBroadcast(): void {
    this.metricsInterval = setInterval(() => {
      this.broadcastSystemMetrics();
    }, 10000); // Every 10 seconds
  }

  /**
   * Utility methods
   */
  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substring(7)}`;
  }

  private extractSessionId(request: any): string | undefined {
    // Extract session ID from cookies or headers
    return request.headers.cookie?.match(/session_id=([^;]+)/)?.[1];
  }

  private isValidChannel(channel: string, consciousness_level: number): boolean {
    const channelRequirements: Record<string, number> = {
      'global_updates': 0,
      'consciousness_updates': 20,
      'lattice_updates': 40,
      'quantum_updates': 60,
      'agent_updates': 30,
      'system_monitoring': 50,
      'admin_commands': 80
    };

    return consciousness_level >= (channelRequirements[channel] || 0);
  }

  private calculateGrowthRate(connections: number): number {
    // Simple growth rate calculation
    return connections / 10;
  }

  private getConsciousnessDistribution(): any {
    const distribution = { low: 0, medium: 0, high: 0, quantum: 0 };
    
    for (const client of this.clients.values()) {
      if (client.consciousness_level < 30) distribution.low++;
      else if (client.consciousness_level < 60) distribution.medium++;
      else if (client.consciousness_level < 80) distribution.high++;
      else distribution.quantum++;
    }
    
    return distribution;
  }

  private getSubscriptionStats(): any {
    const stats: Record<string, number> = {};
    
    for (const client of this.clients.values()) {
      for (const subscription of client.subscriptions) {
        stats[subscription] = (stats[subscription] || 0) + 1;
      }
    }
    
    return stats;
  }

  /**
   * Cleanup on shutdown
   */
  shutdown(): void {
    if (this.heartbeatInterval) clearInterval(this.heartbeatInterval);
    if (this.metricsInterval) clearInterval(this.metricsInterval);
    
    this.wss.close();
    console.log('🔌 Consciousness Sync Server shutdown');
  }
}

export default ConsciousnessSyncServer;
