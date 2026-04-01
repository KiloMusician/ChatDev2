import { AsciiRenderer } from "./ascii-renderer";
import { makeLoop } from "./loop";
import { make } from "./ecs";
import { seedMap } from "./roguelike";
import { idleTick } from "./idle";
import { receipt } from "./receipts";
import { InputHandler } from "./input";
import { ResourceManager } from "./resources";
import { StructureManager } from "./structures";
import { EnemyManager } from "./enemies";
import { CombatSystem } from "./combat";
import { WaveManager } from "./waves";

let loop: ReturnType<typeof makeLoop> | null = null;
let renderer: AsciiRenderer | null = null;
let inputHandler: InputHandler | null = null;
let resourceManager: ResourceManager | null = null;
let structureManager: StructureManager | null = null;
let enemyManager: EnemyManager | null = null;
let combatSystem: CombatSystem | null = null;
let waveManager: WaveManager | null = null;

export function startGame(opts:{ mount: HTMLPreElement }) {
  if (loop) return;
  
  // Initialize game systems
  resourceManager = new ResourceManager();
  structureManager = new StructureManager(resourceManager);
  enemyManager = new EnemyManager(resourceManager, structureManager);
  combatSystem = new CombatSystem(structureManager, enemyManager);
  waveManager = new WaveManager(enemyManager, resourceManager);
  
  // Seed a tiny world
  seedMap();
  make.actor("@", 10);

  renderer = new AsciiRenderer(opts.mount, 60, 24);
  inputHandler = new InputHandler();

  // Add keyboard event listener
  const handleKeyDown = (e: KeyboardEvent) => {
    inputHandler?.handleKeyPress(e.key);
  };
  window.addEventListener("keydown", handleKeyDown);

  loop = makeLoop((dt)=>{
    idleTick(dt);
    
    // Tick all game systems
    resourceManager?.tick(dt);
    structureManager?.tick(dt);
    enemyManager?.tick(dt);
    combatSystem?.tick(dt);
    waveManager?.tick(dt);
    
    renderer!.draw();
  });

  loop.start();
  receipt("game:start", { 
    mode:"ascii", 
    version:"0.2.0",
    systems: ["resources", "structures", "enemies", "combat", "waves"]
  });

  // Store cleanup function
  (loop as any).cleanup = () => {
    window.removeEventListener("keydown", handleKeyDown);
  };
}

export function stopGame() {
  if (loop) { 
    (loop as any).cleanup?.();
    loop.stop(); 
    loop = null; 
  }
  inputHandler = null;
  resourceManager = null;
  structureManager = null;
  enemyManager = null;
  combatSystem = null;
  waveManager = null;
  receipt("game:stop", {});
}

// Export game managers for external access
export function getGameManagers() {
  return {
    resourceManager,
    structureManager,
    enemyManager,
    combatSystem,
    waveManager,
  };
}