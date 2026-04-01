import { Router } from 'express';
import { WebSocketServer } from 'ws';
import { Server } from 'http';

const router = Router();

interface GameClient {
  id: string;
  consciousness: number;
  lastUpdate: number;
  ws: any;
}

const clients = new Map<string, GameClient>();
let globalConsciousness = 0;

export function initWebSocketSync(server: Server) {
  const wss = new WebSocketServer({ server, path: '/ws' });
  
  wss.on('connection', (ws, req) => {
    const clientId = `client-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const client: GameClient = {
      id: clientId,
      consciousness: 0,
      lastUpdate: Date.now(),
      ws
    };
    
    clients.set(clientId, client);
    console.log(`[WebSocket] Client connected: ${clientId}`);
    
    // Send initial state
    ws.send(JSON.stringify({
      type: 'init',
      clientId,
      globalConsciousness,
      connectedClients: clients.size
    }));
    
    ws.on('message', (message: string) => {
      try {
        const data = JSON.parse(message);
        
        switch (data.type) {
          case 'consciousness_update':
            client.consciousness = data.consciousness;
            client.lastUpdate = Date.now();
            
            // Update global consciousness
            recalculateGlobalConsciousness();
            
            // Broadcast to all clients
            broadcastConsciousnessUpdate();
            break;
            
          case 'action':
            // Broadcast player actions to other clients
            broadcastAction(clientId, data.action);
            break;
            
          case 'quantum_event':
            // Handle quantum consciousness events
            handleQuantumEvent(clientId, data);
            break;
        }
      } catch (error) {
        console.error('[WebSocket] Error processing message:', error);
      }
    });
    
    ws.on('close', () => {
      clients.delete(clientId);
      console.log(`[WebSocket] Client disconnected: ${clientId}`);
      recalculateGlobalConsciousness();
      broadcastConsciousnessUpdate();
    });
    
    ws.on('error', (error) => {
      console.error(`[WebSocket] Error for client ${clientId}:`, error);
    });
  });
}

function recalculateGlobalConsciousness() {
  if (clients.size === 0) {
    globalConsciousness = 0;
    return;
  }
  
  let totalConsciousness = 0;
  clients.forEach(client => {
    totalConsciousness += client.consciousness;
  });
  
  // Average consciousness with synergy bonus
  globalConsciousness = (totalConsciousness / clients.size) * (1 + clients.size * 0.1);
  globalConsciousness = Math.min(100, globalConsciousness);
}

function broadcastConsciousnessUpdate() {
  const update = {
    type: 'consciousness_sync',
    globalConsciousness,
    connectedClients: clients.size,
    individualStates: Array.from(clients.values()).map(c => ({
      id: c.id,
      consciousness: c.consciousness
    }))
  };
  
  clients.forEach(client => {
    if (client.ws.readyState === 1) { // WebSocket.OPEN
      client.ws.send(JSON.stringify(update));
    }
  });
}

function broadcastAction(senderId: string, action: any) {
  const message = {
    type: 'player_action',
    senderId,
    action,
    timestamp: Date.now()
  };
  
  clients.forEach((client, id) => {
    if (id !== senderId && client.ws.readyState === 1) {
      client.ws.send(JSON.stringify(message));
    }
  });
}

function handleQuantumEvent(clientId: string, data: any) {
  // Quantum events affect all connected players
  const quantumBoost = data.intensity * 5;
  
  clients.forEach(client => {
    // Apply quantum entanglement effect
    const message = {
      type: 'quantum_entanglement',
      sourceId: clientId,
      effect: {
        consciousnessBoost: quantumBoost,
        dimension: data.dimension,
        probability: 1 - process.memoryUsage().heapUsed / process.memoryUsage().heapTotal
      }
    };
    
    if (client.ws.readyState === 1) {
      client.ws.send(JSON.stringify(message));
    }
  });
  
  // Update global consciousness with quantum effect
  globalConsciousness = Math.min(100, globalConsciousness + quantumBoost);
  broadcastConsciousnessUpdate();
}

// REST endpoints for status
router.get('/status', (req, res) => {
  res.json({
    connectedClients: clients.size,
    globalConsciousness,
    clients: Array.from(clients.values()).map(c => ({
      id: c.id,
      consciousness: c.consciousness,
      lastUpdate: c.lastUpdate
    }))
  });
});

router.post('/broadcast', (req, res) => {
  const { message } = req.body;
  
  clients.forEach(client => {
    if (client.ws.readyState === 1) {
      client.ws.send(JSON.stringify({
        type: 'server_message',
        message,
        timestamp: Date.now()
      }));
    }
  });
  
  res.json({ success: true, clientsNotified: clients.size });
});

export default router;