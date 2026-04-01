import { useState, useEffect } from 'react';

// Hook for managing staggered animations
export function useStaggeredAnimation(items: any[], delay = 0.1) {
  const [animatedItems, setAnimatedItems] = useState<number[]>([]);

  useEffect(() => {
    items.forEach((_, index) => {
      setTimeout(() => {
        setAnimatedItems(prev => [...prev, index]);
      }, index * delay * 1000);
    });

    return () => setAnimatedItems([]);
  }, [items, delay]);

  return animatedItems;
}

// Hook for managing notification state
export function useNotifications() {
  const [notifications, setNotifications] = useState<Array<{
    id: number;
    message: string;
    type: "info" | "success" | "warning" | "error";
    duration?: number;
  }>>([]);

  const addNotification = (
    message: string, 
    type: "info" | "success" | "warning" | "error" = "info",
    duration = 3000
  ) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type, duration }]);
  };

  const removeNotification = (id: number) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return { notifications, addNotification, removeNotification };
}

// Hook for managing smooth value transitions
export function useSmoothTransition(value: number, duration = 800) {
  const [displayValue, setDisplayValue] = useState(value);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (value !== displayValue) {
      setIsTransitioning(true);
      
      const startValue = displayValue;
      const endValue = value;
      const startTime = Date.now();
      
      const updateValue = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Smooth easing function
        const easedProgress = 1 - Math.pow(1 - progress, 3);
        const currentValue = startValue + (endValue - startValue) * easedProgress;
        
        setDisplayValue(currentValue);
        
        if (progress < 1) {
          requestAnimationFrame(updateValue);
        } else {
          setIsTransitioning(false);
        }
      };
      
      updateValue();
    }
  }, [value, displayValue, duration]);

  return { displayValue, isTransitioning };
}

// Hook for managing hover states with delays
export function useHoverDelay(delay = 200) {
  const [isHovered, setIsHovered] = useState(false);
  const [showHover, setShowHover] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (isHovered) {
      timer = setTimeout(() => setShowHover(true), delay);
    } else {
      setShowHover(false);
    }
    
    return () => clearTimeout(timer);
  }, [isHovered, delay]);

  return {
    isHovered,
    showHover,
    onMouseEnter: () => setIsHovered(true),
    onMouseLeave: () => setIsHovered(false)
  };
}

// Hook for managing click feedback
export function useClickFeedback() {
  const [clicks, setClicks] = useState<Array<{ id: number; x: number; y: number }>>([]);

  const handleClick = (event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    const clickId = Date.now();
    setClicks(prev => [...prev, { id: clickId, x, y }]);
    
    setTimeout(() => {
      setClicks(prev => prev.filter(click => click.id !== clickId));
    }, 600);
  };

  return { clicks, handleClick };
}