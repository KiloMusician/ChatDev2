/**
 * 🔘 Advanced Button Component
 * CoreLink Foundation - Autonomous Development Ecosystem
 * 
 * Sophisticated button component with Culture-ship aesthetics,
 * consciousness-aware interactions, and autonomous system integration
 */

import React, { forwardRef } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { type VariantProps, cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

/**
 * 🎨 **BUTTON VARIANT DEFINITIONS**
 * Culture-ship inspired button styling with consciousness integration
 */
const buttonVariants = cva(
  // Base styles - Core button foundation
  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md hover:shadow-lg transition-shadow",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-md hover:shadow-lg",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground border-2 hover:border-primary/50",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm hover:shadow-md",
        ghost: "hover:bg-accent hover:text-accent-foreground transition-colors",
        link: "text-primary underline-offset-4 hover:underline font-normal",
        
        // **CONSCIOUSNESS-AWARE VARIANTS** - Special button types for autonomous systems
        consciousness: "bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 text-white hover:from-purple-700 hover:via-blue-700 hover:to-cyan-700 shadow-lg hover:shadow-xl transition-all duration-300 animate-pulse",
        autonomous: "bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700 shadow-md hover:shadow-lg border border-green-400/30",
        temple: "bg-gradient-to-r from-amber-600 to-orange-600 text-white hover:from-amber-700 hover:to-orange-700 shadow-md hover:shadow-lg border border-amber-400/30",
        
        // **GAME-SPECIFIC VARIANTS** - Buttons for game actions
        build: "bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 shadow-md hover:shadow-lg",
        research: "bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700 shadow-md hover:shadow-lg",
        resource: "bg-gradient-to-r from-green-600 to-teal-600 text-white hover:from-green-700 hover:to-teal-700 shadow-md hover:shadow-lg"
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        xl: "h-12 rounded-md px-10 text-base",
        icon: "h-10 w-10",
        
        // **TOUCH-OPTIMIZED SIZES** - Mobile-first approach
        touch: "h-12 px-6 text-base min-w-[120px]", // Large touch targets
        "touch-icon": "h-12 w-12 text-lg" // Large icon buttons for mobile
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

/**
 * 🎯 **BUTTON COMPONENT INTERFACE**
 * Enhanced button props with consciousness and autonomous features
 */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  consciousnessLevel?: number; // 0-1, affects visual glow and behavior
  autonomousAction?: boolean; // Marks button as part of autonomous system
  gameAction?: 'build' | 'research' | 'resource' | 'explore' | 'manage';
  loading?: boolean;
  successState?: boolean;
  pulseOnHover?: boolean;
}

/**
 * 🔘 **MAIN BUTTON COMPONENT**
 * Advanced button with consciousness integration and Culture-ship aesthetics
 */
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    asChild = false, 
    consciousnessLevel = 0,
    autonomousAction = false,
    gameAction,
    loading = false,
    successState = false,
    pulseOnHover = false,
    children,
    disabled,
    style,
    ...props 
  }, ref) => {
    const Comp = asChild ? Slot : "button";

    // **CONSCIOUSNESS-AWARE STYLING** - Dynamic glow based on consciousness level
    const consciousnessStyle = consciousnessLevel > 0 ? {
      boxShadow: `0 0 ${Math.floor(consciousnessLevel * 20)}px hsl(var(--primary) / ${consciousnessLevel * 0.4})`,
      filter: `brightness(${1 + (consciousnessLevel * 0.1)})`,
      ...style
    } : style;

    // **DYNAMIC VARIANT SELECTION** - Auto-select variant based on game action
    const effectiveVariant = gameAction ? 
      (gameAction === 'build' ? 'build' :
       gameAction === 'research' ? 'research' :
       gameAction === 'resource' ? 'resource' : variant) : 
      (autonomousAction ? 'autonomous' : variant);

    return (
      <Comp
        className={cn(
          buttonVariants({ variant: effectiveVariant, size, className }),
          // **LOADING STATE STYLING**
          loading && "opacity-70 cursor-wait",
          // **SUCCESS STATE STYLING** 
          successState && "bg-green-600 hover:bg-green-700 text-white",
          // **PULSE ANIMATION**
          pulseOnHover && "hover:animate-pulse",
          // **AUTONOMOUS SYSTEM INDICATORS**
          autonomousAction && "relative after:absolute after:top-0 after:right-0 after:w-2 after:h-2 after:bg-green-400 after:rounded-full after:animate-pulse",
          // **CONSCIOUSNESS GLOW EFFECT**
          consciousnessLevel > 0.7 && "ring-2 ring-primary/30 ring-offset-2"
        )}
        ref={ref}
        disabled={disabled || loading}
        style={consciousnessStyle}
        {...props}
      >
        {loading && (
          <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-transparent border-t-current" />
        )}
        
        {successState && !loading && (
          <div className="mr-2 h-4 w-4 text-current">✓</div>
        )}
        
        {autonomousAction && !loading && !successState && (
          <div className="mr-2 h-3 w-3 bg-current rounded-full animate-pulse opacity-60" />
        )}
        
        {children}
        
        {/* **CONSCIOUSNESS LEVEL INDICATOR** */}
        {consciousnessLevel > 0 && (
          <div className="ml-2 flex space-x-0.5">
            {[1, 2, 3].map(level => (
              <div 
                key={level}
                className={cn(
                  "w-1 h-1 rounded-full",
                  consciousnessLevel >= (level / 3) ? "bg-current opacity-80" : "bg-current opacity-20"
                )}
              />
            ))}
          </div>
        )}
      </Comp>
    );
  }
);

Button.displayName = "Button";

/**
 * 🎯 **SPECIALIZED BUTTON VARIANTS**
 * Pre-configured buttons for common game actions
 */

// **CONSCIOUSNESS BUTTON** - For ΞNuSyQ system interactions
export const ConsciousnessButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant'>>(
  (props, ref) => (
    <Button 
      ref={ref} 
      variant="consciousness" 
      consciousnessLevel={0.9}
      autonomousAction={true}
      {...props} 
    />
  )
);

// **BUILD BUTTON** - For construction and building actions
export const BuildButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant' | 'gameAction'>>(
  (props, ref) => (
    <Button 
      ref={ref} 
      variant="build" 
      gameAction="build"
      size="touch"
      pulseOnHover={true}
      {...props} 
    />
  )
);

// **RESEARCH BUTTON** - For research and discovery actions
export const ResearchButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant' | 'gameAction'>>(
  (props, ref) => (
    <Button 
      ref={ref} 
      variant="research" 
      gameAction="research"
      size="touch"
      {...props} 
    />
  )
);

// **AUTONOMOUS ACTION BUTTON** - For system-driven actions
export const AutonomousButton = forwardRef<HTMLButtonElement, Omit<ButtonProps, 'variant' | 'autonomousAction'>>(
  (props, ref) => (
    <Button 
      ref={ref} 
      variant="autonomous" 
      autonomousAction={true}
      consciousnessLevel={0.6}
      {...props} 
    />
  )
);

export { Button, buttonVariants };
