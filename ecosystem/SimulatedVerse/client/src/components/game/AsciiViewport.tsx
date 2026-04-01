import { useEffect, useRef } from "react";
import { useGame } from "../../state/gameStore";

const PALETTE = ["#a3e635","#22d3ee","#60a5fa","#f472b6","#fbbf24","#34d399"];

export default function AsciiViewport() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const setFps = useGame(s => s.setFps);
  const bumpTick = useGame(s => s.bumpTick);
  const nudge = useGame(s => s.nudgeStats);
  const mobile = useGame(s => s.mobile);

  useEffect(() => {
    const cvs = canvasRef.current!;
    const ctx = cvs.getContext("2d")!;
    let last = performance.now(), frames = 0, acc = 0;

    function resize() {
      const w = mobile ? window.innerWidth - 16 : Math.min(900, window.innerWidth - 320);
      const h = mobile ? Math.min(360, window.innerHeight * 0.45) : Math.min(520, window.innerHeight - 240);
      cvs.width = Math.max(280, Math.floor(w));
      cvs.height = Math.max(160, Math.floor(h));
    }
    resize();
    window.addEventListener("resize", resize);

    const charset = " .,:;+*xX#%@" // simple, readable
    function draw(t:number){
      frames++; const dt = t - last; last = t; acc += dt;
      if (acc >= 1000) { setFps(frames); frames = 0; acc = 0; }

      ctx.fillStyle = "#0a0a0a"; ctx.fillRect(0,0,cvs.width,cvs.height);
      const cols = Math.floor(cvs.width/10), rows = Math.floor(cvs.height/18);
      for (let y=0; y<rows; y++){
        for (let x=0; x<cols; x++){
          const v = Math.sin((x+t*0.003)) + Math.cos((y+t*0.002));
          const idx = Math.floor((v+2)/4 * (charset.length-1));
          const ch = charset[idx] ?? ".";
          const fallbackColor = PALETTE[0] ?? "#a3e635";
          const color = PALETTE[(x + y + Math.floor(t / 200)) % PALETTE.length] ?? fallbackColor;
          ctx.fillStyle = color;
          ctx.fillText(ch, x*10+2, y*18+16);
        }
      }
      bumpTick(); if (frames % 30 === 0) nudge();
      requestAnimationFrame(draw);
    }
    ctx.font = "16px ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace";
    ctx.textBaseline = "top";
    requestAnimationFrame(draw);
    return ()=>{ window.removeEventListener("resize", resize); };
  }, [setFps, bumpTick, nudge, mobile]);

  return (
    <div className="rounded-xl border border-white/10 bg-black/50 p-2">
      <canvas ref={canvasRef} />
    </div>
  );
}
