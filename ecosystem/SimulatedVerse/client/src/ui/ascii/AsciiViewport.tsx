// ui/ascii/AsciiViewport.tsx
import React, { useEffect, useRef, useState } from 'react';
import { AsciiEngine } from './engine';
import { SCENES, loadScene } from './presets';

type Props = {
  className?: string;
  startScene?: string; // defaults to Starfield
  onReady?: (api: {
    setState: (k: string, v: any) => void;
    switchScene: (name: string) => void;
  }) => void;
};

export default function AsciiViewport({ className, startScene, onReady }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<AsciiEngine | null>(null);
  const [fps, setFps] = useState(0);
  const [sceneName, setSceneName] = useState(startScene || 'Hologram Starfield');

  useEffect(() => {
    if (!hostRef.current) return;
    const engine = new AsciiEngine({
      parent: hostRef.current,
      fontSize: 14,
      density: 120,
      onFPS: (f) => setFps(Math.round(f))
    });
    engineRef.current = engine;
    const scene = SCENES.find(s => s.name === sceneName) ?? SCENES[0];
    if (scene) {
      loadScene(engine, scene);
      engine.start();
    }

    onReady?.({
      setState: (k, v) => engine.setState(k, v),
      switchScene: (name) => {
        const s = SCENES.find(x => x.name === name);
        if (s) { setSceneName(name); loadScene(engine, s); }
      }
    });

    return () => { engine.stop(); engine.destroy(); };
  }, []);

  // Scene switching from UI
  const handleSceneChange = (name: string) => {
    setSceneName(name);
    if (engineRef.current) {
      const s = SCENES.find(x => x.name === name);
      if (s) {
        loadScene(engineRef.current, s);
      }
    }
  };

  // Jarvis controls
  const bumpEnergy = (delta: number) =>
    engineRef.current?.mergeState({ sceneEnergy: Math.max(0, (engineRef.current as any).state?.sceneEnergy ?? 0 + delta) });

  const tweakTunnel = (delta: number) =>
    engineRef.current?.mergeState({ tunnelFreq: Math.max(0, (engineRef.current as any).state?.tunnelFreq ?? 0 + delta) });

  return (
    <div className={`ascii-root ${className || ''}`}>
      <div className="ascii-hud">
        <div className="left">
          <span className="brand">Ξ NuSyQ Hologram</span>
          <span className="dot" />
          <span className="fps">FPS {fps}</span>
        </div>
        <div className="center">
          {SCENES.map(s => (
            <button
              key={s.name}
              className={s.name === sceneName ? 'kbtn active' : 'kbtn'}
              onClick={() => handleSceneChange(s.name)}
              title={s.hint}
            >
              {s.name}
            </button>
          ))}
        </div>
        <div className="right">
          <button className="kbtn" onClick={() => bumpEnergy(+0.2)}>Energy+</button>
          <button className="kbtn" onClick={() => bumpEnergy(-0.2)}>Energy-</button>
          <button className="kbtn" onClick={() => tweakTunnel(+0.1)}>Tunnel+</button>
          <button className="kbtn" onClick={() => tweakTunnel(-0.1)}>Tunnel-</button>
        </div>
      </div>
      <div ref={hostRef} className="ascii-host" />
    </div>
  );
}
