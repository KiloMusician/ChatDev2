import { Buffer2D } from "./Buffer2D";

export interface Scene {
  id: string;
  tick(dt:number): void;
  draw(buf: Buffer2D): void;
}