// Example Node.js producer that dual-writes: append JSONL and ask Python to ingest
// This example shows a minimal approach: append the JSONL locally and spawn
// a Python worker to ingest the file (or the new line). For production, prefer
// using the Python dual_write helper directly or a small RPC interface.

const fs = require('fs');
const { spawn } = require('child_process');
const path = require('path');

function appendJsonl(jsonlPath, obj) {
  fs.mkdirSync(path.dirname(jsonlPath), { recursive: true });
  fs.appendFileSync(jsonlPath, JSON.stringify(obj) + '\n', { encoding: 'utf8' });
}

function triggerIngest(pyModule, dbPath, inputPath) {
  const py = spawn('python', ['-m', pyModule, '--db-path', dbPath, '--input', inputPath]);
  py.stdout.on('data', (d) => process.stdout.write(d));
  py.stderr.on('data', (d) => process.stderr.write(d));
  py.on('close', (code) => console.log('ingest exited', code));
}

// Usage example
if (require.main === module) {
  const jsonl = process.argv[2] || 'SimulatedVerse/state/shared_cultivation/quest_log.jsonl';
  const db = process.argv[3] || 'data/state.duckdb';

  const obj = {
    timestamp: new Date().toISOString(),
    event: 'add_quest',
    details: {
      id: 'node-1',
      title: 'Node-created task',
      description: 'demo',
      questline: 'General',
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      dependencies: [],
      tags: [],
    },
  };

  appendJsonl(jsonl, obj);
  // spawn the Python ingester to pick up new data
  triggerIngest('src.duckdb_integration.ingest', db, jsonl);
}
