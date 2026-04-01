// packages/consciousness/storyteller.ts
// TypeScript re-export facade for the nurturing storyteller.
// The runtime implementation lives in storyteller.js (plain JS, no private keywords)
// so tsx/esm can load it without a SyntaxError when imported as a .js extension.

export { NurturingStoryteller, nurturingStoryteller } from './storyteller.js';
