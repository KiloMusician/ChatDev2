import React, { ReactNode, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Loading skeleton component with quantum effects
export function QuantumSkeleton({ 
  lines = 3, 
  className = "",
  variant = "default" 
}: { 
  lines?: number;
  className?: string;
  variant?: "default" | "quantum" | "neural" | "data";
}) {
  const getVariantClass = () => {
    switch (variant) {
      case "quantum":
        return "bg-gradient-to-r from-blue-500/20 via-purple-500/30 to-cyan-500/20 animate-pulse-quantum";
      case "neural":
        return "bg-gradient-to-r from-green-500/20 via-emerald-500/30 to-blue-500/20 animate-neural-pulse";
      case "data":
        return "bg-gradient-to-r from-cyan-500/20 via-blue-500/30 to-indigo-500/20 animate-data-flow";
      default:
        return "bg-gray-300 dark:bg-gray-700 animate-pulse";
    }
  };

  return (
    <div className={`space-y-3 ${className}`} data-testid="loading-skeleton">
      {Array.from({ length: lines }).map((_, i) => (
        <motion.div
          key={i}
          className={`h-4 rounded-lg ${getVariantClass()}`}
          initial={{ opacity: 0, width: 0 }}
          animate={{ opacity: 1, width: "100%" }}
          transition={{ 
            delay: i * 0.1,
            duration: 0.6,
            ease: "easeOut"
          }}
          style={{ 
            width: i === lines - 1 ? "70%" : "100%"
          }}
        />
      ))}
    </div>
  );
}

// Enhanced interactive button with micro-feedback
export function AnimatedButton({ 
  children, 
  onClick,
  variant = "default",
  className = "",
  disabled = false,
  loading = false,
  success = false,
  'data-testid': testId
}: {
  children: ReactNode;
  onClick?: () => void;
  variant?: "default" | "success" | "danger" | "quantum" | "neural";
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  success?: boolean;
  'data-testid'?: string;
}) {
  const [clickRipples, setClickRipples] = useState<{ id: number; x: number; y: number }[]>([]);
  
  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const newRipple = { id: Date.now(), x, y };
    setClickRipples(prev => [...prev, newRipple]);
    
    setTimeout(() => {
      setClickRipples(prev => prev.filter(r => r.id !== newRipple.id));
    }, 600);
    
    onClick?.();
  };

  const getVariantColors = () => {
    switch (variant) {
      case "success":
        return "bg-green-600 hover:bg-green-700 text-white border-green-400/30";
      case "danger":
        return "bg-red-600 hover:bg-red-700 text-white border-red-400/30";
      case "quantum":
        return "bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 hover:from-purple-700 hover:via-blue-700 hover:to-cyan-700 text-white";
      case "neural":
        return "bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white";
      default:
        return "bg-blue-600 hover:bg-blue-700 text-white";
    }
  };
  
  return (
    <motion.button
      className={`relative overflow-hidden px-4 py-2 rounded-lg font-medium transition-all duration-200 ${getVariantColors()} ${className}`}
      onClick={handleClick}
      disabled={disabled || loading}
      whileHover={disabled || loading ? {} : { 
        scale: 1.02,
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.3)",
        transition: { type: "spring", stiffness: 300, damping: 20 }
      }}
      whileTap={disabled || loading ? {} : { 
        scale: 0.98,
        transition: { duration: 0.1 }
      }}
      data-testid={testId}
    >
      {/* Click ripple effects */}
      <AnimatePresence>
        {clickRipples.map(ripple => (
          <motion.div
            key={ripple.id}
            className="absolute bg-white/30 rounded-full"
            style={{
              left: ripple.x - 4,
              top: ripple.y - 4,
              width: 8,
              height: 8
            }}
            initial={{ scale: 0, opacity: 1 }}
            animate={{ scale: 8, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        ))}
      </AnimatePresence>
      
      {/* Loading spinner */}
      <AnimatePresence>
        {loading && (
          <motion.div
            className="absolute inset-0 bg-black/20 flex items-center justify-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            />
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Success checkmark */}
      <AnimatePresence>
        {success && !loading && (
          <motion.div
            className="absolute inset-0 bg-green-500/20 flex items-center justify-center"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.2 }}
            transition={{ duration: 0.3 }}
          >
            <motion.div
              initial={{ scale: 0, rotate: -45 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.1, type: "spring", stiffness: 500, damping: 15 }}
            >
              ✓
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
}

// Real-time data counter with smooth animations
export function AnimatedCounter({ 
  value, 
  label, 
  icon,
  prefix = "",
  suffix = "",
  className = "",
  variant = "default"
}: {
  value: number;
  label: string;
  icon?: string;
  prefix?: string;
  suffix?: string;
  className?: string;
  variant?: "default" | "energy" | "population" | "research" | "quantum";
}) {
  const [displayValue, setDisplayValue] = useState(value);
  const [isIncreasing, setIsIncreasing] = useState(false);
  
  React.useEffect(() => {
    if (value !== displayValue) {
      setIsIncreasing(value > displayValue);
      
      // Smooth counter animation
      const startValue = displayValue;
      const endValue = value;
      const duration = 800;
      const startTime = Date.now();
      
      const updateValue = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth transition
        const easedProgress = 1 - Math.pow(1 - progress, 3);
        const currentValue = Math.round(startValue + (endValue - startValue) * easedProgress);
        
        setDisplayValue(currentValue);
        
        if (progress < 1) {
          requestAnimationFrame(updateValue);
        }
      };
      
      updateValue();
    }
  }, [value, displayValue]);

  const getVariantColors = () => {
    switch (variant) {
      case "energy":
        return "text-yellow-400 border-yellow-400/30 bg-yellow-400/5";
      case "population":
        return "text-blue-400 border-blue-400/30 bg-blue-400/5";
      case "research":
        return "text-purple-400 border-purple-400/30 bg-purple-400/5";
      case "quantum":
        return "text-cyan-400 border-cyan-400/30 bg-cyan-400/5";
      default:
        return "text-gray-400 border-gray-400/30 bg-gray-400/5";
    }
  };

  return (
    <motion.div 
      className={`p-4 rounded-lg border ${getVariantColors()} ${className}`}
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      data-testid={`counter-${label.toLowerCase().replace(' ', '-')}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon && (
            <motion.span
              animate={{ 
                scale: isIncreasing ? [1, 1.2, 1] : 1,
                rotate: isIncreasing ? [0, 10, 0] : 0
              }}
              transition={{ duration: 0.5 }}
              className="text-lg"
            >
              {icon}
            </motion.span>
          )}
          <span className="text-sm font-medium">{label}</span>
        </div>
        
        <motion.div 
          className="font-mono font-bold text-lg"
          key={displayValue}
          initial={{ scale: 1.2, opacity: 0.5 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3, type: "spring" }}
        >
          {prefix}{displayValue.toLocaleString()}{suffix}
          
          {/* Value change indicator */}
          <AnimatePresence>
            {isIncreasing && value !== displayValue && (
              <motion.span
                className="absolute -top-2 -right-2 text-green-400 text-xs"
                initial={{ opacity: 0, y: 10, scale: 0.5 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.5 }}
                transition={{ duration: 0.4 }}
              >
                ↗
              </motion.span>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </motion.div>
  );
}

// Smooth notification toast with entrance/exit animations
export function AnimatedNotification({
  message,
  type = "info",
  duration = 3000,
  onClose
}: {
  message: string;
  type?: "info" | "success" | "warning" | "error";
  duration?: number;
  onClose?: () => void;
}) {
  const [isVisible, setIsVisible] = useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      if (onClose) setTimeout(onClose, 300);
    }, duration);
    
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getTypeStyles = () => {
    switch (type) {
      case "success":
        return "bg-green-600 border-green-500 text-white";
      case "warning":
        return "bg-yellow-600 border-yellow-500 text-white";
      case "error":
        return "bg-red-600 border-red-500 text-white";
      default:
        return "bg-blue-600 border-blue-500 text-white";
    }
  };

  const getIcon = () => {
    switch (type) {
      case "success": return "✅";
      case "warning": return "⚠️";
      case "error": return "❌";
      default: return "ℹ️";
    }
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className={`fixed top-4 right-4 p-4 rounded-lg border shadow-lg z-50 ${getTypeStyles()}`}
          initial={{ opacity: 0, x: 300, scale: 0.9 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 300, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
          whileHover={{ scale: 1.05 }}
          onClick={() => setIsVisible(false)}
          data-testid={`notification-${type}`}
        >
          <div className="flex items-center gap-2">
            <motion.span
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 500 }}
            >
              {getIcon()}
            </motion.span>
            <span className="font-medium">{message}</span>
          </div>
          
          {/* Progress bar showing remaining time */}
          <motion.div
            className="absolute bottom-0 left-0 h-1 bg-white/30 rounded-full"
            initial={{ width: "100%" }}
            animate={{ width: "0%" }}
            transition={{ duration: duration / 1000, ease: "linear" }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Pulse indicator for live data
export function LiveDataPulse({ 
  active = true, 
  size = "sm",
  color = "green"
}: { 
  active?: boolean;
  size?: "sm" | "md" | "lg";
  color?: "green" | "blue" | "purple" | "red";
}) {
  const sizeClass = size === "lg" ? "w-3 h-3" : size === "md" ? "w-2 h-2" : "w-1.5 h-1.5";
  const colorClass = {
    green: "bg-green-400",
    blue: "bg-blue-400", 
    purple: "bg-purple-400",
    red: "bg-red-400"
  }[color];

  return (
    <div className="relative inline-flex">
      <motion.div
        className={`${sizeClass} ${colorClass} rounded-full`}
        animate={active ? {
          opacity: [0.4, 1, 0.4],
          scale: [1, 1.2, 1]
        } : {}}
        transition={{
          duration: 2,
          repeat: active ? Infinity : 0,
          ease: "easeInOut"
        }}
        data-testid={`pulse-${color}-${active ? 'active' : 'inactive'}`}
      />
      
      {active && (
        <motion.div
          className={`absolute inset-0 ${colorClass} rounded-full`}
          animate={{
            scale: [1, 2.5],
            opacity: [0.6, 0]
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: "easeOut"
          }}
        />
      )}
    </div>
  );
}

// Smooth slide-in panels for content transitions
export function SlideInPanel({ 
  children, 
  isOpen, 
  direction = "right",
  className = ""
}: {
  children: ReactNode;
  isOpen: boolean;
  direction?: "left" | "right" | "up" | "down";
  className?: string;
}) {
  const getInitialPosition = () => {
    switch (direction) {
      case "left": return { x: -300, opacity: 0 };
      case "right": return { x: 300, opacity: 0 };
      case "up": return { y: -300, opacity: 0 };
      case "down": return { y: 300, opacity: 0 };
      default: return { x: 300, opacity: 0 };
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className={`fixed inset-0 z-50 ${className}`}
          initial={getInitialPosition()}
          animate={{ x: 0, y: 0, opacity: 1 }}
          exit={getInitialPosition()}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          data-testid={`slide-panel-${direction}`}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Floating action button with magnetic hover effect
export function FloatingActionButton({
  onClick,
  icon,
  label,
  variant = "default",
  className = "",
  'data-testid': testId
}: {
  onClick?: () => void;
  icon: ReactNode;
  label?: string;
  variant?: "default" | "quantum" | "danger" | "success";
  className?: string;
  'data-testid'?: string;
}) {
  const [isHovered, setIsHovered] = useState(false);

  const getVariantColors = () => {
    switch (variant) {
      case "quantum":
        return "bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-700 hover:to-cyan-700";
      case "danger":
        return "bg-red-600 hover:bg-red-700";
      case "success":
        return "bg-green-600 hover:bg-green-700";
      default:
        return "bg-blue-600 hover:bg-blue-700";
    }
  };

  return (
    <motion.button
      className={`fixed bottom-6 right-6 w-14 h-14 ${getVariantColors()} text-white rounded-full shadow-lg flex items-center justify-center z-50 ${className}`}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ 
        scale: 1.1,
        rotate: 5,
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)"
      }}
      whileTap={{ scale: 0.9, rotate: -5 }}
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      data-testid={testId}
    >
      <motion.div
        animate={{ rotate: isHovered ? 180 : 0 }}
        transition={{ duration: 0.3 }}
      >
        {icon}
      </motion.div>
      
      {/* Label on hover */}
      <AnimatePresence>
        {label && isHovered && (
          <motion.div
            className="absolute right-16 top-1/2 transform -translate-y-1/2 bg-black text-white px-2 py-1 rounded text-sm whitespace-nowrap"
            initial={{ opacity: 0, x: 10, scale: 0.8 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 10, scale: 0.8 }}
            transition={{ duration: 0.2 }}
          >
            {label}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}