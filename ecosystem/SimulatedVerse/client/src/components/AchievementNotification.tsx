import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Star, X } from 'lucide-react';
import { achievementService, type Achievement } from '@/services/achievementService';

export function AchievementNotification() {
  const [notifications, setNotifications] = useState<Achievement[]>([]);
  
  useEffect(() => {
    const unsubscribe = achievementService.onAchievementUnlocked((achievement) => {
      setNotifications(prev => [...prev, achievement]);
      
      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        dismissNotification(achievement.id);
      }, 5000);
    });
    
    return unsubscribe;
  }, []);
  
  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };
  
  return (
    <div className="fixed top-20 right-4 z-50 space-y-2">
      <AnimatePresence>
        {notifications.map((achievement) => (
          <motion.div
            key={achievement.id}
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            transition={{ type: 'spring', damping: 20 }}
            className="bg-gradient-to-r from-yellow-600 to-orange-600 rounded-lg shadow-2xl p-4 min-w-[300px] border border-yellow-400/50"
            data-testid="achievement-notification"
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center animate-pulse">
                  <Trophy className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-white font-bold text-sm mb-1">
                  Achievement Unlocked!
                </h3>
                <p className="text-yellow-100 font-semibold">
                  {achievement.name}
                </p>
                <p className="text-yellow-200 text-xs mt-1">
                  {achievement.description}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Star className="w-3 h-3 text-yellow-300" />
                  <span className="text-yellow-300 text-xs font-semibold">
                    +{achievement.points} points
                  </span>
                </div>
              </div>
              <button
                onClick={() => dismissNotification(achievement.id)}
                className="text-yellow-300 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            
            {achievement.reward && (
              <div className="mt-3 pt-3 border-t border-yellow-500/30">
                <p className="text-yellow-200 text-xs font-semibold mb-1">Rewards:</p>
                {achievement.reward.resources && (
                  <div className="text-yellow-300 text-xs">
                    {Object.entries(achievement.reward.resources).map(([key, value]) => (
                      <span key={key} className="mr-2">
                        +{value} {key}
                      </span>
                    ))}
                  </div>
                )}
                {achievement.reward.unlocks && (
                  <div className="text-yellow-300 text-xs">
                    Unlocked: {achievement.reward.unlocks.join(', ')}
                  </div>
                )}
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}