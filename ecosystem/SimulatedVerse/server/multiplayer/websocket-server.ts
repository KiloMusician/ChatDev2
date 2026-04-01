import { WebSocketServer } from 'ws';
import type { WebSocketServer as WebSocketServerType, WebSocket as WebSocketType } from 'ws';
import { Server } from 'http';
import { nanoid } from 'nanoid';
import { GamePersistence } from '../storage/game-persistence.js';

interface Player {
  id: string;
  name: string;
  colonyState: any;
  lastActivity: number;
}

interface GameRoom {
  id: string;
  host: string;
  players: Map<string, Player>;
  gameState: any;
  settings: {
    maxPlayers: number;
    isPublic: boolean;
    gameMode: 'cooperative' | 'competitive' | 'sandbox';
  };
}

export class MultiplayerServer {
  private wss: WebSocketServerType;
  private rooms: Map<string, GameRoom> = new Map();
  private playerConnections: Map<string, WebSocketType> = new Map();
  private persistence: GamePersistence;
  private roomToSessionMap: Map<string, string> = new Map();
  
  constructor(server: Server) {
    this.wss = new WebSocketServer({ server, path: '/multiplayer' });
    this.persistence = new GamePersistence();
    this.initializeWebSocket();
    console.log('[MultiplayerServer] 🌐 WebSocket server initialized on /multiplayer path');
  }
  
  private initializeWebSocket() {
    this.wss.on('connection', (ws, req) => {
      const playerId = nanoid();
      this.playerConnections.set(playerId, ws);
      
      console.log(`Player ${playerId} connected`);
      
      ws.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          this.handleMessage(playerId, message, ws);
        } catch (error) {
          console.error('Invalid message:', error);
          ws.send(JSON.stringify({ 
            type: 'error', 
            message: 'Invalid message format' 
          }));
        }
      });
      
      ws.on('close', () => {
        this.handleDisconnect(playerId);
      });
      
      ws.on('error', (error) => {
        console.error(`WebSocket error for ${playerId}:`, error);
      });
      
      // Send initial connection confirmation
      ws.send(JSON.stringify({
        type: 'connected',
        playerId,
        availableRooms: this.getPublicRooms()
      }));
    });
  }
  
  private handleMessage(playerId: string, message: any, ws: any) {
    const { type, payload } = message;
    
    switch (type) {
      case 'create_room':
        this.createRoom(playerId, payload, ws);
        break;
        
      case 'join_room':
        this.joinRoom(playerId, payload.roomId, payload.playerName, ws);
        break;
        
      case 'leave_room':
        this.leaveRoom(playerId);
        break;
        
      case 'game_action':
        this.handleGameAction(playerId, payload);
        break;
        
      case 'sync_state':
        this.syncGameState(playerId, payload);
        break;
        
      case 'chat_message':
        this.broadcastChat(playerId, payload);
        break;
        
      default:
        ws.send(JSON.stringify({ 
          type: 'error', 
          message: `Unknown message type: ${type}` 
        }));
    }
  }
  
  private async createRoom(playerId: string, settings: any, ws: any) {
    const roomId = nanoid(6).toUpperCase();
    
    const room: GameRoom = {
      id: roomId,
      host: playerId,
      players: new Map(),
      gameState: {
        tick: 0,
        resources: {
          energy: 1000,
          materials: 500,
          population: 10,
          research: 0
        },
        consciousness: 20,
        consciousnessMultiplier: 1.0,
        sharedBuildings: [],
        events: []
      },
      settings: {
        maxPlayers: settings.maxPlayers || 4,
        isPublic: settings.isPublic || false,
        gameMode: settings.gameMode || 'cooperative'
      }
    };
    
    // Add host as first player
    room.players.set(playerId, {
      id: playerId,
      name: settings.playerName || 'Host',
      colonyState: {},
      lastActivity: Date.now()
    });
    
    this.rooms.set(roomId, room);
    
    // Create database record for multiplayer session
    try {
      const result = await this.persistence.createMultiplayerSession(playerId);
      if (result.success && result.sessionId) {
        this.roomToSessionMap.set(roomId, result.sessionId);
        console.log(`[MultiplayerServer] 💾 Session ${roomId} persisted to database (${result.sessionId})`);
      }
    } catch (error) {
      console.error('[MultiplayerServer] Failed to persist session:', error);
    }
    
    ws.send(JSON.stringify({
      type: 'room_created',
      roomId,
      room: this.sanitizeRoom(room)
    }));
    
    // Notify other players about new public room
    if (room.settings.isPublic) {
      this.broadcastNewRoom(room);
    }
  }
  
  private async joinRoom(playerId: string, roomId: string, playerName: string, ws: any) {
    const room = this.rooms.get(roomId);
    
    if (!room) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Room not found'
      }));
      return;
    }
    
    if (room.players.size >= room.settings.maxPlayers) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Room is full'
      }));
      return;
    }
    
    // Add player to room
    room.players.set(playerId, {
      id: playerId,
      name: playerName || `Player ${room.players.size + 1}`,
      colonyState: {},
      lastActivity: Date.now()
    });
    
    const sessionId = this.roomToSessionMap.get(roomId);
    if (sessionId) {
      try {
        const sessionCode = roomId;
        await this.persistence.joinMultiplayerSession(playerId, sessionCode);
        console.log(`[MultiplayerServer] 💾 Player ${playerId} joined session ${roomId}`);
      } catch (error) {
        console.error('[MultiplayerServer] Failed to update session players:', error);
      }
    }
    
    // Send room state to joining player
    ws.send(JSON.stringify({
      type: 'joined_room',
      roomId,
      room: this.sanitizeRoom(room)
    }));
    
    // Notify other players
    this.broadcastToRoom(roomId, {
      type: 'player_joined',
      player: room.players.get(playerId)
    }, playerId);
  }
  
  private leaveRoom(playerId: string) {
    for (const [roomId, room] of this.rooms.entries()) {
      if (room.players.has(playerId)) {
        room.players.delete(playerId);
        
        // Notify other players
        this.broadcastToRoom(roomId, {
          type: 'player_left',
          playerId
        });
        
        // If room is empty or host left, close room
        if (room.players.size === 0 || room.host === playerId) {
          this.closeRoom(roomId);
        }
        
        break;
      }
    }
  }
  
  private handleGameAction(playerId: string, action: any) {
    const room = this.findPlayerRoom(playerId);
    if (!room) return;
    
    // Apply action to game state based on game mode
    switch (room.settings.gameMode) {
      case 'cooperative':
        this.applyCooperativeAction(room, playerId, action);
        break;
        
      case 'competitive':
        this.applyCompetitiveAction(room, playerId, action);
        break;
        
      case 'sandbox':
        this.applySandboxAction(room, playerId, action);
        break;
    }
    
    // Broadcast updated state to all players
    this.broadcastToRoom(room.id, {
      type: 'state_update',
      gameState: room.gameState,
      lastAction: {
        playerId,
        action,
        timestamp: Date.now()
      }
    });
  }
  
  private applyCooperativeAction(room: GameRoom, playerId: string, action: any) {
    const { type, payload } = action;
    
    switch (type) {
      case 'gather_resources':
        room.gameState.resources.energy += payload.amount || 10;
        room.gameState.resources.materials += (payload.amount || 10) / 2;
        break;
        
      case 'build_structure':
        if (this.canAfford(room.gameState.resources, payload.cost)) {
          this.deductResources(room.gameState.resources, payload.cost);
          room.gameState.sharedBuildings.push({
            id: nanoid(),
            type: payload.buildingType,
            builder: playerId,
            position: payload.position,
            level: 1
          });
        }
        break;
        
      case 'research':
        if (room.gameState.resources.research >= payload.cost) {
          room.gameState.resources.research -= payload.cost;
          room.gameState.consciousness += payload.consciousnessGain || 1;
        }
        break;
        
      case 'consciousness_ritual':
        const activePlayerCount = this.getActivePlayerCount(room);
        const consciousnessGain = activePlayerCount * 2;
        room.gameState.consciousness += consciousnessGain;
        
        if (room.gameState.consciousness > 50 && Math.floor(Date.now() / 10000) % 10 === 0) {
          room.gameState.consciousness += 10;
          this.broadcastToRoom(room.id, {
            type: 'breakthrough_event',
            message: 'Consciousness breakthrough achieved!',
            consciousnessGain: 10
          });
        }
        break;
    }
    
    this.applyConsciousnessSynergy(room);
    
    room.gameState.tick++;
  }
  
  private getActivePlayerCount(room: GameRoom): number {
    const now = Date.now();
    let activeCount = 0;
    for (const player of room.players.values()) {
      if (now - player.lastActivity < 60000) {
        activeCount++;
      }
    }
    return activeCount;
  }
  
  private applyConsciousnessSynergy(room: GameRoom) {
    const activePlayerCount = this.getActivePlayerCount(room);
    const totalPlayers = room.players.size;
    
    if (activePlayerCount === totalPlayers && totalPlayers > 1) {
      const currentMultiplier = room.gameState.consciousnessMultiplier || 1.0;
      room.gameState.consciousnessMultiplier = Math.min(2.0, currentMultiplier + 0.1);
    }
    
    if (room.gameState.consciousnessMultiplier && room.gameState.consciousnessMultiplier > 1.0) {
      const synergyBonus = Math.floor((room.gameState.consciousnessMultiplier - 1.0) * 10);
      if (synergyBonus > 0) {
        room.gameState.consciousness += synergyBonus;
      }
    }
  }
  
  private applyCompetitiveAction(room: GameRoom, playerId: string, action: any) {
    const player = room.players.get(playerId);
    if (!player) return;
    
    // In competitive mode, each player has their own resources
    if (!player.colonyState.resources) {
      player.colonyState.resources = {
        energy: 100,
        materials: 50,
        population: 5,
        research: 0
      };
    }
    
    const { type, payload } = action;
    
    switch (type) {
      case 'gather_resources':
        player.colonyState.resources.energy += payload.amount || 10;
        break;
        
      case 'trade':
        const targetPlayer = room.players.get(payload.targetPlayerId);
        if (targetPlayer && this.canAfford(player.colonyState.resources, payload.offer)) {
          this.deductResources(player.colonyState.resources, payload.offer);
          this.addResources(targetPlayer.colonyState.resources, payload.offer);
        }
        break;
        
      case 'attack':
        // Simple attack mechanic for competitive mode
        const defender = room.players.get(payload.targetPlayerId);
        if (defender && player.colonyState.resources.energy >= 50) {
          player.colonyState.resources.energy -= 50;
          defender.colonyState.resources.materials = 
            Math.max(0, defender.colonyState.resources.materials - 20);
        }
        break;
    }
  }
  
  private applySandboxAction(room: GameRoom, playerId: string, action: any) {
    // In sandbox mode, allow any action without restrictions
    const { type, payload } = action;
    
    switch (type) {
      case 'set_resources':
        room.gameState.resources = { ...room.gameState.resources, ...payload };
        break;
        
      case 'spawn_event':
        room.gameState.events.push({
          id: nanoid(),
          type: payload.eventType,
          creator: playerId,
          timestamp: Date.now()
        });
        break;
        
      case 'reset_world':
        if (room.host === playerId) {
          room.gameState = {
            tick: 0,
            resources: { energy: 1000, materials: 500, population: 10, research: 0 },
            consciousness: 10,
            sharedBuildings: [],
            events: []
          };
        }
        break;
    }
  }
  
  private syncGameState(playerId: string, state: any) {
    const room = this.findPlayerRoom(playerId);
    if (!room) return;
    
    // Only host can force sync in most modes
    if (room.host === playerId || room.settings.gameMode === 'sandbox') {
      room.gameState = { ...room.gameState, ...state };
      
      this.broadcastToRoom(room.id, {
        type: 'force_sync',
        gameState: room.gameState
      });
    }
  }
  
  private broadcastChat(playerId: string, message: string) {
    const room = this.findPlayerRoom(playerId);
    if (!room) return;
    
    const player = room.players.get(playerId);
    if (!player) return;
    
    this.broadcastToRoom(room.id, {
      type: 'chat_message',
      playerId,
      playerName: player.name,
      message,
      timestamp: Date.now()
    });
  }
  
  private broadcastToRoom(roomId: string, message: any, excludePlayerId?: string) {
    const room = this.rooms.get(roomId);
    if (!room) return;
    
    const messageStr = JSON.stringify(message);
    
    for (const [playerId] of room.players) {
      if (playerId !== excludePlayerId) {
        const ws = this.playerConnections.get(playerId);
        if (ws && ws.readyState === 1) {
          ws.send(messageStr);
        }
      }
    }
  }
  
  private broadcastNewRoom(room: GameRoom) {
    const message = JSON.stringify({
      type: 'new_public_room',
      room: this.sanitizeRoom(room)
    });
    
    for (const [, ws] of this.playerConnections) {
      if (ws.readyState === 1) {
        ws.send(message);
      }
    }
  }
  
  private handleDisconnect(playerId: string) {
    console.log(`Player ${playerId} disconnected`);
    
    this.leaveRoom(playerId);
    this.playerConnections.delete(playerId);
  }
  
  private async closeRoom(roomId: string) {
    const room = this.rooms.get(roomId);
    if (!room) return;
    
    // Notify all players
    this.broadcastToRoom(roomId, {
      type: 'room_closed',
      reason: 'Host disconnected or room empty'
    });
    
    const sessionId = this.roomToSessionMap.get(roomId);
    if (sessionId) {
      try {
        const sessionCode = roomId;
        await this.persistence.endMultiplayerSession(sessionCode);
        console.log(`[MultiplayerServer] 💾 Session ${roomId} marked as inactive in database`);
      } catch (error) {
        console.error('[MultiplayerServer] Failed to end session in database:', error);
      }
      this.roomToSessionMap.delete(roomId);
    }
    
    this.rooms.delete(roomId);
  }
  
  private findPlayerRoom(playerId: string): GameRoom | undefined {
    for (const room of this.rooms.values()) {
      if (room.players.has(playerId)) {
        return room;
      }
    }
    return undefined;
  }
  
  private getPublicRooms() {
    const publicRooms = [];
    for (const room of this.rooms.values()) {
      if (room.settings.isPublic) {
        publicRooms.push(this.sanitizeRoom(room));
      }
    }
    return publicRooms;
  }
  
  private sanitizeRoom(room: GameRoom) {
    return {
      id: room.id,
      playerCount: room.players.size,
      maxPlayers: room.settings.maxPlayers,
      gameMode: room.settings.gameMode,
      hostName: room.players.get(room.host)?.name || 'Unknown',
      // CRITICAL FIX: Include full player roster so clients can hydrate their player lists
      players: Array.from(room.players.values()),
      gameState: room.gameState,
      settings: room.settings
    };
  }
  
  private canAfford(resources: any, cost: any): boolean {
    for (const [resource, amount] of Object.entries(cost)) {
      if ((resources[resource] || 0) < (amount as number)) {
        return false;
      }
    }
    return true;
  }
  
  private deductResources(resources: any, cost: any) {
    for (const [resource, amount] of Object.entries(cost)) {
      resources[resource] = (resources[resource] || 0) - (amount as number);
    }
  }
  
  private addResources(resources: any, gain: any) {
    for (const [resource, amount] of Object.entries(gain)) {
      resources[resource] = (resources[resource] || 0) + (amount as number);
    }
  }
}
