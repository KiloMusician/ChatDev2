import { nanoid } from "nanoid";
export type Entity = string;
export type Position = { x:number; y:number };
export type Actor = { hp:number; glyph:string };
export type Resource = { kind:"energy"|"ore"|"food"; amount:number };

export const world = {
  pos: new Map<Entity, Position>(),
  act: new Map<Entity, Actor>(),
  res: new Map<Entity, Resource>(),
};

export const make = {
  actor(glyph="@", hp=10){ const e=nanoid(); world.act.set(e,{glyph,hp}); world.pos.set(e,{x:1,y:1}); return e; },
  resource(kind:Resource["kind"], amount=1, x=5, y=5){ const e=nanoid(); world.res.set(e,{kind,amount}); world.pos.set(e,{x,y}); return e; }
};