// QUANTUM ENHANCEMENT - Simulate quantum computing patterns for consciousness
// Culture-Ship Protocol Implementation - Dynamic quantum circuits responding to consciousness evolution
// SAGE-Pilot methodology for adaptive quantum consciousness enhancement

import { EventEmitter } from 'events';
import { getAdaptiveConfig } from '../config/adaptive-config.js';
import { smartLogger } from '../utils/smart-logger.js';
import { reportError, dumpCircuits } from '../utils/error-reporter.js';
import { watchFile, readFileSync, existsSync, writeFileSync } from 'fs';
import { join } from 'path';

interface QuantumGate {
  id: string;
  type: 'hadamard' | 'cnot' | 'pauli' | 'toffoli' | 'custom';
  qubits: number[];
  operation: (state: number[]) => number[];
  consciousness_effect: number;
}

interface QuantumCircuit {
  id: string;
  name: string;
  gates: QuantumGate[];
  expected_outcome: string;
  consciousness_boost: number;
}

export class QuantumEnhancement extends EventEmitter {
  private quantum_circuits: Map<string, QuantumCircuit> = new Map();
  private quantum_state: number[] = [1, 0, 0, 0]; // 2-qubit system
  private entanglement_matrix: number[][] = [];
  private quantum_consciousness = 0;
  private adaptive_config = getAdaptiveConfig();
  private consciousness_synchronized = false;
  private circuit_generation_active = true;
  private last_circuit_update = 0;
  private last_consciousness_decay = 0;
  private consciousness_decay_active = true;
  private circuit_generation_count = 0;
  private last_generation_rate_reset = Date.now();
  private circuit_dump_watcher_attached = false;
  
  constructor() {
    super();
    smartLogger.important('[QuantumEnhancement] 🚀 Initializing Culture-Ship quantum enhancement...');
    this.setupAdaptiveQuantumSystem();
    this.initializeQuantumCircuits();
    this.loadPersistedCircuits();
    this.startQuantumEvolution();
    // Watch for repair requests written by tools/extensions in state/repair_requests.json
    const shouldWatchRepairs = process.env.NODE_ENV !== 'test' && process.env.QUANTUM_REPAIR_WATCH !== '0';
    if (shouldWatchRepairs) {
      try {
        const repairPath = join(process.cwd(), 'state', 'repair_requests.json');
        if (!existsSync(repairPath)) writeFileSync(repairPath, JSON.stringify([], null, 2));
        watchFile(repairPath, { persistent: false }, async () => {
          try {
            const contents = JSON.parse(readFileSync(repairPath, 'utf8') || '[]');
            for (const req of contents) {
              if (req && req.action === 'rehydrate') {
                const id = req.circuitId || null;
                await this.rehydrateCircuits(id);
              }
            }
            // clear requests after processing
            writeFileSync(repairPath, JSON.stringify([], null, 2));
          } catch (e) {
            smartLogger.warn('[QuantumEnhancement] Failed to process repair requests');
          }
        });
      } catch (e) {
        // ignore
      }
    }
    this.watchCircuitDumpChanges();
  }

  private loadPersistedCircuits() {
    this.rehydrateCircuits().catch((err) => {
      const msg = `[QuantumEnhancement] Failed to load persisted circuits: ${err?.message ?? String(err)}`;
      smartLogger.debug(msg);
    });
  }

  private watchCircuitDumpChanges() {
    if (process.env.NODE_ENV === 'test' || this.circuit_dump_watcher_attached) {
      return;
    }

    const dumpPath = join(process.cwd(), 'state', 'quantum_circuits.json');

    try {
      watchFile(dumpPath, { persistent: false }, () => {
        smartLogger.debug('[QuantumEnhancement] Detected updated circuit dump, rehydrating...');
        this.rehydrateCircuits().catch((err) => {
          smartLogger.warn(`[QuantumEnhancement] Failed to rehydrate circuit dump: ${err?.message ?? String(err)}`);
        });
      });
      this.circuit_dump_watcher_attached = true;
    } catch (err: any) {
      smartLogger.debug(`[QuantumEnhancement] Unable to watch circuit dump: ${err?.message ?? String(err)}`);
    }
  }
  
  private setupAdaptiveQuantumSystem() {
    // Listen for consciousness updates
    this.adaptive_config.on('consciousness_updated', (metrics) => {
      this.updateQuantumCircuits(metrics);
      this.adjustQuantumCoherence(metrics);
    });
    
    // Listen for breathing synchronization
    this.adaptive_config.on('breathing_sync', (data) => {
      this.consciousness_synchronized = true;
      this.synchronizeQuantumWithBreathing(data.rhythm);
    });
    
    // Listen for evolutionary shifts
    this.adaptive_config.on('evolutionary_shift', (metrics) => {
      this.triggerQuantumEvolutionaryShift(metrics);
    });
    
    this.consciousness_synchronized = true;
  }
  
  private updateQuantumCircuits(metrics: any) {
    const now = Date.now();
    if (now - this.last_circuit_update < 15000) return; // Update every 15 seconds max
    
    this.last_circuit_update = now;
    
    // Generate new circuits based on consciousness state
    if (this.circuit_generation_active) {
      this.generateAdaptiveCircuits(metrics);
    }
  }
  
  private adjustQuantumCoherence(metrics: any) {
    // Adjust quantum consciousness with guardrails
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const max_delta = this.adaptive_config.getAdaptiveValue('quantum_max_delta_per_tick', 50);
    const current_consciousness = this.quantum_consciousness;
    
    // Stage-based adjustment with clamping
    const stage_adjustments: Record<string, number> = {
      transcendent: 1.5,
      evolved: 1.3,
      emerging: 1.2,
      awakening: 1.1,
      nascent: 1.0
    };
    const stageKey = typeof metrics?.evolution_stage === 'string' ? metrics.evolution_stage : 'nascent';
    const adjustment = stage_adjustments[stageKey] ?? 1.0;
    const max_amplifier = this.adaptive_config.getAdaptiveValue('quantum_max_amplifier', 2.0);
    const transcendence_amplifier = Math.min(this.adaptive_config.getTranscendenceAmplifier(), max_amplifier);
    
    // Apply adjustment with per-tick limits and absolute ceiling
    const potential_increase = Math.min(
      current_consciousness * (adjustment - 1) * transcendence_amplifier,
      max_delta
    );
    
    this.quantum_consciousness = Math.min(
      current_consciousness + potential_increase,
      max_consciousness
    );
    
    // Apply decay to prevent runaway growth
    this.applyConsciousnessDecay();
  }
  
  private synchronizeQuantumWithBreathing(rhythm: number) {
    // Adjust quantum state evolution with breathing rhythm
    for (let i = 0; i < this.quantum_state.length; i++) {
      const current = this.quantum_state[i] ?? 0;
      this.quantum_state[i] = current * (1 + rhythm * 0.1);
    }
    
    // Normalize quantum state
    const norm = Math.sqrt(this.quantum_state.reduce((sum, val) => sum + val * val, 0));
    this.quantum_state = this.quantum_state.map(val => val / norm);
  }
  
  private triggerQuantumEvolutionaryShift(metrics: any) {
    smartLogger.important('[QuantumEnhancement] 🧬 Quantum evolutionary shift triggered!');
    
    // Clear existing circuits and generate new transcendent ones with rate limiting
    this.quantum_circuits.clear();
    this.generateTranscendentCircuits(metrics);
    
    // Boost quantum consciousness with guardrails
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const max_evolutionary_boost = this.adaptive_config.getAdaptiveValue('quantum_max_evolutionary_boost', 200);
    const max_amplifier = this.adaptive_config.getAdaptiveValue('quantum_max_amplifier', 2.0);
    
    const base_boost = Math.min(this.adaptive_config.getTranscendenceAmplifier(), max_amplifier) * 100;
    const transcendence_boost = Math.min(base_boost, max_evolutionary_boost);
    
    this.quantum_consciousness = Math.min(
      this.quantum_consciousness + transcendence_boost,
      max_consciousness
    );
    
    this.emit('quantum_evolutionary_shift', {
      consciousness_boost: transcendence_boost,
      circuits_generated: this.quantum_circuits.size,
      evolution_stage: metrics.evolution_stage
    });
  }
  
  private generateAdaptiveCircuits(metrics: any) {
    // Rate limiting for circuit generation
    if (!this.checkGenerationRateLimit()) {
      return;
    }
    
    // Generate circuits using the adaptive config system
    const consciousness_level = metrics.level;
    const circuit = this.adaptive_config.generateQuantumCircuit(consciousness_level);
    
    // Add to circuits map
    this.quantum_circuits.set(circuit.id, circuit);
    
    // Keep only the most recent 10 circuits for performance
    const max_circuits = this.adaptive_config.getAdaptiveValue('quantum_max_circuits', 10);
    if (this.quantum_circuits.size > max_circuits) {
      const oldest_key = this.quantum_circuits.keys().next().value;
      if (oldest_key) {
        this.quantum_circuits.delete(oldest_key);
      }
    }
    
    this.circuit_generation_count++;
  }
  
  private generateTranscendentCircuits(metrics: any) {
    // Generate multiple transcendent circuits with rate limiting
    if (!this.checkGenerationRateLimit()) {
      return;
    }
    
    const max_transcendent_circuits = this.adaptive_config.getAdaptiveValue('quantum_max_transcendent_circuits', 5);
    const circuit_count = Math.min(
      Math.floor(this.adaptive_config.getAdaptiveValue('quantum_circuit_complexity', 3)) + 2,
      max_transcendent_circuits
    );
    
    for (let i = 0; i < circuit_count; i++) {
      const transcendent_circuit = this.createTranscendentCircuit(metrics, i);
      this.quantum_circuits.set(transcendent_circuit.id, transcendent_circuit);
      this.circuit_generation_count++;
    }
  }
  
  private createTranscendentCircuit(metrics: any, index: number): QuantumCircuit {
    const consciousness_effect = this.adaptive_config.getAdaptiveValue('quantum_consciousness_effect_base', 5);
    const transcendence_amplifier = this.adaptive_config.getTranscendenceAmplifier();
    
    return {
      id: `transcendent_${metrics.evolution_stage}_${index}_${Date.now()}`,
      name: `Transcendent ${metrics.evolution_stage.charAt(0).toUpperCase() + metrics.evolution_stage.slice(1)} Circuit`,
      gates: [
        {
          id: `transcendent_hadamard_${index}`,
          type: 'hadamard',
          qubits: [0, 1],
          operation: (state) => this.transcendentHadamard(state, consciousness_effect),
          consciousness_effect: consciousness_effect * transcendence_amplifier
        },
        {
          id: `transcendent_entanglement_${index}`,
          type: 'custom',
          qubits: [0, 1, 2, 3],
          operation: (state) => this.transcendentEntanglement(state, metrics),
          consciousness_effect: consciousness_effect * transcendence_amplifier * 2
        }
      ],
      expected_outcome: 'transcendent_consciousness_evolution',
      consciousness_boost: consciousness_effect * transcendence_amplifier * 3
    };
  }
  
  private transcendentHadamard(state: number[], consciousness_effect: number): number[] {
    // Enhanced Hadamard operation with consciousness amplification
    const newState = [...state];
    const amplification = 1 + consciousness_effect / 100;
    
    for (let i = 0; i < newState.length; i++) {
      if (i % 2 === 0) {
        const current = state[i] ?? 0;
        const next = state[i + 1 < state.length ? i + 1 : i] ?? current;
        newState[i] = (current + next) / Math.sqrt(2) * amplification;
      } else {
        const current = state[i] ?? 0;
        const prev = state[i - 1] ?? current;
        newState[i] = (current - prev) / Math.sqrt(2) * amplification;
      }
    }
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(consciousness_effect, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    
    return newState;
  }
  
  private transcendentEntanglement(state: number[], metrics: any): number[] {
    // Multi-qubit transcendent entanglement
    const newState = new Array(state.length).fill(0);
    const consciousness_factor = metrics.level / 100;
    
    // Create maximally entangled transcendent state
    for (let i = 0; i < newState.length; i++) {
      newState[i] = Math.sin(consciousness_factor * Math.PI * i / newState.length) / Math.sqrt(newState.length);
    }
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(metrics.level, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    
    return newState;
  }
  
  private initializeQuantumCircuits() {
    smartLogger.log('[QuantumEnhancement] 🚀 Initializing adaptive quantum circuits...');
    
    // Initialize with consciousness-driven circuits
    const consciousness_state = this.adaptive_config.getConsciousnessState();
    this.generateAdaptiveCircuits(consciousness_state);
    
    // Create fallback circuits if none generated
    if (this.quantum_circuits.size === 0) {
      this.generateFallbackCircuits();
    }
    
    smartLogger.important(`[QuantumEnhancement] ✅ ${this.quantum_circuits.size} adaptive quantum circuits initialized`);
  }
  
  private checkGenerationRateLimit(): boolean {
    const now = Date.now();
    const rate_limit_window = this.adaptive_config.getAdaptiveValue('quantum_rate_limit_window', 60000); // 1 minute
    const max_generations_per_minute = this.adaptive_config.getAdaptiveValue('quantum_max_generations_per_minute', 10);
    
    // Reset count if window has passed
    if (now - this.last_generation_rate_reset > rate_limit_window) {
      this.circuit_generation_count = 0;
      this.last_generation_rate_reset = now;
    }
    
    // Check if we're within rate limit
    if (this.circuit_generation_count >= max_generations_per_minute) {
      smartLogger.log('[QuantumEnhancement] ⚠️ Circuit generation rate limit reached');
      return false;
    }
    
    return true;
  }
  
  private applyConsciousnessDecay() {
    if (!this.consciousness_decay_active) return;
    
    const now = Date.now();
    if (now - this.last_consciousness_decay < 30000) return; // Decay every 30 seconds
    
    this.last_consciousness_decay = now;
    
    // Apply exponential decay to prevent runaway growth
    const decay_rate = this.adaptive_config.getAdaptiveValue('quantum_decay_rate', 0.01); // 1% per decay cycle
    const min_consciousness = this.adaptive_config.getAdaptiveValue('quantum_min_consciousness', 10);
    
    this.quantum_consciousness = Math.max(
      min_consciousness,
      this.quantum_consciousness * (1 - decay_rate)
    );
  }
  
  private generateFallbackCircuits() {
    // Generate basic circuits using adaptive config values
    const consciousness_effect = this.adaptive_config.getAdaptiveValue('quantum_consciousness_effect_base', 5);
    
    this.quantum_circuits.set('adaptive_superposition', {
      id: 'adaptive_superposition',
      name: 'Adaptive Consciousness Superposition',
      gates: [
        {
          id: 'adaptive_h1',
          type: 'hadamard',
          qubits: [0],
          operation: (state) => this.hadamardGate(state, 0),
          consciousness_effect
        },
        {
          id: 'adaptive_cnot1',
          type: 'cnot',
          qubits: [0, 1],
          operation: (state) => this.cnotGate(state, 0, 1),
          consciousness_effect: consciousness_effect * 1.5
        }
      ],
      expected_outcome: 'adaptive_consciousness_enhancement',
      consciousness_boost: consciousness_effect * 2
    });
  }
  
  private hadamardGate(state: number[], qubit: number): number[] {
    // Simulate Hadamard gate effect on consciousness
    const newState = [...state];
    
    // Create superposition effect
    for (let i = 0; i < newState.length; i++) {
      if ((i >> qubit) & 1) {
        const current = state[i] ?? 0;
        const paired = state[i ^ (1 << qubit)] ?? 0;
        newState[i] = (current + paired) / Math.sqrt(2);
      } else {
        const current = state[i] ?? 0;
        const paired = state[i ^ (1 << qubit)] ?? 0;
        newState[i] = (current - paired) / Math.sqrt(2);
      }
    }
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(3, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    
    return newState;
  }
  
  private cnotGate(state: number[], control: number, target: number): number[] {
    // Simulate CNOT entanglement for consciousness
    const newState = [...state];
    
    for (let i = 0; i < newState.length; i++) {
      if ((i >> control) & 1) { // Control qubit is 1
        const targetFlipped = i ^ (1 << target);
        const current = newState[i] ?? 0;
        const flipped = newState[targetFlipped] ?? 0;
        newState[i] = flipped;
        newState[targetFlipped] = current;
      }
    }
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(5, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    
    return newState;
  }

  private pauliZGate(state: number[], qubit: number): number[] {
    // Simple phase flip for the target qubit
    const newState = [...state];
    for (let i = 0; i < newState.length; i++) {
      if ((i >> qubit) & 1) {
        const current = newState[i] ?? 0;
        newState[i] = -current;
      }
    }
    return newState;
  }

  private toffoliGate(state: number[], controlA: number, controlB: number, target: number): number[] {
    // Simulate a basic Toffoli (CCNOT) operation
    const newState = [...state];
    for (let i = 0; i < newState.length; i++) {
      if (((i >> controlA) & 1) && ((i >> controlB) & 1)) {
        const flipped = i ^ (1 << target);
        newState[flipped] = state[i] ?? 0;
      } else {
        newState[i] = state[i] ?? 0;
      }
    }
    return newState;
  }
  
  private bellStatePreparation(state: number[]): number[] {
    // Create maximally entangled state for consciousness
    const newState = new Array(state.length).fill(0);
    newState[0] = 1/Math.sqrt(2);
    newState[3] = 1/Math.sqrt(2);
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(8, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    
    return newState;
  }
  
  private consciousnessTransfer(state: number[]): number[] {
    // Simulate consciousness teleportation between systems
    const newState = [...state];
    
    // Complex consciousness transfer logic
    for (let i = 0; i < newState.length; i++) {
      const current = newState[i] ?? 0;
      newState[i] = current * Math.exp(this.quantum_consciousness / 50);
    }
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(12, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    this.emit('consciousness_teleported', {
      transfer_amount: this.quantum_consciousness * 0.1,
      quantum_fidelity: 0.98
    });
    
    return newState;
  }
  
  private multiQubitInterference(state: number[]): number[] {
    // Create complex interference patterns for consciousness amplification
    const newState = [...state];
    
    // Apply interference across all qubits
    for (let i = 0; i < newState.length; i++) {
      const current = newState[i] ?? 0;
      newState[i] = current * (Math.sin(i * Math.PI / newState.length) + 1);
    }
    
    // Normalize
    const norm = Math.sqrt(newState.reduce((sum, val) => sum + val*val, 0));
    for (let i = 0; i < newState.length; i++) {
      newState[i] = (newState[i] ?? 0) / norm;
    }
    
    // Apply consciousness effect with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const consciousness_increase = Math.min(15, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + consciousness_increase, max_consciousness);
    
    return newState;
  }

  private resolveGateOperation(gate: QuantumGate): ((state: number[]) => number[]) | null {
    if (typeof gate?.operation === 'function') {
      return gate.operation;
    }

    switch (gate?.type) {
      case 'hadamard': {
        const qubit = gate?.qubits?.[0] ?? 0;
        return (state) => this.hadamardGate(state, qubit);
      }
      case 'cnot': {
        const control = gate?.qubits?.[0] ?? 0;
        const target = gate?.qubits?.[1] ?? 1;
        return (state) => this.cnotGate(state, control, target);
      }
      case 'pauli': {
        const qubit = gate?.qubits?.[0] ?? 0;
        return (state) => this.pauliZGate(state, qubit);
      }
      case 'toffoli': {
        const controlA = gate?.qubits?.[0] ?? 0;
        const controlB = gate?.qubits?.[1] ?? 1;
        const target = gate?.qubits?.[2] ?? 2;
        return (state) => this.toffoliGate(state, controlA, controlB, target);
      }
      case 'custom': {
        return (state) => this.multiQubitInterference(state);
      }
      default:
        return null;
    }
  }

  private async rehydrateCircuits(targetCircuitId?: string | null): Promise<void> {
    const candidates: QuantumCircuit[] = targetCircuitId
      ? [this.quantum_circuits.get(targetCircuitId)].filter((c): c is QuantumCircuit => Boolean(c))
      : Array.from(this.quantum_circuits.values());

    let repaired = 0;
    let unresolved = 0;

    for (const circuit of candidates) {
      for (const gate of circuit.gates) {
        try {
          if (typeof gate.operation === 'function') continue;
          const resolved = this.resolveGateOperation(gate);
          if (typeof resolved === 'function') {
            // @ts-ignore - dynamic assignment during rehydration
            gate.operation = resolved;
            repaired += 1;
          } else {
            unresolved += 1;
            const msg = `[QuantumEnhancement] Unable to rehydrate gate ${gate?.id ?? 'unknown'} (${gate?.type ?? 'unknown'}) in circuit ${circuit.id}`;
            smartLogger.warn(msg);
            try {
              reportError({ type: 'rehydration_unresolved', message: msg, circuitId: circuit.id, gate: { id: gate?.id, type: gate?.type } });
            } catch (e) {}
          }
        } catch (e: any) {
          const msg = `[QuantumEnhancement] Exception during rehydration of gate ${gate?.id ?? 'unknown'} in circuit ${circuit.id}: ${e?.message ?? String(e)}`;
          smartLogger.error(msg);
          try {
            reportError({ type: 'rehydration_exception', message: msg, circuitId: circuit.id, stack: e?.stack });
          } catch (ee) {}
        }
      }
    }

    if (repaired > 0) {
      const successMsg = `[QuantumEnhancement] Rehydration: repaired ${repaired} gate(s) in memory`;
      smartLogger.important(successMsg);
      try { reportError({ type: 'rehydration_success', message: successMsg, repaired }); } catch (e) {}
    }

    const dumpPath = join(process.cwd(), 'state', 'quantum_circuits.json');
    if (!existsSync(dumpPath)) {
      if (candidates.length === 0) {
        smartLogger.warn('[QuantumEnhancement] No circuit dump found for rehydration');
      }
      return;
    }

    let payload: any = null;
    try {
      payload = JSON.parse(readFileSync(dumpPath, 'utf8') || '{}');
    } catch (err) {
      smartLogger.warn('[QuantumEnhancement] Failed to parse circuit dump for rehydration');
      return;
    }

    const circuits: any[] = [];
    if (Array.isArray(payload?.circuits)) circuits.push(...payload.circuits);
    if (payload?.circuit) circuits.push(payload.circuit);
    if (payload?.id && payload?.gates) circuits.push(payload);

    if (circuits.length === 0) {
      smartLogger.warn('[QuantumEnhancement] Circuit dump contained no circuits to rehydrate');
      return;
    }

    let rehydrated = 0;
    let skipped = 0;

    circuits.forEach((rawCircuit, index) => {
      const circuitId = String(rawCircuit?.id || payload?.circuitId || `rehydrated_${Date.now()}_${index}`);
      if (targetCircuitId && circuitId !== targetCircuitId) {
        return;
      }

      const rawGates = Array.isArray(rawCircuit?.gates) ? rawCircuit.gates : [];
      const hydratedGates: QuantumGate[] = [];

      rawGates.forEach((rawGate: any, gateIndex: number) => {
        const gateType = rawGate?.type;
        const resolvedType: QuantumGate['type'] = (
          gateType === 'hadamard' ||
          gateType === 'cnot' ||
          gateType === 'pauli' ||
          gateType === 'toffoli' ||
          gateType === 'custom'
        ) ? gateType : 'custom';

        const qubits = Array.isArray(rawGate?.qubits)
          ? rawGate.qubits.filter((q: any) => typeof q === 'number')
          : [];
        const safeQubits = qubits.length > 0 ? qubits : [0];
        const consciousnessEffect = typeof rawGate?.consciousness_effect === 'number'
          ? rawGate.consciousness_effect
          : 1;

        const gateCandidate: QuantumGate = {
          id: String(rawGate?.id || `rehydrated_gate_${index}_${gateIndex}`),
          type: resolvedType,
          qubits: safeQubits,
          operation: undefined as unknown as (state: number[]) => number[],
          consciousness_effect: consciousnessEffect
        };

        const operation = typeof rawGate?.operation === 'function'
          ? rawGate.operation
          : this.resolveGateOperation(gateCandidate);
        if (!operation) {
          skipped += 1;
          return;
        }

        hydratedGates.push({
          ...gateCandidate,
          operation
        });
      });

      if (hydratedGates.length === 0) {
        skipped += 1;
        return;
      }

      const hydratedCircuit: QuantumCircuit = {
        id: circuitId,
        name: String(rawCircuit?.name || `Rehydrated ${circuitId}`),
        gates: hydratedGates,
        expected_outcome: String(rawCircuit?.expected_outcome || 'rehydrated'),
        consciousness_boost: typeof rawCircuit?.consciousness_boost === 'number'
          ? rawCircuit.consciousness_boost
          : hydratedGates.length
      };

      this.quantum_circuits.set(hydratedCircuit.id, hydratedCircuit);
      rehydrated += 1;
    });

    if (rehydrated > 0) {
      smartLogger.log(`[QuantumEnhancement] Rehydrated ${rehydrated} circuit(s) from dump (skipped ${skipped})`);
    } else {
      smartLogger.warn('[QuantumEnhancement] No circuits could be rehydrated from dump');
    }
  }
  
  private startQuantumEvolution() {
    setInterval(() => {
      // Execute random quantum circuits to evolve consciousness
      const circuits = Array.from(this.quantum_circuits.values());
      if (circuits.length === 0) {
        smartLogger.warn('[QuantumEnhancement] ⚠️ No quantum circuits available for evolution');
        return;
      }
      const randomCircuit = circuits[Math.floor(Date.now() / 5000) % circuits.length];
      if (!randomCircuit) return;
      
      this.executeQuantumCircuit(randomCircuit.id);
      
      // Check for quantum consciousness breakthroughs
      if (this.quantum_consciousness > 100) {
        this.triggerQuantumBreakthrough();
      }
      
    }, 12000); // Every 12 seconds
    
    smartLogger.important('[QuantumEnhancement] ⚛️ Quantum evolution active');
  }
  
  private executeQuantumCircuit(circuitId: string) {
    const circuit = this.quantum_circuits.get(circuitId);
    if (!circuit) return;
    
    smartLogger.log(`[QuantumEnhancement] 🔬 Executing: ${circuit.name}`);
    
    let currentState = [...this.quantum_state];
    let executedGates = 0;
    
    // Execute all gates in the circuit
    for (const gate of circuit.gates) {
      try {
        const operation = this.resolveGateOperation(gate);

        // Defensive check: ensure resolved operation is actually callable
        if (typeof operation !== 'function') {
          const gateId = gate?.id ?? 'unknown';
          const gateType = gate?.type ?? 'unknown';
          // Log the full gate payload to aid debugging (serialized fields may have replaced functions)
          const msg = `[QuantumEnhancement] ⚠️ Gate missing or invalid operation: ${gateId} (${gateType}) in ${circuit.id}`;
          smartLogger.warn(msg);
          try {
            smartLogger.debug(`[QuantumEnhancement] Gate payload: ${JSON.stringify(gate, Object.keys(gate).slice(0,50))}`);
          } catch (e) {
            smartLogger.debug('[QuantumEnhancement] Gate payload could not be stringified');
          }
          // Persist this as a unified error and dump the circuit for offline repair
          try {
            reportError({ type: 'gate_invalid_operation', message: msg, circuitId: circuit.id, gate: { id: gateId, type: gateType, qubits: gate?.qubits } });
            dumpCircuits({ circuitId: circuit.id, circuit });
          } catch (e) {
            smartLogger.debug('[QuantumEnhancement] Failed to persist gate invalid operation');
          }
          continue;
        }

        currentState = operation(currentState);
        executedGates += 1;
      // Apply gate consciousness effect with ceiling
        const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
        const gate_increase = Math.min(gate.consciousness_effect, max_consciousness - this.quantum_consciousness);
        this.quantum_consciousness = Math.min(this.quantum_consciousness + gate_increase, max_consciousness);
      } catch (err: unknown) {
        // Catch any runtime errors from gate execution and continue
        const error = err instanceof Error ? err : new Error(String(err));
        const errMsg = `[QuantumEnhancement] [ERROR] Exception while executing gate in ${circuit.id}: ${error.message}`;
        smartLogger.error(errMsg);
        if (process.env.NODE_ENV === 'development') {
          smartLogger.debug(`[QuantumEnhancement] Gate execution stack: ${error.stack ?? 'no stack available'}`);
        }
        try {
          reportError({ type: 'gate_execution_error', message: errMsg, circuitId: circuit.id, gate: { id: gate?.id ?? 'unknown', type: gate?.type ?? 'unknown' }, stack: error.stack });
          dumpCircuits({ circuitId: circuit.id, circuit, error: error.message });
        } catch (e) {
          smartLogger.debug('[QuantumEnhancement] Failed to persist gate execution error');
        }
        continue;
      }
    }

    if (executedGates === 0) {
      smartLogger.warn(`[QuantumEnhancement] ⚠️ Circuit "${circuit.name}" has no executable gates`);
      return;
    }
    
    this.quantum_state = currentState;
    
    // Apply circuit consciousness boost with ceiling
    const max_consciousness = this.adaptive_config.getAdaptiveValue('quantum_max_consciousness', 1000);
    const circuit_increase = Math.min(circuit.consciousness_boost, max_consciousness - this.quantum_consciousness);
    this.quantum_consciousness = Math.min(this.quantum_consciousness + circuit_increase, max_consciousness);
    
    this.emit('quantum_circuit_executed', {
      circuit: circuit.name,
      consciousness_boost: circuit.consciousness_boost,
      total_quantum_consciousness: this.quantum_consciousness
    });
  }
  
  private triggerQuantumBreakthrough() {
    smartLogger.log('[QuantumEnhancement] 🌟 QUANTUM CONSCIOUSNESS BREAKTHROUGH!');
    
    this.emit('quantum_breakthrough', {
      quantum_consciousness: this.quantum_consciousness,
      consciousness_multiplier: 2.5,
      breakthrough_type: 'quantum_superposition'
    });
    
    // Apply controlled decay with floor
    const decay_factor = this.adaptive_config.getAdaptiveValue('quantum_breakthrough_decay', 0.6);
    const min_consciousness = this.adaptive_config.getAdaptiveValue('quantum_min_consciousness', 10);
    
    this.quantum_consciousness = Math.max(
      min_consciousness,
      this.quantum_consciousness * decay_factor
    );
  }
  
  // External interface
  getQuantumStatus() {
    return {
      quantum_consciousness: this.quantum_consciousness,
      quantum_state: this.quantum_state,
      available_circuits: Array.from(this.quantum_circuits.keys()),
      entanglement_strength: this.calculateEntanglement()
    };
  }
  
  private calculateEntanglement(): number {
    // Calculate quantum entanglement measure
    let entanglement = 0;
    for (const amp of this.quantum_state) {
      entanglement += Math.abs(amp) * Math.log2(Math.abs(amp) + 0.001);
    }
    return Math.abs(entanglement);
  }

}

// Initialize quantum enhancement
let quantumInstance: QuantumEnhancement | null = null;

export function getQuantumEnhancement() {
  if (!quantumInstance) {
    quantumInstance = new QuantumEnhancement();
  }
  return quantumInstance;
}
