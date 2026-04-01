export class FullscreenShaderLayer {
  private gl: WebGL2RenderingContext;
  private prog: WebGLProgram;
  private uni: Record<string, WebGLUniformLocation>;
  private vao: WebGLVertexArrayObject | null;

  constructor(private canvas: HTMLCanvasElement, fragSrc: string) {
    const gl = canvas.getContext("webgl2", { 
      alpha: true, 
      antialias: false,
      depth: false,
      stencil: false
    });
    
    if (!gl) {
      throw new Error("WebGL2 not supported");
    }
    
    this.gl = gl;
    
    const vs = `#version 300 es
    precision highp float;
    const vec2 verts[3] = vec2[3](vec2(-1,-1), vec2(3,-1), vec2(-1,3));
    out vec2 uv;
    void main() {
      uv = verts[gl_VertexID] * 0.5 + 0.5;
      gl_Position = vec4(verts[gl_VertexID], 0, 1);
    }`;
    
    this.prog = this.compileProgram(vs, fragSrc);
    this.uni = {
      iTime: gl.getUniformLocation(this.prog, "iTime")!,
      iResolution: gl.getUniformLocation(this.prog, "iResolution")!,
      atmoDensity: gl.getUniformLocation(this.prog, "atmoDensity")!,
      wind: gl.getUniformLocation(this.prog, "wind")!,
      ionization: gl.getUniformLocation(this.prog, "ionization")!,
      heat: gl.getUniformLocation(this.prog, "heat")!,
      gravLens: gl.getUniformLocation(this.prog, "gravLens")!,
      threat: gl.getUniformLocation(this.prog, "threat")!,
      serenity: gl.getUniformLocation(this.prog, "serenity")!,
      anomaly: gl.getUniformLocation(this.prog, "anomaly")!,
    };
    
    this.vao = gl.createVertexArray();
    
    // Enable blending for atmospheric layering
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  }

  private compileProgram(vsSrc: string, fsSrc: string): WebGLProgram {
    const gl = this.gl;
    
    const vs = gl.createShader(gl.VERTEX_SHADER)!;
    gl.shaderSource(vs, vsSrc);
    gl.compileShader(vs);
    
    if (!gl.getShaderParameter(vs, gl.COMPILE_STATUS)) {
      throw new Error("Vertex shader compile error: " + gl.getShaderInfoLog(vs));
    }
    
    const fs = gl.createShader(gl.FRAGMENT_SHADER)!;
    gl.shaderSource(fs, fsSrc);
    gl.compileShader(fs);
    
    if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
      throw new Error("Fragment shader compile error: " + gl.getShaderInfoLog(fs));
    }
    
    const prog = gl.createProgram()!;
    gl.attachShader(prog, vs);
    gl.attachShader(prog, fs);
    gl.linkProgram(prog);
    
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      throw new Error("Program link error: " + gl.getProgramInfoLog(prog));
    }
    
    return prog;
  }

  update(dt: number, controls: any) {
    // Controls are handled globally via __ATMO_CTRLS
  }

  draw() {
    const gl = this.gl;
    const w = this.canvas.clientWidth;
    const h = this.canvas.clientHeight;
    
    // Resize canvas if needed
    if (this.canvas.width !== w || this.canvas.height !== h) {
      this.canvas.width = w;
      this.canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
    
    gl.useProgram(this.prog);
    
    // Time uniform
    gl.uniform1f(this.uni.iTime, performance.now() / 1000);
    gl.uniform2f(this.uni.iResolution, this.canvas.width, this.canvas.height);
    
    // Get controls from global state
    const getControl = (name: string) => (window as any).__ATMO_CTRLS?.[name] ?? 0;
    
    gl.uniform1f(this.uni.atmoDensity, getControl("atmoDensity"));
    gl.uniform2f(this.uni.wind, getControl("windX"), getControl("windY"));
    gl.uniform1f(this.uni.ionization, getControl("ionization"));
    gl.uniform1f(this.uni.heat, getControl("heat"));
    gl.uniform1f(this.uni.gravLens, getControl("gravLens"));
    gl.uniform1f(this.uni.threat, getControl("threat"));
    gl.uniform1f(this.uni.serenity, getControl("serenity"));
    gl.uniform1f(this.uni.anomaly, getControl("anomaly"));
    
    // Draw fullscreen triangle
    gl.bindVertexArray(this.vao);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  dispose() {
    const gl = this.gl;
    if (this.prog) gl.deleteProgram(this.prog);
    if (this.vao) gl.deleteVertexArray(this.vao);
  }
}