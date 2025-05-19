// =======================
// 1. Imports and Setup
// =======================

// Core/standard libraries
const path = require('path');
const http = require('http');

// Third-party libraries
const express = require('express');

// =======================
// 2. Configuration
// =======================

const PORT = 3000;

// =======================
// 3. Initialize Express
// =======================

const app = express();

// =======================
// 4. Mount Static and API Endpoints
// =======================

// Frontend static files and root index.html
require('./endpoints/frontend')(app);

// ESP32 OTA endpoints
require('./endpoints/esp32')(app);

// Simple health check endpoint
require('./endpoints/ping')(app);

// =======================
// 5. HTTP & WebSocket Setup
// =======================

// Create HTTP server
const server = http.createServer(app);

// WebSocket server (shared with HTTP)
const { wss } = require('./endpoints/websocket')(server);

// =======================
// 6. Custom Control Endpoints
// =======================

// Modular endpoints for ESP32 control commands
require('./endpoints/control')(app, wss);

// =======================
// 7. Start Server
// =======================

server.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Server running at http://0.0.0.0:${PORT}`);
  console.log(`🌐 ESP32 OTA endpoint: http://0.0.0.0:${PORT}/esp32/files`);
});
