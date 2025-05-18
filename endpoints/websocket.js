// endpoints/websocket.js

const WebSocket = require('ws');

module.exports = function setupWebsocket(server) {
  const wss = new WebSocket.Server({ server });

  // Shared state for all clients
  let currentState = {
    color: "255,0,0",
    intensity: "100"
  };

  wss.on('connection', ws => {
    console.log('⚡ WS client connected');
    ws.send(JSON.stringify(currentState));

    ws.on('message', message => {
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

  return {
    wss,
    getCurrentState: () => currentState
  };
};
