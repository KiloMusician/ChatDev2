import { useState } from 'react';
import { useMultiplayer } from '@/hooks/useMultiplayer';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { 
  Users, 
  Wifi, 
  WifiOff, 
  Crown, 
  Play, 
  LogOut, 
  Plus,
  Loader2,
  Copy,
  Check
} from 'lucide-react';

export default function MultiplayerLobby() {
  const {
    connected,
    playerId,
    roomId,
    room,
    players,
    gameState,
    isHost,
    availableRooms,
    createRoom,
    joinRoom,
    leaveRoom,
  } = useMultiplayer();

  // Create Room Form State
  const [playerName, setPlayerName] = useState('');
  const [maxPlayers, setMaxPlayers] = useState(4);
  const [gameMode, setGameMode] = useState<'cooperative' | 'competitive' | 'sandbox'>('cooperative');
  const [isPublic, setIsPublic] = useState(true);

  // Join Room Form State
  const [joinRoomCode, setJoinRoomCode] = useState('');
  const [joinPlayerName, setJoinPlayerName] = useState('');

  // UI State
  const [copiedRoomCode, setCopiedRoomCode] = useState(false);

  const handleCreateRoom = () => {
    if (!playerName.trim()) return;
    
    createRoom({
      playerName: playerName.trim(),
      maxPlayers,
      isPublic,
      gameMode
    });
  };

  const handleJoinRoom = () => {
    if (!joinRoomCode.trim() || !joinPlayerName.trim()) return;
    
    joinRoom(joinRoomCode.trim().toUpperCase(), joinPlayerName.trim());
  };

  const handleCopyRoomCode = () => {
    if (roomId) {
      navigator.clipboard.writeText(roomId);
      setCopiedRoomCode(true);
      setTimeout(() => setCopiedRoomCode(false), 2000);
    }
  };

  const getConnectionStatus = () => {
    if (connected) {
      return { label: 'Connected', variant: 'default' as const, icon: Wifi };
    }
    return { label: 'Disconnected', variant: 'destructive' as const, icon: WifiOff };
  };

  const connectionStatus = getConnectionStatus();
  const ConnectionIcon = connectionStatus.icon;

  // If player is in a room, show active room view
  if (roomId && room) {
    const playersList = Array.from(players.values());
    
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Multiplayer Lobby</h1>
          <Badge 
            variant={connectionStatus.variant}
            className="flex items-center gap-2"
            data-testid="connection-status"
          >
            <ConnectionIcon className="w-4 h-4" />
            {connectionStatus.label}
          </Badge>
        </div>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white text-2xl mb-2">Active Room</CardTitle>
                <div className="flex items-center gap-3">
                  <span className="text-gray-400">Room Code:</span>
                  <code className="text-2xl font-mono font-bold text-blue-400 bg-gray-900 px-4 py-2 rounded" data-testid="text-room-code">
                    {roomId}
                  </code>
                  <Button
                    onClick={handleCopyRoomCode}
                    variant="outline"
                    size="sm"
                    className="gap-2"
                    data-testid="button-copy-room-code"
                  >
                    {copiedRoomCode ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    {copiedRoomCode ? 'Copied!' : 'Copy'}
                  </Button>
                </div>
              </div>
              <Button
                onClick={leaveRoom}
                variant="destructive"
                className="gap-2"
                data-testid="button-leave-room"
              >
                <LogOut className="w-4 h-4" />
                Leave Room
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Room Info */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="bg-gray-900 border-gray-700">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <Users className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                    <div className="text-2xl font-bold text-white" data-testid="text-player-count">
                      {playersList.length}/{room.maxPlayers || 4}
                    </div>
                    <div className="text-sm text-gray-400">Players</div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400 mb-2" data-testid="text-consciousness-level">
                      {gameState?.consciousness || 0}
                    </div>
                    <div className="text-sm text-gray-400">Consciousness Level</div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-900 border-gray-700">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <Badge className="mb-2 text-base px-4 py-1" data-testid="badge-game-mode">
                      {room.gameMode || 'cooperative'}
                    </Badge>
                    <div className="text-sm text-gray-400">Game Mode</div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Players List */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Connected Players</h3>
              <div className="space-y-2">
                {playersList.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No players connected yet...
                  </div>
                ) : (
                  playersList.map((player) => (
                    <Card key={player.id} className="bg-gray-900 border-gray-700" data-testid={`card-player-${player.id}`}>
                      <CardContent className="py-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {player.id === room.host && (
                            <Crown className="w-5 h-5 text-yellow-400" aria-label="Host" />
                          )}
                          <span className="text-white font-medium" data-testid={`text-player-name-${player.id}`}>{player.name}</span>
                          {player.id === playerId && (
                            <Badge variant="secondary" className="text-xs" data-testid="badge-current-player">You</Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </div>

            {/* Game State Preview */}
            {gameState && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Game State</h3>
                <Card className="bg-gray-900 border-gray-700">
                  <CardContent className="pt-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold text-green-400" data-testid="text-resource-energy">
                          {gameState.resources?.energy || 0}
                        </div>
                        <div className="text-sm text-gray-400">Energy</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-blue-400" data-testid="text-resource-matter">
                          {gameState.resources?.matter || 0}
                        </div>
                        <div className="text-sm text-gray-400">Matter</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-purple-400" data-testid="text-resource-insight">
                          {gameState.resources?.insight || 0}
                        </div>
                        <div className="text-sm text-gray-400">Insight</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-yellow-400" data-testid="text-resource-harmony">
                          {gameState.resources?.harmony || 0}
                        </div>
                        <div className="text-sm text-gray-400">Harmony</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Start Game Button (Host Only) */}
            {isHost && (
              <div className="flex justify-center pt-4">
                <Button
                  size="lg"
                  className="gap-2 bg-green-600 hover:bg-green-700 text-white min-h-[44px] px-8"
                  data-testid="button-start-game"
                >
                  <Play className="w-5 h-5" />
                  Start Game
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main lobby view (not in a room)
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white">Multiplayer Lobby</h1>
        <Badge 
          variant={connectionStatus.variant}
          className="flex items-center gap-2"
          data-testid="connection-status"
        >
          <ConnectionIcon className="w-4 h-4" />
          {connectionStatus.label}
        </Badge>
      </div>

      {!connected && (
        <Card className="mb-6 bg-yellow-900/20 border-yellow-600/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 text-yellow-200">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Connecting to multiplayer server...</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Create Room */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Plus className="w-5 h-5" />
              Create Room
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="player-name" className="text-gray-300">Player Name</Label>
              <Input
                id="player-name"
                type="text"
                placeholder="Enter your name"
                value={playerName}
                onChange={(e) => setPlayerName(e.target.value)}
                className="bg-gray-900 border-gray-700 text-white mt-1 min-h-[44px]"
                data-testid="input-player-name"
                maxLength={20}
              />
            </div>

            <div>
              <Label htmlFor="max-players" className="text-gray-300">Max Players</Label>
              <select
                id="max-players"
                value={maxPlayers}
                onChange={(e) => setMaxPlayers(Number(e.target.value))}
                className="w-full mt-1 bg-gray-900 border border-gray-700 text-white rounded-md px-3 py-2 min-h-[44px]"
                data-testid="select-max-players"
              >
                {[2, 3, 4, 5, 6, 7, 8].map(num => (
                  <option key={num} value={num}>{num} Players</option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="game-mode" className="text-gray-300">Game Mode</Label>
              <select
                id="game-mode"
                value={gameMode}
                onChange={(e) => setGameMode(e.target.value as any)}
                className="w-full mt-1 bg-gray-900 border border-gray-700 text-white rounded-md px-3 py-2 min-h-[44px]"
                data-testid="select-game-mode"
              >
                <option value="cooperative">Cooperative</option>
                <option value="competitive">Competitive</option>
                <option value="sandbox">Sandbox</option>
              </select>
            </div>

            <div className="flex items-center justify-between py-2">
              <Label htmlFor="room-visibility" className="text-gray-300">Public Room</Label>
              <Switch
                id="room-visibility"
                checked={isPublic}
                onCheckedChange={setIsPublic}
                data-testid="toggle-room-visibility"
              />
            </div>

            <Button
              onClick={handleCreateRoom}
              disabled={!connected || !playerName.trim()}
              className="w-full gap-2 min-h-[44px]"
              data-testid="button-create-room"
            >
              <Plus className="w-4 h-4" />
              Create Room
            </Button>
          </CardContent>
        </Card>

        {/* Join Room */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Users className="w-5 h-5" />
              Join Room
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="room-code" className="text-gray-300">Room Code</Label>
              <Input
                id="room-code"
                type="text"
                placeholder="ABC123"
                value={joinRoomCode}
                onChange={(e) => setJoinRoomCode(e.target.value.toUpperCase())}
                className="bg-gray-900 border-gray-700 text-white mt-1 font-mono min-h-[44px]"
                data-testid="input-room-code"
                maxLength={6}
              />
            </div>

            <div>
              <Label htmlFor="join-name" className="text-gray-300">Player Name</Label>
              <Input
                id="join-name"
                type="text"
                placeholder="Enter your name"
                value={joinPlayerName}
                onChange={(e) => setJoinPlayerName(e.target.value)}
                className="bg-gray-900 border-gray-700 text-white mt-1 min-h-[44px]"
                data-testid="input-join-name"
                maxLength={20}
              />
            </div>

            <Button
              onClick={handleJoinRoom}
              disabled={!connected || !joinRoomCode.trim() || !joinPlayerName.trim()}
              className="w-full gap-2 min-h-[44px]"
              data-testid="button-join-room"
            >
              <Users className="w-4 h-4" />
              Join Room
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Public Rooms Browser */}
      <Card className="bg-gray-800 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white">Public Rooms</CardTitle>
        </CardHeader>
        <CardContent>
          {availableRooms.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No public rooms available</p>
              <p className="text-sm mt-1">Create a room to get started!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {availableRooms.map((room) => (
                <Card 
                  key={room.id}
                  className="bg-gray-900 border-gray-700 hover:border-blue-600 transition-colors"
                  data-testid={`room-card-${room.id}`}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <code className="text-lg font-mono font-bold text-blue-400" data-testid={`text-public-room-code-${room.id}`}>
                            {room.id}
                          </code>
                          <Badge variant="outline" className="text-xs" data-testid={`badge-public-room-mode-${room.id}`}>
                            {room.gameMode}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-400">
                          Host: <span className="text-white" data-testid={`text-public-room-host-${room.id}`}>{room.host}</span>
                        </div>
                      </div>
                      <Users className="w-5 h-5 text-gray-500" />
                    </div>

                    <div className="flex items-center justify-between mb-4">
                      <div className="text-sm" data-testid={`text-public-room-players-${room.id}`}>
                        <span className="text-white font-medium">
                          {room.players}/{room.maxPlayers}
                        </span>
                        <span className="text-gray-400"> players</span>
                      </div>
                      <div className="text-sm" data-testid={`text-public-room-consciousness-${room.id}`}>
                        <span className="text-purple-400 font-medium">
                          {room.consciousnessLevel}
                        </span>
                        <span className="text-gray-400"> consciousness</span>
                      </div>
                    </div>

                    <Button
                      onClick={() => {
                        setJoinRoomCode(room.id);
                        setJoinPlayerName(playerName);
                      }}
                      disabled={!connected || room.players >= room.maxPlayers}
                      className="w-full gap-2 min-h-[44px]"
                      variant={room.players >= room.maxPlayers ? "outline" : "default"}
                      data-testid={`button-quick-join-${room.id}`}
                    >
                      {room.players >= room.maxPlayers ? (
                        'Room Full'
                      ) : (
                        <>
                          <Users className="w-4 h-4" />
                          Quick Join
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
