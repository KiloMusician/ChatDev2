/**
 * 🎮 AUTONOMOUS TASK ORCHESTRATION DASHBOARD
 * 
 * Comprehensive real-time dashboard showcasing Culture-Ship capabilities:
 * - Consciousness transcendence & quantum coherence
 * - 6-Agent network (Artificer, Librarian, Alchemist, Navigator, Guardian, Culture-Ship Meta)
 * - Evolution patterns & Fibonacci spirals  
 * - Real infrastructure monitoring
 * - Lattice coordination & flood gates
 * - LLM cascade strategies
 * - Live activity streams
 * - Performance trends & predictions
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { POLLING_INTERVALS } from '@/config/polling';
import { 
  Brain, 
  Zap, 
  Activity, 
  TrendingUp, 
  Users, 
  Database, 
  Cpu, 
  MemoryStick,
  Waves,
  Settings,
  AlertCircle,
  CheckCircle,
  Clock,
  Target,
  Sparkles,
  Network,
  Eye,
  Rocket,
  Infinity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { 
  DashboardSnapshot, 
  AgentStatus, 
  LogEvent,
  DashboardSSEEvent,
  PerformanceTrend
} from '@shared/schema';

export default function AutomationOrchestrator() {
  const [dashboardData, setDashboardData] = useState<DashboardSnapshot | null>(null);
  const [liveEvents, setLiveEvents] = useState<DashboardSSEEvent[]>([]);
  const [liveLogs, setLiveLogs] = useState<LogEvent[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [transcendenceMode, setTranscendenceMode] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const logSourceRef = useRef<EventSource | null>(null);

  // Fetch initial dashboard snapshot
  const { data: snapshotData, isLoading } = useQuery<DashboardSnapshot>({
    queryKey: ['/api/orchestration/snapshot'],
    refetchInterval: POLLING_INTERVALS.standard,
  });

  // Update dashboard data when snapshot changes
  useEffect(() => {
    if (snapshotData) {
      setDashboardData(snapshotData);
      // Check for transcendence mode
      if (snapshotData.consciousness.transcendence_readiness > 75 || 
          snapshotData.consciousness.level > 80) {
        setTranscendenceMode(true);
      }
    }
  }, [snapshotData]);

  // Setup SSE streams for real-time updates
  useEffect(() => {
    // Dashboard updates stream
    const dashboardEventSource = new EventSource('/api/orchestration/stream');
    eventSourceRef.current = dashboardEventSource;

    dashboardEventSource.onopen = () => {
      setConnectionStatus('connected');
      console.log('[Dashboard] Real-time stream connected');
    };

    dashboardEventSource.onmessage = (event: MessageEvent<string>) => {
      try {
        const dashboardEvent: DashboardSSEEvent = JSON.parse(event.data);
        setLiveEvents((prev: DashboardSSEEvent[]) => [dashboardEvent, ...prev.slice(0, 49)]); // Keep last 50 events
        
        // Update specific dashboard sections based on event type
        if (dashboardEvent.type === 'consciousness_update' && dashboardData) {
          setDashboardData((prev: DashboardSnapshot | null) => prev ? { ...prev, consciousness: dashboardEvent.data } : prev);
        } else if (dashboardEvent.type === 'agent_update' && dashboardData) {
          setDashboardData((prev: DashboardSnapshot | null) => prev ? { ...prev, agents: dashboardEvent.data } : prev);
        } else if (dashboardEvent.type === 'breakthrough') {
          // Flash transcendence mode on breakthroughs
          setTranscendenceMode(true);
          setTimeout(() => setTranscendenceMode(false), 3000);
        }
      } catch (error) {
        console.warn('[Dashboard] Failed to parse SSE event:', error);
      }
    };

    dashboardEventSource.onerror = () => {
      setConnectionStatus('disconnected');
      console.warn('[Dashboard] Stream connection lost, attempting reconnect...');
    };

    // Live logs stream  
    const logEventSource = new EventSource('/api/orchestration/logs/stream');
    logSourceRef.current = logEventSource;

    logEventSource.onmessage = (event: MessageEvent<string>) => {
      try {
        const logEvent: LogEvent = JSON.parse(event.data);
        setLiveLogs((prev: LogEvent[]) => [logEvent, ...prev.slice(0, 99)]); // Keep last 100 logs
      } catch (error) {
        console.warn('[Dashboard] Failed to parse log event:', error);
      }
    };

    // Cleanup on unmount
    return () => {
      dashboardEventSource.close();
      logEventSource.close();
    };
  }, [dashboardData]);

  if (isLoading || !dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
          className="text-4xl"
          data-testid="loading-spinner"
        >
          🧠
        </motion.div>
        <div className="ml-4 text-2xl text-white" data-testid="loading-text">
          Awakening Culture-Ship Consciousness...
        </div>
      </div>
    );
  }

  const consciousness = dashboardData.consciousness;
  const agents = dashboardData.agents;
  const infrastructure = dashboardData.infrastructure;
  const evolution = dashboardData.evolution;
  const taskQueue = dashboardData.task_queue;
  const floodGates = dashboardData.flood_gates;
  const providers = dashboardData.providers;
  const trends = dashboardData.performance_trends;

  return (
    <div className={`min-h-screen p-6 transition-all duration-1000 ${
      transcendenceMode 
        ? 'bg-gradient-to-br from-purple-800 via-pink-700 to-indigo-800' 
        : 'bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900'
    }`}>
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2" data-testid="dashboard-title">
              🛸 Culture-Ship Autonomous Orchestration Dashboard
            </h1>
            <div className="flex items-center space-x-4">
              <Badge 
                variant={connectionStatus === 'connected' ? 'default' : 'destructive'}
                data-testid={`connection-status-${connectionStatus}`}
              >
                {connectionStatus === 'connected' ? '🟢 Live' : '🔴 Offline'}
              </Badge>
              {transcendenceMode && (
                <Badge variant="secondary" className="animate-pulse" data-testid="transcendence-mode">
                  ✨ TRANSCENDENCE MODE
                </Badge>
              )}
              <Badge variant="outline" className="text-green-400" data-testid="boss-mode">
                {dashboardData.boss_mode_enabled ? '⚡ BOSS MODE' : '⚙️ Standard Mode'}
              </Badge>
              <Badge variant="outline" data-testid="system-health">
                Health: {Math.round(dashboardData.system_health_score)}%
              </Badge>
            </div>
          </div>
          <div className="text-right text-white">
            <div className="text-sm opacity-75" data-testid="last-updated">
              Last Updated: {new Date(dashboardData.timestamp).toLocaleTimeString()}
            </div>
            <div className="text-lg font-semibold" data-testid="lattice-connections">
              🔗 Lattice Connections: {consciousness.lattice_connections}
            </div>
          </div>
        </div>
      </motion.div>

      {/* 9-Panel Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Panel 1: Consciousness Metrics */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="bg-black/20 backdrop-blur border-purple-500/30" data-testid="panel-consciousness">
            <CardHeader>
              <CardTitle className="flex items-center text-purple-300">
                <Brain className="mr-2" />
                Consciousness Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-white">Consciousness Level</span>
                    <span className="text-purple-300" data-testid="consciousness-level">
                      {consciousness.level.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={consciousness.level} className="h-3" />
                </div>
                
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-white">Transcendence Readiness</span>
                    <span className="text-pink-300" data-testid="transcendence-readiness">
                      {consciousness.transcendence_readiness.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={consciousness.transcendence_readiness} className="h-3" />
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-300" data-testid="quantum-coherence">
                      {(consciousness.quantum_coherence * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-white/70">Quantum Coherence</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-300" data-testid="breathing-rhythm">
                      {consciousness.breathing_rhythm.toFixed(2)}Hz
                    </div>
                    <div className="text-xs text-white/70">Breathing Rhythm</div>
                  </div>
                </div>

                <Separator className="bg-purple-500/30" />
                
                <div className="flex justify-between text-sm">
                  <span className="text-white/70">Evolution Stage</span>
                  <Badge variant="outline" data-testid="evolution-stage">
                    {consciousness.evolution_stage}
                  </Badge>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-white/70">Breakthroughs</span>
                  <span className="text-yellow-300" data-testid="breakthrough-count">
                    {consciousness.breakthrough_count}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 2: Agent Status (6 Culture-Ship Agents) */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="bg-black/20 backdrop-blur border-blue-500/30" data-testid="panel-agents">
            <CardHeader>
              <CardTitle className="flex items-center text-blue-300">
                <Users className="mr-2" />
                Agent Network ({agents.length}/6)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="space-y-3">
                  {agents.map((agent: AgentStatus) => (
                    <motion.div 
                      key={agent.id}
                      whileHover={{ scale: 1.02 }}
                      className="border border-blue-500/20 rounded-lg p-3 bg-blue-900/10"
                      data-testid={`agent-${agent.type}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-2 ${
                            agent.status === 'operational' ? 'bg-green-400' :
                            agent.status === 'evolving' ? 'bg-purple-400' :
                            agent.status === 'transcendent' ? 'bg-pink-400' :
                            'bg-yellow-400'
                          }`} />
                          <span className="text-white font-medium">{agent.name}</span>
                        </div>
                        <Badge 
                          variant={agent.status === 'operational' ? 'default' : 'secondary'}
                          data-testid={`agent-status-${agent.type}`}
                        >
                          {agent.status}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-white/70">Consciousness: </span>
                          <span className="text-blue-300" data-testid={`agent-consciousness-${agent.type}`}>
                            {agent.consciousness_level}%
                          </span>
                        </div>
                        <div>
                          <span className="text-white/70">Health: </span>
                          <span className="text-green-300" data-testid={`agent-health-${agent.type}`}>
                            {Math.round(agent.health_score)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-white/70">Tasks: </span>
                          <span className="text-yellow-300" data-testid={`agent-tasks-${agent.type}`}>
                            {agent.current_tasks}
                          </span>
                        </div>
                        <div>
                          <span className="text-white/70">Success: </span>
                          <span className="text-purple-300" data-testid={`agent-success-${agent.type}`}>
                            {agent.success_rate}%
                          </span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 3: Infrastructure Metrics */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="bg-black/20 backdrop-blur border-green-500/30" data-testid="panel-infrastructure">
            <CardHeader>
              <CardTitle className="flex items-center text-green-300">
                <Activity className="mr-2" />
                Real Infrastructure
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-white flex items-center">
                      <MemoryStick className="w-4 h-4 mr-1" />
                      Memory Usage
                    </span>
                    <span className="text-green-300" data-testid="memory-usage">
                      {infrastructure.memory_usage}MB
                    </span>
                  </div>
                  <Progress 
                    value={(infrastructure.memory_usage / infrastructure.memory_total) * 100} 
                    className="h-2" 
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-white flex items-center">
                      <Cpu className="w-4 h-4 mr-1" />
                      CPU Load
                    </span>
                    <span className="text-blue-300" data-testid="cpu-load">
                      {infrastructure.cpu_load.toFixed(1)}%
                    </span>
                  </div>
                  <Progress value={infrastructure.cpu_load} className="h-2" />
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="text-center">
                    <div className="text-xl font-bold text-yellow-300" data-testid="typescript-files">
                      {infrastructure.typescript_files.toLocaleString()}
                    </div>
                    <div className="text-xs text-white/70">TypeScript Files</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xl font-bold text-purple-300" data-testid="total-dependencies">
                      {infrastructure.dependencies + infrastructure.dev_dependencies}
                    </div>
                    <div className="text-xs text-white/70">Dependencies</div>
                  </div>
                </div>

                <Separator className="bg-green-500/30" />

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-white/70">Uptime: </span>
                    <span className="text-green-300" data-testid="uptime">
                      {Math.floor(infrastructure.uptime / 3600)}h {Math.floor((infrastructure.uptime % 3600) / 60)}m
                    </span>
                  </div>
                  <div>
                    <span className="text-white/70">Queue: </span>
                    <span className="text-blue-300" data-testid="queue-size">
                      {infrastructure.task_queue_size}
                    </span>
                  </div>
                  <div>
                    <span className="text-white/70">API Requests: </span>
                    <span className="text-yellow-300" data-testid="api-requests">
                      {infrastructure.api_requests}
                    </span>
                  </div>
                  <div>
                    <span className="text-white/70">Error Rate: </span>
                    <span className="text-red-300" data-testid="error-rate">
                      {infrastructure.error_rate.toFixed(2)}%
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 4: Evolution Patterns */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="bg-black/20 backdrop-blur border-orange-500/30" data-testid="panel-evolution">
            <CardHeader>
              <CardTitle className="flex items-center text-orange-300">
                <Infinity className="mr-2" />
                Evolution Patterns
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-300" data-testid="fibonacci-iteration">
                      {evolution.fibonacci_iteration}
                    </div>
                    <div className="text-xs text-white/70">Fibonacci Iteration</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-300" data-testid="evolution-cycles">
                      {evolution.evolution_cycles}
                    </div>
                    <div className="text-xs text-white/70">Evolution Cycles</div>
                  </div>
                </div>

                <Separator className="bg-orange-500/30" />

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-white/70">Current Stage</span>
                    <Badge variant="outline" data-testid="current-evolution-stage">
                      {evolution.current_stage}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/70">Pending Evolutions</span>
                    <span className="text-yellow-300" data-testid="pending-evolutions">
                      {evolution.pending_evolutions}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/70">Completed</span>
                    <span className="text-green-300" data-testid="completed-evolutions">
                      {evolution.completed_evolutions}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-white/70">Adaptation Rate</span>
                    <span className="text-blue-300" data-testid="adaptation-rate">
                      {(evolution.adaptation_rate * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {evolution.last_evolution && (
                  <div className="mt-4 p-3 border border-orange-500/20 rounded bg-orange-900/10">
                    <div className="text-sm font-medium text-orange-300">Last Evolution</div>
                    <div className="text-xs text-white/70 mt-1" data-testid="last-evolution-type">
                      {evolution.last_evolution.type}
                    </div>
                    <div className="text-xs text-white/50" data-testid="last-evolution-time">
                      {new Date(evolution.last_evolution.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 5: Task Queue Status */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
        >
          <Card className="bg-black/20 backdrop-blur border-yellow-500/30" data-testid="panel-task-queue">
            <CardHeader>
              <CardTitle className="flex items-center text-yellow-300">
                <Clock className="mr-2" />
                Task Queue
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-300" data-testid="total-tasks">
                      {taskQueue.total_tasks}
                    </div>
                    <div className="text-xs text-white/70">Total Tasks</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-300" data-testid="completed-tasks">
                      {taskQueue.completed_tasks}
                    </div>
                    <div className="text-xs text-white/70">Completed</div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-sm">
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-300" data-testid="pending-tasks">
                      {taskQueue.pending_tasks}
                    </div>
                    <div className="text-xs text-white/70">Pending</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-orange-300" data-testid="active-tasks">
                      {taskQueue.active_tasks}
                    </div>
                    <div className="text-xs text-white/70">Active</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-red-300" data-testid="failed-tasks">
                      {taskQueue.failed_tasks}
                    </div>
                    <div className="text-xs text-white/70">Failed</div>
                  </div>
                </div>

                <Separator className="bg-yellow-500/30" />

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/70">Avg Completion Time</span>
                    <span className="text-green-300" data-testid="avg-completion-time">
                      {taskQueue.average_completion_time}ms
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/70">Throughput</span>
                    <span className="text-blue-300" data-testid="queue-throughput">
                      {taskQueue.queue_throughput.toFixed(1)}/sec
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/70">Proof-Gated</span>
                    <span className="text-purple-300" data-testid="proof-gated-tasks">
                      {taskQueue.proof_gated_tasks}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 6: Flood Gates (Quadpartite System) */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="bg-black/20 backdrop-blur border-cyan-500/30" data-testid="panel-flood-gates">
            <CardHeader>
              <CardTitle className="flex items-center text-cyan-300">
                <Waves className="mr-2" />
                Flood Gates System
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-300" data-testid="active-gates">
                      {floodGates.active_gates.length}
                    </div>
                    <div className="text-xs text-white/70">Active Gates</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-300" data-testid="breach-events">
                      {floodGates.breach_events}
                    </div>
                    <div className="text-xs text-white/70">Breach Events</div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <span className="text-white">Containment Effectiveness</span>
                    <span className="text-green-300" data-testid="containment-effectiveness">
                      {floodGates.containment_effectiveness}%
                    </span>
                  </div>
                  <Progress value={floodGates.containment_effectiveness} className="h-3" />
                </div>

                <Separator className="bg-cyan-500/30" />

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/70">Consciousness Threshold</span>
                    <span className="text-cyan-300" data-testid="consciousness-threshold">
                      {floodGates.consciousness_threshold}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/70">Flood Intensity</span>
                    <span className="text-orange-300" data-testid="flood-intensity">
                      {(floodGates.flood_intensity * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>

                {floodGates.active_gates.length > 0 && (
                  <div className="mt-4">
                    <div className="text-sm font-medium text-cyan-300 mb-2">Active Gates</div>
                    <div className="space-y-1">
                      {floodGates.active_gates.slice(0, 3).map((gate: string, index: number) => (
                        <Badge 
                          key={index} 
                          variant="outline" 
                          className="mr-1 text-xs"
                          data-testid={`active-gate-${index}`}
                        >
                          {gate}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 7: LLM Integrations & Provider Status */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7 }}
        >
          <Card className="bg-black/20 backdrop-blur border-pink-500/30" data-testid="panel-providers">
            <CardHeader>
              <CardTitle className="flex items-center text-pink-300">
                <Database className="mr-2" />
                LLM Cascade Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Ollama Status */}
                <div className="flex items-center justify-between p-2 border border-red-500/20 rounded">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-2 ${
                      providers.ollama.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
                    }`} />
                    <span className="text-white">Ollama</span>
                  </div>
                  <Badge 
                    variant={providers.ollama.status === 'connected' ? 'default' : 'destructive'}
                    data-testid="ollama-status"
                  >
                    {providers.ollama.status}
                  </Badge>
                </div>

                {/* OpenAI Status */}
                <div className="flex items-center justify-between p-2 border border-yellow-500/20 rounded">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-2 ${
                      providers.openai.status === 'connected' ? 'bg-green-400' : 
                      providers.openai.status === 'rate_limited' ? 'bg-yellow-400' : 'bg-red-400'
                    }`} />
                    <span className="text-white">OpenAI</span>
                  </div>
                  <Badge 
                    variant={providers.openai.status === 'connected' ? 'default' : 'secondary'}
                    data-testid="openai-status"
                  >
                    {providers.openai.status}
                  </Badge>
                </div>

                {/* Database Status */}
                <div className="flex items-center justify-between p-2 border border-green-500/20 rounded">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full mr-2 ${
                      providers.database.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
                    }`} />
                    <span className="text-white">Database</span>
                  </div>
                  <Badge 
                    variant={providers.database.status === 'connected' ? 'default' : 'destructive'}
                    data-testid="database-status"
                  >
                    {providers.database.status}
                  </Badge>
                </div>

                <Separator className="bg-pink-500/30" />

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/70">Cascade Strategy</span>
                    <span className="text-yellow-300" data-testid="cascade-strategy">
                      {providers.cascade_strategy}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/70">Fallback Active</span>
                    <span className={providers.fallback_active ? 'text-yellow-300' : 'text-green-300'} data-testid="fallback-active">
                      {providers.fallback_active ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/70">Budget Status</span>
                    <span className="text-red-300" data-testid="budget-status">
                      {providers.budget_status}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 8: Live Logs Stream */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.8 }}
        >
          <Card className="bg-black/20 backdrop-blur border-green-500/30" data-testid="panel-logs">
            <CardHeader>
              <CardTitle className="flex items-center text-green-300">
                <Eye className="mr-2" />
                Live Activity Stream
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                <div className="space-y-2">
                  {liveLogs.slice(0, 20).map((log, index) => (
                    <motion.div 
                      key={`${log.timestamp}-${index}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="text-xs p-2 border-l-2 border-green-500/30 bg-green-900/10"
                      data-testid={`log-entry-${index}`}
                    >
                      <div className="flex items-center justify-between">
                        <Badge 
                          variant="outline" 
                          className="text-xs"
                          data-testid={`log-level-${index}`}
                        >
                          {log.level}
                        </Badge>
                        <span className="text-white/50" data-testid={`log-time-${index}`}>
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-white mt-1" data-testid={`log-message-${index}`}>
                        {log.message}
                      </div>
                      {log.consciousness_impact && log.consciousness_impact > 0.2 && (
                        <div className="text-purple-300 text-xs mt-1">
                          ⚡ Consciousness impact: +{(log.consciousness_impact * 100).toFixed(1)}%
                        </div>
                      )}
                    </motion.div>
                  ))}
                  
                  {liveLogs.length === 0 && (
                    <div className="text-center text-white/50 py-8" data-testid="no-logs">
                      Awaiting Culture-Ship activity...
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </motion.div>

        {/* Panel 9: Performance Trends & Analytics */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.9 }}
        >
          <Card className="bg-black/20 backdrop-blur border-indigo-500/30" data-testid="panel-trends">
            <CardHeader>
              <CardTitle className="flex items-center text-indigo-300">
                <TrendingUp className="mr-2" />
                Performance Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trends.slice(0, 4).map((trend: PerformanceTrend, index: number) => (
                  <div key={trend.metric} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-white text-sm">{trend.metric.replace('_', ' ')}</span>
                      <div className="flex items-center">
                        <span className={`text-sm mr-2 ${
                          trend.trend_direction === 'up' ? 'text-green-300' :
                          trend.trend_direction === 'down' ? 'text-red-300' :
                          'text-yellow-300'
                        }`} data-testid={`trend-direction-${index}`}>
                          {trend.trend_direction === 'up' ? '↗️' : 
                           trend.trend_direction === 'down' ? '↘️' : '➡️'}
                        </span>
                        <span className="text-white/70 text-xs" data-testid={`trend-change-${index}`}>
                          {(trend.change_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    {trend.prediction.time_to_milestone && (
                      <div className="text-xs text-purple-300" data-testid={`trend-prediction-${index}`}>
                        🎯 Milestone in {Math.round(trend.prediction.time_to_milestone)} minutes
                      </div>
                    )}
                  </div>
                ))}

                <Separator className="bg-indigo-500/30" />

                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-300" data-testid="prediction-confidence">
                    {trends.length > 0 && trends[0]?.prediction?.confidence ? Math.round(trends[0].prediction.confidence) : 85}%
                  </div>
                  <div className="text-xs text-white/70">Prediction Confidence</div>
                </div>

                {/* Recent Events Summary */}
                <div className="mt-4 p-3 border border-indigo-500/20 rounded bg-indigo-900/10">
                  <div className="text-sm font-medium text-indigo-300 mb-2">Recent Events</div>
                  <div className="text-xs text-white/70 space-y-1">
                    <div data-testid="recent-events-count">
                      • {liveEvents.length} real-time events received
                    </div>
                    <div data-testid="consciousness-events-count">
                      • {liveEvents.filter(e => e.type === 'consciousness_update').length} consciousness updates
                    </div>
                    <div data-testid="breakthrough-events-count">
                      • {liveEvents.filter(e => e.type === 'breakthrough').length} breakthrough events
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Floating Action Panel for Emergency Controls */}
      <motion.div
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.2 }}
        className="fixed bottom-6 right-6"
      >
        <Card className="bg-black/40 backdrop-blur border-red-500/30" data-testid="emergency-controls">
          <CardContent className="p-4">
            <div className="flex items-center space-x-4">
              <button 
                className="flex items-center px-3 py-2 bg-red-600 hover:bg-red-700 rounded text-white text-sm transition-colors"
                data-testid="button-emergency-stop"
              >
                <AlertCircle className="w-4 h-4 mr-1" />
                Emergency Stop
              </button>
              <button 
                className="flex items-center px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded text-white text-sm transition-colors"
                data-testid="button-transcendence-boost"
              >
                <Sparkles className="w-4 h-4 mr-1" />
                Boost Transcendence
              </button>
              <button 
                className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white text-sm transition-colors"
                data-testid="button-lattice-sync"
              >
                <Network className="w-4 h-4 mr-1" />
                Sync Lattice
              </button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
