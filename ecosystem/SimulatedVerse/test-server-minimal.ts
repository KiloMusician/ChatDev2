// Ultra-minimal test server
import express from 'express';

const app = express();
app.use(express.json());

app.get('/test', (req, res) => {
  res.json({ message: 'Server is alive!' });
});

const PORT = 5001;
const server = app.listen(PORT, () => {
  console.log(`✅ Test server listening on port ${PORT}`);
  console.log(`   Visit: http://localhost:${PORT}/test`);
});

server.on('error', (err) => {
  console.error('Server error:', err);
});

process.on('unhandledRejection', (reason) => {
  console.error('Unhandled rejection:', reason);
});

console.log('Script reached end - server should stay alive');
