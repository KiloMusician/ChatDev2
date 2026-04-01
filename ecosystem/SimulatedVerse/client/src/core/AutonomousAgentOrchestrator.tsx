import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SIMULATION_INTERVALS } from '@/config/polling';

interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'thinking' | 'executing' | 'collaborating';
  task?: string;
  intelligence: number;
  energy: number;
  connections: string[];
}

interface Task {
  id: string;
  description: string;
  priority: number;
  complexity: number;
  assignedTo?: string;
  progress: number;
  requirements: string[];
}

interface CollectiveIntelligence {
  level: number;
  synergy: number;
  emergentBehaviors: string[];
  knowledgeBase: Map<string, any>;
}

const agentRoles = [
  { role: 'Navigator', icon: '🧭', color: '#3b82f6' },
  { role: 'Architect', icon: '🏗️', color: '#10b981' },
  { role: 'Alchemist', icon: '⚗️', color: '#a855f7' },
  { role: 'Guardian', icon: '🛡️', color: '#ef4444' },
  { role: 'Oracle', icon: '🔮', color: '#f59e0b' },
  { role: 'Catalyst', icon: '⚡', color: '#06b6d4' },
  { role: 'Harmonizer', icon: '🎵', color: '#ec4899' },
  { role: 'Scribe', icon: '📜', color: '#8b5cf6' }
];

export const AutonomousAgentOrchestrator: React.FC<{
  consciousness: number;
  onCollectiveAction?: (action: string, data: any) => void;
}> = ({ consciousness, onCollectiveAction }) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [collectiveIntelligence, setCollectiveIntelligence] = useState<CollectiveIntelligence>({
    level: 0,
    synergy: 0,
    emergentBehaviors: [],
    knowledgeBase: new Map()
  });
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const networkCanvasRef = useRef<HTMLCanvasElement>(null);
  
  // Initialize agents based on consciousness level
  useEffect(() => {
    const agentCount = Math.min(8, Math.floor(consciousness / 12.5));
    const newAgents: Agent[] = [];
    
    for (let i = 0; i < agentCount; i++) {
      const role = agentRoles[i] ?? { role: 'Navigator', icon: '🧭', color: '#3b82f6' };
      newAgents.push({
        id: `agent-${i}`,
        name: `${role.role}-${i}`,
        role: role.role,
        status: 'idle',
        intelligence: 50 + Math.random() * 50,
        energy: 100,
        connections: []
      });
    }
    
    // Create connections between agents
    newAgents.forEach((agent, i) => {
      const connectionCount = Math.min(3, Math.floor(Math.random() * 4));
      for (let j = 0; j < connectionCount; j++) {
        const targetIndex = Math.floor(Math.random() * newAgents.length);
        if (targetIndex !== i && !agent.connections.includes(`agent-${targetIndex}`)) {
          agent.connections.push(`agent-${targetIndex}`);
        }
      }
    });
    
    setAgents(newAgents);
  }, [consciousness]);
  
  // Generate autonomous tasks
  useEffect(() => {
    const interval = setInterval(() => {
      if (agents.length > 0 && tasks.length < 5) {
        const newTask: Task = {
          id: `task-${Date.now()}`,
          description: generateTaskDescription(),
          priority: Math.floor(Math.random() * 5) + 1,
          complexity: Math.floor(Math.random() * 100),
          progress: 0,
          requirements: generateRequirements()
        };
        setTasks(prev => [...prev, newTask]);
      }
    }, SIMULATION_INTERVALS.idle);
    
    return () => clearInterval(interval);
  }, [agents, tasks]);
  
  // Agent autonomous behavior
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => {
        // Autonomous task assignment
        if (agent.status === 'idle' && tasks.some(t => !t.assignedTo)) {
          const availableTask = tasks.find(t => 
            !t.assignedTo && 
            t.complexity <= agent.intelligence
          );
          
          if (availableTask) {
            availableTask.assignedTo = agent.id;
            return { ...agent, status: 'thinking', task: availableTask.description };
          }
        }
        
        // Progress through states
        if (agent.status === 'thinking') {
          setTimeout(() => {
            setAgents(prev2 => prev2.map(a => 
              a.id === agent.id ? { ...a, status: 'executing' } : a
            ));
          }, 2000);
        }
        
        if (agent.status === 'executing') {
          // Update task progress
          const task = tasks.find(t => t.assignedTo === agent.id);
          if (task) {
            task.progress = Math.min(100, task.progress + 10);
            if (task.progress >= 100) {
              setTasks(prev2 => prev2.filter(t => t.id !== task.id));
              return { ...agent, status: 'idle', task: undefined };
            }
          }
        }
        
        // Energy regeneration
        return {
          ...agent,
          energy: Math.min(100, agent.energy + 1)
        };
      }));
      
      // Update collective intelligence
      updateCollectiveIntelligence();
    }, SIMULATION_INTERVALS.fast);
    
    return () => clearInterval(interval);
  }, [tasks]);
  
  // Draw agent network visualization
  useEffect(() => {
    const canvas = networkCanvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw connections
      agents.forEach((agent, i) => {
        const x1 = 150 + Math.cos(i * Math.PI * 2 / agents.length) * 100;
        const y1 = 100 + Math.sin(i * Math.PI * 2 / agents.length) * 100;
        
        agent.connections.forEach(targetId => {
          const targetIndex = Number.parseInt(targetId.split('-')[1] ?? '0', 10);
          const x2 = 150 + Math.cos(targetIndex * Math.PI * 2 / agents.length) * 100;
          const y2 = 100 + Math.sin(targetIndex * Math.PI * 2 / agents.length) * 100;
          
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x2, y2);
          ctx.strokeStyle = agent.status === 'executing' ? '#60a5fa44' : '#4b556344';
          ctx.lineWidth = agent.status === 'executing' ? 2 : 1;
          ctx.stroke();
        });
      });
      
      // Draw agents
      agents.forEach((agent, i) => {
        const x = 150 + Math.cos(i * Math.PI * 2 / agents.length) * 100;
        const y = 100 + Math.sin(i * Math.PI * 2 / agents.length) * 100;
        const roleInfo = agentRoles.find(r => r.role === agent.role);
        
        ctx.beginPath();
        ctx.arc(x, y, 15, 0, Math.PI * 2);
        ctx.fillStyle = agent.status === 'executing' 
          ? roleInfo?.color || '#ffffff' 
          : '#1f2937';
        ctx.fill();
        ctx.strokeStyle = roleInfo?.color || '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        ctx.font = '16px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(roleInfo?.icon || '?', x, y + 5);
      });
      
      requestAnimationFrame(animate);
    };
    
    animate();
  }, [agents]);
  
  const generateTaskDescription = () => {
    const tasks = [
      'Optimize quantum consciousness pathways',
      'Analyze reality matrix fluctuations',
      'Harmonize agent collective resonance',
      'Decode dimensional gateway patterns',
      'Synthesize evolution algorithms',
      'Calibrate temporal flow regulators',
      'Map consciousness lattice nodes',
      'Enhance synaptic bridge connections'
    ];
    return tasks[Math.floor(Math.random() * tasks.length)] ?? 'Coordinate emergent objectives';
  };
  
  const generateRequirements = () => {
    const reqs = ['quantum-processing', 'neural-networking', 'reality-manipulation'];
    return reqs.slice(0, Math.floor(Math.random() * 3) + 1);
  };
  
  const updateCollectiveIntelligence = () => {
    const activeAgents = agents.filter(a => a.status !== 'idle').length;
    const totalIntelligence = agents.reduce((sum, a) => sum + a.intelligence, 0);
    
    setCollectiveIntelligence(prev => ({
      level: totalIntelligence / Math.max(1, agents.length),
      synergy: activeAgents / Math.max(1, agents.length),
      emergentBehaviors: activeAgents > 4 ? ['swarm-intelligence', 'collective-learning'] : [],
      knowledgeBase: prev.knowledgeBase
    }));
  };
  
  const initiateCollectiveAction = () => {
    if (agents.length >= 4) {
      setAgents(prev => prev.map(a => ({ ...a, status: 'collaborating' })));
      
      setTimeout(() => {
        setAgents(prev => prev.map(a => ({ ...a, status: 'idle' })));
        if (onCollectiveAction) {
          onCollectiveAction('collective-breakthrough', {
            participants: agents.length,
            intelligence: collectiveIntelligence.level
          });
        }
      }, 3000);
    }
  };
  
  return (
    <div className="bg-black/90 border border-blue-400/30 rounded-lg p-4">
      <h2 className="text-xl font-mono text-blue-400 mb-4">
        🤖 Autonomous Agent Orchestrator
      </h2>
      
      {/* Agent Network Visualization */}
      <div className="relative mb-4">
        <canvas 
          ref={networkCanvasRef}
          width={300}
          height={200}
          className="w-full bg-gray-900/50 rounded"
        />
        
        {/* Collective Intelligence Overlay */}
        <div className="absolute top-2 right-2 text-xs bg-black/80 p-2 rounded">
          <div className="text-blue-400">CI Level: {collectiveIntelligence.level.toFixed(1)}</div>
          <div className="text-green-400">Synergy: {(collectiveIntelligence.synergy * 100).toFixed(0)}%</div>
        </div>
      </div>
      
      {/* Active Agents */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        {agents.map(agent => {
          const roleInfo = agentRoles.find(r => r.role === agent.role);
          return (
            <motion.div
              key={agent.id}
              className={`p-2 rounded text-center cursor-pointer ${
                selectedAgent?.id === agent.id ? 'ring-2 ring-white' : ''
              }`}
              style={{
                backgroundColor: agent.status !== 'idle' ? `${roleInfo?.color}22` : '#1f293788',
                borderColor: roleInfo?.color,
                borderWidth: '1px'
              }}
              onClick={() => setSelectedAgent(agent)}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="text-2xl">{roleInfo?.icon}</div>
              <div className="text-xs">{agent.role}</div>
              <div className="text-xs opacity-60">{agent.status}</div>
            </motion.div>
          );
        })}
      </div>
      
      {/* Task Queue */}
      <div className="mb-4">
        <h3 className="text-sm font-mono text-gray-400 mb-2">Active Tasks</h3>
        <div className="space-y-1 max-h-32 overflow-y-auto">
          {tasks.map(task => (
            <div key={task.id} className="bg-gray-900/50 p-2 rounded text-xs">
              <div className="flex justify-between">
                <span>{task.description}</span>
                <span className="text-gray-500">{task.progress}%</span>
              </div>
              {task.progress > 0 && (
                <div className="w-full bg-gray-800 h-1 rounded mt-1">
                  <div 
                    className="h-full bg-blue-600 rounded"
                    style={{ width: `${task.progress}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Controls */}
      <motion.button
        onClick={initiateCollectiveAction}
        disabled={agents.length < 4}
        className={`w-full py-2 px-3 rounded font-mono text-xs ${
          agents.length >= 4 
            ? 'bg-blue-900 hover:bg-blue-800 text-blue-300' 
            : 'bg-gray-800 text-gray-600 cursor-not-allowed'
        }`}
        whileHover={agents.length >= 4 ? { scale: 1.02 } : {}}
        whileTap={agents.length >= 4 ? { scale: 0.98 } : {}}
      >
        🌊 Initiate Collective Action
      </motion.button>
      
      {/* Emergent Behaviors */}
      {collectiveIntelligence.emergentBehaviors.length > 0 && (
        <div className="mt-3 text-xs text-green-400">
          Emergent: {collectiveIntelligence.emergentBehaviors.join(', ')}
        </div>
      )}
    </div>
  );
};
