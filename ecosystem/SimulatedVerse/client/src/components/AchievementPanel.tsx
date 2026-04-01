import React, { useState, useEffect } from 'react';
import { Trophy, Lock, Star, Clock, Users, Brain, Target } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { achievementService, type Achievement } from '@/services/achievementService';

const categoryIcons = {
  progression: <Target className="w-4 h-4" />,
  discovery: <Brain className="w-4 h-4" />,
  social: <Users className="w-4 h-4" />,
  mastery: <Star className="w-4 h-4" />,
  time: <Clock className="w-4 h-4" />
};

const categoryColors = {
  progression: 'from-green-500/20 to-emerald-500/20',
  discovery: 'from-purple-500/20 to-indigo-500/20',
  social: 'from-blue-500/20 to-cyan-500/20',
  mastery: 'from-yellow-500/20 to-orange-500/20',
  time: 'from-gray-500/20 to-slate-500/20'
};

export function AchievementPanel() {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Achievement['category'] | 'all'>('all');
  
  useEffect(() => {
    const loadAchievements = async () => {
      const playerId = localStorage.getItem('playerId') || 'default-player';
      await achievementService.loadPlayerAchievements(playerId);
      setAchievements(achievementService.getAchievements());
    };
    
    loadAchievements();
    
    // Listen for new achievements
    const unsubscribe = achievementService.onAchievementUnlocked((achievement) => {
      setAchievements([...achievementService.getAchievements()]);
    });
    
    return unsubscribe;
  }, []);
  
  const filteredAchievements = selectedCategory === 'all' 
    ? achievements 
    : achievements.filter(a => a.category === selectedCategory);
  
  const unlockedCount = achievementService.getUnlockedCount();
  const totalPoints = achievementService.getTotalPoints();
  const progress = achievementService.getProgress();
  
  const AchievementCard = ({ achievement }: { achievement: Achievement }) => {
    const isUnlocked = achievement.unlocked;
    const isHidden = achievement.hidden && !isUnlocked;
    
    return (
      <Card 
        className={`relative overflow-hidden transition-all ${
          isUnlocked 
            ? 'bg-gradient-to-br ' + categoryColors[achievement.category] + ' border-yellow-500/50' 
            : 'bg-gray-800/50 border-gray-700/50 opacity-75'
        }`}
        data-testid={`achievement-${achievement.code.toLowerCase()}`}
      >
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className={`text-2xl ${isUnlocked ? '' : 'grayscale opacity-50'}`}>
              {isHidden ? '❓' : achievement.icon || <Trophy className="w-6 h-6" />}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-sm mb-1">
                {isHidden ? '???' : achievement.name}
              </h3>
              <p className="text-xs text-gray-400 mb-2">
                {isHidden ? 'Hidden achievement' : achievement.description}
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {categoryIcons[achievement.category]}
                  <span className="text-xs capitalize">{achievement.category}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Star className="w-3 h-3 text-yellow-500" />
                  <span className="text-xs font-semibold">{achievement.points}</span>
                </div>
              </div>
              {achievement.progress !== undefined && !isUnlocked && (
                <div className="mt-2">
                  <Progress value={achievement.progress} className="h-1" />
                  <p className="text-xs text-gray-500 mt-1">
                    {achievement.progress}% Complete
                  </p>
                </div>
              )}
              {isUnlocked && achievement.unlockedAt && (
                <p className="text-xs text-green-400 mt-2">
                  Unlocked: {new Date(achievement.unlockedAt).toLocaleDateString()}
                </p>
              )}
            </div>
            {isUnlocked && (
              <div className="absolute top-2 right-2">
                <Trophy className="w-4 h-4 text-yellow-500" />
              </div>
            )}
            {!isUnlocked && !isHidden && (
              <div className="absolute top-2 right-2">
                <Lock className="w-4 h-4 text-gray-500" />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };
  
  return (
    <div className="space-y-6">
      {/* Stats Header */}
      <Card className="bg-gradient-to-r from-purple-900/20 to-blue-900/20 border-purple-500/30">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-yellow-500" />
              Achievements
            </span>
            <span className="text-sm font-normal">
              {unlockedCount} / {achievements.length} Unlocked
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Overall Progress</span>
                <span>{progress.toFixed(1)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-yellow-500">{unlockedCount}</p>
                <p className="text-xs text-gray-400">Achievements</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-purple-500">{totalPoints}</p>
                <p className="text-xs text-gray-400">Total Points</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-500">{progress.toFixed(0)}%</p>
                <p className="text-xs text-gray-400">Completion</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={(v) => setSelectedCategory(v as any)}>
        <TabsList className="grid grid-cols-6 w-full">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="progression">Progression</TabsTrigger>
          <TabsTrigger value="discovery">Discovery</TabsTrigger>
          <TabsTrigger value="social">Social</TabsTrigger>
          <TabsTrigger value="mastery">Mastery</TabsTrigger>
          <TabsTrigger value="time">Time</TabsTrigger>
        </TabsList>
        
        <TabsContent value={selectedCategory} className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredAchievements.map((achievement) => (
              <AchievementCard key={achievement.id} achievement={achievement} />
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}