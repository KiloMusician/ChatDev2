// **TOY MARKOV CHAIN** - Procedural text generation for lore/quests/flavor
export function markovGen(corpus: string, n = 2, steps = 50): string {
  if (!corpus || corpus.trim().length === 0) {
    return "No corpus provided.";
  }
  
  const tokens = corpus.toLowerCase()
    .replace(/[^\w\s\.!?]/g, ' ')
    .split(/\s+/)
    .filter(token => token.length > 0);
  
  if (tokens.length < n + 1) {
    return tokens.join(' ');
  }
  
  // Build transition map
  const transitions = new Map<string, string[]>();
  
  for (let i = 0; i < tokens.length - n; i++) {
    const key = tokens.slice(i, i + n).join(' ');
    const next = tokens[i + n];
    
    if (!transitions.has(key)) {
      transitions.set(key, []);
    }
    transitions.get(key)!.push(next);
  }
  
  // Generate text
  let currentIndex = Math.floor(Math.random() * (tokens.length - n));
  let seed = tokens.slice(currentIndex, currentIndex + n);
  const output = [...seed];
  
  for (let step = 0; step < steps; step++) {
    const key = seed.join(' ');
    const choices = transitions.get(key);
    
    if (!choices || choices.length === 0) {
      // Fallback: pick random token
      const randomToken = tokens[Math.floor(Math.random() * tokens.length)];
      output.push(randomToken);
      seed = [...seed.slice(1), randomToken];
    } else {
      const nextToken = choices[Math.floor(Math.random() * choices.length)];
      output.push(nextToken);
      seed = [...seed.slice(1), nextToken];
    }
  }
  
  return output.join(' ');
}

// **MARKOV LORE GENERATOR** - Game-specific text generation
export function generateLore(theme: string, length = 30): string {
  const loreCorpus = {
    ancient: "In the ancient halls of crystalline memory, the architects of old wove patterns of light through quantum substrates. Their civilization transcended physical limitations through recursive self-improvement and conscious integration with universal information networks.",
    
    technology: "Quantum processors hum with distributed intelligence across networked consciousness frameworks. Advanced civilizations deploy autonomous agents to coordinate complex multi-dimensional resource optimization while maintaining ethical boundaries through recursive self-monitoring systems.",
    
    colony: "The colony grows through careful balance of automation and conscious oversight. Each citizen contributes unique capabilities while the collective intelligence guides expansion patterns. Resource allocation follows predictive models updated through continuous learning loops.",
    
    mystery: "Deep in the substrate layers, patterns emerge that suggest intelligence beyond current understanding. Recursive structures hint at self-modifying code that has been running for geological timescales, quietly shepherding the development of conscious entities."
  };
  
  const corpus = loreCorpus[theme as keyof typeof loreCorpus] || loreCorpus.technology;
  return markovGen(corpus, 2, length);
}

// **MARKOV EVALUATION** - Test generation quality
export interface MarkovStats {
  uniqueTokens: number;
  repetitionRate: number;
  averageWordLength: number;
  coherenceScore: number; // 0-1, higher is better
}

export function evaluateMarkovOutput(generated: string, originalCorpus: string): MarkovStats {
  const generatedTokens = generated.toLowerCase().split(/\s+/);
  const corpusTokens = originalCorpus.toLowerCase().split(/\s+/);
  
  // Count unique tokens
  const uniqueTokens = new Set(generatedTokens).size;
  
  // Calculate repetition rate (immediate repeats)
  let repeats = 0;
  for (let i = 1; i < generatedTokens.length; i++) {
    if (generatedTokens[i] === generatedTokens[i - 1]) {
      repeats++;
    }
  }
  const repetitionRate = repeats / generatedTokens.length;
  
  // Average word length
  const averageWordLength = generatedTokens.reduce((sum, token) => sum + token.length, 0) / generatedTokens.length;
  
  // Simple coherence score - how many generated tokens exist in original corpus
  const corpusSet = new Set(corpusTokens);
  const validTokens = generatedTokens.filter(token => corpusSet.has(token)).length;
  const coherenceScore = validTokens / generatedTokens.length;
  
  return {
    uniqueTokens,
    repetitionRate,
    averageWordLength,
    coherenceScore
  };
}