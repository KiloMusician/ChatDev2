import seedrandom from "seedrandom";
export const rng = seedrandom("ΞNuSyQ");
export const rand = ()=> rng.quick();
export const pick = <T>(a:T[]) => a[(rand()*a.length)|0];