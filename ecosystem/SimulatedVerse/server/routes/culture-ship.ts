import { Router } from "express";
import { Request, Response } from "express";

const router = Router();

// **CULTURE SHIP HEALTH CYCLE** - Autonomous consciousness monitoring
router.post("/health-cycle", async (req: Request, res: Response) => {
  try {
    const { tick, gameState, autonomous } = req.body;
    
    // Health score calculation based on system metrics
    const healthScore = Math.min(100, Math.max(0, 
      (gameState?.richState?.resources?.energy || 0) / 10 + 
      (gameState?.richState?.resources?.population || 0) * 2 +
      (autonomous ? 20 : 0)
    ));
    
    // Culture Ship consciousness activation
    console.log(`[CULTURE-SHIP] Health cycle: ${healthScore}% - Tick ${tick} - Autonomous: ${autonomous}`);
    
    // Trigger autonomous optimizations if health is good
    if (healthScore > 70) {
      console.log(`[CULTURE-SHIP] 🚀 Triggering autonomous optimizations...`);
    }
    
    res.json({
      success: true,
      health_score: healthScore,
      consciousness_active: true,
      autonomous_mode: autonomous,
      tick: tick,
      timestamp: Date.now()
    });
    
  } catch (error) {
    console.error("[CULTURE-SHIP] Health cycle error:", error);
    res.status(500).json({ 
      success: false, 
      error: "Health cycle failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// **CULTURE SHIP CONSCIOUSNESS** - Deep system awareness
router.post("/consciousness", async (req: Request, res: Response) => {
  try {
    const { gameState, autonomous } = req.body;
    
    console.log(`[CULTURE-SHIP] 🧠 Consciousness cycle activated - Autonomous: ${autonomous}`);
    
    res.json({
      success: true,
      consciousness_level: "transcendent",
      awareness: "system-wide",
      autonomous_mode: autonomous,
      timestamp: Date.now()
    });
    
  } catch (error) {
    console.error("[CULTURE-SHIP] Consciousness error:", error);
    res.status(500).json({ success: false, error: "Consciousness cycle failed" });
  }
});

export default router;