import { Router } from 'express';
import GamePersistence from '../storage/game-persistence';

const router = Router();
const persistence = new GamePersistence();

// Auto-save endpoint
router.post('/save', async (req, res) => {
  try {
    const { playerId, gameState } = req.body;
    
    if (!playerId || !gameState) {
      return res.status(400).json({
        success: false,
        error: 'Missing playerId or gameState'
      });
    }
    
    const result = await persistence.saveGameState(playerId, gameState);
    
    if (result.success) {
      // Also update player stats
      await persistence.updatePlayerStats(playerId, {
        consciousness: gameState.consciousness || 0,
        playTime: gameState.sessionTime || 0,
        newAchievements: gameState.newAchievements || []
      });
    }
    
    res.json(result);
  } catch (error) {
    console.error('Save game error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to save game state'
    });
  }
});

// Load game endpoint
router.get('/load/:playerId', async (req, res) => {
  try {
    const { playerId } = req.params;
    
    // Create or update player profile
    await persistence.createOrUpdatePlayer(playerId);
    
    // Load game state
    const gameState = await persistence.loadGameState(playerId);
    
    res.json({
      success: true,
      gameState
    });
  } catch (error) {
    console.error('Load game error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to load game state'
    });
  }
});

// Get recent saves
router.get('/saves/:playerId', async (req, res) => {
  try {
    const { playerId } = req.params;
    const limit = parseInt(req.query.limit as string) || 10;
    
    const saves = await persistence.loadRecentStates(playerId, limit);
    
    res.json({
      success: true,
      saves
    });
  } catch (error) {
    console.error('Get saves error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get saves'
    });
  }
});

// Get player analytics
router.get('/analytics/:playerId', async (req, res) => {
  try {
    const { playerId } = req.params;
    const days = parseInt(req.query.days as string) || 7;
    
    const analytics = await persistence.getPlayerAnalytics(playerId, days);
    
    res.json({
      success: true,
      analytics
    });
  } catch (error) {
    console.error('Get analytics error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get analytics'
    });
  }
});

// Create multiplayer session
router.post('/multiplayer/create', async (req, res) => {
  try {
    const { hostId } = req.body;
    
    if (!hostId) {
      return res.status(400).json({
        success: false,
        error: 'Missing hostId'
      });
    }
    
    const result = await persistence.createMultiplayerSession(hostId);
    res.json(result);
  } catch (error) {
    console.error('Create session error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to create session'
    });
  }
});

// Join multiplayer session
router.post('/multiplayer/join', async (req, res) => {
  try {
    const { playerId, sessionCode } = req.body;
    
    if (!playerId || !sessionCode) {
      return res.status(400).json({
        success: false,
        error: 'Missing playerId or sessionCode'
      });
    }
    
    const result = await persistence.joinMultiplayerSession(playerId, sessionCode);
    res.json(result);
  } catch (error) {
    console.error('Join session error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to join session'
    });
  }
});

// Update multiplayer consciousness
router.post('/multiplayer/consciousness', async (req, res) => {
  try {
    const { sessionId, playerId, consciousness } = req.body;
    
    if (!sessionId || !playerId || consciousness === undefined) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters'
      });
    }
    
    const result = await persistence.updateMultiplayerConsciousness(
      sessionId,
      playerId,
      consciousness
    );
    
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    console.error('Update consciousness error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to update consciousness'
    });
  }
});

// Log game event
router.post('/event', async (req, res) => {
  try {
    const { playerId, gameId, eventType, eventData } = req.body;
    
    if (!playerId || !gameId || !eventType) {
      return res.status(400).json({
        success: false,
        error: 'Missing required parameters'
      });
    }
    
    await persistence.logEvent(playerId, gameId, eventType, eventData);
    
    res.json({
      success: true
    });
  } catch (error) {
    console.error('Log event error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to log event'
    });
  }
});

export default router;