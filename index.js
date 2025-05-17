const express = require('express');
const path = require('path');
const fs = require('fs');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const PORT = 3000;
const publicDir = path.join(__dirname, 'public');

// Create 'public' folder if it doesn't exist
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
  console.log('✅ "public" folder created automatically.');
} else {
  console.log('📂 "public" folder already exists.');
}

// Serve static files
app.use(express.static(publicDir));

// List available files
app.get('/files', (req, res) => {
  fs.readdir(publicDir, (err, files) => {
    if (err) return res.status(500).json({ error: 'Cannot read directory.' });
    res.json(files);
  });
});

// Create HTTP and WebSocket server
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// When a client connects via WebSocket
wss.on('connection', ws => {
  console.log('⚡ WS client connected');
  ws.on('close', () => console.log('🛑 WS client disconnected'));
});

// Route to reset all ESP32 clients
app.post('/reset-all', (req, res) => {
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ reset: true }));
    }
  });
  console.log('🌀 Reset command sent to all clients.');
  res.send('Reset command sent.');
});

// Route: /led/:rgb/:intensity
app.post('/led/:rgb/:intensity', (req, res) => {
  const rgb = req.params.rgb; // '255,255,255'
  const intensity = req.params.intensity; // '100' (string)
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ color: rgb, intensity }));
    }
  });
  console.log(`🎨 Color sent: ${rgb} Intensity: ${intensity}`);
  res.send(`Color ${rgb} (intensity ${intensity}%) sent to all clients.`);
});

// Alternative route: only color (default intensity 100%)
app.post('/led/:rgb', (req, res) => {
  // If route already included intensity, this one does NOT run. Express uses the most specific route.
  const rgb = req.params.rgb;
  const intensity = '100';
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ color: rgb, intensity }));
    }
  });
  console.log(`🎨 Color sent: ${rgb} Intensity: ${intensity}`);
  res.send(`Color ${rgb} (intensity ${intensity}%) sent to all clients.`);
});

// Start server
server.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});
