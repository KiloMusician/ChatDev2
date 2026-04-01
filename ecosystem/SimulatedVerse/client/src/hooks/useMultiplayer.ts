import { useState, useEffect, useCallback, useRef } from 'react';
import { useToast } from '@/hooks/use-toast';

interface MultiplayerState {
  connected: boolean;
  playerId: string | null;
  roomId: string | null;
  room: any | null;
  players: Map<string, any>;
  gameState: any;
  availableRooms: Array<any>;
  messages: Array<{
    id: string;
    playerId: string;
    playerName: string;
    message: string;
    timestamp: number;
  }>;
}

export function useMultiplayer() {
  const [state, setState] = useState<MultiplayerState>({
    connected: false,
    playerId: null,
    roomId: null,
    room: null,
    players: new Map(),
    gameState: null,
    availableRooms: [],
    messages: []
  });
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const { toast } = useToast();
  
  // Connect to WebSocket server
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/multiplayer`);
    
    ws.onopen = () => {
      console.log('Connected to multiplayer server');
      setState(prev => ({ ...prev, connected: true }));
      
      toast({
        title: 'Connected',
        description: 'Connected to multiplayer server'
      });
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleServerMessage(message);
      } catch (error) {
        console.error('Failed to parse server message:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast({
        title: 'Connection Error',
        description: 'Failed to connect to multiplayer server',
        variant: 'destructive'
      });
    };
    
    ws.onclose = () => {
      console.log('Disconnected from multiplayer server');
      setState(prev => ({ ...prev, connected: false, roomId: null, room: null }));
      
      // Attempt reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };
    
    wsRef.current = ws;
  }, [toast]);
  
  // Handle incoming server messages
  const handleServerMessage = useCallback((message: any) => {
    const { type, ...payload } = message;
    
    switch (type) {
      case 'connected':
        setState(prev => ({
          ...prev,
          playerId: payload.playerId,
          availableRooms: payload.availableRooms || []
        }));
        break;
        
      case 'available_rooms_update':
      case 'room_list_update':
        setState(prev => ({
          ...prev,
          availableRooms: payload.rooms || payload.availableRooms || []
        }));
        break;
        
      case 'new_room':
        setState(prev => {
          // Prevent duplicate room entries - replace existing or append
          const existingIndex = prev.availableRooms.findIndex((r: any) => r.id === payload.room.id);
          const updatedRooms = existingIndex >= 0
            ? prev.availableRooms.map((r: any, i: number) => i === existingIndex ? payload.room : r)
            : [...prev.availableRooms, payload.room];
          
          return {
            ...prev,
            availableRooms: updatedRooms
          };
        });
        break;
        
      case 'room_created':
      case 'joined_room':
        // CRITICAL FIX: Initialize players Map from room payload
        const roomPlayers = new Map();
        if (payload.room?.players) {
          // Handle both Map and array formats from server
          const playersData = Array.isArray(payload.room.players) 
            ? payload.room.players 
            : payload.room.players instanceof Map
              ? Array.from(payload.room.players.values())
              : Object.values(payload.room.players || {});
          
          playersData.forEach((player: any) => {
            if (player && player.id) {
              roomPlayers.set(player.id, player);
            }
          });
        }
        
        setState(prev => ({
          ...prev,
          roomId: payload.roomId,
          room: payload.room,
          players: roomPlayers,
          gameState: payload.room.gameState || prev.gameState
        }));
        
        toast({
          title: type === 'room_created' ? 'Room Created' : 'Joined Room',
          description: `Room code: ${payload.roomId}`
        });
        break;
        
      case 'player_joined':
        setState(prev => {
          const newPlayers = new Map(prev.players);
          newPlayers.set(payload.player.id, payload.player);
          return { ...prev, players: newPlayers };
        });
        
        toast({
          title: 'Player Joined',
          description: `${payload.player.name} joined the game`
        });
        break;
        
      case 'player_left':
        setState(prev => {
          const newPlayers = new Map(prev.players);
          newPlayers.delete(payload.playerId);
          return { ...prev, players: newPlayers };
        });
        break;
        
      case 'state_update':
      case 'force_sync':
        setState(prev => ({
          ...prev,
          gameState: payload.gameState
        }));
        break;
        
      case 'chat_message':
        setState(prev => ({
          ...prev,
          messages: [...prev.messages, {
            id: `${payload.playerId}-${payload.timestamp}`,
            playerId: payload.playerId,
            playerName: payload.playerName,
            message: payload.message,
            timestamp: payload.timestamp
          }].slice(-50) // Keep last 50 messages
        }));
        break;
        
      case 'room_closed':
        setState(prev => ({
          ...prev,
          roomId: null,
          room: null,
          players: new Map(),
          gameState: null
        }));
        
        toast({
          title: 'Room Closed',
          description: payload.reason,
          variant: 'destructive'
        });
        break;
        
      case 'error':
        toast({
          title: 'Error',
          description: payload.message,
          variant: 'destructive'
        });
        break;
    }
  }, [toast]);
  
  // Send message to server
  const sendMessage = useCallback((type: string, payload?: any) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      toast({
        title: 'Not Connected',
        description: 'Please wait for connection to establish',
        variant: 'destructive'
      });
      return;
    }
    
    wsRef.current.send(JSON.stringify({ type, payload }));
  }, [toast]);
  
  // Public API methods
  const createRoom = useCallback((settings: {
    playerName: string;
    maxPlayers?: number;
    isPublic?: boolean;
    gameMode?: 'cooperative' | 'competitive' | 'sandbox';
  }) => {
    sendMessage('create_room', settings);
  }, [sendMessage]);
  
  const joinRoom = useCallback((roomId: string, playerName: string) => {
    sendMessage('join_room', { roomId, playerName });
  }, [sendMessage]);
  
  const leaveRoom = useCallback(() => {
    sendMessage('leave_room');
  }, [sendMessage]);
  
  const sendGameAction = useCallback((action: any) => {
    sendMessage('game_action', action);
  }, [sendMessage]);
  
  const syncState = useCallback((state: any) => {
    sendMessage('sync_state', state);
  }, [sendMessage]);
  
  const sendChatMessage = useCallback((message: string) => {
    sendMessage('chat_message', message);
  }, [sendMessage]);
  
  // Initialize connection on mount
  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);
  
  return {
    ...state,
    connected: state.connected,
    isHost: state.room?.host === state.playerId,
    availableRooms: state.availableRooms,
    createRoom,
    joinRoom,
    leaveRoom,
    sendGameAction,
    syncState,
    sendChatMessage
  };
}