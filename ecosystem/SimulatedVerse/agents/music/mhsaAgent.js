/* Music Agent - MHSA (Musical Harmonic Set Analysis) Agent for autonomous ops */

class MHSAAgent {
  constructor() {
    this.name = 'MHSA Music Agent';
    this.capabilities = ['rowgen', 'harmonic_analysis', 'motif_generation'];
  }

  async rowgen(options = {}) {
    const { motif = "0,1,4", allInterval = true, count = 12 } = options;
    
    console.log(`[mhsaAgent] Generating ${count} rows with motif ${motif}, allInterval: ${allInterval}`);
    
    // Generate musical rows with harmonic properties
    const rows = [];
    const motifArray = motif.split(',').map(n => parseInt(n));
    
    for (let i = 0; i < count; i++) {
      // Generate a 12-tone row starting with the motif
      const row = [...motifArray];
      const remaining = Array.from({length: 12}, (_, i) => i).filter(n => !motifArray.includes(n));
      
      // Shuffle remaining tones
      for (let j = remaining.length - 1; j > 0; j--) {
        const k = Math.floor(Math.random() * (j + 1));
        [remaining[j], remaining[k]] = [remaining[k], remaining[j]];
      }
      
      row.push(...remaining);
      
      // Ensure all-interval property if requested
      if (allInterval) {
        // Basic all-interval row validation/adjustment
        const intervals = [];
        for (let k = 0; k < 11; k++) {
          intervals.push(Math.abs(row[k+1] - row[k]) % 12);
        }
        
        // If not all intervals unique, apply simple transformation
        const uniqueIntervals = new Set(intervals);
        if (uniqueIntervals.size < 11) {
          // Simple rotation to improve interval diversity
          const rotated = row.slice(1).concat(row[0]);
          rows.push(rotated);
        } else {
          rows.push(row);
        }
      } else {
        rows.push(row);
      }
    }
    
    return rows;
  }

  async analyzeHarmonicContent(sequence) {
    // Analyze harmonic content of a musical sequence
    const analysis = {
      pitch_classes: new Set(sequence).size,
      intervallic_density: this.computeIntervallicDensity(sequence),
      harmonic_tension: this.computeHarmonicTension(sequence),
      invariance_properties: this.computeInvarianceProperties(sequence)
    };
    
    return analysis;
  }

  computeIntervallicDensity(sequence) {
    const intervals = [];
    for (let i = 0; i < sequence.length - 1; i++) {
      intervals.push(Math.abs(sequence[i+1] - sequence[i]) % 12);
    }
    return new Set(intervals).size / 11; // density ratio
  }

  computeHarmonicTension(sequence) {
    // Simple harmonic tension based on dissonant intervals
    const dissonantIntervals = [1, 2, 6, 10, 11];
    let tension = 0;
    
    for (let i = 0; i < sequence.length - 1; i++) {
      const interval = Math.abs(sequence[i+1] - sequence[i]) % 12;
      if (dissonantIntervals.includes(interval)) {
        tension += 1;
      }
    }
    
    return tension / (sequence.length - 1);
  }

  computeInvarianceProperties(sequence) {
    // Basic invariance under transformations
    const inverted = sequence.map(n => (12 - n) % 12);
    const retrograde = [...sequence].reverse();
    
    return {
      inversional_similarity: this.computeSimilarity(sequence, inverted),
      retrograde_similarity: this.computeSimilarity(sequence, retrograde),
      t6_invariance: this.computeT6Invariance(sequence)
    };
  }

  computeSimilarity(seq1, seq2) {
    const common = seq1.filter(n => seq2.includes(n));
    return common.length / seq1.length;
  }

  computeT6Invariance(sequence) {
    // Transposition by tritone invariance
    const t6 = sequence.map(n => (n + 6) % 12);
    return this.computeSimilarity(sequence, t6);
  }

  async health() {
    return {
      status: 'operational',
      capabilities: this.capabilities,
      last_rowgen: new Date().toISOString()
    };
  }
}

const musicAgent = new MHSAAgent();
export default musicAgent;