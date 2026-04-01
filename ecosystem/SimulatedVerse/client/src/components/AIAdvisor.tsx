import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Brain, Zap, TrendingUp, AlertCircle, ChevronRight } from 'lucide-react';
import { POLLING_INTERVALS } from '@/config/polling';

interface AIDecision {
  action: string;
  priority: number;
  reasoning: string;
  requirements: { [key: string]: number };
  expectedBenefit: number;
}

interface AIRecommendResponse {
  bestAction?: AIDecision;
  recommendations?: AIDecision[];
  analytics?: {
    decisionCount?: number;
    gamePhase?: string;
    learningProgress?: number;
  };
}

interface AIAdvisorProps {
  colonyState: any;
  onExecuteAction: (action: string) => void;
}

export function AIAdvisor({ colonyState, onExecuteAction }: AIAdvisorProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [autoMode, setAutoMode] = useState(false);
  
  // Fetch AI recommendations
  const { data: aiData, refetch } = useQuery<AIRecommendResponse>({
    queryKey: ['/api/ai/recommend', colonyState],
    queryFn: async () => {
      const response = await fetch(`/api/ai/recommend?state=${encodeURIComponent(JSON.stringify(colonyState))}`);
      return response.json() as Promise<AIRecommendResponse>;
    },
    enabled: !!colonyState,
    refetchInterval: autoMode ? POLLING_INTERVALS.standard : false
  });
  
  // Execute AI decision
  const executeMutation = useMutation({
    mutationFn: async (decision: AIDecision) => {
      const response = await fetch('/api/ai/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, colonyState })
      });
      return response.json();
    },
    onSuccess: (data, variables) => {
      onExecuteAction(variables.action);
    }
  });
  
  const bestAction = aiData?.bestAction;

  // Auto-execute in auto mode
  useEffect(() => {
    if (autoMode && bestAction && !executeMutation.isPending) {
      const canAfford = Object.entries(bestAction.requirements).every(
        ([resource, required]) => (colonyState.resources[resource] || 0) >= required
      );
      
      if (canAfford) {
        executeMutation.mutate(bestAction);
      }
    }
  }, [autoMode, bestAction, colonyState, executeMutation]);
  
  const getPriorityColor = (priority: number) => {
    if (priority >= 8) return 'text-red-400';
    if (priority >= 5) return 'text-yellow-400';
    return 'text-green-400';
  };
  
  const canAfford = (requirements: { [key: string]: number }) => {
    return Object.entries(requirements).every(
      ([resource, required]) => (colonyState.resources[resource] || 0) >= required
    );
  };
  
  return (
    <div className="bg-gradient-to-br from-purple-900/20 to-blue-900/20 rounded-lg p-4 border border-purple-500/30">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-bold text-purple-300">AI Advisor</h3>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-purple-400 hover:text-purple-300"
          >
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
          
          <button
            onClick={() => setAutoMode(!autoMode)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              autoMode 
                ? 'bg-purple-600 text-white' 
                : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
          >
            {autoMode ? 'AUTO' : 'MANUAL'}
          </button>
        </div>
      </div>
      
      {bestAction && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4"
        >
          <div className="bg-black/30 rounded p-3 border border-purple-500/20">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Zap className={`w-4 h-4 ${getPriorityColor(bestAction.priority)}`} />
                  <span className="font-medium text-white">
                    {bestAction.action.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className={`text-xs ${getPriorityColor(bestAction.priority)}`}>
                    Priority: {bestAction.priority}
                  </span>
                </div>
                
                <p className="text-sm text-gray-400 mb-2">
                  {bestAction.reasoning}
                </p>
                
                {Object.keys(bestAction.requirements).length > 0 && (
                  <div className="flex gap-3 text-xs">
                    {Object.entries(bestAction.requirements).map(([resource, amount]) => (
                      <span key={resource} className={canAfford({ [resource]: amount }) ? 'text-green-400' : 'text-red-400'}>
                        {resource}: {amount}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              <button
                onClick={() => executeMutation.mutate(bestAction)}
                disabled={!canAfford(bestAction.requirements) || executeMutation.isPending}
                className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                  canAfford(bestAction.requirements)
                    ? 'bg-purple-600 hover:bg-purple-500 text-white'
                    : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                }`}
              >
                {executeMutation.isPending ? 'Executing...' : 'Execute'}
              </button>
            </div>
          </div>
        </motion.div>
      )}
      
      <AnimatePresence>
        {showDetails && aiData?.recommendations && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <div className="text-sm text-purple-400 mb-2">Alternative Actions:</div>
            
            {aiData.recommendations.map((rec: AIDecision, index: number) => (
              <div key={index} className="bg-black/20 rounded p-2 text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ChevronRight className="w-3 h-3 text-purple-400" />
                    <span className="text-gray-300">
                      {rec.action.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    Benefit: +{rec.expectedBenefit}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1 ml-5">
                  {rec.reasoning}
                </p>
              </div>
            ))}
            
            {aiData.analytics && (
              <div className="mt-3 pt-3 border-t border-purple-500/20">
                <div className="text-xs text-purple-400 mb-1">AI Analytics:</div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-gray-500">Decisions Made:</span>
                    <span className="ml-1 text-gray-300">{aiData.analytics.decisionCount ?? 0}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Game Phase:</span>
                    <span className="ml-1 text-gray-300">{aiData.analytics.gamePhase ?? 'Unknown'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Learning Progress:</span>
                    <span className="ml-1 text-gray-300">
                      {aiData.analytics.learningProgress?.toFixed(1) ?? '0.0'}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
      
      {autoMode && (
        <motion.div
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="mt-3 flex items-center gap-2 text-xs text-purple-400"
        >
          <AlertCircle className="w-3 h-3" />
          <span>AI Auto-Mode Active - Making decisions every 5 seconds</span>
        </motion.div>
      )}
    </div>
  );
}
