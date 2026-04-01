import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Globe, MessageCircle, Settings, Copy, LogOut } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useMultiplayer } from '@/hooks/useMultiplayer';
import { useToast } from '@/hooks/use-toast';

export function MultiplayerPanel({ onGameAction }: { onGameAction?: (action: any) => void }) {
  const {
    connected,
    playerId,
    roomId,
    room,
    players,
    messages,
    isHost,
    createRoom,
    joinRoom,
    leaveRoom,
    sendChatMessage,
    sendGameAction
  } = useMultiplayer();
  
  const [playerName, setPlayerName] = useState('');
  const [roomCode, setRoomCode] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [gameMode, setGameMode] = useState<'cooperative' | 'competitive' | 'sandbox'>('cooperative');
  const [maxPlayers, setMaxPlayers] = useState('4');
  const [isPublic, setIsPublic] = useState(false);
  const { toast } = useToast();
  
  const handleCreateRoom = () => {
    if (!playerName.trim()) {
      toast({
        title: 'Name Required',
        description: 'Please enter your player name',
        variant: 'destructive'
      });
      return;
    }
    
    createRoom({
      playerName: playerName.trim(),
      maxPlayers: parseInt(maxPlayers),
      isPublic,
      gameMode
    });
  };
  
  const handleJoinRoom = () => {
    if (!playerName.trim() || !roomCode.trim()) {
      toast({
        title: 'Missing Information',
        description: 'Please enter your name and room code',
        variant: 'destructive'
      });
      return;
    }
    
    joinRoom(roomCode.trim().toUpperCase(), playerName.trim());
  };
  
  const handleSendChat = () => {
    if (chatInput.trim()) {
      sendChatMessage(chatInput.trim());
      setChatInput('');
    }
  };
  
  const copyRoomCode = () => {
    if (roomId) {
      navigator.clipboard.writeText(roomId);
      toast({
        title: 'Copied!',
        description: 'Room code copied to clipboard'
      });
    }
  };
  
  // Sync game actions with multiplayer
  React.useEffect(() => {
    if (onGameAction) {
      const originalAction = onGameAction;
      onGameAction = (action) => {
        originalAction(action);
        if (roomId) {
          sendGameAction(action);
        }
      };
    }
  }, [roomId, sendGameAction, onGameAction]);
  
  if (!connected) {
    return (
      <Card className="bg-gradient-to-br from-gray-900/50 to-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-gray-400" />
            Multiplayer
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="animate-pulse text-yellow-400 mb-2">
              Connecting to server...
            </div>
            <p className="text-xs text-gray-500">
              Please wait while we establish connection
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (!roomId) {
    // Room creation/joining UI
    return (
      <Card className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-purple-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-purple-400" />
            Multiplayer Lobby
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Your Name</label>
            <Input
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="Enter your name"
              className="bg-black/30 border-purple-500/30"
              maxLength={20}
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Create Room */}
            <div className="space-y-3 p-4 bg-black/30 rounded-lg border border-purple-500/20">
              <h3 className="font-semibold text-purple-300">Create Room</h3>
              
              <Select value={gameMode} onValueChange={(v: any) => setGameMode(v)}>
                <SelectTrigger className="bg-black/30 border-purple-500/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cooperative">Cooperative</SelectItem>
                  <SelectItem value="competitive">Competitive</SelectItem>
                  <SelectItem value="sandbox">Sandbox</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={maxPlayers} onValueChange={setMaxPlayers}>
                <SelectTrigger className="bg-black/30 border-purple-500/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2">2 Players</SelectItem>
                  <SelectItem value="3">3 Players</SelectItem>
                  <SelectItem value="4">4 Players</SelectItem>
                  <SelectItem value="8">8 Players</SelectItem>
                </SelectContent>
              </Select>
              
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="rounded"
                />
                <span className="text-gray-400">Public Room</span>
              </label>
              
              <Button
                onClick={handleCreateRoom}
                className="w-full bg-purple-600 hover:bg-purple-500"
              >
                Create Room
              </Button>
            </div>
            
            {/* Join Room */}
            <div className="space-y-3 p-4 bg-black/30 rounded-lg border border-blue-500/20">
              <h3 className="font-semibold text-blue-300">Join Room</h3>
              
              <Input
                value={roomCode}
                onChange={(e) => setRoomCode(e.target.value)}
                placeholder="Enter room code"
                className="bg-black/30 border-blue-500/30 uppercase"
                maxLength={6}
              />
              
              <Button
                onClick={handleJoinRoom}
                className="w-full bg-blue-600 hover:bg-blue-500"
              >
                Join Room
              </Button>
              
              <div className="text-xs text-gray-500 mt-4">
                <p>Ask your friend for the room code</p>
                <p>or browse public rooms below</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // In-room UI
  return (
    <Card className="bg-gradient-to-br from-cyan-900/20 to-teal-900/20 border-cyan-500/30">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            Multiplayer Room
          </div>
          <div className="flex items-center gap-2">
            <code className="px-2 py-1 bg-black/50 rounded text-cyan-300 text-sm">
              {roomId}
            </code>
            <Button
              size="sm"
              variant="ghost"
              onClick={copyRoomCode}
              className="h-7 w-7 p-0"
            >
              <Copy className="w-4 h-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={leaveRoom}
              className="h-7 w-7 p-0 text-red-400 hover:text-red-300"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Room Info */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Mode: <span className="text-cyan-300">{room?.gameMode || 'Unknown'}</span>
          </span>
          <span className="text-gray-400">
            Players: <span className="text-cyan-300">{players.size + 1}/{room?.maxPlayers || 4}</span>
          </span>
          {isHost && (
            <span className="px-2 py-1 bg-yellow-900/30 text-yellow-400 rounded text-xs">
              HOST
            </span>
          )}
        </div>
        
        {/* Players List */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-400">Players</h4>
          <div className="space-y-1">
            {Array.from(players.values()).map((player) => (
              <div
                key={player.id}
                className="flex items-center justify-between px-2 py-1 bg-black/30 rounded"
              >
                <span className="text-sm">{player.name}</span>
                {player.id === playerId && (
                  <span className="text-xs text-cyan-400">(You)</span>
                )}
              </div>
            ))}
          </div>
        </div>
        
        {/* Chat */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-400 flex items-center gap-1">
            <MessageCircle className="w-4 h-4" />
            Chat
          </h4>
          
          <div className="h-32 overflow-y-auto bg-black/30 rounded p-2 space-y-1">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-xs"
                >
                  <span className="text-cyan-400">{msg.playerName}:</span>
                  <span className="ml-1 text-gray-300">{msg.message}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            {messages.length === 0 && (
              <div className="text-xs text-gray-500 text-center py-4">
                No messages yet
              </div>
            )}
          </div>
          
          <div className="flex gap-2">
            <Input
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendChat()}
              placeholder="Type a message..."
              className="flex-1 bg-black/30 border-cyan-500/30 text-sm"
              maxLength={200}
            />
            <Button
              onClick={handleSendChat}
              size="sm"
              className="bg-cyan-600 hover:bg-cyan-500"
            >
              Send
            </Button>
          </div>
        </div>
        
        {/* Game Actions */}
        {room?.gameMode === 'cooperative' && (
          <div className="pt-2 border-t border-cyan-500/20">
            <p className="text-xs text-gray-400 mb-2">
              Working together! All resources are shared.
            </p>
            <div className="grid grid-cols-2 gap-2">
              <Button
                size="sm"
                variant="outline"
                className="border-cyan-500/30 text-cyan-400"
                onClick={() => sendGameAction({
                  type: 'gather_resources',
                  payload: { amount: 20 }
                })}
              >
                Gather Resources
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-cyan-500/30 text-cyan-400"
                onClick={() => sendGameAction({
                  type: 'research',
                  payload: { cost: 10, consciousnessGain: 2 }
                })}
              >
                Research Tech
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}