// @vitest-environment node
import { afterEach, describe, expect, it } from 'vitest';
import { execFile } from 'node:child_process';
import { existsSync, readFileSync, unlinkSync } from 'node:fs';
import { join } from 'node:path';
import { promisify } from 'node:util';

const stateDir = join(process.cwd(), 'state');
const resultPath = join(stateDir, 'rehydration_harness_result.json');
const errorPath = join(stateDir, 'rehydration_harness_error.json');
const execFileAsync = promisify(execFile);
const tsxCli = join(process.cwd(), 'node_modules', 'tsx', 'dist', 'cli.mjs');
describe('Rehydration harness integration', () => {
  afterEach(() => {
    if (existsSync(resultPath)) {
      unlinkSync(resultPath);
    }
    if (existsSync(errorPath)) {
      unlinkSync(errorPath);
    }
  });

  it('rehydrates the deterministic dump successfully', async () => {
    await execFileAsync(process.execPath, [tsxCli, 'server/utils/rehydration_harness.ts'], {
      cwd: process.cwd(),
      env: {
        ...process.env,
        NODE_ENV: 'test'
      },
      stdio: 'inherit'
    });

    expect(existsSync(resultPath)).toBe(true);
    const result = JSON.parse(readFileSync(resultPath, 'utf8'));
    expect(result.circuitFound).toBe(true);
    expect(result.gatesWithOperation).toBe(result.totalGates);
  });
});
