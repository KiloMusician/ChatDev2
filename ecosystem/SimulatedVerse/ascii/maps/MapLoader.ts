export type Tile = "#"|"."|"+"|" ";
export type MapData = { w:number; h:number; tiles: Tile[] };

export function blank(w:number,h:number):MapData{
  return { w,h,tiles: Array(w*h).fill(".") as Tile[] };
}