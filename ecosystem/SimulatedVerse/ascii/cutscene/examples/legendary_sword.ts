import { Director } from "../Director";
import { Buffer2D } from "../../core/Buffer2D";

export const legendarySword = ()=> new Director([
  { t: 0.0, text: "…the final strike…" },
  { t: 0.4, text: "…sparks fly…" },
  { t: 0.8, text: "★ LEGENDARY BLADE FORGED ★" }
], ()=>{/* on done */});