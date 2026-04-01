const express = require('express');
const path = require('path');

const app = express();
const PORT = 5000;

// Basic middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'client')));

// Simple API route for testing
app.get('/api/test', (req, res) => {
  res.json({ message: 'CoreLink Foundation API Active', timestamp: new Date().toISOString() });
});

// Serve React app for all non-API routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'client', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌌 CoreLink Foundation Server running on http://0.0.0.0:${PORT}`);
});