import { useEffect } from "react";
import { useGame } from "../../state/gameStore";

export default function BootGate() {
  const setPhase = useGame(s => s.setPhase);
  
  useEffect(() => {
    const t = setTimeout(() => setPhase("TITLE"), 800); // quick boot
    return () => clearTimeout(t);
  }, [setPhase]);
  
  return (
    <div className="min-h-dvh grid place-items-center bg-black text-neutral-200">
      <div className="animate-pulse text-center">
        <div className="text-2xl">ΞNuSyQ • Culture-Ship</div>
        <div className="opacity-70 mt-2">Initializing subsystems…</div>
      </div>
    </div>
  );
}