import React from "react";
import { motion } from "framer-motion";
import { safePct, safeNum } from "../lib/safe";
import { LiveDataPulse } from "./AnimatedElements";

const Percent = ({ v }: { v?: number }) => <>{safePct(v)}</>;

function KV({ 
  title, 
  children, 
  index, 
  variant = "default" 
}: { 
  title: string; 
  children: React.ReactNode;
  index: number;
  variant?: "success" | "warning" | "info" | "quantum" | "default";
}) {
  const getVariantColors = () => {
    switch (variant) {
      case "success":
        return "border-green-400/20 bg-green-400/5 text-green-400";
      case "warning":
        return "border-yellow-400/20 bg-yellow-400/5 text-yellow-400";
      case "info":
        return "border-blue-400/20 bg-blue-400/5 text-blue-400";
      case "quantum":
        return "border-purple-400/20 bg-purple-400/5 text-purple-400";
      default:
        return "border-green-400/20 bg-green-400/5 text-green-400";
    }
  };
  
  return (
    <motion.div 
      className={`p-3 rounded border ${getVariantColors()} relative overflow-hidden`}
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ 
        delay: index * 0.1,
        duration: 0.4,
        type: "spring",
        stiffness: 300,
        damping: 25
      }}
      whileHover={{ 
        scale: 1.05,
        transition: { type: "spring", stiffness: 400, damping: 20 }
      }}
    >
      {/* Subtle animated background effect */}
      <motion.div
        className="absolute top-0 right-0 w-8 h-8 bg-current opacity-5 rounded-full"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.05, 0.15, 0.05]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div 
        className="font-medium text-sm relative z-10 flex items-center gap-2"
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: index * 0.1 + 0.2, duration: 0.3 }}
      >
        <LiveDataPulse active={true} size="sm" color={variant === "success" ? "green" : variant === "warning" ? "red" : "blue"} />
        {title}
      </motion.div>
      <motion.div 
        className="text-sm text-white relative z-10"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 + 0.3, duration: 0.3 }}
      >
        {children}
      </motion.div>
    </motion.div>
  );
}

export default function StatusGrid({ s }: { s: any }) {
  if (!s) {
    return (
      <motion.div 
        className="text-center py-4 text-gray-500"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
      >
        <motion.div
          animate={{ rotate: [0, 360] }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="inline-block"
        >
          ⚪
        </motion.div>
        <div className="mt-2">No system state available</div>
      </motion.div>
    );
  }

  const health = s.health ?? {};
  const queue = s.pu_queue ?? {};
  const recent = s.recent ?? {};
  const consciousness = s.consciousness ?? {};

  const statusCards: Array<{
    title: string;
    value: React.ReactNode;
    variant: "success" | "warning" | "info" | "quantum";
  }> = [
    { title: "Invariance", value: <Percent v={health.invariance_score} />, variant: health.invariance_score > 0.7 ? "success" : "warning" },
    { title: "Build Success", value: <Percent v={health.build_success_rate} />, variant: health.build_success_rate > 0.8 ? "success" : "info" },
    { title: "Agent Joy", value: <Percent v={health.agent_joy_average} />, variant: "success" },
    { title: "Throughput", value: safeNum(health.event_throughput, "/min"), variant: "info" },
    { title: "Cognitive Load", value: <Percent v={health.cognitive_load} />, variant: health.cognitive_load < 0.7 ? "success" : "warning" },
    { title: "Consciousness", value: <Percent v={consciousness.level} />, variant: "quantum" }
  ];
  
  // Generic extras: show any additional numeric fields automatically
  const extraHealth = Object.entries(health)
    .filter(([k, v]) => !["invariance_score", "build_success_rate", "agent_joy_average", "event_throughput", "cognitive_load"].includes(k))
    .filter(([k, v]) => typeof v === "number");
  
  return (
    <motion.div 
      className="grid grid-cols-2 gap-3 text-sm"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      {statusCards.map((card, index) => (
        <KV key={card.title} title={card.title} index={index} variant={card.variant}>
          {card.value}
        </KV>
      ))}
      
      <KV title="PU Queue" index={6} variant="info">
        {safeNum(queue.completed)} / {safeNum(queue.total)}
        <div className="text-xs text-gray-400 truncate mt-1">
          {queue.processing ? "🔄 " : "⏸️ "}
          {queue.current_type || "idle"}
        </div>
        <div className="text-xs text-gray-500 truncate">
          next: {queue.next_task?.slice(0, 30) || "—"}
        </div>
      </KV>
      
      <KV title="System Energy" index={7} variant="quantum">
        ⚡ {safeNum(consciousness.energy)}
        <div className="text-xs text-gray-400">
          👥 {safeNum(consciousness.population)} • 🏗️ {safeNum(consciousness.research)}
        </div>
      </KV>

      {/* Auto-render any extra health metrics */}
      {extraHealth.map(([key, value], index) => (
        <KV key={key} title={key.replace(/_/g, ' ')} index={statusCards.length + 2 + index} variant="default">
          {typeof value === "number" && value < 1 ? safePct(value) : safeNum(value as number)}
        </KV>
      ))}
    </motion.div>
  );
}
