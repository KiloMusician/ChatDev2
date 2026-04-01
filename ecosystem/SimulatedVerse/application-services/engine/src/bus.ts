import { WebSocketServer } from 'ws';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import type { BusEvent, BusMessage, BusConnection, Rpc } from '../../../shared/bus/contracts';

const ajv = new Ajv();
addFormats(ajv);

// Event validation schema
const eventSchema = {
  type: "object",
  required: ["type"],
  properties: {
    type: { type: "string" },
    dt: { type: "number" },
    timestamp: { type: "number" },
    action: { type: "string" },
    payload: {},
    id: { type: "string" },
    phase: { type: "number" },
    path: { type: "string" },
    tier: { type: "number" },
    node: { type: "string" },
    data: {},
    hash: { type: "string" },
    state: {},
    key: { type: "string" },
    value: { type: "number" },
    t: { type: "number" }
  }
};

const validateEvent = ajv.compile(eventSchema);

export class EventBus {
  private wss: WebSocketServer;
  private connections: Map<string, BusConnection> = new Map();
  private handlers: Map<keyof Rpc, Function> = new Map();
  private eventLog: BusEvent[] = [];

  constructor(port: number = 7070) {
    this.wss = new WebSocketServer({ port });
    this.setupServer();
    console.log(`[BUS] Event bus running on port ${port}`);
  }

  private setupServer() {
    this.wss.on('connection', (ws, req) => {
      const connectionId = `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const connection: BusConnection = {
        id: connectionId,
        type: 'engine', // Default, will be updated based on first message
        connected: Date.now(),
        lastSeen: Date.now()
      };

      this.connections.set(connectionId, connection);
      console.log(`[BUS] New connection: ${connectionId}`);

      ws.on('message', (raw) => {
        try {
          const message: BusMessage = JSON.parse(raw.toString());
          this.handleMessage(connectionId, message, ws);
          connection.lastSeen = Date.now();
        } catch (error) {
          console.error(`[BUS] Invalid message from ${connectionId}:`, error);
          ws.send(JSON.stringify({
            error: 'Invalid message format',
            timestamp: Date.now()
          }));
        }
      });

      ws.on('close', () => {
        this.connections.delete(connectionId);
        console.log(`[BUS] Connection closed: ${connectionId}`);
      });

      ws.on('error', (error) => {
        console.error(`[BUS] Connection error ${connectionId}:`, error);
        this.connections.delete(connectionId);
      });
    });
  }

  private handleMessage(connectionId: string, message: BusMessage, ws: any) {
    if (message.type === 'event') {
      this.handleEvent(message.data as BusEvent, connectionId);
    } else if (message.type === 'rpc') {
      this.handleRpc(message.data as any, connectionId, ws);
    }
  }

  private handleEvent(event: BusEvent, fromConnection: string) {
    // Validate event
    if (!validateEvent(event)) {
      console.error(`[BUS] Invalid event from ${fromConnection}:`, validateEvent.errors);
      return;
    }

    // Log event
    this.eventLog.push(event);
    if (this.eventLog.length > 10000) {
      this.eventLog = this.eventLog.slice(-5000); // Keep last 5000 events
    }

    // Broadcast to all other connections
    this.broadcast(event, fromConnection);

    // Handle specific event types
    this.processEvent(event);
  }

  private async handleRpc(rpcData: { method: keyof Rpc; params: any[]; id: string }, fromConnection: string, ws: any) {
    const { method, params, id } = rpcData;
    
    try {
      const handler = this.handlers.get(method);
      if (!handler) {
        throw new Error(`No handler for method: ${method}`);
      }

      const result = await handler(...params);
      
      ws.send(JSON.stringify({
        type: 'rpc_response',
        id,
        result,
        timestamp: Date.now()
      }));
    } catch (error) {
      ws.send(JSON.stringify({
        type: 'rpc_error',
        id,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now()
      }));
    }
  }

  private broadcast(event: BusEvent, excludeConnection?: string) {
    const message = JSON.stringify({
      type: 'event',
      data: event,
      timestamp: Date.now()
    });

    this.wss.clients.forEach((client) => {
      if (client.readyState === 1) { // WebSocket.OPEN
        client.send(message);
      }
    });
  }

  private processEvent(event: BusEvent) {
    // Handle specific event processing
    switch (event.type) {
      case 'TICK':
        // Engine tick - broadcast to all systems
        break;
      case 'UI.CLICK':
        console.log(`[BUS] UI Click: ${event.node}`);
        break;
      case 'STORY.EVENT':
        console.log(`[BUS] Story Event: ${event.id} Phase ${event.phase}`);
        break;
      case 'TIER.ADVANCE':
        console.log(`[BUS] Tier Advanced: ${event.fromTier} -> ${event.toTier}`);
        break;
      case 'DIRECTIVE.SPAWNED':
        console.log(`[BUS] Directive Spawned: ${event.path} (Tier ${event.tier})`);
        break;
    }
  }

  // Register RPC handlers
  registerHandler<K extends keyof Rpc>(method: K, handler: Rpc[K]) {
    this.handlers.set(method, handler);
  }

  // Emit event to all connections
  emit(event: BusEvent) {
    this.handleEvent(event, 'system');
  }

  // Get recent events for analytics
  getEventLog(limit: number = 100): BusEvent[] {
    return this.eventLog.slice(-limit);
  }

  // Get connection stats
  getConnections(): BusConnection[] {
    return Array.from(this.connections.values());
  }
}

// Singleton instance
export const eventBus = new EventBus(parseInt(process.env.BUS_PORT || '7070'));