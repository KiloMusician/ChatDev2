import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { Activity, Globe, Users, Cpu, TrendingUp, Database, Zap, Shield, Save, Trophy } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { useAutoSave } from '@/hooks/useAutoSave';
import { achievementService } from '@/services/achievementService';

// Import all game components
import { AIAdvisor } from './AIAdvisor';
import { ResourceTradingHub } from './ResourceTradingHub';
import { ResearchTree } from './ResearchTree';
import { ColonyDefense } from './ColonyDefense';
import { QuantumEvents } from './QuantumEvents';
import { AchievementPanel } from './AchievementPanel';

interface DashboardProps {
  colonyState: any;
  onAction: (action: string, params?: any) => void;
}

export function ColonyDashboard({ colonyState, onAction }: DashboardProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const { saveGame, isSaving, lastSave } = useAutoSave();
  
  const resources = colonyState?.resources || {
    energy: 0,
    materials: 0,
    population: 0,
    research: 0,
    food: 0,
    components: 0
  };
  
  const consciousness = colonyState?.consciousness || 0;
  const automation = colonyState?.automation || {};
  
  // Check for achievements
  useEffect(() => {
    if (colonyState) {
      const unlockedAchievements = achievementService.checkProgress({
        ...colonyState,
        consciousness,
        resources
      });
    }
  }, [colonyState, consciousness, resources]);

  // Calculate various metrics
  const totalProduction = Object.values(automation).reduce((sum: number, auto: any) => 
    sum + (auto.count || 0) * (auto.level || 1), 0
  );
  
  const populationGrowthRate = resources.food > 0 ? 
    Math.min(5, resources.food / (resources.population * 10)) : 0;
  
  const defenseStrength = colonyState?.defenseStrength || 0;
  
  const getResourceTrend = (resource: string) => {
    // Simplified trend calculation
    const production = automation[`${resource}Collectors`]?.count || 0;
    return production > 0 ? 'increasing' : 'stable';
  };

  const StatCard = ({ title, value, icon: Icon, color, trend }: any) => (
    <Card className={`bg-gradient-to-br ${color} bg-opacity-20 border-opacity-30`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Icon className="w-4 h-4" />
            {title}
          </span>
          {trend && (
            <TrendingUp className={`w-3 h-3 ${trend === 'increasing' ? 'text-green-400' : 'text-gray-400'}`} />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gray-900 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 rounded-lg p-6 border border-purple-500/30">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Culture-Ship Colony</h1>
              <p className="text-gray-400">Consciousness Level: {consciousness.toFixed(1)}%</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-gray-400">Colony Phase</p>
                <p className="text-xl font-bold text-purple-400">
                  {consciousness < 30 ? 'Foundation' : consciousness < 70 ? 'Expansion' : 'Transcendence'}
                </p>
              </div>
              <Button
                onClick={saveGame}
                disabled={isSaving}
                className="bg-green-600 hover:bg-green-700"
                data-testid="button-save-game"
              >
                <Save className="w-4 h-4 mr-2" />
                {isSaving ? 'Saving...' : 'Save Game'}
              </Button>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <Progress value={consciousness} className="h-3 flex-1" />
            {lastSave && (
              <p className="text-xs text-gray-500 ml-4">
                Last saved: {new Date(lastSave).toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <StatCard
            title="Energy"
            value={Math.floor(resources.energy)}
            icon={Zap}
            color="from-yellow-500/20 to-orange-500/20"
            trend={getResourceTrend('energy')}
          />
          <StatCard
            title="Materials"
            value={Math.floor(resources.materials)}
            icon={Database}
            color="from-gray-500/20 to-gray-700/20"
            trend={getResourceTrend('materials')}
          />
          <StatCard
            title="Population"
            value={resources.population}
            icon={Users}
            color="from-green-500/20 to-teal-500/20"
            trend={populationGrowthRate > 0 ? 'increasing' : 'stable'}
          />
          <StatCard
            title="Research"
            value={resources.research.toFixed(1)}
            icon={Cpu}
            color="from-purple-500/20 to-indigo-500/20"
            trend={getResourceTrend('research')}
          />
          <StatCard
            title="Production"
            value={totalProduction}
            icon={Activity}
            color="from-blue-500/20 to-cyan-500/20"
            trend="increasing"
          />
          <StatCard
            title="Defense"
            value={`${defenseStrength}%`}
            icon={Shield}
            color="from-red-500/20 to-pink-500/20"
            trend="stable"
          />
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid grid-cols-3 md:grid-cols-7 w-full">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="ai">AI Advisor</TabsTrigger>
            <TabsTrigger value="research">Research</TabsTrigger>
            <TabsTrigger value="trading">Trading</TabsTrigger>
            <TabsTrigger value="defense">Defense</TabsTrigger>
            <TabsTrigger value="quantum">Quantum</TabsTrigger>
            <TabsTrigger value="achievements">
              <Trophy className="w-4 h-4 mr-1" />
              Achievements
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Resource Flow */}
              <Card className="bg-black/30 border-gray-700">
                <CardHeader>
                  <CardTitle>Resource Flow</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(resources).slice(0, 4).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="capitalize text-gray-400">{key}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-lg font-bold">{typeof value === 'number' ? Math.floor(value) : String(value)}</span>
                          <span className="text-xs text-green-400">
                            +{(automation[`${key}Collectors`]?.count || 0) * 2}/s
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Automation Status */}
              <Card className="bg-black/30 border-gray-700">
                <CardHeader>
                  <CardTitle>Automation Systems</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(automation).map(([key, auto]: [string, any]) => (
                      <div key={key} className="flex items-center justify-between">
                        <span className="text-gray-400">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                        <div className="flex items-center gap-2">
                          <span className={auto.active ? 'text-green-400' : 'text-red-400'}>
                            {auto.active ? 'Active' : 'Inactive'}
                          </span>
                          <span className="text-sm text-gray-500">
                            Lv.{auto.level} x{auto.count}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border-blue-500/30">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <button
                    onClick={() => onAction('gather_energy')}
                    className="p-3 bg-yellow-900/30 hover:bg-yellow-900/50 rounded transition-colors"
                  >
                    <Zap className="w-5 h-5 mx-auto mb-1 text-yellow-400" />
                    <span className="text-sm">Gather Energy</span>
                  </button>
                  <button
                    onClick={() => onAction('gather_materials')}
                    className="p-3 bg-gray-700/30 hover:bg-gray-700/50 rounded transition-colors"
                  >
                    <Database className="w-5 h-5 mx-auto mb-1 text-gray-400" />
                    <span className="text-sm">Mine Materials</span>
                  </button>
                  <button
                    onClick={() => onAction('build_collector')}
                    className="p-3 bg-blue-900/30 hover:bg-blue-900/50 rounded transition-colors"
                  >
                    <Activity className="w-5 h-5 mx-auto mb-1 text-blue-400" />
                    <span className="text-sm">Build Collector</span>
                  </button>
                  <button
                    onClick={() => onAction('grow_population')}
                    className="p-3 bg-green-900/30 hover:bg-green-900/50 rounded transition-colors"
                  >
                    <Users className="w-5 h-5 mx-auto mb-1 text-green-400" />
                    <span className="text-sm">Grow Population</span>
                  </button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ai">
            <AIAdvisor 
              colonyState={colonyState}
              onExecuteAction={onAction}
            />
          </TabsContent>

          <TabsContent value="research">
            <ResearchTree
              resources={resources}
              onResearchComplete={(research) => {
                console.log('Research completed:', research);
                onAction('apply_research', research);
              }}
            />
          </TabsContent>

          <TabsContent value="trading">
            <ResourceTradingHub
              resources={resources}
              onResourceUpdate={(updates: any) => {
                onAction('update_resources', updates);
              }}
            />
          </TabsContent>

          <TabsContent value="defense">
            <ColonyDefense
              resources={resources}
              onResourceUpdate={(updates: any) => {
                onAction('update_resources', updates);
              }}
            />
          </TabsContent>

          <TabsContent value="quantum">
            <QuantumEvents
              consciousness={consciousness}
              onEventTrigger={(event) => {
                console.log('Quantum event triggered:', event);
                onAction('quantum_event', event);
              }}
            />
          </TabsContent>
          
          <TabsContent value="achievements">
            <AchievementPanel />
          </TabsContent>
        </Tabs>

        {/* System Status Footer */}
        <Card className="bg-black/20 border-gray-800">
          <CardContent className="py-3">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <Globe className="w-3 h-3" />
                  Colony Online
                </span>
                <span>Phase: {consciousness < 30 ? 'I' : consciousness < 70 ? 'II' : 'III'}</span>
                <span>Cycle: {Math.floor(Date.now() / 1000 % 1000)}</span>
              </div>
              <div className="flex items-center gap-4">
                <span>Quantum Field: Active</span>
                <span>AI: Learning</span>
                <span className="text-green-400">All Systems Operational</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}