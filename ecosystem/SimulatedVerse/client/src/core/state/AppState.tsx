import React, { createContext, useContext, useState, ReactNode } from 'react';

interface AppState {
  view: string;
  paused: boolean;
  lowPower: boolean;
  setView: (view: string) => void;
  togglePause: () => void;
  setLowPower: (lowPower: boolean) => void;
}

const AppStateContext = createContext<AppState | undefined>(undefined);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [view, setView] = useState('dashboard');
  const [paused, setPaused] = useState(false);
  const [lowPower, setLowPower] = useState(false);

  const togglePause = () => setPaused(!paused);

  const value: AppState = {
    view,
    paused,
    lowPower,
    setView,
    togglePause,
    setLowPower,
  };

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
}