const express = require('express');
const path = require('path');
const fs = require('fs');
const http = require('http');
const WebSocket = require('ws');
const app = express();
const PORT = 3000;
const publicDir = path.join(__dirname, 'public');

const frontendPath = path.join(__dirname, 'frontend');
app.use(express.static(frontendPath));

app.get('/', (req, res) => {
  res.sendFile(path.join(frontendPath, 'index.html'));
});



// Create 'public' folder if it doesn't exist
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
  console.log('✅ "public" folder created automatically.');
} else {
  console.log('📂 "public" folder already exists.');
}

// =============== ESP32 OTA API ===============

// List files for ESP32 OTA
app.get('/esp32/files', (req, res) => {
  fs.readdir(publicDir, (err, files) => {
    if (err) return res.status(500).json({ error: 'Cannot read directory.' });
    res.json(files);
  });
});

// Serve ESP32 OTA files (raw download)
app.get('/esp32/:filename', (req, res) => {
  const filename = req.params.filename;
  const filePath = path.join(publicDir, filename);
  // Extra: avoid serving non-files
  if (filename.includes('/') || filename.includes('\\')) {
    return res.status(400).send('Invalid filename.');
  }
  fs.access(filePath, fs.constants.R_OK, (err) => {
    if (err) return res.status(404).send('File not found.');
    res.sendFile(filePath);
  });
});

// ========== WebSocket and Other API ==========

// Serve static files for browser (if you want)
// app.use(express.static(publicDir)); // <-- comment this if you want only ESP32 API!

// WebSocket logic
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

let currentState = {
  color: "255,0,0",
  intensity: "100"
};

wss.on('connection', ws => {
  console.log('⚡ WS client connected');
  // Immediately send current state to the newly connected client
  ws.send(JSON.stringify(currentState));

  ws.on('message', (message) => {
    console.log('📨 WS received:', message.toString());
    try {
      const data = JSON.parse(message);
      let updated = false;
      if (data.color && typeof data.color === "string") {
        currentState.color = data.color;
        updated = true;
      }
      if (data.intensity && typeof data.intensity === "string") {
        currentState.intensity = data.intensity;
        updated = true;
      }
      // If state updated, broadcast to all clients (INCLUDING the sender!)
      if (updated) {
        wss.clients.forEach(client => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(currentState));
          }
        });
      }
    } catch {}
  });

  ws.on('close', () => console.log('🛑 WS client disconnected'));
});

// Reset all ESP32 clients
app.post('/reset-all', (req, res) => {
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ reset: true }));
    }
  });
  console.log('🌀 Reset command sent to all clients.');
  res.send('Reset command sent.');
});

// /led/:rgb/:intensity
app.post('/led/:rgb/:intensity', (req, res) => {
  const rgb = req.params.rgb;
  const intensity = req.params.intensity;
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(JSON.stringify({ color: rgb, intensity }));
    }
  });
  console.log(`🎨 Color sent: ${rgb} Intensity: ${intensity}`);
  res.send(`Color ${rgb} (intensity ${intensity}%) sent to all clients.`);
});

// /led/:rgb (default intensity 100%)
app.post('/led/:rgb', (req, res) => {
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

app.get('/ping', (req, res) => {
  res.send('pong');
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server running at http://0.0.0.0:${PORT}`);
  console.log(`🌐 ESP32 OTA endpoint: http://<your-ip>:${PORT}/esp32/files`);
});