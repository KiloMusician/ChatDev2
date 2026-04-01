import { VFXDirector } from "./packages/kpulse-atmo/src/director/VFXDirector.ts";
import { bindMappings } from "./packages/kpulse-atmo/src/director/mappings.ts";
import { FullscreenShaderLayer } from "./packages/kpulse-atmo/src/layers/FullscreenShaderLayer.ts";
import { Particles2DLayer } from "./packages/kpulse-atmo/src/layers/Particles2DLayer.ts";

// Import shader source
const fogFragmentShader = `#version 300 es
precision highp float;
out vec4 fragColor;
in vec2 uv;

uniform float iTime;
uniform vec2 iResolution;
uniform float atmoDensity;
uniform vec2 wind;
uniform float ionization, heat, gravLens, threat, serenity, anomaly;

float hash(vec2 p) { 
  return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); 
}

float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  float a = hash(i), b = hash(i + vec2(1, 0)), c = hash(i + vec2(0, 1)), d = hash(i + vec2(1, 1));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

float fbm(vec2 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { 
    s += a * noise(p); 
    p *= 2.02; 
    a *= 0.52; 
  }
  return s;
}

vec3 tonemap(vec3 c) { 
  return c / (1.0 + c); 
}

void main() {
  vec2 p = (uv * 2.0 - 1.0);
  p.x *= iResolution.x / iResolution.y;

  float lens = gravLens * 0.2 * sin(3.0 * p.y + iTime * 0.6);
  p += lens * 0.1;

  vec2 flow = vec2(wind.x, wind.y) * iTime * 0.15;
  float fogBase = fbm(uv * 3.0 + flow);
  float fogDensity = atmoDensity * 1.6;
  
  fogBase += threat * 0.3 * fbm(uv * 8.0 + flow * 2.0);
  float fog = fogBase * fogDensity;

  float arcPattern = sin(10.0 * uv.y + iTime * 4.0 + fbm(uv * 8.0)) * 0.5 + 0.5;
  float arcs = smoothstep(0.6, 1.0, arcPattern) * ionization * 0.8;
  
  float lightning = smoothstep(0.95, 1.0, sin(50.0 * uv.x + iTime * 8.0)) * ionization * 0.6;
  arcs = max(arcs, lightning);

  float ripplePhase = 12.0 * length(p) - iTime * 2.0 + fbm(p * 5.0);
  float ripple = sin(ripplePhase) * anomaly * 0.4;
  
  if (anomaly > 0.1) {
    float angle = atan(p.y, p.x) + anomaly * iTime * 0.5;
    float spiral = sin(8.0 * angle + 4.0 * length(p)) * anomaly * 0.3;
    ripple += spiral;
  }

  float hazePattern = fbm(uv * 12.0 + vec2(iTime * 0.8, -iTime * 0.5));
  float haze = heat * 0.3 * hazePattern;

  vec3 coldTone = vec3(0.25, 0.35, 0.55);
  vec3 warmTone = vec3(0.9, 0.55, 0.25);
  vec3 sereneTone = vec3(0.75, 0.9, 1.2);
  vec3 threatTone = vec3(1.2, 0.4, 0.3);
  
  vec3 baseTone = mix(coldTone, warmTone, heat);
  baseTone = mix(baseTone, sereneTone, serenity * 0.7);
  baseTone = mix(baseTone, threatTone, threat * 0.5);

  float totalFog = clamp(fog + arcs + abs(ripple), 0.0, 1.0);
  
  vec3 color = baseTone * (0.25 + 0.9 * totalFog);
  color += haze * vec3(0.8, 0.4, 0.2);
  color += lens * vec3(0.6, 0.8, 1.0);
  color *= 1.0 + 0.35 * threat;
  
  float altitude = 1.0 - uv.y;
  color += altitude * 0.1 * serenity * vec3(0.5, 0.7, 1.0);

  color = tonemap(color);
  float alpha = clamp(totalFog * 0.85 + lens * 0.3, 0.0, 0.9);
  
  fragColor = vec4(color, alpha);
}`;

export interface AtmosphereOptions {
  mount: HTMLElement;
  bus?: any;
  stateSource: () => any;
  particleCount?: number;
  enableShaders?: boolean;
}

export function bootstrapAtmosphere(options: AtmosphereOptions) {
  const { mount, bus, stateSource, particleCount = 180, enableShaders = true } = options;
  
  // Create canvas layers
  const shaderCanvas = document.createElement("canvas");
  shaderCanvas.className = "atmo-canvas atmo-shader";
  
  const particleCanvas = document.createElement("canvas");
  particleCanvas.className = "atmo-canvas atmo-particles";
  
  // Apply styles
  const style = document.createElement("style");
  style.textContent = `
    .atmo-root {
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 0;
    }
    .atmo-canvas {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }
    .atmo-shader {
      z-index: 1;
    }
    .atmo-particles {
      z-index: 2;
    }
  `;
  document.head.appendChild(style);
  
  // Add canvases to mount
  mount.appendChild(shaderCanvas);
  mount.appendChild(particleCanvas);
  
  // Ensure mount has proper styling
  if (!mount.classList.contains('atmo-root')) {
    mount.classList.add('atmo-root');
  }

  // Initialize VFX Director
  const director = new VFXDirector();
  
  try {
    // Initialize layers
    let fogLayer: FullscreenShaderLayer | null = null;
    let dustLayer: Particles2DLayer | null = null;
    
    if (enableShaders) {
      try {
        fogLayer = new FullscreenShaderLayer(shaderCanvas, fogFragmentShader);
        console.log("Atmospheric shader layer initialized");
      } catch (error) {
        console.warn("WebGL2 shader layer failed, falling back to particles only:", error);
        shaderCanvas.style.display = 'none';
      }
    }
    
    dustLayer = new Particles2DLayer(particleCanvas, particleCount);
    console.log("Atmospheric particle layer initialized");
    
    // Add layers to director
    director.addLayer({
      update(dt, controls) {
        // Update global controls for shader access
        (window as any).__ATMO_CTRLS = controls;
        
        if (fogLayer) fogLayer.update(dt, controls);
        if (dustLayer) dustLayer.update(dt, controls);
      },
      draw() {
        if (fogLayer) fogLayer.draw();
        if (dustLayer) dustLayer.draw();
      }
    });

    // Bind to game state and events
    let cleanup: (() => void) | undefined;
    try {
      cleanup = bindMappings(director, bus, stateSource);
      console.log("Atmospheric mappings bound to game state");
    } catch (error) {
      console.warn("Failed to bind atmospheric mappings:", error);
    }

    // Start the director
    director.start();
    console.log("Atmospheric system started");

    // Return cleanup function
    return () => {
      director.stop();
      
      if (cleanup) cleanup();
      
      if (fogLayer) fogLayer.dispose();
      if (dustLayer) dustLayer.dispose();
      
      mount.removeChild(shaderCanvas);
      mount.removeChild(particleCanvas);
      
      if (style.parentNode) {
        style.parentNode.removeChild(style);
      }
      
      // Clean up global state
      delete (window as any).__ATMO_CTRLS;
      
      console.log("Atmospheric system disposed");
    };
    
  } catch (error) {
    console.error("Failed to initialize atmospheric system:", error);
    
    // Cleanup on failure
    if (shaderCanvas.parentNode) shaderCanvas.parentNode.removeChild(shaderCanvas);
    if (particleCanvas.parentNode) particleCanvas.parentNode.removeChild(particleCanvas);
    
    // Return empty cleanup function
    return () => {};
  }
}

// Re-export key types and classes for external use
export { VFXDirector } from "./packages/kpulse-atmo/src/director/VFXDirector.ts";
export { FullscreenShaderLayer } from "./packages/kpulse-atmo/src/layers/FullscreenShaderLayer.ts";
export { Particles2DLayer } from "./packages/kpulse-atmo/src/layers/Particles2DLayer.ts";