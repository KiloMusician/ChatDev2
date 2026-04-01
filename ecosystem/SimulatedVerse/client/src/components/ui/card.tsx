import React from "react";

export function Card({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-lg border border-gray-200 bg-white shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col space-y-1.5 p-6 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3 className={`text-lg font-semibold leading-none tracking-tight ${className}`}>
      {children}
    </h3>
  );
}

export function CardDescription({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <p className={`text-sm text-gray-600 ${className}`}>
      {children}
    </p>
  );
}

export function CardContent({ children, className = "" }: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`p-6 pt-0 ${className}`}>
      {children}
    </div>
  );
}