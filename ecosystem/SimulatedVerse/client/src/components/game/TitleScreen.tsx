import { useGame } from "../../state/gameStore";

export default function TitleScreen() {
  const setPhase = useGame(s => s.setPhase);
  const mobile = useGame(s => s.mobile);
  
  return (
    <div className="min-h-dvh grid place-items-center bg-gradient-to-b from-slate-900 to-black text-slate-100">
      <div className="w-full max-w-md p-6 rounded-2xl bg-black/40 backdrop-blur border border-white/10">
        <div className="text-center space-y-2">
          <div className="text-3xl font-bold">SimulatedVerse</div>
          <div className="text-xs opacity-75">CoreLink Foundation • Culture-Ship Module</div>
        </div>
        <div className="mt-6 space-y-3">
          <button className="w-full py-3 rounded-lg bg-emerald-500/90 hover:bg-emerald-400"
                  onClick={()=>setPhase("GAME")}>
            Start New Run
          </button>
          <button className="w-full py-3 rounded-lg bg-indigo-500/80 hover:bg-indigo-400">Load / Continue</button>
          <button className="w-full py-3 rounded-lg bg-slate-700/80 hover:bg-slate-600">Settings</button>
        </div>
        <div className="mt-6 text-center text-xs opacity-70">
          {mobile ? "Mobile profile active • compact HUD" : "Desktop profile active • expanded HUD"}
        </div>
      </div>
    </div>
  );
}