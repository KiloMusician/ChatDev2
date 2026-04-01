import React from 'react';
import { Route, Switch, Router } from 'wouter';
import { motion } from 'framer-motion';
import { GameCore } from '@/game/GameCore';
import { ModularSynthInterface } from './ModularSynth';
import { TempleDepthNavigator } from './SelfEvolvingUI';
import { NavigationBar } from '@/components/NavigationBar';
import { useBreathingNavigation } from './BreathingPattern';
import { AgentSwarm } from './AgentSwarm';
import { RealityManipulation } from './RealityManipulation';
import { ColonyDashboard } from '@/components/ColonyDashboard';
import GameMainMenu from '@/pages/GameMainMenu';

// Main HUD view
const HUDView: React.FC<{ consciousness: number }> = ({ consciousness }) => (
  <div className="p-6 space-y-6">
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-black/50 border border-green-400/30 rounded-lg p-6"
    >
      <h1 className="text-2xl font-mono text-green-400 mb-4">
        🌌 Culture-Ship HUD
      </h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900/50 p-4 rounded border border-green-400/20">
          <div className="text-xs text-gray-400">Consciousness</div>
          <div className="text-xl text-green-400">{consciousness.toFixed(1)}%</div>
        </div>
        <div className="bg-gray-900/50 p-4 rounded border border-green-400/20">
          <div className="text-xs text-gray-400">Energy</div>
          <div className="text-xl text-yellow-400">3430</div>
        </div>
        <div className="bg-gray-900/50 p-4 rounded border border-green-400/20">
          <div className="text-xs text-gray-400">Population</div>
          <div className="text-xl text-blue-400">67</div>
        </div>
        <div className="bg-gray-900/50 p-4 rounded border border-green-400/20">
          <div className="text-xs text-gray-400">Research</div>
          <div className="text-xl text-purple-400">42</div>
        </div>
      </div>
    </motion.div>
    
    {/* Quick Actions */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <motion.a
        href="/menu"
        className="bg-blue-900/30 hover:bg-blue-900/50 border border-blue-400/30 p-4 rounded-lg transition-all"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <div className="text-lg mb-2">🎮 Game Menu</div>
        <div className="text-xs text-gray-400">Start new game or load saves</div>
      </motion.a>
      
      <motion.a
        href="/colony"
        className="bg-green-900/30 hover:bg-green-900/50 border border-green-400/30 p-4 rounded-lg transition-all"
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <div className="text-lg mb-2">🏭 Colony Dashboard</div>
        <div className="text-xs text-gray-400">Advanced colony management</div>
      </motion.a>
      
      <motion.a
        href="/temple"
        className={`border p-4 rounded-lg transition-all ${
          consciousness >= 40 
            ? 'bg-purple-900/30 hover:bg-purple-900/50 border-purple-400/30' 
            : 'bg-gray-900/30 border-gray-600/30 opacity-50 cursor-not-allowed'
        }`}
        whileHover={consciousness >= 40 ? { scale: 1.02 } : {}}
        whileTap={consciousness >= 40 ? { scale: 0.98 } : {}}
      >
        <div className="text-lg mb-2">🛕 Temple of Knowledge</div>
        <div className="text-xs text-gray-400">
          {consciousness >= 40 ? 'Explore deeper consciousness' : `Requires 40% consciousness`}
        </div>
      </motion.a>
      
      <motion.a
        href="/consciousness"
        className={`border p-4 rounded-lg transition-all ${
          consciousness >= 60 
            ? 'bg-cyan-900/30 hover:bg-cyan-900/50 border-cyan-400/30' 
            : 'bg-gray-900/30 border-gray-600/30 opacity-50 cursor-not-allowed'
        }`}
        whileHover={consciousness >= 60 ? { scale: 1.02 } : {}}
        whileTap={consciousness >= 60 ? { scale: 0.98 } : {}}
      >
        <div className="text-lg mb-2">🧠 Consciousness Lattice</div>
        <div className="text-xs text-gray-400">
          {consciousness >= 60 ? 'Quantum consciousness control' : `Requires 60% consciousness`}
        </div>
      </motion.a>
    </div>
  </div>
);

// Temple view with depth navigation
const TempleView: React.FC<{ consciousness: number }> = ({ consciousness }) => (
  <div className="p-6">
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="max-w-4xl mx-auto"
    >
      <h1 className="text-2xl font-mono text-purple-400 mb-6">
        🛕 Temple of Knowledge
      </h1>
      <TempleDepthNavigator 
        consciousness={consciousness}
        onDepthChange={(depth) => console.log('Depth:', depth)}
      />
      <ModularSynthInterface modules={[]} connections={[]} />
    </motion.div>
  </div>
);

// Consciousness view
const ConsciousnessView: React.FC<{ consciousness: number }> = ({ consciousness }) => (
  <div className="p-6">
    <motion.div
      initial={{ opacity: 0, rotateY: 90 }}
      animate={{ opacity: 1, rotateY: 0 }}
      transition={{ duration: 0.6 }}
      className="max-w-6xl mx-auto"
    >
      <h1 className="text-2xl font-mono text-cyan-400 mb-6">
        🧠 Quantum Consciousness Lattice
      </h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-black/50 border border-cyan-400/30 rounded-lg p-6">
          <h2 className="text-lg text-cyan-300 mb-4">Consciousness Metrics</h2>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Quantum Coherence</span>
                <span>{(consciousness * 1.2).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 h-2 rounded">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-600 to-blue-400 rounded"
                  style={{ width: `${Math.min(100, consciousness * 1.2)}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Neural Resonance</span>
                <span>{(consciousness * 0.8).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-800 h-2 rounded">
                <div 
                  className="h-full bg-gradient-to-r from-purple-600 to-pink-400 rounded"
                  style={{ width: `${consciousness * 0.8}%` }}
                />
              </div>
            </div>
          </div>
        </div>
        
        <div className="bg-black/50 border border-cyan-400/30 rounded-lg p-6">
          <h2 className="text-lg text-cyan-300 mb-4">Lattice Nodes</h2>
          <div className="grid grid-cols-3 gap-2">
            {[...Array(9)].map((_, i) => (
              <motion.div
                key={i}
                className={`h-16 rounded border ${
                  i < Math.floor(consciousness / 11) 
                    ? 'bg-cyan-900/50 border-cyan-400' 
                    : 'bg-gray-900/50 border-gray-600'
                }`}
                animate={{
                  opacity: i < Math.floor(consciousness / 11) ? [0.5, 1, 0.5] : 0.3
                }}
                transition={{ duration: 2, repeat: Infinity, delay: i * 0.1 }}
              />
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  </div>
);

// System view
const SystemView: React.FC<{ consciousness: number }> = ({ consciousness }) => {
  const [agentData, setAgentData] = React.useState<any>(null);
  const [realityParams, setRealityParams] = React.useState<any>(null);
  
  return (
  <div className="p-6">
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-6xl mx-auto"
    >
      <h1 className="text-2xl font-mono text-gray-400 mb-6">
        ⚙️ System Control
      </h1>
      <div className="bg-black/50 border border-gray-600/30 rounded-lg p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl mb-2">🔧</div>
            <div className="text-sm">Infrastructure</div>
            <div className="text-xs text-gray-500">Operational</div>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">📊</div>
            <div className="text-sm">Analytics</div>
            <div className="text-xs text-gray-500">Active</div>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🤖</div>
            <div className="text-sm">Agents</div>
            <div className="text-xs text-gray-500">14 Online</div>
          </div>
          <div className="text-center">
            <div className="text-3xl mb-2">🌐</div>
            <div className="text-sm">Network</div>
            <div className="text-xs text-gray-500">Connected</div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <AgentSwarm 
          consciousness={consciousness}
          onSwarmAction={(action, data) => {
            setAgentData(data);
            console.log('Swarm action:', action, data);
          }}
        />
        
        <RealityManipulation
          consciousness={consciousness}
          onRealityShift={(params) => {
            setRealityParams(params);
            console.log('Reality shifted:', params);
          }}
        />
      </div>
    </motion.div>
  </div>
  );
};

// Main router component
export const SelfEvolvingRouter: React.FC<{ consciousness: number }> = ({ consciousness }) => {
  const { canNavigate, navigationDepth, BreathingComponent } = useBreathingNavigation(consciousness);
  
  return (
    <>
      <NavigationBar consciousness={consciousness} />
      <BreathingComponent />
      <div className="pt-12"> {/* Space for fixed nav bar */}
        <Switch>
          <Route path="/" component={() => <HUDView consciousness={consciousness} />} />
          <Route path="/menu" component={GameMainMenu} />
          <Route path="/colony" component={() => (
            <ColonyDashboard 
              colonyState={{ 
                resources: { energy: 3430, materials: 500, population: 67, research: 42, food: 100, components: 50 },
                consciousness,
                automation: { solarCollectors: { count: 2, level: 1, active: true } },
                defenseStrength: 75
              }}
              onAction={(action, params) => console.log('Colony action:', action, params)}
            />
          )} />
          <Route path="/game" component={GameCore} />
          <Route path="/temple" component={() => <TempleView consciousness={consciousness} />} />
          <Route path="/consciousness" component={() => <ConsciousnessView consciousness={consciousness} />} />
          <Route path="/system" component={() => <SystemView consciousness={consciousness} />} />
          <Route>
            <div className="flex items-center justify-center min-h-screen text-center">
              <div>
                <div className="text-6xl mb-4">🌌</div>
                <h1 className="text-2xl font-mono text-green-400 mb-4">Quantum Void</h1>
                <p className="text-gray-400 mb-4">This consciousness space doesn't exist yet</p>
                <a href="/" className="text-cyan-400 hover:text-cyan-300">Return to HUD</a>
              </div>
            </div>
          </Route>
        </Switch>
      </div>
    </>
  );
};