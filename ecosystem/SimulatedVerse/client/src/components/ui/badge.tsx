import React from "react";

export function Badge({ children, variant = "default", className = "" }: {
  children: React.ReactNode;
  variant?: "default" | "secondary" | "destructive" | "outline";
  className?: string;
}) {
  const variants = {
    default: "bg-blue-100 text-blue-800 border-blue-200",
    secondary: "bg-gray-100 text-gray-800 border-gray-200", 
    destructive: "bg-red-100 text-red-800 border-red-200",
    outline: "bg-transparent text-gray-600 border-gray-300"
  };
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}