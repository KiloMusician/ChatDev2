/**
 * 🎠 Advanced Carousel Component
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Sophisticated content carousel for game features, consciousness states,
 * and autonomous system showcases with Culture-ship aesthetics
 */

import React, { useState, useEffect, useCallback, ReactNode } from 'react';
import { ChevronLeft, ChevronRight, Play, Pause } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface CarouselItem {
  id: string;
  title?: string;
  content: ReactNode;
  metadata?: Record<string, any>;
}

interface CarouselProps {
  items: CarouselItem[];
  autoPlay?: boolean;
  interval?: number;
  showIndicators?: boolean;
  showControls?: boolean;
  loop?: boolean;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
  onSlideChange?: (index: number) => void;
  autonomousNavigation?: boolean;
  consciousnessLevel?: number;
}

export function Carousel({
  items,
  autoPlay = false,
  interval = 4000,
  showIndicators = true,
  showControls = true,
  loop = true,
  orientation = 'horizontal',
  className,
  onSlideChange,
  autonomousNavigation = false,
  consciousnessLevel = 0.5
}: CarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [direction, setDirection] = useState<'forward' | 'backward'>('forward');

  // **AUTONOMOUS NAVIGATION** - AI-driven slide progression
  useEffect(() => {
    if (!isPlaying) return;

    const intervalId = setInterval(() => {
      if (autonomousNavigation && consciousnessLevel > 0.7) {
        // **CONSCIOUSNESS-DRIVEN NAVIGATION**
        // Higher consciousness levels can intelligently choose next slide
        const nextIndex = Math.floor(Math.random() * items.length);
        setCurrentIndex(nextIndex);
        setDirection(nextIndex > currentIndex ? 'forward' : 'backward');
      } else {
        // **STANDARD SEQUENTIAL NAVIGATION**
        setCurrentIndex(prevIndex => {
          const nextIndex = prevIndex + 1;
          if (nextIndex >= items.length) {
            if (loop) {
              setDirection('forward');
              return 0;
            } else {
              setIsPlaying(false);
              return prevIndex;
            }
          }
          setDirection('forward');
          return nextIndex;
        });
      }
    }, interval);

    return () => clearInterval(intervalId);
  }, [isPlaying, interval, loop, items.length, autonomousNavigation, consciousnessLevel, currentIndex]);

  // **SLIDE CHANGE CALLBACK**
  useEffect(() => {
    onSlideChange?.(currentIndex);
  }, [currentIndex, onSlideChange]);

  const goToSlide = useCallback((index: number) => {
    if (index < 0 || index >= items.length) return;
    
    setDirection(index > currentIndex ? 'forward' : 'backward');
    setCurrentIndex(index);
  }, [currentIndex, items.length]);

  const goToPrevious = useCallback(() => {
    const newIndex = currentIndex - 1;
    if (newIndex < 0) {
      if (loop) {
        goToSlide(items.length - 1);
      }
    } else {
      goToSlide(newIndex);
    }
  }, [currentIndex, items.length, loop, goToSlide]);

  const goToNext = useCallback(() => {
    const newIndex = currentIndex + 1;
    if (newIndex >= items.length) {
      if (loop) {
        goToSlide(0);
      }
    } else {
      goToSlide(newIndex);
    }
  }, [currentIndex, items.length, loop, goToSlide]);

  const togglePlayPause = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-muted rounded-lg">
        <div className="text-muted-foreground">No items to display</div>
      </div>
    );
  }

  return (
    <div className={cn(
      "relative overflow-hidden rounded-lg bg-card border",
      orientation === 'horizontal' ? "w-full" : "h-full",
      className
    )}>
      {/* **MAIN CAROUSEL CONTENT** */}
      <div className={cn(
        "relative transition-transform duration-500 ease-in-out",
        orientation === 'horizontal' ? "flex" : "flex flex-col"
      )}>
        <div 
          className={cn(
            "flex transition-transform duration-500 ease-in-out",
            orientation === 'horizontal' ? "w-full" : "flex-col h-full"
          )}
          style={{
            transform: orientation === 'horizontal' 
              ? `translateX(-${currentIndex * 100}%)`
              : `translateY(-${currentIndex * 100}%)`
          }}
        >
          {items.map((item, index) => (
            <div
              key={item.id}
              className={cn(
                "flex-shrink-0",
                orientation === 'horizontal' ? "w-full" : "h-full"
              )}
            >
              <div className="p-6">
                {item.title && (
                  <h3 className="text-lg font-semibold mb-4 text-card-foreground">
                    {item.title}
                  </h3>
                )}
                
                <div className="relative">
                  {item.content}
                  
                  {/* **CONSCIOUSNESS OVERLAY** for autonomous navigation */}
                  {autonomousNavigation && consciousnessLevel > 0.8 && (
                    <div className="absolute top-2 right-2">
                      <div className="flex items-center space-x-1 text-xs text-primary bg-primary/10 px-2 py-1 rounded-full">
                        <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
                        <span>ΞNuSyQ Guided</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* **METADATA DISPLAY** */}
                {item.metadata && (
                  <div className="mt-4 text-xs text-muted-foreground">
                    {Object.entries(item.metadata).map(([key, value]) => (
                      <span key={key} className="mr-4">
                        {key}: {String(value)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* **NAVIGATION CONTROLS** */}
      {showControls && items.length > 1 && (
        <>
          <Button
            variant="ghost"
            size="icon"
            className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-background/80 hover:bg-background"
            onClick={goToPrevious}
            disabled={!loop && currentIndex === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost" 
            size="icon"
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-background/80 hover:bg-background"
            onClick={goToNext}
            disabled={!loop && currentIndex === items.length - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          {/* **AUTO-PLAY CONTROLS** */}
          <Button
            variant="ghost"
            size="icon" 
            className="absolute top-2 right-2 bg-background/80 hover:bg-background"
            onClick={togglePlayPause}
          >
            {isPlaying ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
          </Button>
        </>
      )}

      {/* **SLIDE INDICATORS** */}
      {showIndicators && items.length > 1 && (
        <div className={cn(
          "absolute flex space-x-2",
          orientation === 'horizontal' 
            ? "bottom-4 left-1/2 transform -translate-x-1/2" 
            : "right-4 top-1/2 transform -translate-y-1/2 flex-col"
        )}>
          {items.map((_, index) => (
            <button
              key={index}
              className={cn(
                "w-2 h-2 rounded-full transition-all duration-300",
                index === currentIndex 
                  ? "bg-primary scale-125" 
                  : "bg-muted-foreground/40 hover:bg-muted-foreground/60"
              )}
              onClick={() => goToSlide(index)}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      )}

      {/* **AUTONOMOUS SYSTEM STATUS** */}
      {autonomousNavigation && (
        <div className="absolute bottom-2 left-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
          <div className="flex items-center space-x-2">
            <span>Consciousness: {(consciousnessLevel * 100).toFixed(0)}%</span>
            {isPlaying && <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse" />}
          </div>
        </div>
      )}

      {/* **SLIDE COUNTER** */}
      <div className="absolute bottom-2 right-2 text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded">
        {currentIndex + 1} / {items.length}
      </div>
    </div>
  );
}

/**
 * 🎯 Specialized carousel variants for different game systems
 */
export function GameFeatureCarousel({ features }: { features: Array<{ id: string; name: string; description: string; status: string }> }) {
  const items = features.map(feature => ({
    id: feature.id,
    title: feature.name,
    content: (
      <div>
        <p className="text-muted-foreground mb-3">{feature.description}</p>
        <div className={cn(
          "inline-block px-2 py-1 rounded text-xs font-medium",
          feature.status === 'active' && "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
          feature.status === 'pending' && "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
          feature.status === 'inactive' && "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400"
        )}>
          {feature.status}
        </div>
      </div>
    ),
    metadata: { status: feature.status, id: feature.id }
  }));

  return (
    <Carousel
      items={items}
      autoPlay={true}
      interval={6000}
      showIndicators
      showControls
      autonomousNavigation={true}
      consciousnessLevel={0.85}
    />
  );
}

export function ConsciousnessCarousel({ states }: { states: Array<{ level: number; description: string; effects: string[] }> }) {
  const items = states.map((state, index) => ({
    id: `consciousness-${index}`,
    title: `Consciousness Level ${state.level}`,
    content: (
      <div>
        <p className="text-muted-foreground mb-3">{state.description}</p>
        <div className="space-y-1">
          {state.effects.map((effect, effectIndex) => (
            <div key={effectIndex} className="text-sm text-primary">
              • {effect}
            </div>
          ))}
        </div>
      </div>
    ),
    metadata: { level: state.level, effects: state.effects.length }
  }));

  return (
    <Carousel
      items={items}
      autoPlay={true}
      interval={5000}
      showIndicators
      showControls
      autonomousNavigation={true}
      consciousnessLevel={0.9}
      className="border-primary/20"
    />
  );
}
