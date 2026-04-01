/**
 * OnboardingProvider
 * Renders interactive onboarding tooltips when active
 */

import React from 'react';
import { useOnboarding } from '../hooks/useOnboarding';
import { InteractiveTooltip } from './InteractiveTooltip';

export function OnboardingProvider({ children }: { children: React.ReactNode }) {
  const onboarding = useOnboarding();

  return (
    <>
      {children}
      
      {/* Render active onboarding tooltip */}
      {onboarding.isActive && onboarding.currentStep && (
        <InteractiveTooltip
          step={onboarding.currentStep}
          currentStep={onboarding.currentStepIndex}
          totalSteps={onboarding.totalSteps}
          onNext={onboarding.nextStep}
          onPrevious={onboarding.previousStep}
          onSkip={onboarding.skipStep}
          onClose={onboarding.closeFlow}
        />
      )}
    </>
  );
}

// Onboarding trigger button for manual activation
interface OnboardingTriggerProps {
  flowId?: string;
  children: React.ReactNode;
  className?: string;
}

export function OnboardingTrigger({ 
  flowId, 
  children, 
  className = '' 
}: OnboardingTriggerProps) {
  const onboarding = useOnboarding();
  
  const handleTrigger = () => {
    if (flowId) {
      onboarding.startFlow(flowId);
    } else {
      // Auto-detect best flow
      const available = onboarding.availableFlows;
      if (available.length > 0) {
        onboarding.startFlow(available[0].id);
      }
    }
  };
  
  return (
    <button
      onClick={handleTrigger}
      className={`onboarding-trigger ${className}`}
      data-testid="onboarding-trigger"
      title="Start guided tour"
    >
      {children}
    </button>
  );
}

// Quick onboarding status display
export function OnboardingStatus() {
  const onboarding = useOnboarding();
  const stats = onboarding.completionStats;
  
  if (!onboarding.hasAvailableFlows && stats.completed === 0) {
    return null;
  }
  
  return (
    <div className="text-xs text-gray-500 p-2 border border-gray-700 rounded">
      <div className="flex items-center justify-between mb-1">
        <span>Onboarding</span>
        <span>{stats.completed}/{stats.total_flows}</span>
      </div>
      
      <div className="w-full bg-gray-800 rounded-full h-1.5">
        <div 
          className="bg-cyan-500 h-1.5 rounded-full transition-all duration-300"
          style={{ width: `${stats.completion_rate * 100}%` }}
        />
      </div>
      
      {onboarding.isActive && (
        <div className="mt-1 text-cyan-400 text-xs">
          Active: {onboarding.currentFlow?.name}
        </div>
      )}
    </div>
  );
}
