import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import { searchContext } from './rag.ts';
import type { BusEvent } from '@shared/types';

const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'mistral';
const EMBED_MODEL = process.env.EMBED_MODEL || 'nomic-embed-text';

export async function askLLM(question: string) {
  try {
    // Get relevant context from RAG
    const context = await searchContext(question, 5);
    const contextText = context.map(c => `# ${c.file}\n${c.content}`).join('\n---\n');
    
    // Get current state context
    const stateContext = collectStateContext();
    
    const prompt = `You are RepoPilot, an AI assistant for the KPulse ecosystem. You have deep knowledge of the codebase and can help with questions about architecture, implementation, and debugging.

Current Context:
${stateContext}

Relevant Code:
${contextText}

Question: ${question}

Provide a helpful, accurate answer based on the codebase. If you're suggesting code changes, be specific about file locations and implementations.`;

    const result = spawnSync('ollama', ['run', OLLAMA_MODEL], {
      input: prompt,
      encoding: 'utf8',
      timeout: 30000
    });

    if (result.error) {
      throw new Error(`Ollama error: ${result.error.message}`);
    }

    if (result.status !== 0) {
      throw new Error(`Ollama exited with code ${result.status}: ${result.stderr}`);
    }

    return {
      answer: result.stdout.trim(),
      context: context.map(c => c.file),
      model: OLLAMA_MODEL
    };
  } catch (error) {
    console.error('[RepoPilot] LLM error:', error);
    throw error;
  }
}

export async function proposePatch(goal: string) {
  try {
    // Get relevant context
    const context = await searchContext(goal, 3);
    const contextText = context.map(c => `# ${c.file}\n${c.content}`).join('\n---\n');
    
    const prompt = `You are RepoPilot, an expert code generator for the KPulse ecosystem. Generate a unified diff to accomplish the following goal:

Goal: ${goal}

Current Codebase Context:
${contextText}

Instructions:
1. Analyze the existing code structure and patterns
2. Generate a proper unified diff format
3. Follow the existing code style and conventions
4. Ensure the change integrates cleanly with the event bus system
5. Include proper TypeScript types if applicable

Return ONLY the git diff format, no explanations.`;

    const result = spawnSync('ollama', ['run', OLLAMA_MODEL], {
      input: prompt,
      encoding: 'utf8',
      timeout: 45000
    });

    if (result.error) {
      throw new Error(`Ollama error: ${result.error.message}`);
    }

    if (result.status !== 0) {
      throw new Error(`Ollama exited with code ${result.status}: ${result.stderr}`);
    }

    const diff = result.stdout.trim();
    
    // Validate diff format
    if (!diff.includes('diff --git') && !diff.includes('@@')) {
      console.warn('[RepoPilot] Generated output is not a valid diff');
    }

    return {
      diff,
      files: extractFilesFromDiff(diff),
      model: OLLAMA_MODEL
    };
  } catch (error) {
    console.error('[RepoPilot] Patch error:', error);
    throw error;
  }
}

export async function analyzeCodebase(logs: string[], events: BusEvent[]) {
  try {
    // Summarize events
    const eventSummary = summarizeEvents(events);
    const logSummary = logs.slice(-50).join('\n'); // Last 50 log entries
    
    const prompt = `You are RepoPilot, analyzing gameplay data from the KPulse ecosystem to provide insights for development and balancing.

Recent Events:
${eventSummary}

Recent Logs:
${logSummary}

Analyze this data and provide:
1. Insights about player behavior and game balance
2. Suggestions for improvements or new features
3. Potential bugs or issues to investigate
4. Recommendations for the next development iteration

Focus on actionable insights that can improve the player experience.`;

    const result = spawnSync('ollama', ['run', OLLAMA_MODEL], {
      input: prompt,
      encoding: 'utf8',
      timeout: 30000
    });

    if (result.error) {
      throw new Error(`Ollama error: ${result.error.message}`);
    }

    const analysis = result.stdout.trim();
    
    // Parse insights and suggestions
    const insights = extractInsights(analysis);
    const suggestions = extractSuggestions(analysis);

    return {
      insights,
      suggestions,
      analysis,
      model: OLLAMA_MODEL
    };
  } catch (error) {
    console.error('[RepoPilot] Analysis error:', error);
    throw error;
  }
}

function collectStateContext(): string {
  try {
    const contextFiles = [
      'shared/bus/contracts.ts',
      'shared/types/core.ts',
      'apps/engine/src/loop.ts',
      'package.json'
    ];

    const context = contextFiles
      .map(file => {
        const fullPath = path.join(process.cwd(), file);
        if (fs.existsSync(fullPath)) {
          const content = fs.readFileSync(fullPath, 'utf8').slice(0, 2000);
          return `# ${file}\n${content}`;
        }
        return null;
      })
      .filter(Boolean)
      .join('\n---\n');

    return context;
  } catch (error) {
    console.error('[RepoPilot] Context collection error:', error);
    return 'Context unavailable';
  }
}

function summarizeEvents(events: BusEvent[]): string {
  const eventCounts = events.reduce((acc, event) => {
    acc[event.type] = (acc[event.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const summary = Object.entries(eventCounts)
    .map(([type, count]) => `${type}: ${count}`)
    .join(', ');

  return `Event counts: ${summary}`;
}

function extractFilesFromDiff(diff: string): string[] {
  const fileMatches = diff.match(/diff --git a\/(.+?) b\/(.+)/g);
  if (!fileMatches) return [];
  
  return fileMatches.map(match => {
    const parts = match.split(' ');
    return parts[2]?.replace('b/', '') || '';
  }).filter(Boolean);
}

function extractInsights(analysis: string): string[] {
  // Simple extraction - in production this would be more sophisticated
  const lines = analysis.split('\n');
  const insights = lines
    .filter(line => line.toLowerCase().includes('insight') || line.includes('•') || line.includes('-'))
    .map(line => line.replace(/^[•\-\s]+/, '').trim())
    .filter(Boolean)
    .slice(0, 5);
  
  return insights.length > 0 ? insights : ['Analysis completed - see full report for details'];
}

function extractSuggestions(analysis: string): string[] {
  // Simple extraction - in production this would be more sophisticated
  const lines = analysis.split('\n');
  const suggestions = lines
    .filter(line => line.toLowerCase().includes('suggest') || line.toLowerCase().includes('recommend'))
    .map(line => line.replace(/^[•\-\s]+/, '').trim())
    .filter(Boolean)
    .slice(0, 5);
  
  return suggestions.length > 0 ? suggestions : ['Continue monitoring player behavior patterns'];
}