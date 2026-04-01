import React from "react";

export function Select({ children, value, onValueChange, ...props }: {
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  [key: string]: any;
}) {
  return (
    <select 
      value={value} 
      onChange={(e) => onValueChange?.(e.target.value)}
      className="border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      {...props}
    >
      {children}
    </select>
  );
}

export function SelectContent({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function SelectItem({ children, value }: { children: React.ReactNode; value: string }) {
  return <option value={value}>{children}</option>;
}

export function SelectTrigger({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={className}>{children}</div>;
}

export function SelectValue({ placeholder }: { placeholder?: string }) {
  return <span>{placeholder}</span>;
}