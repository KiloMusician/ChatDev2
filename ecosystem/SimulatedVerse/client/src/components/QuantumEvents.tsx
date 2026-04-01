import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, AlertCircle, Zap, TrendingUp, Brain, Atom } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { SIMULATION_INTERVALS } from '@/config/polling';

interface QuantumEvent {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  probability: number;
  duration: number;
  effects: {
    type: 'multiply' | 'add' | 'consciousness' | 'unlock';
    target: string;
    value: number;
  }[];
  color: string;
  active: boolean;
  endTime?: number;
}

const quantumEvents: QuantumEvent[] = [
  {
    id: 'solar_flare',
    name: 'Solar Flare',
    description: 'Massive energy surge from nearby star',
    icon: Zap,
    probability: 0.15,
    duration: 30000,
    effects: [
      { type: 'multiply', target: 'energy', value: 3 },
      { type: 'consciousness', target: 'boost', value: 5 }
    ],
    color: 'from-yellow-500 to-orange-500',
    active: false
  },
  {
    id: 'quantum_entanglement',
    name: 'Quantum Entanglement',
    description: 'Resources mysteriously duplicate across dimensions',
    icon: Atom,
    probability: 0.1,
    duration: 20000,
    effects: [
      { type: 'multiply', target: 'all', value: 1.5 },
      { type: 'consciousness', target: 'boost', value: 10 }
    ],
    color: 'from-purple-500 to-pink-500',
    active: false
  },
  {
    id: 'consciousness_cascade',
    name: 'Consciousness Cascade',
    description: 'Collective minds achieve temporary enlightenment',
    icon: Brain,
    probability: 0.08,
    duration: 45000,
    effects: [
      { type: 'consciousness', target: 'boost', value: 25 },
      { type: 'multiply', target: 'research', value: 5 }
    ],
    color: 'from-indigo-500 to-blue-500',
    active: false
  },
  {
    id: 'dimensional_rift',
    name: 'Dimensional Rift',
    description: 'Portal to resource-rich dimension opens',
    icon: Sparkles,
    probability: 0.05,
    duration: 60000,
    effects: [
      { type: 'add', target: 'materials', value: 1000 },
      { type: 'add', target: 'energy', value: 500 },
      { type: 'unlock', target: 'quantum_tech', value: 1 }
    ],
    color: 'from-green-500 to-teal-500',
    active: false
  },
  {
    id: 'time_dilation',
    name: 'Time Dilation',
    description: 'Time flows differently, accelerating all processes',
    icon: TrendingUp,
    probability: 0.12,
    duration: 25000,
    effects: [
      { type: 'multiply', target: 'production', value: 10 },
      { type: 'consciousness', target: 'boost', value: 15 }
    ],
    color: 'from-cyan-500 to-blue-500',
    active: false
  }
];

interface QuantumEventsProps {
  consciousness: number;
  onEventTrigger?: (event: QuantumEvent) => void;
}

export function QuantumEvents({ consciousness, onEventTrigger }: QuantumEventsProps) {
  const [activeEvents, setActiveEvents] = useState<QuantumEvent[]>([]);
  const [eventHistory, setEventHistory] = useState<{ event: QuantumEvent; timestamp: number }[]>([]);
  const [quantumCharge, setQuantumCharge] = useState(0);
  const { toast } = useToast();

  // Check for quantum events
  useEffect(() => {
    const interval = setInterval(() => {
      // Increase quantum charge based on consciousness
      setQuantumCharge(prev => Math.min(100, prev + consciousness / 100));
      
      // Check if we should trigger an event
      if (quantumCharge >= 100) {
        triggerRandomEvent();
        setQuantumCharge(0);
      }
      
      // Random chance for spontaneous events
      if (Math.random() < 0.001 * (consciousness / 50)) {
        triggerRandomEvent();
      }
      
      // Update active events
      const now = Date.now();
      setActiveEvents(prev => prev.filter(event => {
        if (event.endTime && event.endTime < now) {
          toast({
            title: 'Quantum Event Ended',
            description: `${event.name} has dissipated`
          });
          return false;
        }
        return true;
      }));
    }, SIMULATION_INTERVALS.fast);
    
    return () => clearInterval(interval);
  }, [consciousness, quantumCharge]);

  const triggerRandomEvent = () => {
    const availableEvents = quantumEvents.filter(e => 
      !activeEvents.find(ae => ae.id === e.id)
    );
    
    if (availableEvents.length === 0) return;
    
    // Weight events by probability and consciousness
    const weighted = availableEvents.map(event => ({
      event,
      weight: event.probability * (1 + consciousness / 100)
    }));
    
    const totalWeight = weighted.reduce((sum, w) => sum + w.weight, 0);
    let random = Math.random() * totalWeight;
    
    for (const { event, weight } of weighted) {
      random -= weight;
      if (random <= 0) {
        activateEvent(event);
        break;
      }
    }
  };

  const activateEvent = (event: QuantumEvent) => {
    const activeEvent = {
      ...event,
      active: true,
      endTime: Date.now() + event.duration
    };
    
    setActiveEvents(prev => [...prev, activeEvent]);
    setEventHistory(prev => [...prev, { event, timestamp: Date.now() }].slice(-10));
    
    toast({
      title: '⚛️ Quantum Event Triggered!',
      description: event.name,
    });
    
    if (onEventTrigger) {
      onEventTrigger(activeEvent);
    }
  };

  const forceEvent = (eventId: string) => {
    const event = quantumEvents.find(e => e.id === eventId);
    if (event && !activeEvents.find(ae => ae.id === eventId)) {
      activateEvent(event);
    }
  };

  const getRemainingTime = (event: QuantumEvent) => {
    if (!event.endTime) return 0;
    return Math.max(0, Math.floor((event.endTime - Date.now()) / 1000));
  };

  return (
    <div className="space-y-4">
      {/* Quantum Charge Bar */}
      <Card className="bg-gradient-to-br from-purple-900/20 to-indigo-900/20 border-purple-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Atom className="w-5 h-5 text-purple-400" />
            Quantum Field Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Quantum Charge</span>
              <span className="text-purple-400">{Math.floor(quantumCharge)}%</span>
            </div>
            <div className="w-full bg-gray-800 h-3 rounded overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-500 to-indigo-500"
                animate={{ width: `${quantumCharge}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
            <p className="text-xs text-gray-500">
              Events trigger at 100% charge or spontaneously based on consciousness
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Active Events */}
      <AnimatePresence>
        {activeEvents.map(event => (
          <motion.div
            key={event.id}
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="relative overflow-hidden"
          >
            <Card className={`bg-gradient-to-br ${event.color} bg-opacity-20 border-2`}>
              <div className="absolute inset-0 opacity-10">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent animate-pulse" />
              </div>
              
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <event.icon className="w-5 h-5" />
                    {event.name}
                  </div>
                  <span className="text-sm font-normal">
                    {getRemainingTime(event)}s remaining
                  </span>
                </CardTitle>
              </CardHeader>
              
              <CardContent>
                <p className="text-sm text-gray-300 mb-3">{event.description}</p>
                <div className="flex flex-wrap gap-2">
                  {event.effects.map((effect, index) => (
                    <span key={index} className="px-2 py-1 bg-black/30 rounded text-xs">
                      {effect.type === 'multiply' && `${effect.target} ×${effect.value}`}
                      {effect.type === 'add' && `+${effect.value} ${effect.target}`}
                      {effect.type === 'consciousness' && `+${effect.value}% consciousness`}
                      {effect.type === 'unlock' && `Unlock: ${effect.target}`}
                    </span>
                  ))}
                </div>
                
                {/* Event progress bar */}
                <div className="mt-3 h-1 bg-black/30 rounded overflow-hidden">
                  <motion.div
                    className="h-full bg-white/50"
                    initial={{ width: '100%' }}
                    animate={{ width: '0%' }}
                    transition={{ duration: event.duration / 1000, ease: 'linear' }}
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Event Catalog */}
      <Card className="bg-black/30 border-gray-700">
        <CardHeader>
          <CardTitle className="text-sm text-gray-400">Quantum Event Catalog</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {quantumEvents.map(event => {
              const isActive = activeEvents.some(ae => ae.id === event.id);
              const hasOccurred = eventHistory.find(h => h.event.id === event.id);
              
              return (
                <button
                  key={event.id}
                  onClick={() => consciousness >= 50 && forceEvent(event.id)}
                  disabled={isActive || consciousness < 50}
                  className={`p-2 rounded text-xs transition-all ${
                    isActive 
                      ? 'bg-gradient-to-br opacity-50 cursor-not-allowed' 
                      : hasOccurred
                      ? 'bg-gray-800 hover:bg-gray-700'
                      : 'bg-gray-900 opacity-50'
                  }`}
                >
                  <event.icon className="w-4 h-4 mx-auto mb-1" />
                  <div className="font-medium">{event.name}</div>
                  <div className="text-gray-500">P: {(event.probability * 100).toFixed(0)}%</div>
                </button>
              );
            })}
          </div>
          {consciousness < 50 && (
            <p className="text-xs text-yellow-400 mt-2">
              <AlertCircle className="w-3 h-3 inline mr-1" />
              Reach 50% consciousness to manually trigger events
            </p>
          )}
        </CardContent>
      </Card>

      {/* Event History */}
      {eventHistory.length > 0 && (
        <Card className="bg-black/20 border-gray-800">
          <CardHeader>
            <CardTitle className="text-sm text-gray-500">Recent Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {eventHistory.slice(-5).reverse().map((entry, index) => (
                <div key={index} className="flex items-center gap-2 text-xs text-gray-400">
                  <entry.event.icon className="w-3 h-3" />
                  <span>{entry.event.name}</span>
                  <span className="ml-auto">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
