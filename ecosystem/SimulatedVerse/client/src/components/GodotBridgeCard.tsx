import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Gamepad2, Zap, Users, Activity } from 'lucide-react';
import { POLLING_INTERVALS } from '@/config/polling';

interface GodotState {
  fps: number;
  entities: number;
  memory_mb?: number;
  scene?: string;
}

interface BridgeStatus {
  connected: boolean;
  clients: number;
  lastState?: GodotState;
  lastUpdate?: number;
}

export function GodotBridgeCard() {
  const [status, setStatus] = useState<BridgeStatus>({
    connected: false,
    clients: 0
  });

  useEffect(() => {
    // Mock WebSocket connection to bridge (replace with actual connection)
    const updateStatus = () => {
      // In a real implementation, this would connect to ws://localhost:8765
      // For now, we'll simulate status updates
      const mockConnected = Math.random() > 0.3; // 70% chance connected
      setStatus({
        connected: mockConnected,
        clients: mockConnected ? Math.floor(Math.random() * 3) + 1 : 0,
        lastState: mockConnected ? {
          fps: Math.floor(Math.random() * 60) + 20,
          entities: Math.floor(Math.random() * 50) + 5,
          memory_mb: Math.floor(Math.random() * 100) + 50,
          scene: ['TestScene', 'GameWorld', 'MenuScene'][Math.floor(Math.random() * 3)]
        } : undefined,
        lastUpdate: Date.now()
      });
    };

    updateStatus();
    const interval = setInterval(updateStatus, POLLING_INTERVALS.standard);
    return () => clearInterval(interval);
  }, []);

  const testAction = async (action: string) => {
    try {
      // In real implementation, send actions to bridge
      console.log(`[Bridge] Testing ${action} action`);
      
      // Mock translator API call
      if (action === 'translate') {
        const response = await fetch('http://localhost:7878/py2gd', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            code: 'def hello_world():\n    print("Hello from Python!")' 
          })
        });
        const result = await response.json();
        console.log('[Translator] Result:', result.gdscript);
      }
    } catch (error) {
      console.log(`[Bridge] ${action} test failed:`, error);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Gamepad2 className="w-5 h-5" />
          Godot Bridge
          <Badge variant={status.connected ? "default" : "destructive"}>
            {status.connected ? "Connected" : "Disconnected"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            <span>Clients: {status.clients}</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            <span>Bridge: ws://localhost:8765</span>
          </div>
        </div>

        {status.lastState && (
          <div className="p-3 bg-muted rounded-lg space-y-2">
            <div className="text-sm font-medium">Last Godot State:</div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>FPS: {status.lastState.fps}</div>
              <div>Entities: {status.lastState.entities}</div>
              <div>Memory: {status.lastState.memory_mb}MB</div>
              <div>Scene: {status.lastState.scene}</div>
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => testAction('translate')}
          >
            <Zap className="w-3 h-3 mr-1" />
            Test Translator
          </Button>
          <Button 
            size="sm" 
            variant="outline"
            onClick={() => testAction('spawn')}
          >
            Test Bridge
          </Button>
        </div>

        <div className="text-xs text-muted-foreground">
          Translator: http://localhost:7878 • TouchDesigner OSC: :9000
        </div>
      </CardContent>
    </Card>
  );
}
