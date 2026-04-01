// Hover Tooltip Component - QoL Tier-1 unlock
import React from 'react';

interface TooltipProps {
  title: string;
  description: string;
  price?: number;
  currency?: string;
  affordable?: boolean;
  eta?: string;
  status: 'available' | 'locked' | 'coming_soon';
  children: React.ReactNode;
  className?: string;
}

export function HoverTooltip({ 
  title, 
  description, 
  price, 
  currency = 'energy',
  affordable = false,
  eta,
  status,
  children,
  className = ''
}: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false);
  const [position, setPosition] = React.useState({ x: 0, y: 0 });

  const handleMouseEnter = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPosition({ 
      x: rect.left + rect.width / 2, 
      y: rect.top - 10 
    });
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  const getStatusColor = () => {
    switch (status) {
      case 'available': return 'border-green-500 bg-green-50';
      case 'coming_soon': return 'border-yellow-500 bg-yellow-50';
      case 'locked': return 'border-red-500 bg-red-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'available': return '✅';
      case 'coming_soon': return '⏳';
      case 'locked': return '🔒';
      default: return '❓';
    }
  };

  return (
    <div className="relative inline-block">
      <div
        className={`cursor-help ${className}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </div>
      
      {isVisible && (
        <div
          className={`absolute z-50 px-3 py-2 text-sm rounded-lg border-2 shadow-lg max-w-xs ${getStatusColor()}`}
          style={{
            left: position.x - 150, // Center tooltip
            top: position.y - 80,
            transform: 'translateY(-100%)'
          }}
        >
          {/* Tooltip content */}
          <div className="font-semibold text-gray-800 mb-1">
            {getStatusIcon()} {title}
          </div>
          
          <div className="text-gray-600 text-xs mb-2">
            {description}
          </div>
          
          {price !== undefined && (
            <div className="text-sm">
              <span className={affordable ? 'text-green-600' : 'text-red-600'}>
                Cost: {price} {currency}
              </span>
              {!affordable && eta && (
                <div className="text-blue-600 text-xs mt-1">
                  Ready in: {eta}
                </div>
              )}
            </div>
          )}
          
          {/* Tooltip arrow */}
          <div 
            className={`absolute w-3 h-3 transform rotate-45 border-r-2 border-b-2 ${getStatusColor().split(' ')[0]} ${getStatusColor().split(' ')[1]}`}
            style={{
              left: '50%',
              bottom: '-6px',
              marginLeft: '-6px'
            }}
          />
        </div>
      )}
    </div>
  );
}

// Hook for using ETA system
export function useHoverETA() {
  const [etas, setEtas] = React.useState<any[]>([]);
  const [unlocked, setUnlocked] = React.useState(false);

  React.useEffect(() => {
    // In real implementation, this would connect to the game state
    // For now, simulate the nanobots unlock after 3 seconds
    const timer = setTimeout(() => {
      setUnlocked(true);
      setEtas([
        {
          item_id: 'generator_upgrade',
          title: 'Generator Upgrade',
          description: 'Increase energy generation by 2x',
          current_price: 150,
          currency: 'energy',
          affordable: false,
          eta_display: '2m 30s',
          status: 'coming_soon'
        },
        {
          item_id: 'nanobots',
          title: 'Nanobots',
          description: 'Unlock hover tooltips and ETA predictions',
          current_price: 500,
          currency: 'energy',
          affordable: true,
          status: 'available'
        }
      ]);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  return { etas, unlocked };
}