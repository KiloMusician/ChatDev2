import { useGame } from "../../state/gameStore";
import { useState, useEffect } from "react";
import { POLLING_INTERVALS } from "@/config/polling";

function runScript(cmd: string){
  // Log the request - can be picked up by devshell or browser extension
  console.log("REQUEST_RUN", cmd);
}

async function runPipeline(suggestion: any) {
  try {
    const response = await fetch('/api/chatdev/pipeline/idler_feature/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer admin-token'
      },
      body: JSON.stringify({
        task: {
          id: suggestion.name.toLowerCase().replace(/\s+/g, '-'),
          type: suggestion.type,
          title: suggestion.name,
          description: suggestion.description
        }
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('Pipeline executed:', result);
      return true;
    }
  } catch (error) {
    console.error('Pipeline execution failed:', error);
  }
  return false;
}

export default function Controls(){
  const setView = useGame(s=>s.setView);
  const toggleSound = useGame(s=>s.toggleSound);
  const [gameState, setGameState] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  
  // Fetch game state for intelligent suggestions
  useEffect(() => {
    const fetchGameState = async () => {
      try {
        const response = await fetch('/api/game/state');
        const data = await response.json();
        setGameState(data);
        
        // Generate smart suggestions based on resources
        const energy = data.resources?.energy || 0;
        const materials = data.resources?.materials || 0;
        const newSuggestions = [];
        
        if (energy >= 100) {
          newSuggestions.push({
            name: "Quantum Generator", 
            type: "UXPU",
            description: "Advanced energy systems"
          });
        }
        if (materials >= 50) {
          newSuggestions.push({
            name: "Auto-Production", 
            type: "RefactorPU",
            description: "Material synthesis automation"
          });
        }
        
        setSuggestions(newSuggestions);
      } catch (error) {
        console.warn('Game state fetch failed:', error);
      }
    };
    
    fetchGameState();
    const interval = setInterval(fetchGameState, POLLING_INTERVALS.standard);
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="space-y-3">
      {/* Original Controls */}
      <div className="flex flex-wrap gap-2">
        <button className="btn" onClick={()=>setView("ASCII")}>ASCII</button>
        <button className="btn" onClick={()=>setView("HUD")}>HUD</button>
        <button className="btn" onClick={()=>setView("CHATDEV")}>ChatDev</button>
        <button className="btn" onClick={()=>setView("VANTAGES")}>Vantages</button>
      </div>
      
      {/* Advanced Controls */}
      <div className="flex flex-wrap gap-2">
        <button className="btn" onClick={()=>runScript("npm run cascade")}>Cascade</button>
        <button className="btn" onClick={()=>runScript("npm run temple:open")}>Temple</button>
        <button className="btn" onClick={toggleSound}>Sound</button>
      </div>
      
      {/* AI Pipeline Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs opacity-70">🤖 AI Suggestions</div>
          {suggestions.map((suggestion, i) => (
            <button 
              key={i}
              className="btn-ai w-full text-left" 
              onClick={() => runPipeline(suggestion)}
              title={suggestion.description}
            >
              ✨ {suggestion.name}
            </button>
          ))}
        </div>
      )}
      
      {/* Game Status Integration */}
      {gameState && (
        <div className="text-xs space-y-1 opacity-80">
          <div>⚡ Energy: {gameState.resources?.energy || 0}</div>
          <div>🔧 Materials: {gameState.resources?.materials || 0}</div>
          {gameState.research?.active && (
            <div>🔬 Research: {gameState.research.active} ({gameState.research.progress || 0}%)</div>
          )}
        </div>
      )}
      
      <style>{`
        .btn{padding:.5rem .75rem;border-radius:.5rem;background:#1f2937;color:#e5e7eb;border:1px solid #374151;transition:all 0.2s}
        .btn:hover{background:#374151}
        .btn-ai{padding:.5rem .75rem;border-radius:.5rem;background:#312e81;color:#c7d2fe;border:1px solid #4338ca;transition:all 0.2s}
        .btn-ai:hover{background:#4338ca}
      `}</style>
    </div>
  );
}
