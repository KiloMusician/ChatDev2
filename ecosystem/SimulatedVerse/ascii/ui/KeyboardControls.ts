import { bus } from "../core/Bus";

export class KeyboardControls {
  private handlers = new Map<string, () => void>();
  
  constructor() {
    this.handlers.set("F1", () => bus.emit("ascii/toggleHUD"));
    this.handlers.set("F2", () => bus.emit("ascii/toggleBackend"));
    this.handlers.set("F3", () => bus.emit("ascii/switchVantage"));
    this.handlers.set("KeyP", () => bus.emit("ascii/pause"));
    this.handlers.set("Escape", () => bus.emit("ascii/pause"));
    
    document.addEventListener("keydown", this.handleKeyDown);
  }
  
  private handleKeyDown = (e: KeyboardEvent) => {
    const handler = this.handlers.get(e.code) || this.handlers.get(e.key);
    if (handler) {
      e.preventDefault();
      handler();
    }
  }
  
  destroy() {
    document.removeEventListener("keydown", this.handleKeyDown);
  }
}