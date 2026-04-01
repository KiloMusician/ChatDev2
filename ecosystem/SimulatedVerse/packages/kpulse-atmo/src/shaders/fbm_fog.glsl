#version 300 es
precision highp float;
out vec4 fragColor;
in vec2 uv;

uniform float iTime;
uniform vec2 iResolution;
uniform float atmoDensity;
uniform vec2 wind;
uniform float ionization, heat, gravLens, threat, serenity, anomaly;

// Hash function for noise generation
float hash(vec2 p) { 
  return fract(sin(dot(p, vec2(41.3, 289.1))) * 43758.5453); 
}

// Simple noise function
float noise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  float a = hash(i), b = hash(i + vec2(1, 0)), c = hash(i + vec2(0, 1)), d = hash(i + vec2(1, 1));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

// Fractal Brownian Motion for atmospheric effects
float fbm(vec2 p) {
  float s = 0.0, a = 0.5;
  for (int i = 0; i < 5; i++) { 
    s += a * noise(p); 
    p *= 2.02; 
    a *= 0.52; 
  }
  return s;
}

// Simple tone mapping
vec3 tonemap(vec3 c) { 
  return c / (1.0 + c); 
}

void main() {
  vec2 p = (uv * 2.0 - 1.0);
  p.x *= iResolution.x / iResolution.y;

  // Gravitational lens shimmer effect
  float lens = gravLens * 0.2 * sin(3.0 * p.y + iTime * 0.6);
  p += lens * 0.1;

  // Wind-advected fog using FBM
  vec2 flow = vec2(wind.x, wind.y) * iTime * 0.15;
  float fogBase = fbm(uv * 3.0 + flow);
  float fogDensity = atmoDensity * 1.6;
  
  // Add turbulence based on threat level
  fogBase += threat * 0.3 * fbm(uv * 8.0 + flow * 2.0);
  
  float fog = fogBase * fogDensity;

  // Ion arcs during storms and high ionization
  float arcPattern = sin(10.0 * uv.y + iTime * 4.0 + fbm(uv * 8.0)) * 0.5 + 0.5;
  float arcs = smoothstep(0.6, 1.0, arcPattern) * ionization * 0.8;
  
  // Add horizontal lightning bolts
  float lightning = smoothstep(0.95, 1.0, sin(50.0 * uv.x + iTime * 8.0)) * ionization * 0.6;
  arcs = max(arcs, lightning);

  // Warp ripples from anomalies
  float ripplePhase = 12.0 * length(p) - iTime * 2.0 + fbm(p * 5.0);
  float ripple = sin(ripplePhase) * anomaly * 0.4;
  
  // Add spiral distortion for anomalies
  if (anomaly > 0.1) {
    float angle = atan(p.y, p.x) + anomaly * iTime * 0.5;
    float spiral = sin(8.0 * angle + 4.0 * length(p)) * anomaly * 0.3;
    ripple += spiral;
  }

  // Heat haze effect
  float hazePattern = fbm(uv * 12.0 + vec2(iTime * 0.8, -iTime * 0.5));
  float haze = heat * 0.3 * hazePattern;

  // Color grading based on mood and conditions
  vec3 coldTone = vec3(0.25, 0.35, 0.55);  // Blue-gray
  vec3 warmTone = vec3(0.9, 0.55, 0.25);   // Orange-red
  vec3 sereneTone = vec3(0.75, 0.9, 1.2);  // Bright blue-white
  vec3 threatTone = vec3(1.2, 0.4, 0.3);   // Danger red
  
  // Blend between cold and warm based on heat
  vec3 baseTone = mix(coldTone, warmTone, heat);
  
  // Blend with serenity (peaceful blue-white)
  baseTone = mix(baseTone, sereneTone, serenity * 0.7);
  
  // Add threat coloring (red tint)
  baseTone = mix(baseTone, threatTone, threat * 0.5);

  // Combine all atmospheric effects
  float totalFog = clamp(fog + arcs + abs(ripple), 0.0, 1.0);
  
  // Calculate final color
  vec3 color = baseTone * (0.25 + 0.9 * totalFog);
  
  // Add heat haze as orange glow
  color += haze * vec3(0.8, 0.4, 0.2);
  
  // Add lens shimmer
  color += lens * vec3(0.6, 0.8, 1.0);
  
  // Boost intensity during high threat
  color *= 1.0 + 0.35 * threat;
  
  // Add atmospheric scattering effect
  float altitude = 1.0 - uv.y;
  color += altitude * 0.1 * serenity * vec3(0.5, 0.7, 1.0);

  // Apply tone mapping and output
  color = tonemap(color);
  
  // Alpha channel for layering - more opaque during high atmospheric activity
  float alpha = clamp(totalFog * 0.85 + lens * 0.3, 0.0, 0.9);
  
  fragColor = vec4(color, alpha);
}