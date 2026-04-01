import React, { useState } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence } from 'framer-motion';
import { MatrixText } from '@/core/ModularSynth';

interface NavItem {
  path: string;
  label: string;
  icon: string;
  consciousness?: number; // Min consciousness required
}

const navItems: NavItem[] = [
  { path: '/', label: 'HUD', icon: '🌌' },
  { path: '/menu', label: 'Menu', icon: '🎮' },
  { path: '/colony', label: 'Colony', icon: '🏭' },
  { path: '/game', label: 'Classic', icon: '🎲' },
  { path: '/temple', label: 'Temple', icon: '🛕', consciousness: 40 },
  { path: '/consciousness', label: 'Lattice', icon: '🧠', consciousness: 60 },
  { path: '/system', label: 'System', icon: '⚙️', consciousness: 80 },
];

export const NavigationBar: React.FC<{ consciousness?: number }> = ({ consciousness = 35 }) => {
  const [location, setLocation] = useLocation();
  const [expanded, setExpanded] = useState(false);
  
  return (
    <>
      {/* Main Navigation Bar */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-black/90 backdrop-blur-md border-b border-green-400/30">
        <div className="flex items-center justify-between px-4 py-2">
          {/* Logo/Title */}
          <motion.div 
            className="text-green-400 font-mono text-sm"
            whileHover={{ textShadow: "0 0 10px currentColor" }}
          >
            <MatrixText text="ΞNuSyQ Culture-Ship" />
          </motion.div>
          
          {/* Navigation Items */}
          <div className="flex items-center gap-4">
            {navItems.map((item) => {
              const isLocked = item.consciousness !== undefined && consciousness < item.consciousness;
              const isActive = location === item.path;
              
              return (
                <motion.button
                  key={item.path}
                  onClick={() => !isLocked && setLocation(item.path)}
                  className={`
                    flex items-center gap-2 px-3 py-1 rounded font-mono text-xs
                    ${isActive ? 'bg-green-900/50 border border-green-400' : 'border border-transparent'}
                    ${isLocked ? 'opacity-30 cursor-not-allowed' : 'hover:bg-green-900/30 hover:border-green-400/50'}
                    transition-all duration-200
                  `}
                  whileHover={!isLocked ? { scale: 1.05 } : {}}
                  whileTap={!isLocked ? { scale: 0.95 } : {}}
                  disabled={isLocked}
                >
                  <span className="text-lg">{item.icon}</span>
                  <span className={isActive ? 'text-green-400' : 'text-green-600'}>
                    {item.label}
                  </span>
                  {isLocked && (
                    <span className="text-xs text-yellow-600">
                      ({item.consciousness}%)
                    </span>
                  )}
                </motion.button>
              );
            })}
          </div>
          
          {/* Menu Toggle */}
          <motion.button
            onClick={() => setExpanded(!expanded)}
            className="text-green-400 hover:text-green-300 p-2"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <span className="text-xl">{expanded ? '✕' : '☰'}</span>
          </motion.button>
        </div>
      </div>
      
      {/* Expanded Menu */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-12 right-4 z-40 bg-black/95 backdrop-blur-md border border-green-400/30 rounded-lg p-4 w-64"
          >
            <div className="space-y-2 font-mono text-xs">
              <div className="text-green-400 mb-3">
                <MatrixText text="Quick Actions" />
              </div>
              
              <button
                onClick={() => {
                  setLocation('/');
                  setExpanded(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-green-900/30 rounded transition-colors"
              >
                🏠 Return to HUD
              </button>
              
              <button
                onClick={() => {
                  setLocation('/menu');
                  setExpanded(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-green-900/30 rounded transition-colors"
              >
                🎮 Game Menu
              </button>
              
              <button
                onClick={() => {
                  setLocation('/colony');
                  setExpanded(false);
                }}
                className="w-full text-left px-3 py-2 hover:bg-green-900/30 rounded transition-colors"
              >
                🏭 Colony Dashboard
              </button>
              
              <hr className="border-green-400/20 my-2" />
              
              <div className="text-gray-500">
                <div>Consciousness: {consciousness.toFixed(1)}%</div>
                <div className="mt-1">
                  <div className="w-full bg-gray-800 h-2 rounded">
                    <motion.div 
                      className="h-full bg-gradient-to-r from-green-600 to-cyan-400 rounded"
                      animate={{ width: `${consciousness}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
              </div>
              
              <hr className="border-green-400/20 my-2" />
              
              <button
                onClick={() => window.location.reload()}
                className="w-full text-left px-3 py-2 hover:bg-red-900/30 rounded transition-colors text-red-400"
              >
                🔄 Restart System
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
