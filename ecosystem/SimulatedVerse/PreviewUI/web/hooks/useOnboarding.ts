/**
 * useOnboarding Hook
 * React hook for managing interactive onboarding flows
 */

import { useState, useEffect } from 'react';
import { onboardingService, OnboardingState } from '@ui/web/services/OnboardingService';
import { OnboardingFlow, OnboardingStep } from '@ui/web/components/InteractiveTooltip';
import { useGame } from '@ui/web/core/store';

export function useOnboarding() {
  const [onboardingState, setOnboardingState] = useState<OnboardingState>(onboardingService.getState());
  const game = useGame();

  // Subscribe to onboarding service changes
  useEffect(() => {
    const unsubscribe = onboardingService.subscribe(setOnboardingState);
    return unsubscribe;
  }, []);

  // Auto-trigger onboarding based on mode/phase changes
  useEffect(() => {
    // Check if onboarding should auto-trigger
    const suggestedFlow = onboardingService.checkAutoTrigger(game.mode, game.uiPhase);
    
    if (suggestedFlow && !onboardingState.active_flow) {
      console.log(`[Onboarding] Auto-triggering: ${suggestedFlow}`);
      onboardingService.startFlow(suggestedFlow, game);
    }
  }, [game.mode, game.uiPhase, onboardingState.active_flow]);

  const actions = {
    startFlow: (flowId: string) => {
      return onboardingService.startFlow(flowId, game);
    },

    nextStep: () => {
      return onboardingService.nextStep();
    },

    previousStep: () => {
      return onboardingService.previousStep();
    },

    skipStep: () => {
      onboardingService.skipCurrentStep();
    },

    closeFlow: () => {
      onboardingService.closeFlow();
    },

    completeFlow: () => {
      const flow = onboardingService.getCurrentFlow();
      if (flow?.completion_flag) {
        // Set completion flag in game state
        game.setFlag(flow.completion_flag as any, true);
      }
      onboardingService.completeCurrentFlow();
    },

    // Manual controls for dev/testing
    resetFlow: (flowId: string) => {
      onboardingService.resetFlow(flowId);
    },

    resetAll: () => {
      onboardingService.resetAllOnboarding();
    },

    addCustomFlow: (flow: OnboardingFlow) => {
      onboardingService.addCustomFlow(flow);
    }
  };

  const derived = {
    isActive: onboardingState.active_flow !== null,
    currentFlow: onboardingService.getCurrentFlow(),
    currentStep: onboardingService.getCurrentStep(),
    currentStepIndex: onboardingState.current_step,
    totalSteps: onboardingService.getCurrentFlow()?.steps.length || 0,
    availableFlows: onboardingService.getAvailableFlows(game.mode, game.uiPhase),
    completionStats: onboardingService.getCompletionStats(),
    stepValid: onboardingService.validateCurrentStep()
  };

  return {
    ...onboardingState,
    ...actions,
    ...derived
  };
}

// Lightweight hook for checking onboarding availability
export function useOnboardingAvailable() {
  const game = useGame();
  
  return {
    hasAvailableFlows: onboardingService.getAvailableFlows(game.mode, game.uiPhase).length > 0,
    isActive: onboardingService.isActive(),
    autoTriggerSuggestion: onboardingService.checkAutoTrigger(game.mode, game.uiPhase)
  };
}
