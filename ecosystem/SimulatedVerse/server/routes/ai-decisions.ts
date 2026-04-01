import { Router } from 'express';
import AIDecisionEngine from '../consciousness/ai-decision-engine';

const router = Router();
const aiEngine = new AIDecisionEngine();

// Get AI recommendation
router.get('/recommend', async (req, res) => {
  const playerId = (req as { session?: { playerId?: string } }).session?.playerId || 'default';
  
  // Get current colony state from request or fetch it
  const rawStateValue = Array.isArray(req.query.state) ? req.query.state[0] : req.query.state;
  const rawState = typeof rawStateValue === 'string' ? rawStateValue : null;
  const colonyState = rawState ? JSON.parse(rawState) : null;
  
  if (!colonyState) {
    return res.status(400).json({ error: 'Colony state required' });
  }
  
  aiEngine.updateState(colonyState);
  const decision = await aiEngine.makeDecision();
  const recommendations = aiEngine.getRecommendations(3);
  
  res.json({
    bestAction: decision,
    recommendations,
    analytics: aiEngine.getAnalytics()
  });
});

// Execute AI decision
router.post('/execute', async (req, res) => {
  const { decision, colonyState } = req.body;
  
  if (!decision || !colonyState) {
    return res.status(400).json({ error: 'Decision and state required' });
  }
  
  aiEngine.updateState(colonyState);
  
  // Log the AI decision
  console.log('[AI] Executing decision:', decision.action, '-', decision.reasoning);
  
  res.json({
    success: true,
    decision,
    message: `AI executed: ${decision.action}`
  });
});

// Get AI analytics
router.get('/analytics', (req, res) => {
  res.json(aiEngine.getAnalytics());
});

// Train AI with outcome feedback
router.post('/feedback', (req, res) => {
  const { decision, outcome, newState } = req.body;
  
  if (newState) {
    aiEngine.updateState(newState);
  }
  
  // The AI will learn from this feedback
  console.log('[AI] Learning from outcome:', outcome);
  
  res.json({
    success: true,
    message: 'AI learning updated'
  });
});

export default router;
