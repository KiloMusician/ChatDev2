import express from 'express';
import cors from 'cors';
import { askLLM, proposePatch, analyzeCodebase } from './application-services/repopilot/src/llm.ts';
import { indexRepository, searchContext } from './application-services/repopilot/src/rag.ts';
import type { BusEvent } from '../../../shared/bus/contracts';

const app = express();
const PORT = parseInt(process.env.REPOPILOT_PORT || '7411');

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'RepoPilot',
    model: process.env.OLLAMA_MODEL || 'mistral',
    timestamp: new Date().toISOString()
  });
});

// Ask endpoint - general questions about the codebase
app.post('/ask', async (req, res) => {
  try {
    const { q: question } = req.body;
    
    if (!question) {
      return res.status(400).json({ error: 'Question is required' });
    }

    console.log(`[RepoPilot] Question: ${question}`);
    
    const result = await askLLM(question);
    
    res.json(result);
  } catch (error) {
    console.error('[RepoPilot] Ask error:', error);
    res.status(500).json({ 
      error: 'Failed to process question',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Patch endpoint - generate code changes
app.post('/patch', async (req, res) => {
  try {
    const { goal } = req.body;
    
    if (!goal) {
      return res.status(400).json({ error: 'Goal is required' });
    }

    console.log(`[RepoPilot] Patch goal: ${goal}`);
    
    const result = await proposePatch(goal);
    
    res.json(result);
  } catch (error) {
    console.error('[RepoPilot] Patch error:', error);
    res.status(500).json({ 
      error: 'Failed to generate patch',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Analyze endpoint - process gameplay logs for insights
app.post('/analyze', async (req, res) => {
  try {
    const { logs, events } = req.body;
    
    console.log(`[RepoPilot] Analyzing ${logs?.length || 0} logs, ${events?.length || 0} events`);
    
    const result = await analyzeCodebase(logs || [], events || []);
    
    res.json(result);
  } catch (error) {
    console.error('[RepoPilot] Analysis error:', error);
    res.status(500).json({ 
      error: 'Failed to analyze data',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Index endpoint - rebuild RAG index
app.post('/index', async (req, res) => {
  try {
    console.log('[RepoPilot] Rebuilding repository index...');
    
    await indexRepository();
    
    res.json({ 
      status: 'success',
      message: 'Repository index rebuilt',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('[RepoPilot] Index error:', error);
    res.status(500).json({ 
      error: 'Failed to rebuild index',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Search endpoint - find relevant code context
app.post('/search', async (req, res) => {
  try {
    const { query, limit = 10 } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Search query is required' });
    }
    
    const results = await searchContext(query, limit);
    
    res.json({ results });
  } catch (error) {
    console.error('[RepoPilot] Search error:', error);
    res.status(500).json({ 
      error: 'Failed to search',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🤖 RepoPilot server running on port ${PORT}`);
  console.log(`Model: ${process.env.OLLAMA_MODEL || 'mistral'}`);
  
  // Initialize RAG index on startup
  indexRepository().catch(console.error);
});

export default app;