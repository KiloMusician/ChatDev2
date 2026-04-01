const degradedMode = process.argv.includes('--degraded');

if (degradedMode) {
  console.warn('[Server] Starting degraded mode via minimal surface');
  await import('./minimal_server.js');
} else {
  await import('./full_server.js');
}
