import { VFXDirector } from "./packages/kpulse-atmo/src/director/VFXDirector.ts";

const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const clamp = (a: number, b: number, x: number) => Math.max(a, Math.min(b, x));
const ease01 = (x: number) => clamp01(1 - Math.exp(-3 * clamp01(x)));

export function bindMappings(director: VFXDirector, bus: any, stateSource: () => any) {
  // Periodic polling for slow-changing fields (weather, resources, colony state)
  const pollInterval = setInterval(() => {
    try {
      const state = stateSource();
      
      // Map weather state to atmospheric controls
      const weatherControls: any = {};
      
      if (state.weather) {
        // Wind from weather
        if (state.weather.current === 'windy' || state.weather.current === 'storm') {
          weatherControls.windX = clamp(-1, 1, (Math.sin(performance.now() * 0.001) * 0.3));
          weatherControls.windY = clamp(-1, 1, (Math.cos(performance.now() * 0.0015) * 0.2));
        }
        
        // Atmospheric density from weather type
        const densityMap = {
          'clear': 0.05,
          'overcast': 0.25,
          'windy': 0.15,
          'rain': 0.45,
          'storm': 0.7
        };
        weatherControls.atmoDensity = densityMap[state.weather.current as keyof typeof densityMap] || 0.15;
        
        // Ionization for storms
        if (state.weather.current === 'storm') {
          weatherControls.ionization = 0.6 + 0.3 * Math.sin(performance.now() * 0.003);
        }
      }
      
      // Map colony state
      if (state.colony) {
        // Power state affects overall lighting and stability
        const powerHealth = state.colony.grid ? 
          state.colony.grid.current_wh / state.colony.grid.capacity_wh : 1.0;
        
        if (powerHealth < 0.3) {
          weatherControls.threat = Math.max(weatherControls.threat || 0, 0.4);
        }
        
        // Shelter quality affects environmental protection
        if (state.colony.shelter_quality < 30) {
          weatherControls.atmoDensity = Math.max(weatherControls.atmoDensity || 0, 0.3);
        }
        
        // Morale affects serenity
        if (state.colony.morale) {
          weatherControls.serenity = clamp01(state.colony.morale / 100 * 0.6);
        }
      }
      
      // Map tension from storyteller
      if (typeof state.tension === 'number') {
        weatherControls.threat = ease01(state.tension);
        weatherControls.serenity = clamp01(0.8 - state.tension);
      }
      
      // Map anomaly intensity
      if (state.anomaly_intensity) {
        weatherControls.anomaly = ease01(state.anomaly_intensity);
        weatherControls.gravLens = clamp01(state.anomaly_intensity * 0.3);
      }
      
      director.setControls(weatherControls);
    } catch (error) {
      console.warn('Atmosphere mapping error:', error);
    }
  }, 200);

  // Fast reactive events from AST and game systems
  if (bus && typeof bus.on === 'function') {
    bus.on("ast:event", (event: any) => {
      const controls: any = {};
      
      switch (event.type) {
        case "atmospheric":
          controls.serenity = 0.1;
          controls.anomaly = 0.3;
          break;
          
        case "technical":
          controls.threat = 0.4;
          controls.ionization = 0.2;
          break;
          
        case "weather":
          if (event.name === "Severe Storm Cell") {
            controls.atmoDensity = 0.8;
            controls.ionization = 0.7;
            controls.windX = 0.6;
            controls.threat = 0.5;
          }
          break;
          
        case "hostile":
          controls.threat = 0.8;
          controls.serenity = 0.0;
          controls.ionization = 0.3;
          break;
          
        case "crisis":
          controls.threat = 1.0;
          controls.anomaly = 0.9;
          controls.gravLens = 0.4;
          controls.atmoDensity = 0.6;
          break;
          
        case "opportunity":
          controls.serenity = 0.7;
          controls.gravLens = 0.2;
          break;
      }
      
      if (Object.keys(controls).length > 0) {
        director.setControls(controls);
        
        // Auto-decay dramatic effects after their duration
        setTimeout(() => {
          const decayControls: any = {};
          if (controls.threat > 0.5) decayControls.threat = 0.2;
          if (controls.ionization > 0.3) decayControls.ionization = 0.1;
          if (controls.anomaly > 0.5) decayControls.anomaly = 0.1;
          director.setControls(decayControls);
        }, 5000);
      }
    });

    bus.on("combat:phase", (phase: { phase: string, intensity: number }) => {
      director.setControls({
        threat: ease01(phase.intensity),
        serenity: 0,
        ionization: phase.intensity * 0.4
      });
    });

    bus.on("weather:storm", (storm: { type: "ion" | "dust" | "rain", power: number }) => {
      const controls: any = {
        atmoDensity: clamp01(0.2 + 0.5 * storm.power)
      };
      
      if (storm.type === "ion") {
        controls.ionization = ease01(storm.power);
        controls.gravLens = storm.power * 0.2;
      }
      
      director.setControls(controls);
    });

    bus.on("narrative:beat", (beat: { mood: "wonder" | "tension" | "melancholy" | "triumph" }) => {
      const moodMappings = {
        wonder: { serenity: 0.7, gravLens: 0.2, anomaly: 0.3, threat: 0.1 },
        tension: { serenity: 0.0, threat: 0.8, ionization: 0.3 },
        melancholy: { serenity: 0.3, threat: 0.1, atmoDensity: 0.35 },
        triumph: { serenity: 0.9, threat: 0.0, gravLens: 0.15, anomaly: 0.1 }
      };
      
      const mood = moodMappings[beat.mood];
      if (mood) {
        director.setControls(mood);
      }
    });
  }

  // Cleanup function
  return () => {
    clearInterval(pollInterval);
  };
}