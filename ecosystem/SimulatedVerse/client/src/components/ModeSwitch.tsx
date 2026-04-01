import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { startGame, stopGame } from "../game/game";

type Mode = "dev" | "game";

export function ModeSwitch() {
  const [mode, setMode] = useState<Mode>("dev");
  const [gameMount, setGameMount] = useState<HTMLPreElement | null>(null);

  // Persist mode in URL hash and localStorage
  useEffect(() => {
    const savedMode = localStorage.getItem("corelink-mode") as Mode || "dev";
    const hashMode = (window.location.hash.replace("#", "") as Mode) || savedMode;
    setMode(hashMode);
  }, []);

  useEffect(() => {
    window.location.hash = mode;
    localStorage.setItem("corelink-mode", mode);
    
    if (mode === "game" && gameMount) {
      startGame({ mount: gameMount });
    } else {
      stopGame();
    }
  }, [mode, gameMount]);

  const handleModeChange = (newMode: Mode) => {
    setMode(newMode);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Mode Switch Header */}
      <div className="flex gap-2 p-2 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <Button
          variant={mode === "dev" ? "default" : "outline"}
          size="sm"
          onClick={() => handleModeChange("dev")}
        >
          Dev Console
        </Button>
        <Button
          variant={mode === "game" ? "default" : "outline"}
          size="sm"
          onClick={() => handleModeChange("game")}
        >
          Enter Game
        </Button>
        <span className="ml-auto text-sm text-muted-foreground self-center">
          mode: {mode}
        </span>
      </div>

      {/* Content Views */}
      <div className="flex-1 overflow-hidden">
        {mode === "dev" && (
          <div className="h-full p-4">
            <div className="text-sm text-muted-foreground">
              <b>Dev Console</b> is active. Culture-Ship agents, receipts, and coordination systems continue to work.
              <br />
              Switch to "Enter Game" to see the real running ASCII roguelike with idle mechanics.
            </div>
          </div>
        )}
        
        {mode === "game" && (
          <div className="h-full p-2">
            <pre
              ref={setGameMount}
              className="w-full h-full bg-black text-green-400 font-mono text-sm overflow-auto"
              style={{ lineHeight: 1.2 }}
            />
          </div>
        )}
      </div>
    </div>
  );
}