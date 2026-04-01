import React, { createContext, useContext, useState } from "react";

interface TabsContextValue {
  value: string;
  onValueChange: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | undefined>(undefined);

export interface TabsProps {
  children: React.ReactNode;
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  className?: string;
}

export function Tabs({ children, value: controlledValue, defaultValue = "", onValueChange, className = "" }: TabsProps) {
  const [uncontrolledValue, setUncontrolledValue] = useState(defaultValue);
  
  const value = controlledValue !== undefined ? controlledValue : uncontrolledValue;
  const handleValueChange = (newValue: string) => {
    if (controlledValue === undefined) {
      setUncontrolledValue(newValue);
    }
    onValueChange?.(newValue);
  };
  
  return (
    <TabsContext.Provider value={{ value, onValueChange: handleValueChange }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex space-x-1 rounded-lg bg-gray-100 p-1 ${className}`}>
      {children}
    </div>
  );
}

export function TabsTrigger({ children, value, className = "" }: {
  children: React.ReactNode;
  value: string;
  className?: string;
}) {
  const context = useContext(TabsContext);
  const isActive = context?.value === value;
  
  return (
    <button
      onClick={() => context?.onValueChange(value)}
      className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
        isActive 
          ? 'bg-white text-gray-900 shadow-sm' 
          : 'text-gray-600 hover:text-gray-900'
      } ${className}`}
    >
      {children}
    </button>
  );
}

export function TabsContent({ children, value, className = "" }: {
  children: React.ReactNode;
  value: string;
  className?: string;
}) {
  const context = useContext(TabsContext);
  
  if (context?.value !== value) return null;
  
  return <div className={className}>{children}</div>;
}