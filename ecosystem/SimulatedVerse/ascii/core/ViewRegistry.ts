import { Scene } from "./Scene";

export type Vantage = "roguelike" | "builder" | "defense" | "visualizer" | "matrix";

export class ViewRegistry {
  private scenes = new Map<Vantage, Scene>();
  private currentVantage: Vantage = "roguelike";
  
  register(vantage: Vantage, scene: Scene) {
    this.scenes.set(vantage, scene);
  }
  
  switch(vantage: Vantage) {
    if (this.scenes.has(vantage)) {
      this.currentVantage = vantage;
    }
  }
  
  getCurrentScene(): Scene | undefined {
    return this.scenes.get(this.currentVantage);
  }
  
  cycle() {
    const vantages: Vantage[] = ["roguelike", "builder", "defense", "visualizer", "matrix"];
    const current = vantages.indexOf(this.currentVantage);
    const next = (current + 1) % vantages.length;
    this.currentVantage = vantages[next];
  }
}