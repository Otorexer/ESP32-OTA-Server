const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
const PORT = 3000;
const publicDir = path.join(__dirname, 'public');
const frontendPath = path.join(__dirname, 'frontend');

require('./endpoints/frontend')(app, frontendPath);
require('./endpoints/esp32')(app, publicDir);
require('./endpoints/ping')(app);

const server = http.createServer(app);
const { wss } = require('./endpoints/websocket')(server);

// Control endpoints now modular:
require('./endpoints/control')(app, wss);

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server running at http://0.0.0.0:${PORT}`);
  console.log(`🌐 ESP32 OTA endpoint: http://<your-ip>:${PORT}/esp32/files`);
});
