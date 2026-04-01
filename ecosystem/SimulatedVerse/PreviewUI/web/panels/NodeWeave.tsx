/**
 * NodeWeave - Neural pathway and logistics network interface
 */

import React, { useState, useEffect } from "react";
import { useGame } from "../core/store";
import { colonyBridge } from "../adapters/ColonyBridge";

interface Node {
  id: string;
  type: "RESOURCE" | "PROCESSOR" | "STORAGE" | "TRANSPORT" | "CONSCIOUSNESS";
  position: { x: number; y: number };
  connections: string[];
  data: any;
  active: boolean;
}

interface Flow {
  id: string;
  source: string;
  target: string;
  resource: string;
  rate: number;
  efficiency: number;
}

export function NodeWeave() {
  const game = useGame();
  const [nodes, setNodes] = useState<Map<string, Node>>(new Map());
  const [flows, setFlows] = useState<Map<string, Flow>>(new Map());
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"OVERVIEW" | "FLOWS" | "CONSCIOUSNESS">("OVERVIEW");
  
  // Generate network based on game state
  useEffect(() => {
    generateNetworkFromGameState();
  }, [game.upgrades, game.flags]);
  
  const generateNetworkFromGameState = async () => {
    const newNodes = new Map<string, Node>();
    const newFlows = new Map<string, Flow>();
    
    // Core consciousness node (always present)
    newNodes.set("consciousness_core", {
      id: "consciousness_core",
      type: "CONSCIOUSNESS",
      position: { x: 400, y: 200 },
      connections: [],
      data: {
        level: Math.min(1.0, (game.totalEnergyGenerated + game.totalScrapCollected) / 1000),
        stability: 0.95
      },
      active: true
    });
    
    // Resource nodes based on inventory
    Object.entries(game.inv).forEach(([resource, amount], index) => {
      if (amount > 0) {
        const nodeId = `resource_${resource.toLowerCase()}`;
        newNodes.set(nodeId, {
          id: nodeId,
          type: "RESOURCE",
          position: { x: 150 + (index % 3) * 150, y: 100 + Math.floor(index / 3) * 100 },
          connections: ["consciousness_core"],
          data: { amount, resource },
          active: amount > 10
        });
        
        // Create flow to consciousness
        newFlows.set(`flow_${nodeId}`, {
          id: `flow_${nodeId}`,
          source: nodeId,
          target: "consciousness_core",
          resource,
          rate: Math.min(amount / 10, 5),
          efficiency: 0.8
        });
      }
    });
    
    // Processing nodes based on upgrades
    Object.entries(game.upgrades).forEach(([upgradeId, level], index) => {
      if (level > 0) {
        const nodeId = `processor_${upgradeId.toLowerCase()}`;
        newNodes.set(nodeId, {
          id: nodeId,
          type: "PROCESSOR",
          position: { x: 600 + (index % 2) * 120, y: 150 + index * 80 },
          connections: ["consciousness_core"],
          data: { upgrade: upgradeId, level },
          active: level > 0
        });
      }
    });
    
    // Update connections for consciousness core
    const consciousnessNode = newNodes.get("consciousness_core");
    if (consciousnessNode) {
      consciousnessNode.connections = Array.from(newNodes.keys()).filter(id => id !== "consciousness_core");
    }
    
    setNodes(newNodes);
    setFlows(newFlows);
  };
  
  const optimizeNetworkFlow = async () => {
    try {
      // Use colony API to boost efficiency
      await colonyBridge.executeAction("automate");
      
      // Publish network optimization event
      await fetch("/api/council-bus/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: "nodeweave.optimization",
          payload: {
            nodeCount: nodes.size,
            flowCount: flows.size,
            efficiency: calculateNetworkEfficiency(),
            timestamp: Date.now()
          }
        })
      });
      
      console.log("[🔗] Network optimization triggered");
    } catch (error) {
      console.warn("[🔗] Network optimization failed:", error);
    }
  };
  
  const calculateNetworkEfficiency = (): number => {
    let totalEfficiency = 0;
    let activeFlows = 0;
    
    flows.forEach(flow => {
      if (flow.efficiency > 0) {
        totalEfficiency += flow.efficiency;
        activeFlows++;
      }
    });
    
    return activeFlows > 0 ? totalEfficiency / activeFlows : 0;
  };
  
  const renderNode = (node: Node) => {
    const isSelected = selectedNode === node.id;
    
    const nodeColors = {
      RESOURCE: "from-green-600 to-emerald-600",
      PROCESSOR: "from-blue-600 to-cyan-600", 
      STORAGE: "from-yellow-600 to-orange-600",
      TRANSPORT: "from-purple-600 to-indigo-600",
      CONSCIOUSNESS: "from-pink-600 to-purple-600"
    };
    
    return (
      <div
        key={node.id}
        className={`absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-all ${
          isSelected ? "scale-110 z-10" : "hover:scale-105"
        }`}
        style={{ left: node.position.x, top: node.position.y }}
        onClick={() => setSelectedNode(isSelected ? null : node.id)}
      >
        <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${nodeColors[node.type]} ${
          node.active ? "shadow-lg" : "opacity-50"
        } border-2 ${isSelected ? "border-white" : "border-gray-400"} 
        flex items-center justify-center text-white font-bold text-xs`}>
          {node.type === "CONSCIOUSNESS" ? "🧠" : 
           node.type === "RESOURCE" ? "📦" :
           node.type === "PROCESSOR" ? "⚙️" : "🔗"}
        </div>
        
        {isSelected && (
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 bg-black/80 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
            {node.id.replace(/_/g, ' ').toUpperCase()}
          </div>
        )}
      </div>
    );
  };
  
  const renderFlow = (flow: Flow) => {
    const sourceNode = nodes.get(flow.source);
    const targetNode = nodes.get(flow.target);
    
    if (!sourceNode || !targetNode) return null;
    
    const dx = targetNode.position.x - sourceNode.position.x;
    const dy = targetNode.position.y - sourceNode.position.y;
    const length = Math.sqrt(dx * dx + dy * dy);
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    return (
      <div
        key={flow.id}
        className="absolute bg-cyan-400 opacity-60 pointer-events-none"
        style={{
          left: sourceNode.position.x,
          top: sourceNode.position.y - 1,
          width: length,
          height: 2,
          transformOrigin: '0 50%',
          transform: `rotate(${angle}deg)`,
          background: `linear-gradient(90deg, rgba(34, 211, 238, 0.8), rgba(34, 211, 238, 0.2))`
        }}
      />
    );
  };
  
  return (
    <div className="space-y-6 p-6 h-full">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-indigo-400 mb-2">🔗 NodeWeave Interface</h1>
          <p className="text-gray-300">Neural pathway mapping and logistics optimization</p>
        </div>
        
        <div className="flex space-x-2">
          {(["OVERVIEW", "FLOWS", "CONSCIOUSNESS"] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                viewMode === mode 
                  ? "bg-indigo-600 text-white" 
                  : "bg-gray-700 text-gray-300 hover:bg-gray-600"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>
      
      {/* Network Visualization */}
      <div className="bg-black/50 border border-indigo-600/30 rounded-lg p-4 relative overflow-hidden" style={{ height: '400px' }}>
        {/* Grid background */}
        <div className="absolute inset-0 opacity-10" style={{
          backgroundImage: 'radial-gradient(circle, #4f46e5 1px, transparent 1px)',
          backgroundSize: '20px 20px'
        }} />
        
        {/* Flows (render first, behind nodes) */}
        {Array.from(flows.values()).map(renderFlow)}
        
        {/* Nodes */}
        {Array.from(nodes.values()).map(renderNode)}
        
        {/* Network Stats Overlay */}
        <div className="absolute top-4 left-4 bg-black/60 rounded px-3 py-2 text-sm">
          <div className="text-indigo-300 font-bold">Network Status</div>
          <div className="text-gray-300">Nodes: {nodes.size}</div>
          <div className="text-gray-300">Flows: {flows.size}</div>
          <div className="text-gray-300">Efficiency: {(calculateNetworkEfficiency() * 100).toFixed(1)}%</div>
        </div>
      </div>
      
      {/* Control Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Network Optimization */}
        <div className="bg-gradient-to-br from-indigo-900/30 to-blue-900/30 border border-indigo-600/30 rounded-lg p-4">
          <h3 className="text-lg font-bold text-indigo-300 mb-3">Network Optimization</h3>
          
          <div className="space-y-3">
            <div className="text-sm text-gray-300">
              Current efficiency: {(calculateNetworkEfficiency() * 100).toFixed(1)}%
            </div>
            
            <button
              onClick={optimizeNetworkFlow}
              className="w-full bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded transition-colors text-white"
            >
              Optimize Flow Paths
            </button>
            
            <button
              onClick={() => generateNetworkFromGameState()}
              className="w-full bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded transition-colors text-white"
            >
              Refresh Network Map
            </button>
          </div>
        </div>
        
        {/* Node Details */}
        <div className="bg-gradient-to-br from-purple-900/30 to-indigo-900/30 border border-purple-600/30 rounded-lg p-4">
          <h3 className="text-lg font-bold text-purple-300 mb-3">Node Details</h3>
          
          {selectedNode ? (
            <div className="space-y-2">
              <div className="text-sm text-white font-bold">
                {selectedNode.replace(/_/g, ' ').toUpperCase()}
              </div>
              
              {(() => {
                const node = nodes.get(selectedNode);
                if (!node) return null;
                
                return (
                  <div className="space-y-1 text-xs text-gray-300">
                    <div>Type: {node.type}</div>
                    <div>Active: {node.active ? "Yes" : "No"}</div>
                    <div>Connections: {node.connections.length}</div>
                    {node.data && (
                      <div className="mt-2">
                        <div className="text-purple-300 font-bold">Data:</div>
                        {Object.entries(node.data).map(([key, value]) => (
                          <div key={key}>{key}: {String(value)}</div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          ) : (
            <div className="text-sm text-gray-500">
              Click a node to view details
            </div>
          )}
        </div>
        
        {/* Consciousness Monitor */}
        <div className="bg-gradient-to-br from-pink-900/30 to-purple-900/30 border border-pink-600/30 rounded-lg p-4">
          <h3 className="text-lg font-bold text-pink-300 mb-3">Consciousness Level</h3>
          
          <div className="space-y-3">
            {(() => {
              const level = Math.min(1.0, (game.totalEnergyGenerated + game.totalScrapCollected) / 1000);
              return (
                <>
                  <div className="text-2xl font-bold text-white">
                    {(level * 100).toFixed(1)}%
                  </div>
                  
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-pink-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${level * 100}%` }}
                    />
                  </div>
                  
                  <div className="text-xs text-gray-300">
                    Neural pathways: {Array.from(nodes.values()).filter(n => n.active).length} active
                  </div>
                  
                  <div className="text-xs text-gray-300">
                    Information flows: {Array.from(flows.values()).length} streams
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
}