import React, { useState } from 'react';
import { useLocation } from 'wouter';
import { motion, AnimatePresence } from 'framer-motion';

interface NavLinkProps {
  href: string;
  children: React.ReactNode;
  active?: boolean;
}

const NavLink = ({ href, children, active }: NavLinkProps) => {
  const [isHovered, setIsHovered] = useState(false);
  
  return (
    <motion.a 
      href={href}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 relative overflow-hidden ${
        active 
          ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30' 
          : 'text-gray-300 hover:text-white'
      }`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ 
        scale: 1.05,
        transition: { type: "spring", stiffness: 400, damping: 17 }
      }}
      whileTap={{ 
        scale: 0.95,
        transition: { duration: 0.1 }
      }}
      data-testid={`nav-${href.replace('/', '') || 'home'}`}
    >
      <AnimatePresence>
        {isHovered && !active && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-md"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.2 }}
          />
        )}
      </AnimatePresence>
      
      {active && (
        <motion.div
          className="absolute inset-0 bg-blue-600 rounded-md -z-10"
          layoutId="activeNavIndicator"
          transition={{ type: "spring", stiffness: 380, damping: 30 }}
        />
      )}
      
      <span className="relative z-10">{children}</span>
    </motion.a>
  );
};

export function Navigation() {
  const [location] = useLocation();

  return (
    <motion.nav 
      className="bg-gray-800 border-b border-gray-700 relative overflow-hidden"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
    >
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute w-2 h-2 bg-blue-400/30 rounded-full"
          animate={{
            x: [0, 100, 200, 300],
            y: [0, -20, 0, -10],
            opacity: [0, 1, 1, 0]
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "linear"
          }}
        />
        <motion.div
          className="absolute right-20 w-1 h-1 bg-purple-400/40 rounded-full"
          animate={{
            x: [300, 200, 100, 0],
            y: [0, 15, 0, 20],
            opacity: [0, 1, 1, 0]
          }}
          transition={{
            duration: 6,
            repeat: Infinity,
            ease: "linear",
            delay: 2
          }}
        />
      </div>
      
      <div className="container mx-auto px-4 relative">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <motion.h1 
              className="text-xl font-bold text-white cursor-pointer select-none"
              whileHover={{ 
                scale: 1.05,
                textShadow: "0px 0px 8px rgb(59, 130, 246)",
                transition: { duration: 0.2 }
              }}
              data-testid="logo-title"
            >
              ΞNuSyQ
            </motion.h1>
            <div className="flex space-x-1">
              <NavLink href="/" active={location === "/"}>
                🌌 Culture-Ship
              </NavLink>
              <NavLink href="/game-menu" active={location === "/game-menu"}>
                🎮 Game Menu
              </NavLink>
              <NavLink href="/chatdev" active={location === "/chatdev"}>
                🧠 Agent Console
              </NavLink>
              <NavLink href="/vantages" active={location === "/vantages"}>
                🗺️ System Views
              </NavLink>
              <NavLink href="/infrastructure" active={location === "/infrastructure"}>
                🔧 Infrastructure
              </NavLink>
              <NavLink href="/admin" active={location === "/admin"}>
                ⚡ Admin
              </NavLink>
              <NavLink href="/chat" active={location === "/chat"}>
                💬 Agent Chat
              </NavLink>
            </div>
          </div>
          <motion.div 
            className="text-sm text-gray-400 relative"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <motion.span
              animate={{ 
                opacity: [0.4, 1, 0.4],
              }}
              transition={{
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut"
              }}
            >
              Autonomous Development Ecosystem
            </motion.span>
          </motion.div>
        </div>
      </div>
    </motion.nav>
  );
}