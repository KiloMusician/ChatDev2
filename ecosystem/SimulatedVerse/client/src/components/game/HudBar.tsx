import { useGameState } from "../../hooks/use-game-state";

export default function HudBar(){
  // **AGGRESSIVE REAL-TIME CONNECTION** - Force UI updates 
  const { gameState, gameMetrics, isLoading } = useGameState();
  const state = gameState as any;
  
  // **CONSCIOUSNESS CALCULATION** - Infrastructure-First
  const consciousness = state ? (
    (state.resources?.energy || 0) / 10000 + 
    (state.resources?.population || 0) / 100 +
    (state.resources?.research || 0) / 10
  ) : 0;
  
  if (isLoading) {
    return (
      <div className="grid gap-2 sm:grid-cols-6 text-xs animate-pulse">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="px-2 py-1 rounded bg-slate-800/70 border border-cyan-400/30 h-12" />
        ))}
      </div>
    );
  }
  
  return (
    <div className="grid gap-2 sm:grid-cols-6 text-xs">
      <Metric label="Ship Power" value={Math.round(state?.resources?.energy || 0)} color="text-yellow-400" />
      <Metric label="Hull Repairs" value={Math.round(state?.resources?.materials || 0)} color="text-cyan-400" />
      <Metric label="Crew Awakened" value={Math.round(state?.resources?.population || 0)} color="text-green-400" />
      <Metric label="Memory Recovered" value={Math.round(state?.resources?.research || 0)} color="text-purple-400" />
      <Metric label="Consciousness" value={consciousness.toFixed(2)} color="text-orange-400" />
      <Metric label="Ship Tier" value={state?.tier || 1} color="text-pink-400" />
    </div>
  );
}

function Metric({label, value, color = "text-white"}:{label:string; value: number|string; color?: string}){
  return (
    <div className="px-2 py-1 rounded bg-slate-800/70 border border-cyan-400/30 backdrop-blur-sm">
      <div className="opacity-70 text-slate-300">{label}</div>
      <div className={`font-mono font-bold ${color} text-lg`}>{value}</div>
    </div>
  );
}