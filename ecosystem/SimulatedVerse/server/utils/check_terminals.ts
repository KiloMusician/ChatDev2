import fs from 'fs';
import path from 'path';

const cwd = process.cwd();
const candidates = [
  'terminals/preset-terminal.sh',
  'terminals/preset-terminal.ps1',
  'scripts/terminal_presets.js',
  'server/utils/terminal_presets.ts',
  'scripts/preset_terminals.sh'
];

let missing: string[] = [];
for (const c of candidates) {
  const p = path.join(cwd, c);
  if (!fs.existsSync(p)) missing.push(c);
}

if (missing.length > 0) {
  console.error('[check_terminals] Missing preset terminal files:', missing.join(', '));
  process.exit(2);
}

console.log('[check_terminals] All preset terminal candidate files present (or none required).');
process.exit(0);
