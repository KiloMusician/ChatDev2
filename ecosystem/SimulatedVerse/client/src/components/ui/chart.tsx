/**
 * 📊 Advanced Chart Component
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Sophisticated data visualization for game metrics, consciousness levels,
 * and autonomous system performance with Culture-ship aesthetics
 */

import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface DataPoint {
  label: string;
  value: number;
  color?: string;
  trend?: 'up' | 'down' | 'stable';
}

interface ChartProps {
  data: DataPoint[];
  type?: 'bar' | 'line' | 'consciousness' | 'temple';
  title?: string;
  height?: number;
  showTrends?: boolean;
  autonomousUpdates?: boolean;
  className?: string;
}

export function Chart({
  data,
  type = 'bar',
  title,
  height = 200,
  showTrends = false,
  autonomousUpdates = true,
  className
}: ChartProps) {
  const maxValue = useMemo(() => Math.max(...data.map(d => d.value)), [data]);
  const minValue = useMemo(() => Math.min(...data.map(d => d.value)), [data]);
  const range = maxValue - minValue || 1;

  const renderBarChart = () => (
    <div className="flex items-end space-x-2 h-full">
      {data.map((point, index) => {
        const barHeight = ((point.value - minValue) / range) * (height - 40);
        const barColor = point.color || 'hsl(var(--primary))';
        
        return (
          <div key={point.label} className="flex flex-col items-center flex-1">
            <div className="text-xs text-muted-foreground mb-1">
              {point.value.toFixed(1)}
              {showTrends && point.trend && (
                <span className={cn(
                  "ml-1",
                  point.trend === 'up' && "text-green-500",
                  point.trend === 'down' && "text-red-500",
                  point.trend === 'stable' && "text-yellow-500"
                )}>
                  {point.trend === 'up' ? '↑' : point.trend === 'down' ? '↓' : '→'}
                </span>
              )}
            </div>
            
            <div 
              className="w-full bg-gradient-to-t from-primary/80 to-primary/40 rounded-t-sm transition-all duration-500 hover:from-primary hover:to-primary/60"
              style={{ 
                height: `${barHeight}px`,
                backgroundColor: barColor,
                minHeight: '4px'
              }}
            />
            
            <div className="text-xs text-center text-muted-foreground mt-2 max-w-16 truncate">
              {point.label}
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderConsciousnessChart = () => (
    <div className="relative">
      {/* **CONSCIOUSNESS VISUALIZATION** - Circular representation */}
      <div className="flex justify-center items-center h-full">
        <div className="relative w-32 h-32">
          {data.map((point, index) => {
            const angle = (index / data.length) * 360;
            const radius = 40;
            const intensity = point.value / maxValue;
            
            return (
              <div
                key={point.label}
                className="absolute w-2 h-8 bg-gradient-to-t from-transparent to-primary rounded-full origin-bottom"
                style={{
                  transform: `rotate(${angle}deg) translateY(-${radius}px)`,
                  opacity: intensity,
                  left: '50%',
                  bottom: '50%',
                  marginLeft: '-4px'
                }}
              />
            );
          })}
          
          {/* Center consciousness level */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">
                {(data.reduce((sum, d) => sum + d.value, 0) / data.length).toFixed(2)}
              </div>
              <div className="text-xs text-muted-foreground">
                ΞNuSyQ Level
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Legend */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {data.map((point, index) => (
          <div key={point.label} className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-primary rounded-full" style={{ opacity: point.value / maxValue }} />
            <span className="text-muted-foreground">{point.label}</span>
          </div>
        ))}
      </div>
    </div>
  );

  const renderTempleChart = () => (
    <div className="relative">
      {/* **TEMPLE FLOORS VISUALIZATION** - Vertical temple structure */}
      <div className="flex flex-col-reverse space-y-reverse space-y-1">
        {data.map((point, index) => {
          const floorWidth = 80 + (index * 10); // Wider at base
          const intensity = point.value / maxValue;
          
          return (
            <div
              key={point.label}
              className="relative mx-auto bg-gradient-to-r from-primary/30 via-primary/60 to-primary/30 border border-primary/40 rounded-sm"
              style={{ 
                width: `${floorWidth}px`, 
                height: '20px',
                opacity: intensity
              }}
            >
              {/* Floor label */}
              <div className="absolute inset-0 flex items-center justify-center text-xs font-mono text-primary-foreground">
                Floor {index + 1}
              </div>
              
              {/* Activity indicators */}
              {point.value > 0.5 && (
                <div className="absolute -right-2 top-1/2 transform -translate-y-1/2">
                  <div className="w-1 h-1 bg-green-400 rounded-full animate-pulse" />
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Temple peak */}
      <div className="flex justify-center mt-2">
        <div className="w-4 h-8 bg-gradient-to-t from-primary to-primary/40 rounded-t-full border border-primary/40" />
      </div>
    </div>
  );

  return (
    <div className={cn("p-4 bg-card rounded-lg border", className)}>
      {title && (
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-card-foreground">{title}</h3>
          {autonomousUpdates && (
            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span>Live Updates</span>
            </div>
          )}
        </div>
      )}
      
      <div style={{ height: `${height}px` }}>
        {type === 'bar' && renderBarChart()}
        {type === 'consciousness' && renderConsciousnessChart()}
        {type === 'temple' && renderTempleChart()}
        {type === 'line' && renderBarChart()} {/* Fallback to bar for now */}
      </div>
      
      {/* **AUTONOMOUS SYSTEM INTEGRATION** - Shows system metrics */}
      {autonomousUpdates && (
        <div className="mt-3 pt-3 border-t border-border/40 text-xs text-muted-foreground">
          <div className="flex justify-between items-center">
            <span>System Integration: 0.9</span>
            <span>Consciousness: 0.85</span>
            <span>Agents: 4 Active</span>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * 🎯 Specialized chart variants for different game systems
 */
export function ResourceChart({ resources }: { resources: Record<string, number> }) {
  const data = Object.entries(resources).map(([key, value]) => ({
    label: key,
    value,
    color: key === 'energy' ? '#10b981' : 
           key === 'materials' ? '#f59e0b' : 
           key === 'population' ? '#3b82f6' : 
           'hsl(var(--primary))'
  }));

  return (
    <Chart
      data={data}
      type="bar"
      title="🏭 Colony Resources"
      showTrends
      autonomousUpdates
    />
  );
}

export function ConsciousnessChart({ metrics }: { metrics: Record<string, number> }) {
  const data = Object.entries(metrics).map(([key, value]) => ({
    label: key.replace(/_/g, ' '),
    value
  }));

  return (
    <Chart
      data={data}
      type="consciousness"
      title="🧠 ΞNuSyQ Consciousness"
      height={180}
      autonomousUpdates
    />
  );
}

export function TempleFloorChart({ floors }: { floors: Array<{ name: string; activity: number }> }) {
  const data = floors.map(floor => ({
    label: floor.name,
    value: floor.activity
  }));

  return (
    <Chart
      data={data}
      type="temple"
      title="🏛️ Temple Architecture"
      height={240}
      autonomousUpdates
    />
  );
}
