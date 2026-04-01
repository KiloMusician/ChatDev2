/**
 * Dimensional Gesture Recognition Hook
 * Provides intuitive gesture-based interactions for dimensional navigation
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface GesturePattern {
  type: 'swipe' | 'circle' | 'pinch' | 'tap' | 'hold';
  direction?: 'up' | 'down' | 'left' | 'right' | 'clockwise' | 'counterclockwise';
  intensity: number;
  duration: number;
}

interface DimensionalGesture {
  intent: 'explore' | 'focus' | 'boost' | 'harmonize' | 'navigate';
  dimension?: string;
  pattern: GesturePattern;
  confidence: number;
}

export const useDimensionalGestures = () => {
  const [isListening, setIsListening] = useState(false);
  const [lastGesture, setLastGesture] = useState<DimensionalGesture | null>(null);
  const [gestureHistory, setGestureHistory] = useState<GesturePattern[]>([]);
  
  const touchStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const touchMoveHistory = useRef<Array<{ x: number; y: number; time: number }>>([]);

  // Gesture pattern recognition
  const recognizeGesture = useCallback((touchHistory: Array<{ x: number; y: number; time: number }>): GesturePattern | null => {
    if (touchHistory.length < 2) return null;

    const start = touchHistory[0];
    const end = touchHistory[touchHistory.length - 1];
    if (!start || !end) return null;
    
    const duration = end.time - start.time;
    const deltaX = end.x - start.x;
    const deltaY = end.y - start.y;
    const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

    // Quick tap
    if (duration < 200 && distance < 10) {
      return {
        type: 'tap',
        intensity: 0.5,
        duration
      };
    }

    // Hold gesture
    if (duration > 1000 && distance < 15) {
      return {
        type: 'hold',
        intensity: Math.min(duration / 2000, 1),
        duration
      };
    }

    // Swipe gestures
    if (distance > 50 && duration < 800) {
      const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
      let direction: 'up' | 'down' | 'left' | 'right';
      
      if (angle > -45 && angle <= 45) direction = 'right';
      else if (angle > 45 && angle <= 135) direction = 'down';
      else if (angle > 135 || angle <= -135) direction = 'left';
      else direction = 'up';

      return {
        type: 'swipe',
        direction,
        intensity: Math.min(distance / 200, 1),
        duration
      };
    }

    // Circular gesture detection
    if (touchHistory.length > 10 && duration > 300) {
      const centerX = touchHistory.reduce((sum, p) => sum + p.x, 0) / touchHistory.length;
      const centerY = touchHistory.reduce((sum, p) => sum + p.y, 0) / touchHistory.length;
      
      let totalAngle = 0;
      for (let i = 1; i < touchHistory.length; i++) {
        const prev = touchHistory[i - 1];
        const curr = touchHistory[i];
        if (!prev || !curr) continue;
        
        const angle1 = Math.atan2(prev.y - centerY, prev.x - centerX);
        const angle2 = Math.atan2(curr.y - centerY, curr.x - centerX);
        let angleDiff = angle2 - angle1;
        
        // Normalize angle difference
        if (angleDiff > Math.PI) angleDiff -= 2 * Math.PI;
        if (angleDiff < -Math.PI) angleDiff += 2 * Math.PI;
        
        totalAngle += angleDiff;
      }

      if (Math.abs(totalAngle) > Math.PI) {
        return {
          type: 'circle',
          direction: totalAngle > 0 ? 'counterclockwise' : 'clockwise',
          intensity: Math.min(Math.abs(totalAngle) / (2 * Math.PI), 1),
          duration
        };
      }
    }

    return null;
  }, []);

  // Interpret gesture intent
  const interpretGesture = useCallback((pattern: GesturePattern): DimensionalGesture => {
    let intent: DimensionalGesture['intent'] = 'explore';
    let dimension: string | undefined;
    let confidence = 0.7;

    switch (pattern.type) {
      case 'tap':
        intent = 'focus';
        confidence = 0.9;
        break;
        
      case 'hold':
        intent = 'boost';
        confidence = 0.8;
        break;
        
      case 'swipe':
        intent = 'navigate';
        // Map swipe directions to dimensions
        switch (pattern.direction) {
          case 'up':
            dimension = 'consciousness';
            break;
          case 'right':
            dimension = 'energy';
            break;
          case 'down':
            dimension = 'population';
            break;
          case 'left':
            dimension = 'research';
            break;
        }
        confidence = 0.85;
        break;
        
      case 'circle':
        intent = 'harmonize';
        confidence = 0.75;
        break;
    }

    return {
      intent,
      dimension,
      pattern,
      confidence
    };
  }, []);

  // Touch event handlers
  const handleTouchStart = useCallback((event: TouchEvent) => {
    if (!isListening) return;
    
    const touch = event.touches[0];
    if (!touch) return;
    
    touchStartRef.current = {
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now()
    };
    touchMoveHistory.current = [touchStartRef.current];
  }, [isListening]);

  const handleTouchMove = useCallback((event: TouchEvent) => {
    if (!isListening || !touchStartRef.current) return;
    
    const touch = event.touches[0];
    if (!touch) return;
    
    touchMoveHistory.current.push({
      x: touch.clientX,
      y: touch.clientY,
      time: Date.now()
    });

    // Limit history size for performance
    if (touchMoveHistory.current.length > 50) {
      touchMoveHistory.current = touchMoveHistory.current.slice(-50);
    }
  }, [isListening]);

  const handleTouchEnd = useCallback((event: TouchEvent) => {
    if (!isListening || !touchStartRef.current) return;
    
    const pattern = recognizeGesture(touchMoveHistory.current);
    if (pattern) {
      const gesture = interpretGesture(pattern);
      setLastGesture(gesture);
      setGestureHistory(prev => [...prev.slice(-9), pattern]);
    }

    touchStartRef.current = null;
    touchMoveHistory.current = [];
  }, [isListening, recognizeGesture, interpretGesture]);

  // Mouse event handlers for desktop
  const handleMouseDown = useCallback((event: MouseEvent) => {
    if (!isListening) return;
    
    touchStartRef.current = {
      x: event.clientX,
      y: event.clientY,
      time: Date.now()
    };
    touchMoveHistory.current = [touchStartRef.current];
  }, [isListening]);

  const handleMouseMove = useCallback((event: MouseEvent) => {
    if (!isListening || !touchStartRef.current || event.buttons !== 1) return;
    
    touchMoveHistory.current.push({
      x: event.clientX,
      y: event.clientY,
      time: Date.now()
    });

    if (touchMoveHistory.current.length > 50) {
      touchMoveHistory.current = touchMoveHistory.current.slice(-50);
    }
  }, [isListening]);

  const handleMouseUp = useCallback((event: MouseEvent) => {
    if (!isListening || !touchStartRef.current) return;
    
    const pattern = recognizeGesture(touchMoveHistory.current);
    if (pattern) {
      const gesture = interpretGesture(pattern);
      setLastGesture(gesture);
      setGestureHistory(prev => [...prev.slice(-9), pattern]);
    }

    touchStartRef.current = null;
    touchMoveHistory.current = [];
  }, [isListening, recognizeGesture, interpretGesture]);

  // Set up event listeners
  useEffect(() => {
    if (!isListening) return;

    // Touch events
    document.addEventListener('touchstart', handleTouchStart, { passive: false });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd, { passive: false });

    // Mouse events
    document.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isListening, handleTouchStart, handleTouchMove, handleTouchEnd, handleMouseDown, handleMouseMove, handleMouseUp]);

  return {
    isListening,
    setIsListening,
    lastGesture,
    gestureHistory,
    clearLastGesture: () => setLastGesture(null)
  };
};