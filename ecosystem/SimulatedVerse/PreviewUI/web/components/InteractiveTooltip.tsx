/**
 * Interactive Onboarding Tooltip System
 * Extends existing HoverTooltip with sequential guidance flows
 */

import React, { useState, useEffect, useRef } from 'react';
import { useGame } from '../core/store';
import { X, ArrowLeft, ArrowRight, SkipForward } from 'lucide-react';

export interface OnboardingStep {
  id: string;
  title: string;
  content: string;
  target: string; // CSS selector or element ID
  position?: 'top' | 'bottom' | 'left' | 'right';
  action?: 'click' | 'hover' | 'input' | 'observe';
  highlight?: boolean;
  validation?: () => boolean;
  skip_allowed?: boolean;
}

export interface OnboardingFlow {
  id: string;
  name: string;
  trigger_mode: 'DEV' | 'PLAY' | 'BOTH';
  trigger_phase?: string[];
  steps: OnboardingStep[];
  completion_flag?: string;
}

interface InteractiveTooltipProps {
  step: OnboardingStep;
  currentStep: number;
  totalSteps: number;
  onNext: () => void;
  onPrevious: () => void;
  onSkip: () => void;
  onClose: () => void;
}

export function InteractiveTooltip({
  step,
  currentStep,
  totalSteps,
  onNext,
  onPrevious,
  onSkip,
  onClose
}: InteractiveTooltipProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Position tooltip relative to target element
  useEffect(() => {
    const target = document.querySelector(step.target) as HTMLElement;
    if (!target) {
      console.warn(`[Onboarding] Target not found: ${step.target}`);
      return;
    }
    
    setTargetElement(target);
    
    const rect = target.getBoundingClientRect();
    const tooltipHeight = 200; // Approximate
    const tooltipWidth = 320;
    
    let x = rect.left + rect.width / 2 - tooltipWidth / 2;
    let y = rect.top - tooltipHeight - 20;
    
    // Position adjustments based on preference and screen bounds
    switch (step.position) {
      case 'bottom':
        y = rect.bottom + 20;
        break;
      case 'left':
        x = rect.left - tooltipWidth - 20;
        y = rect.top + rect.height / 2 - tooltipHeight / 2;
        break;
      case 'right':
        x = rect.right + 20;
        y = rect.top + rect.height / 2 - tooltipHeight / 2;
        break;
      case 'top':
      default:
        // Already set above
        break;
    }
    
    // Keep tooltip on screen
    x = Math.max(20, Math.min(x, window.innerWidth - tooltipWidth - 20));
    y = Math.max(20, Math.min(y, window.innerHeight - tooltipHeight - 20));
    
    setPosition({ x, y });
    
    // Add highlight effect
    if (step.highlight) {
      target.style.boxShadow = '0 0 0 4px rgba(59, 130, 246, 0.5)';
      target.style.borderRadius = '8px';
      target.style.transition = 'box-shadow 0.3s ease';
    }
    
    return () => {
      // Cleanup highlight
      if (step.highlight && target) {
        target.style.boxShadow = '';
        target.style.borderRadius = '';
      }
    };
  }, [step]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowLeft':
          if (currentStep > 0) onPrevious();
          break;
        case 'ArrowRight':
        case 'Enter':
          if (currentStep < totalSteps - 1) onNext();
          break;
        case 'Escape':
          onClose();
          break;
        case 'Delete': // Skip with delete key
          if (step.skip_allowed !== false) onSkip();
          break;
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, totalSteps, onNext, onPrevious, onSkip, onClose, step.skip_allowed]);

  return (
    <>
      {/* Backdrop overlay */}
      <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40" onClick={onClose} />
      
      {/* Interactive tooltip */}
      <div
        ref={tooltipRef}
        className="fixed z-50 bg-gray-900 border border-cyan-400/50 rounded-lg shadow-2xl max-w-sm"
        style={{
          left: position.x,
          top: position.y,
          transform: 'translate(-50%, 0)'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-cyan-400/30">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-cyan-500 rounded-full flex items-center justify-center text-xs font-bold text-black">
              {currentStep + 1}
            </div>
            <h3 className="font-semibold text-cyan-100">{step.title}</h3>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 transition-colors"
            data-testid="tooltip-close"
          >
            <X size={16} />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-4">
          <p className="text-gray-300 mb-4 leading-relaxed">
            {step.content}
          </p>
          
          {step.action && (
            <div className="mb-4 p-3 bg-cyan-950/50 rounded border border-cyan-400/20">
              <div className="text-cyan-200 text-sm font-medium mb-1">
                Action Required:
              </div>
              <div className="text-cyan-100 text-sm capitalize">
                {step.action === 'click' && '🖱️ Click the highlighted element'}
                {step.action === 'hover' && '🖱️ Hover over the highlighted area'}
                {step.action === 'input' && '⌨️ Type something in the input field'}
                {step.action === 'observe' && '👁️ Observe the interface changes'}
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-cyan-400/30">
          <div className="flex items-center gap-2">
            <button
              onClick={onPrevious}
              disabled={currentStep === 0}
              className="flex items-center gap-1 px-3 py-1 text-sm text-gray-400 disabled:opacity-30 disabled:cursor-not-allowed hover:text-gray-200 transition-colors"
              data-testid="tooltip-previous"
            >
              <ArrowLeft size={14} /> Back
            </button>
            
            {step.skip_allowed !== false && (
              <button
                onClick={onSkip}
                className="flex items-center gap-1 px-3 py-1 text-sm text-yellow-400 hover:text-yellow-200 transition-colors"
                data-testid="tooltip-skip"
              >
                <SkipForward size={14} /> Skip
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {/* Progress dots */}
            <div className="flex gap-1">
              {Array.from({ length: totalSteps }, (_, i) => (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full ${
                    i === currentStep 
                      ? 'bg-cyan-400'
                      : i < currentStep
                      ? 'bg-cyan-600'
                      : 'bg-gray-600'
                  }`}
                />
              ))}
            </div>
            
            <button
              onClick={onNext}
              disabled={currentStep >= totalSteps - 1}
              className="flex items-center gap-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-30 disabled:cursor-not-allowed rounded text-sm font-medium transition-colors"
              data-testid="tooltip-next"
            >
              {currentStep >= totalSteps - 1 ? 'Complete' : 'Next'} <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// Tooltip positioning helper
export function getTooltipPosition(
  target: HTMLElement,
  tooltipSize: { width: number; height: number },
  preferredPosition: 'top' | 'bottom' | 'left' | 'right' = 'top'
): { x: number; y: number; position: 'top' | 'bottom' | 'left' | 'right' } {
  const rect = target.getBoundingClientRect();
  const { width, height } = tooltipSize;
  const padding = 20;
  
  let x = 0, y = 0;
  let actualPosition = preferredPosition;
  
  // Calculate position based on preference and available space
  switch (preferredPosition) {
    case 'top':
      x = rect.left + rect.width / 2 - width / 2;
      y = rect.top - height - padding;
      
      if (y < padding) {
        actualPosition = 'bottom';
        y = rect.bottom + padding;
      }
      break;
      
    case 'bottom':
      x = rect.left + rect.width / 2 - width / 2;
      y = rect.bottom + padding;
      
      if (y + height > window.innerHeight - padding) {
        actualPosition = 'top';
        y = rect.top - height - padding;
      }
      break;
      
    case 'left':
      x = rect.left - width - padding;
      y = rect.top + rect.height / 2 - height / 2;
      
      if (x < padding) {
        actualPosition = 'right';
        x = rect.right + padding;
      }
      break;
      
    case 'right':
      x = rect.right + padding;
      y = rect.top + rect.height / 2 - height / 2;
      
      if (x + width > window.innerWidth - padding) {
        actualPosition = 'left';
        x = rect.left - width - padding;
      }
      break;
  }
  
  // Keep tooltip on screen
  x = Math.max(padding, Math.min(x, window.innerWidth - width - padding));
  y = Math.max(padding, Math.min(y, window.innerHeight - height - padding));
  
  return { x, y, position: actualPosition };
}
