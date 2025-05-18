const WebSocket = require('ws');

module.exports = function setupWebsocket(server) {
  const wss = new WebSocket.Server({ server });

  wss.on('connection', ws => {
    console.log('⚡ WS client connected');

    ws.on('message', message => {
      console.log('📨 WS received:', message.toString());
    });

    ws.on('close', () => console.log('🛑 WS client disconnected'));
  });

  return {
    wss
  };
};
