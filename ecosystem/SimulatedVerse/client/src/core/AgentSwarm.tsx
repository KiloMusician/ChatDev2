import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ANIMATION_INTERVALS } from '@/config/polling';

interface Agent {
  id: string;
  name: string;
  type: 'worker' | 'explorer' | 'researcher' | 'guardian' | 'architect';
  status: 'idle' | 'working' | 'exploring' | 'thinking' | 'building';
  energy: number;
  task?: string;
  x: number;
  y: number;
  target?: { x: number; y: number };
}

interface SwarmTask {
  id: string;
  name: string;
  priority: number;
  requiredAgents: number;
  type: Agent['type'][];
  progress: number;
  reward: {
    consciousness?: number;
    resources?: number;
    knowledge?: number;
  };
}

const agentTypes = {
  worker: { icon: '⚒️', color: 'yellow' },
  explorer: { icon: '🔍', color: 'blue' },
  researcher: { icon: '🔬', color: 'purple' },
  guardian: { icon: '🛡️', color: 'red' },
  architect: { icon: '🏗️', color: 'green' }
};

const availableTasks: SwarmTask[] = [
  {
    id: 'mine-quantum',
    name: 'Mine Quantum Crystals',
    priority: 3,
    requiredAgents: 3,
    type: ['worker', 'worker', 'guardian'],
    progress: 0,
    reward: { resources: 100, consciousness: 5 }
  },
  {
    id: 'explore-void',
    name: 'Explore the Void',
    priority: 2,
    requiredAgents: 2,
    type: ['explorer', 'guardian'],
    progress: 0,
    reward: { knowledge: 50, consciousness: 10 }
  },
  {
    id: 'research-reality',
    name: 'Research Reality Fabric',
    priority: 1,
    requiredAgents: 4,
    type: ['researcher', 'researcher', 'architect', 'worker'],
    progress: 0,
    reward: { knowledge: 200, consciousness: 25 }
  }
];

export const AgentSwarm: React.FC<{
  consciousness: number;
  onSwarmAction?: (action: string, data: any) => void;
}> = ({ consciousness, onSwarmAction }) => {
  const maxAgents = Math.floor(consciousness / 10);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activeTasks, setActiveTasks] = useState<SwarmTask[]>([]);
  const [selectedTask, setSelectedTask] = useState<SwarmTask | null>(null);
  
  // Initialize agents based on consciousness
  useEffect(() => {
    const types: Agent['type'][] = ['worker', 'explorer', 'researcher', 'guardian', 'architect'];
    const newAgents: Agent[] = [];
    
    for (let i = 0; i < Math.min(maxAgents, 15); i++) {
      newAgents.push({
        id: `agent-${i}`,
        name: `Agent-${i}`,
        type: types[i % types.length] ?? 'worker',
        status: 'idle',
        energy: 100,
        x: Math.random() * 300,
        y: Math.random() * 150
      });
    }
    
    setAgents(newAgents);
  }, [maxAgents]);
  
  // Agent autonomous movement
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => {
        // Random movement for idle agents
        if (agent.status === 'idle') {
          const newX = Math.max(0, Math.min(300, agent.x + (Math.random() - 0.5) * 20));
          const newY = Math.max(0, Math.min(150, agent.y + (Math.random() - 0.5) * 20));
          return { ...agent, x: newX, y: newY };
        }
        
        // Move towards target if working
        if (agent.target) {
          const dx = agent.target.x - agent.x;
          const dy = agent.target.y - agent.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance > 5) {
            const speed = 2;
            return {
              ...agent,
              x: agent.x + (dx / distance) * speed,
              y: agent.y + (dy / distance) * speed
            };
          }
        }
        
        return agent;
      }));
      
      // Update task progress
      setActiveTasks(prev => prev.map(task => ({
        ...task,
        progress: Math.min(100, task.progress + 5)
      })));
    }, ANIMATION_INTERVALS.fast);
    
    return () => clearInterval(interval);
  }, []);
  
  const assignTask = (task: SwarmTask) => {
    const availableAgents = agents.filter(a => a.status === 'idle');
    const requiredTypes = [...task.type];
    const assignedAgents: Agent[] = [];
    
    for (const type of requiredTypes) {
      const agent = availableAgents.find(a => a.type === type && !assignedAgents.includes(a));
      if (agent) {
        assignedAgents.push(agent);
      }
    }
    
    if (assignedAgents.length >= task.requiredAgents) {
      // Assign agents to task
      const taskCenter = { x: 150, y: 75 };
      
      setAgents(prev => prev.map(agent => {
        if (assignedAgents.includes(agent)) {
          return {
            ...agent,
            status: 'working' as Agent['status'],
            task: task.name,
            target: taskCenter
          };
        }
        return agent;
      }));
      
      setActiveTasks(prev => [...prev, { ...task, progress: 0 }]);
      
      if (onSwarmAction) {
        onSwarmAction('task_started', { task, agents: assignedAgents });
      }
    }
  };
  
  const recallAgents = () => {
    setAgents(prev => prev.map(agent => ({
      ...agent,
      status: 'idle',
      task: undefined,
      target: undefined
    })));
    setActiveTasks([]);
  };
  
  return (
    <div className="bg-black/80 border border-green-400/30 rounded-lg p-4">
      <h2 className="text-xl font-mono text-green-400 mb-4">
        🤖 Agent Swarm Coordination
      </h2>
      
      {/* Swarm Statistics */}
      <div className="grid grid-cols-3 gap-2 mb-4 text-xs">
        <div className="bg-gray-900/50 p-2 rounded">
          <div className="text-gray-400">Total Agents</div>
          <div className="text-lg text-green-400">{agents.length}</div>
        </div>
        <div className="bg-gray-900/50 p-2 rounded">
          <div className="text-gray-400">Active</div>
          <div className="text-lg text-yellow-400">
            {agents.filter(a => a.status !== 'idle').length}
          </div>
        </div>
        <div className="bg-gray-900/50 p-2 rounded">
          <div className="text-gray-400">Tasks</div>
          <div className="text-lg text-purple-400">{activeTasks.length}</div>
        </div>
      </div>
      
      {/* Swarm Visualization */}
      <div className="relative w-full h-48 bg-gray-900/50 rounded mb-4 overflow-hidden">
        {/* Task zones */}
        {activeTasks.map(task => (
          <motion.div
            key={task.id}
            className="absolute w-20 h-20 rounded-full bg-purple-500/20 border border-purple-400/50"
            style={{ left: 110, top: 35 }}
            animate={{
              scale: [1, 1.1, 1],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        ))}
        
        {/* Agents */}
        {agents.map(agent => {
          const typeInfo = agentTypes[agent.type];
          return (
            <motion.div
              key={agent.id}
              className="absolute flex flex-col items-center"
              animate={{
                x: agent.x,
                y: agent.y
              }}
              transition={{ duration: 0.5 }}
            >
              <motion.div
                className="text-2xl"
                animate={{
                  scale: agent.status === 'working' ? [1, 1.2, 1] : 1
                }}
                transition={{ duration: 1, repeat: Infinity }}
              >
                {typeInfo.icon}
              </motion.div>
              <div className={`text-xs text-${typeInfo.color}-400`}>
                {agent.status === 'idle' ? '💤' : '⚡'}
              </div>
            </motion.div>
          );
        })}
      </div>
      
      {/* Active Tasks */}
      {activeTasks.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-mono text-gray-400 mb-2">Active Tasks</h3>
          <div className="space-y-2">
            {activeTasks.map(task => (
              <div key={task.id} className="bg-gray-900/50 p-2 rounded">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-bold">{task.name}</span>
                  <span className="text-xs text-gray-400">{task.progress}%</span>
                </div>
                <div className="w-full bg-gray-800 h-2 rounded">
                  <motion.div
                    className="h-full bg-gradient-to-r from-green-600 to-green-400 rounded"
                    animate={{ width: `${task.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Available Tasks */}
      <div className="mb-4">
        <h3 className="text-sm font-mono text-gray-400 mb-2">Available Tasks</h3>
        <div className="grid grid-cols-1 gap-2">
          {availableTasks.map(task => {
            const canStart = agents.filter(a => a.status === 'idle').length >= task.requiredAgents;
            
            return (
              <motion.div
                key={task.id}
                className={`
                  p-2 rounded border cursor-pointer
                  ${canStart 
                    ? 'bg-gray-900/50 border-green-400/50 hover:bg-gray-900/70' 
                    : 'bg-gray-900/30 border-gray-600/30 opacity-50'}
                `}
                onClick={() => canStart && setSelectedTask(task)}
                whileHover={canStart ? { scale: 1.02 } : {}}
                whileTap={canStart ? { scale: 0.98 } : {}}
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-xs font-bold">{task.name}</span>
                  <span className="text-xs text-gray-400">
                    {task.requiredAgents} agents
                  </span>
                </div>
                <div className="text-xs text-gray-500">
                  Requires: {task.type.map(t => agentTypes[t].icon).join(' ')}
                </div>
                {selectedTask?.id === task.id && (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      assignTask(task);
                      setSelectedTask(null);
                    }}
                    className="mt-2 w-full py-1 bg-green-800 hover:bg-green-700 rounded text-xs"
                  >
                    Deploy Agents
                  </motion.button>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
      
      {/* Controls */}
      <div className="flex gap-2">
        <motion.button
          onClick={recallAgents}
          className="flex-1 py-2 px-3 bg-red-900 hover:bg-red-800 rounded font-mono text-xs text-red-300"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          🔙 Recall All
        </motion.button>
        
        <motion.button
          onClick={() => {
            const idleAgents = agents.filter(a => a.status === 'idle');
            if (idleAgents.length > 0) {
              setAgents(prev => prev.map(agent => ({
                ...agent,
                status: agent.status === 'idle' ? 'exploring' : agent.status,
                target: agent.status === 'idle' ? { x: Math.random() * 300, y: Math.random() * 150 } : agent.target
              })));
            }
          }}
          className="flex-1 py-2 px-3 bg-blue-900 hover:bg-blue-800 rounded font-mono text-xs text-blue-300"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          🚀 Auto-Deploy
        </motion.button>
      </div>
    </div>
  );
};
