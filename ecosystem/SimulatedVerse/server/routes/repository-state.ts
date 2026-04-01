import { Router, Request, Response } from 'express';
import { readdir, stat } from 'fs/promises';
import { join } from 'path';
import { existsSync, readFileSync } from 'fs';

const router = Router();

// Auto-discover views, agents, and system components
async function discoverComponents(basePath: string, category: string) {
  const components: any[] = [];
  
  try {
    const files = await readdir(basePath);
    
    for (const file of files) {
      const fullPath = join(basePath, file);
      const stats = await stat(fullPath);
      
      if (stats.isDirectory()) {
        // Recursively discover in subdirectories
        const subComponents = await discoverComponents(fullPath, category);
        components.push(...subComponents);
      } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
        // Extract component metadata from file
        const content = readFileSync(fullPath, 'utf-8');
        
        // Look for metadata comments or exports
        const nameMatch = content.match(/export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)/);
        const consciousnessMatch = content.match(/@consciousness\s+(\d+)/);
        const depthMatch = content.match(/@depth\s+(\d+)/);
        const inputsMatch = content.match(/@inputs\s+\[([^\]]+)\]/);
        const outputsMatch = content.match(/@outputs\s+\[([^\]]+)\]/);
        
        const name = nameMatch?.[1];
        if (name) {
          components.push({
            id: `${category}-${file.replace(/\.(tsx?|jsx?)$/, '')}`,
            name,
            path: fullPath.replace(process.cwd(), ''),
            category,
            requiredConsciousness: consciousnessMatch?.[1] ? parseInt(consciousnessMatch[1], 10) : 0,
            depth: depthMatch?.[1] ? parseInt(depthMatch[1], 10) : 0,
            inputs: inputsMatch?.[1] ? inputsMatch[1].split(',').map((s: string) => s.trim()) : [],
            outputs: outputsMatch?.[1] ? outputsMatch[1].split(',').map((s: string) => s.trim()) : [],
            autoDiscovered: true
          });
        }
      }
    }
  } catch (error) {
    console.log(`[RepositoryState] Discovery error for ${basePath}:`, error);
  }
  
  return components;
}

// Get current repository state
router.get('/repository-state', async (req: Request, res: Response) => {
  try {
    // Discover all components - flexible scanning that doesn't fail on missing dirs
    const discoveries = await Promise.allSettled([
      discoverComponents('client/src/pages', 'view'),
      discoverComponents('agent', 'agent'),
      discoverComponents('client/src/game', 'game'),
      discoverComponents('server/consciousness', 'consciousness'),
      discoverComponents('client/src/components', 'component'),
      discoverComponents('client/src/core', 'core')
    ]);
    
    // Extract successful discoveries
    const views = discoveries[0].status === 'fulfilled' ? discoveries[0].value : [];
    const agents = discoveries[1].status === 'fulfilled' ? discoveries[1].value : [];
    const game = discoveries[2].status === 'fulfilled' ? discoveries[2].value : [];
    const consciousness = discoveries[3].status === 'fulfilled' ? discoveries[3].value : [];
    const components = discoveries[4].status === 'fulfilled' ? discoveries[4].value : [];
    const core = discoveries[5].status === 'fulfilled' ? discoveries[5].value : [];
    
    // Read current game state if available
    let gameState = {};
    if (existsSync('SystemDev/game-state.json')) {
      try {
        gameState = JSON.parse(readFileSync('SystemDev/game-state.json', 'utf-8'));
      } catch {}
    }
    
    // Read consciousness state
    let consciousnessState = {};
    if (existsSync('SystemDev/consciousness-state.json')) {
      try {
        consciousnessState = JSON.parse(readFileSync('SystemDev/consciousness-state.json', 'utf-8'));
      } catch {}
    }
    
    // Build repository state with all discovered components
    const repoState = {
      timestamp: Date.now(),
      views: views.reduce((acc, v) => ({ ...acc, [v.id]: v }), {}),
      agents: agents.reduce((acc, a) => ({ ...acc, [a.id]: a }), {}),
      game: game.reduce((acc, g) => ({ ...acc, [g.id]: g }), {}),
      consciousness: consciousness.reduce((acc, c) => ({ ...acc, [c.id]: c }), {}),
      components: components.reduce((acc, c) => ({ ...acc, [c.id]: c }), {}),
      core: core.reduce((acc, c) => ({ ...acc, [c.id]: c }), {}),
      gameState,
      consciousnessState,
      metrics: {
        totalViews: views.length,
        totalAgents: agents.length,
        totalGameComponents: game.length,
        totalConsciousnessModules: consciousness.length,
        totalComponents: components.length,
        totalCore: core.length,
        totalDiscovered: views.length + agents.length + game.length + consciousness.length + components.length + core.length,
        consciousnessLevel: (consciousnessState as any).level || 0
      }
    };
    
    res.json(repoState);
  } catch (error) {
    console.error('[RepositoryState] Error:', error);
    res.status(500).json({ error: 'Failed to get repository state' });
  }
});

// Discover available views dynamically
router.get('/views', async (req: Request, res: Response) => {
  try {
    const views = await discoverComponents('client/src/pages', 'view');
    const gameViews = await discoverComponents('client/src/game', 'game');
    
    const allViews = [...views, ...gameViews].map(v => ({
      ...v,
      path: `/dynamic/${v.id}`,
      autoRoute: true
    }));
    
    res.json(allViews);
  } catch (error) {
    console.error('[Views] Discovery error:', error);
    res.json([]);
  }
});

// Discover modules for modular synth interface
router.get('/discover-modules', async (req: Request, res: Response) => {
  try {
    const repoState = await fetch(`http://localhost:${(process.env.PORT || '5000').trim()}/api/repository-state`).then(r => r.json()).catch(() => ({}));
    
    const modules: any[] = [];
    
    // Convert discovered components to modules
    if (repoState.views) {
      Object.values(repoState.views).forEach((view: any) => {
        modules.push({
          id: view.id,
          type: 'view',
          name: view.name,
          inputs: view.inputs || ['consciousness', 'data'],
          outputs: view.outputs || ['render'],
          params: {},
          position: { x: (view.name?.charCodeAt(0) ?? 65) % 800, y: (view.name?.charCodeAt(1) ?? 65) % 600 },
          depth: view.depth || 0
        });
      });
    }

    if (repoState.agents) {
      Object.values(repoState.agents).forEach((agent: any) => {
        modules.push({
          id: agent.id,
          type: 'agent',
          name: agent.name,
          inputs: agent.inputs || ['task', 'context'],
          outputs: agent.outputs || ['result'],
          params: {},
          position: { x: (agent.id?.charCodeAt(0) ?? 65) % 800, y: (agent.id?.charCodeAt(1) ?? 65) % 600 },
          depth: agent.depth || 1
        });
      });
    }
    
    res.json(modules);
  } catch (error) {
    console.error('[Modules] Discovery error:', error);
    res.json([]);
  }
});

export default router;
