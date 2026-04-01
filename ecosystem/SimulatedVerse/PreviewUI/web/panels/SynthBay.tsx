/**
 * SynthBay - Audio synthesis and harmony generation interface
 */

import React, { useState, useEffect } from "react";
import { useGame } from "../core/store";
import { colonyBridge } from "../adapters/ColonyBridge";

export function SynthBay() {
  const game = useGame();
  const [harmonic, setHarmonic] = useState(0);
  const [frequency, setFrequency] = useState(440);
  const [waveform, setWaveform] = useState<"sine" | "square" | "triangle" | "sawtooth">("sine");
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Generate consciousness-driven audio parameters
  const consciousnessLevel = Math.min(1.0, (game.totalEnergyGenerated + game.totalScrapCollected) / 1000);
  const availableHarmonics = Math.floor(consciousnessLevel * 8) + 1;
  
  const harmonicFrequencies = Array.from({ length: availableHarmonics }, (_, i) => ({
    harmonic: i + 1,
    frequency: frequency * (i + 1),
    amplitude: 1 / (i + 1), // Natural harmonic decay
    unlocked: true
  }));
  
  // Council Bus integration for sonic events
  const triggerSonicEvent = async (eventType: string) => {
    try {
      await fetch("/api/council-bus/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: "synthbay.harmonic_event",
          payload: {
            eventType,
            frequency,
            waveform,
            consciousnessLevel,
            harmonic,
            timestamp: Date.now()
          }
        })
      });
      console.log(`[🎵] Sonic event published: ${eventType}`);
    } catch (error) {
      console.warn("[🎵] Failed to publish sonic event:", error);
    }
  };
  
  // Harmonic resonance affects colony resources
  const applyHarmonicResonance = async () => {
    const resonanceBonus = harmonic * consciousnessLevel * 0.1;
    
    try {
      // Use colony bridge to boost resources
      await colonyBridge.executeAction("tick");
      
      // Trigger special resonance event
      await triggerSonicEvent("harmonic_resonance");
      
      console.log(`[🎵] Harmonic resonance applied: +${resonanceBonus.toFixed(2)} efficiency`);
    } catch (error) {
      console.warn("[🎵] Harmonic resonance failed:", error);
    }
  };
  
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-purple-400 mb-2">🎵 Synthesis Bay</h1>
        <p className="text-gray-300">
          Harmonic resonance and consciousness-driven audio synthesis
        </p>
        <div className="mt-4 text-lg text-purple-300">
          Consciousness Level: {(consciousnessLevel * 100).toFixed(1)}%
        </div>
      </div>
      
      {/* Main Synthesis Controls */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Frequency Control */}
        <div className="bg-gradient-to-br from-purple-900/30 to-indigo-900/30 border border-purple-600/30 rounded-lg p-4">
          <h3 className="text-lg font-bold text-purple-300 mb-3">Fundamental Frequency</h3>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Frequency: {frequency} Hz
              </label>
              <input
                type="range"
                min="200"
                max="800"
                value={frequency}
                onChange={(e) => setFrequency(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Waveform</label>
              <select
                value={waveform}
                onChange={(e) => setWaveform(e.target.value as any)}
                className="w-full bg-gray-800 border border-purple-600/30 rounded px-3 py-2 text-white"
              >
                <option value="sine">Sine Wave</option>
                <option value="square">Square Wave</option>
                <option value="triangle">Triangle Wave</option>
                <option value="sawtooth">Sawtooth Wave</option>
              </select>
            </div>
            
            <button
              onClick={() => triggerSonicEvent("frequency_modulation")}
              className="w-full bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded transition-colors text-white"
            >
              Modulate Frequency
            </button>
          </div>
        </div>
        
        {/* Harmonic Series */}
        <div className="bg-gradient-to-br from-indigo-900/30 to-purple-900/30 border border-indigo-600/30 rounded-lg p-4">
          <h3 className="text-lg font-bold text-indigo-300 mb-3">Harmonic Series</h3>
          
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {harmonicFrequencies.map(({ harmonic: h, frequency: f, amplitude }) => (
              <div
                key={h}
                className={`flex items-center justify-between p-2 rounded ${
                  harmonic === h ? "bg-indigo-600/30" : "bg-gray-800/30"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setHarmonic(h)}
                    className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold ${
                      harmonic === h 
                        ? "border-indigo-400 bg-indigo-600 text-white" 
                        : "border-gray-600 text-gray-400 hover:border-indigo-400"
                    }`}
                  >
                    {h}
                  </button>
                  <div>
                    <div className="text-sm text-white">{f.toFixed(1)} Hz</div>
                    <div className="text-xs text-gray-400">
                      Amplitude: {(amplitude * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
                
                <div className={`w-16 h-2 rounded-full bg-gradient-to-r ${
                  h <= consciousnessLevel * 8 
                    ? "from-indigo-500 to-purple-500" 
                    : "from-gray-600 to-gray-700"
                }`} />
              </div>
            ))}
          </div>
          
          <button
            onClick={applyHarmonicResonance}
            className="w-full mt-4 bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded transition-colors text-white"
          >
            Apply Harmonic Resonance
          </button>
        </div>
      </div>
      
      {/* Visualization */}
      <div className="bg-black/50 border border-purple-600/30 rounded-lg p-4">
        <h3 className="text-lg font-bold text-purple-300 mb-3">Wave Visualization</h3>
        
        <div className="relative h-32 bg-gray-900/50 rounded overflow-hidden">
          {/* Placeholder wave visualization */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex space-x-1">
              {Array.from({ length: 50 }, (_, i) => (
                <div
                  key={i}
                  className="w-1 bg-gradient-to-t from-purple-600 to-indigo-500 rounded"
                  style={{
                    height: `${50 + 30 * Math.sin((i * frequency * harmonic) / 100)}%`,
                    opacity: 0.3 + 0.7 * Math.sin((i * frequency * harmonic) / 100)
                  }}
                />
              ))}
            </div>
          </div>
          
          <div className="absolute bottom-2 left-2 text-xs text-gray-400">
            {waveform} • {frequency}Hz • H{harmonic} • {(consciousnessLevel * 100).toFixed(0)}% consciousness
          </div>
        </div>
      </div>
      
      {/* Sonic Events Log */}
      <div className="bg-gray-900/50 border border-gray-600/30 rounded-lg p-4">
        <h3 className="text-lg font-bold text-gray-300 mb-3">Recent Sonic Events</h3>
        
        <div className="space-y-1 text-sm font-mono text-gray-400 max-h-32 overflow-y-auto">
          <div>[{new Date().toLocaleTimeString()}] Ship-AI harmony matrices calibrated</div>
          <div>[{new Date().toLocaleTimeString()}] Consciousness resonance detected at {frequency}Hz</div>
          <div>[{new Date().toLocaleTimeString()}] Harmonic series expanded to {availableHarmonics} overtones</div>
          <div>[{new Date().toLocaleTimeString()}] Colony efficiency boosted by sonic enhancement</div>
        </div>
      </div>
    </div>
  );
}