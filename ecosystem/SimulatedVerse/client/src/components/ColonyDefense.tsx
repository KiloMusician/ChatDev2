import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Zap, AlertTriangle, Target, Heart } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface Enemy {
  id: string;
  x: number;
  y: number;
  health: number;
  maxHealth: number;
  speed: number;
  damage: number;
  type: 'drone' | 'tank' | 'swarm';
  color: string;
}

interface Turret {
  id: string;
  x: number;
  y: number;
  type: 'laser' | 'missile' | 'plasma';
  damage: number;
  range: number;
  fireRate: number;
  lastFired: number;
  level: number;
}

interface Wave {
  number: number;
  enemies: Enemy[];
  reward: number;
  difficulty: number;
}

export function ColonyDefense({ resources, onResourceUpdate }: any) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const [gameState, setGameState] = useState<'idle' | 'playing' | 'paused' | 'gameover'>('idle');
  const [wave, setWave] = useState(1);
  const [enemies, setEnemies] = useState<Enemy[]>([]);
  const [turrets, setTurrets] = useState<Turret[]>([]);
  const [colonyHealth, setColonyHealth] = useState(100);
  const [score, setScore] = useState(0);
  const [selectedTurretType, setSelectedTurretType] = useState<'laser' | 'missile' | 'plasma'>('laser');
  const { toast } = useToast();

  const turretCosts = {
    laser: { materials: 50, energy: 25 },
    missile: { materials: 100, energy: 50 },
    plasma: { materials: 200, energy: 100 }
  };

  const turretStats = {
    laser: { damage: 10, range: 150, fireRate: 500 },
    missile: { damage: 30, range: 200, fireRate: 1500 },
    plasma: { damage: 50, range: 250, fireRate: 2000 }
  };

  // Generate enemies for current wave
  const generateWave = (waveNumber: number): Enemy[] => {
    const enemyCount = 5 + waveNumber * 2;
    const newEnemies: Enemy[] = [];
    
    for (let i = 0; i < enemyCount; i++) {
      const type = Math.random() < 0.6 ? 'drone' : Math.random() < 0.8 ? 'swarm' : 'tank';
      const enemy: Enemy = {
        id: `enemy-${Date.now()}-${i}`,
        x: 800 + i * 50,
        y: 100 + Math.random() * 300,
        health: type === 'drone' ? 20 : type === 'swarm' ? 10 : 50,
        maxHealth: type === 'drone' ? 20 : type === 'swarm' ? 10 : 50,
        speed: type === 'drone' ? 2 : type === 'swarm' ? 3 : 1,
        damage: type === 'drone' ? 5 : type === 'swarm' ? 2 : 10,
        type,
        color: type === 'drone' ? '#ff6b6b' : type === 'swarm' ? '#ffd93d' : '#6bcf7f'
      };
      newEnemies.push(enemy);
    }
    
    return newEnemies;
  };

  // Place turret
  const placeTurret = (x: number, y: number) => {
    const cost = turretCosts[selectedTurretType];
    
    if (resources.materials < cost.materials || resources.energy < cost.energy) {
      toast({
        title: 'Insufficient Resources',
        description: `Need ${cost.materials} materials and ${cost.energy} energy`,
        variant: 'destructive'
      });
      return;
    }
    
    const newTurret: Turret = {
      id: `turret-${Date.now()}`,
      x,
      y,
      type: selectedTurretType,
      ...turretStats[selectedTurretType],
      lastFired: 0,
      level: 1
    };
    
    setTurrets(prev => [...prev, newTurret]);
    onResourceUpdate({
      materials: resources.materials - cost.materials,
      energy: resources.energy - cost.energy
    });
  };

  // Game loop
  const gameLoop = (timestamp: number) => {
    if (!canvasRef.current) return;
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.fillStyle = '#0a0a0f';
    ctx.fillRect(0, 0, 800, 500);
    
    // Draw grid
    ctx.strokeStyle = '#1a1a2e';
    for (let x = 0; x < 800; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 500);
      ctx.stroke();
    }
    for (let y = 0; y < 500; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(800, y);
      ctx.stroke();
    }
    
    // Draw colony base
    ctx.fillStyle = '#4a5568';
    ctx.fillRect(0, 200, 100, 100);
    ctx.fillStyle = '#2d3748';
    ctx.fillRect(10, 210, 80, 80);
    ctx.fillStyle = '#00ff00';
    ctx.font = '20px monospace';
    ctx.fillText('COLONY', 15, 250);
    
    // Update and draw enemies
    setEnemies(prev => {
      const updated = prev.map(enemy => {
        // Move enemy towards colony
        const newX = enemy.x - enemy.speed;
        
        // Check if enemy reached colony
        if (newX <= 100) {
          setColonyHealth(h => Math.max(0, h - enemy.damage));
          return null;
        }
        
        // Check turret targeting
        turrets.forEach(turret => {
          const distance = Math.sqrt((turret.x - newX) ** 2 + (turret.y - enemy.y) ** 2);
          if (distance <= turret.range && timestamp - turret.lastFired > turret.fireRate) {
            // Fire at enemy
            ctx.strokeStyle = turret.type === 'laser' ? '#00ffff' : turret.type === 'missile' ? '#ff9900' : '#ff00ff';
            ctx.lineWidth = turret.type === 'laser' ? 2 : 3;
            ctx.beginPath();
            ctx.moveTo(turret.x, turret.y);
            ctx.lineTo(newX, enemy.y);
            ctx.stroke();
            
            enemy.health -= turret.damage;
            turret.lastFired = timestamp;
          }
        });
        
        // Check if enemy destroyed
        if (enemy.health <= 0) {
          setScore(s => s + (enemy.type === 'tank' ? 30 : enemy.type === 'drone' ? 10 : 5));
          return null;
        }
        
        // Draw enemy
        ctx.fillStyle = enemy.color;
        ctx.fillRect(newX - 15, enemy.y - 15, 30, 30);
        
        // Draw health bar
        ctx.fillStyle = '#ff0000';
        ctx.fillRect(newX - 15, enemy.y - 20, 30, 3);
        ctx.fillStyle = '#00ff00';
        ctx.fillRect(newX - 15, enemy.y - 20, 30 * (enemy.health / enemy.maxHealth), 3);
        
        return { ...enemy, x: newX };
      }).filter(Boolean) as Enemy[];
      
      return updated;
    });
    
    // Draw turrets
    turrets.forEach(turret => {
      // Draw range circle
      ctx.strokeStyle = 'rgba(100, 100, 255, 0.2)';
      ctx.beginPath();
      ctx.arc(turret.x, turret.y, turret.range, 0, Math.PI * 2);
      ctx.stroke();
      
      // Draw turret
      ctx.fillStyle = turret.type === 'laser' ? '#00cccc' : turret.type === 'missile' ? '#cc6600' : '#cc00cc';
      ctx.fillRect(turret.x - 20, turret.y - 20, 40, 40);
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px monospace';
      ctx.fillText(turret.type.charAt(0).toUpperCase(), turret.x - 5, turret.y + 5);
    });
    
    // Check win/lose conditions
    if (colonyHealth <= 0) {
      setGameState('gameover');
      return;
    }
    
    if (enemies.length === 0 && gameState === 'playing') {
      // Wave complete
      const reward = wave * 50;
      onResourceUpdate({
        materials: resources.materials + reward,
        energy: resources.energy + reward / 2,
        research: resources.research + wave * 2
      });
      
      toast({
        title: 'Wave Complete!',
        description: `Earned ${reward} materials and ${reward/2} energy`
      });
      
      setWave(w => w + 1);
      setEnemies(generateWave(wave + 1));
    }
    
    if (gameState === 'playing') {
      animationRef.current = requestAnimationFrame(gameLoop);
    }
  };

  // Start game
  const startGame = () => {
    setGameState('playing');
    setWave(1);
    setColonyHealth(100);
    setScore(0);
    setTurrets([]);
    setEnemies(generateWave(1));
  };

  // Handle canvas click
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (gameState !== 'playing') return;
    
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // Don't place turrets on colony or too far right
    if (x > 150 && x < 600) {
      placeTurret(x, y);
    }
  };

  useEffect(() => {
    if (gameState === 'playing' && canvasRef.current) {
      animationRef.current = requestAnimationFrame(gameLoop);
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [gameState, enemies, turrets]);

  return (
    <Card className="bg-gradient-to-br from-red-900/20 to-orange-900/20 border-red-500/30">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-red-400" />
            Colony Defense
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1">
              <Heart className="w-4 h-4 text-red-400" />
              {colonyHealth}%
            </span>
            <span className="text-yellow-400">Wave: {wave}</span>
            <span className="text-green-400">Score: {score}</span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Game Canvas */}
          <div className="relative">
            <canvas
              ref={canvasRef}
              width={800}
              height={500}
              className="w-full border border-red-500/30 rounded cursor-crosshair"
              onClick={handleCanvasClick}
            />
            
            {gameState === 'idle' && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <Button
                  onClick={startGame}
                  className="bg-red-600 hover:bg-red-500"
                >
                  Start Defense
                </Button>
              </div>
            )}
            
            {gameState === 'gameover' && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <div className="text-center">
                  <h3 className="text-2xl font-bold text-red-400 mb-2">Colony Destroyed!</h3>
                  <p className="text-gray-400 mb-4">Score: {score}</p>
                  <Button
                    onClick={startGame}
                    className="bg-red-600 hover:bg-red-500"
                  >
                    Try Again
                  </Button>
                </div>
              </div>
            )}
          </div>
          
          {/* Turret Selection */}
          {gameState === 'playing' && (
            <div className="flex gap-2">
              {(['laser', 'missile', 'plasma'] as const).map(type => (
                <button
                  key={type}
                  onClick={() => setSelectedTurretType(type)}
                  className={`flex-1 p-3 rounded border transition-all ${
                    selectedTurretType === type
                      ? 'bg-blue-900/30 border-blue-500'
                      : 'bg-black/30 border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <div className="text-sm font-medium capitalize">{type} Turret</div>
                  <div className="text-xs text-gray-400">
                    {turretCosts[type].materials}M / {turretCosts[type].energy}E
                  </div>
                  <div className="text-xs text-green-400">
                    DMG: {turretStats[type].damage} | RNG: {turretStats[type].range}
                  </div>
                </button>
              ))}
            </div>
          )}
          
          {/* Instructions */}
          <div className="text-xs text-gray-400 border-t border-gray-700 pt-2">
            Click on the battlefield to place turrets. Defend your colony from incoming waves!
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
