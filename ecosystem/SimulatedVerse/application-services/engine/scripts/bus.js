#!/usr/bin/env node

/**
 * Standalone Event Bus Server
 * Can be run independently for testing or as a microservice
 */

import { eventBus } from '../src/bus.js';

console.log('🚌 KPulse Event Bus Server');
console.log(`WebSocket server running on ws://localhost:${process.env.BUS_PORT || 7070}`);
console.log('Press Ctrl+C to stop');

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down event bus...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n🛑 Event bus terminated');
  process.exit(0);
});

// Keep the process alive
setInterval(() => {
  const connections = eventBus.getConnections();
  if (connections.length > 0) {
    console.log(`💓 Heartbeat - ${connections.length} active connections`);
  }
}, 30000); // Every 30 seconds