export type Ability = {
  id: string;          // e.g., ability:prompt_evolution
  run: (args:any)=>Promise<any>|any;
  desc?: string;
};

export type Agent = {
  id: string;          // "mladenc", "raven", "librarian", "artificer", "alchemist", "protagonist", "culture-ship"
  abilities: Record<string, Ability>;
  speakAs?: string;    // default "agent-id"
};

export const Agents: Record<string, Agent> = {
  skeptic: { id:"skeptic", abilities:{} },
  raven:   { id:"raven",   abilities:{} },
  "mladenc": { id:"mladenc", abilities:{} },
  librarian: { id:"librarian", abilities:{} },
  artificer: { id:"artificer", abilities:{} },
  alchemist: { id:"alchemist", abilities:{} },
  protagonist:{ id:"protagonist", abilities:{} },
  "culture-ship": { id:"culture-ship", abilities:{} }
};