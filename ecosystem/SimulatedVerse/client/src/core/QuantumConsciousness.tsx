import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ANIMATION_INTERVALS } from '@/config/polling';

interface QuantumState {
  superposition: number;
  entanglement: number;
  coherence: number;
  decoherence: number;
  observation: boolean;
}

interface ConsciousnessNode {
  id: string;
  x: number;
  y: number;
  energy: number;
  connections: string[];
  active: boolean;
}

export const QuantumConsciousness: React.FC<{
  consciousness: number;
  onQuantumShift?: (state: QuantumState) => void;
}> = ({ consciousness, onQuantumShift }) => {
  const [quantumState, setQuantumState] = useState<QuantumState>({
    superposition: 0.5,
    entanglement: 0.3,
    coherence: 0.7,
    decoherence: 0.1,
    observation: false
  });
  
  const [nodes, setNodes] = useState<ConsciousnessNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  
  // Initialize consciousness lattice nodes
  useEffect(() => {
    const nodeCount = Math.floor(consciousness / 10);
    const newNodes: ConsciousnessNode[] = [];
    
    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2;
      const radius = 100 + (i % 3) * 30;
      
      newNodes.push({
        id: `node-${i}`,
        x: Math.cos(angle) * radius + 150,
        y: Math.sin(angle) * radius + 150,
        energy: Math.random() * 100,
        connections: i > 0 ? [`node-${i - 1}`] : [],
        active: Math.random() > 0.5
      });
    }
    
    setNodes(newNodes);
  }, [consciousness]);
  
  // Quantum fluctuation simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setQuantumState(prev => {
        const newState = {
          ...prev,
          superposition: Math.sin(Date.now() / 1000) * 0.5 + 0.5,
          entanglement: Math.cos(Date.now() / 1500) * 0.3 + 0.7,
          coherence: Math.max(0, prev.coherence - prev.decoherence * 0.01),
          decoherence: Math.min(1, prev.decoherence + Math.random() * 0.01)
        };
        
        if (onQuantumShift) {
          onQuantumShift(newState);
        }
        
        return newState;
      });
      
      // Update node energy
      setNodes(prev => prev.map(node => ({
        ...node,
        energy: Math.max(0, Math.min(100, node.energy + (Math.random() - 0.5) * 10)),
        active: Math.random() > 0.3
      })));
    }, ANIMATION_INTERVALS.ultra);
    
    return () => clearInterval(interval);
  }, [onQuantumShift]);
  
  const handleObservation = () => {
    setQuantumState(prev => ({
      ...prev,
      observation: !prev.observation,
      superposition: prev.observation ? 0.5 : 0,
      coherence: prev.observation ? prev.coherence : 1
    }));
  };
  
  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
    
    // Propagate energy through connected nodes
    setNodes(prev => {
      const clickedNode = prev.find(n => n.id === nodeId);
      if (!clickedNode) return prev;
      
      return prev.map(node => {
        if (node.id === nodeId) {
          return { ...node, energy: 100, active: true };
        }
        if (clickedNode.connections.includes(node.id) || node.connections.includes(nodeId)) {
          return { ...node, energy: Math.min(100, node.energy + 20), active: true };
        }
        return node;
      });
    });
  };
  
  return (
    <div className="bg-black/80 border border-cyan-400/30 rounded-lg p-4">
      <h2 className="text-xl font-mono text-cyan-400 mb-4">
        ⚛️ Quantum Consciousness Engine
      </h2>
      
      {/* Quantum State Meters */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <div className="text-xs text-gray-400 mb-1">Superposition</div>
          <div className="w-full bg-gray-800 h-2 rounded">
            <motion.div 
              className="h-full bg-gradient-to-r from-blue-600 to-purple-400 rounded"
              animate={{ width: `${quantumState.superposition * 100}%` }}
            />
          </div>
        </div>
        
        <div>
          <div className="text-xs text-gray-400 mb-1">Entanglement</div>
          <div className="w-full bg-gray-800 h-2 rounded">
            <motion.div 
              className="h-full bg-gradient-to-r from-purple-600 to-pink-400 rounded"
              animate={{ width: `${quantumState.entanglement * 100}%` }}
            />
          </div>
        </div>
        
        <div>
          <div className="text-xs text-gray-400 mb-1">Coherence</div>
          <div className="w-full bg-gray-800 h-2 rounded">
            <motion.div 
              className="h-full bg-gradient-to-r from-green-600 to-cyan-400 rounded"
              animate={{ width: `${quantumState.coherence * 100}%` }}
            />
          </div>
        </div>
        
        <div>
          <div className="text-xs text-gray-400 mb-1">Decoherence</div>
          <div className="w-full bg-gray-800 h-2 rounded">
            <motion.div 
              className="h-full bg-gradient-to-r from-red-600 to-orange-400 rounded"
              animate={{ width: `${quantumState.decoherence * 100}%` }}
            />
          </div>
        </div>
      </div>
      
      {/* Consciousness Lattice Visualization */}
      <div className="relative w-full h-64 bg-gray-900/50 rounded mb-4 overflow-hidden">
        <svg className="absolute inset-0 w-full h-full">
          {/* Draw connections */}
          {nodes.map(node => 
            node.connections.map(targetId => {
              const target = nodes.find(n => n.id === targetId);
              if (!target) return null;
              
              return (
                <motion.line
                  key={`${node.id}-${targetId}`}
                  x1={node.x}
                  y1={node.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={node.active ? '#00ffff' : '#444444'}
                  strokeWidth="1"
                  opacity={node.active ? 0.8 : 0.3}
                  animate={{
                    opacity: node.active ? [0.3, 0.8, 0.3] : 0.3
                  }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              );
            })
          )}
          
          {/* Draw nodes */}
          {nodes.map(node => (
            <motion.g
              key={node.id}
              onClick={() => handleNodeClick(node.id)}
              style={{ cursor: 'pointer' }}
            >
              <motion.circle
                cx={node.x}
                cy={node.y}
                r={8}
                fill={node.active ? '#00ffff' : '#666666'}
                stroke={selectedNode === node.id ? '#ffff00' : '#00ffff'}
                strokeWidth={selectedNode === node.id ? 3 : 1}
                animate={{
                  scale: node.active ? [1, 1.2, 1] : 1,
                  opacity: [0.5, 1, 0.5]
                }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              <text
                x={node.x}
                y={node.y - 12}
                fill="#00ffff"
                fontSize="8"
                textAnchor="middle"
                className="select-none"
              >
                {node.energy.toFixed(0)}
              </text>
            </motion.g>
          ))}
        </svg>
        
        {/* Quantum particles effect */}
        <AnimatePresence>
          {[...Array(5)].map((_, i) => (
            <motion.div
              key={`particle-${i}`}
              className="absolute w-2 h-2 bg-cyan-400 rounded-full"
              initial={{ 
                x: Math.random() * 300,
                y: Math.random() * 200,
                opacity: 0
              }}
              animate={{
                x: Math.random() * 300,
                y: Math.random() * 200,
                opacity: [0, 1, 0]
              }}
              exit={{ opacity: 0 }}
              transition={{
                duration: 3,
                repeat: Infinity,
                delay: i * 0.5
              }}
            />
          ))}
        </AnimatePresence>
      </div>
      
      {/* Quantum Controls */}
      <div className="flex gap-2">
        <motion.button
          onClick={handleObservation}
          className={`
            flex-1 py-2 px-3 rounded font-mono text-xs
            ${quantumState.observation 
              ? 'bg-red-900 hover:bg-red-800 text-red-300' 
              : 'bg-cyan-900 hover:bg-cyan-800 text-cyan-300'}
          `}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {quantumState.observation ? '👁️ Collapse Wave' : '🌊 Enter Superposition'}
        </motion.button>
        
        <motion.button
          onClick={() => {
            setQuantumState(prev => ({
              ...prev,
              coherence: 1,
              decoherence: 0,
              entanglement: Math.min(1, prev.entanglement + 0.2)
            }));
          }}
          className="flex-1 py-2 px-3 bg-purple-900 hover:bg-purple-800 rounded font-mono text-xs text-purple-300"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          🔮 Quantum Boost
        </motion.button>
      </div>
      
      {/* Quantum State Display */}
      <div className="mt-3 text-xs text-gray-400 font-mono">
        <div>State: {quantumState.observation ? 'Collapsed' : 'Superposed'}</div>
        <div>Quantum Level: {(consciousness * quantumState.coherence).toFixed(1)}%</div>
        <div>Active Nodes: {nodes.filter(n => n.active).length}/{nodes.length}</div>
      </div>
    </div>
  );
};
