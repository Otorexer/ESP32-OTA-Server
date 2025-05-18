module.exports = function setupControlEndpoints(app, wss) {
  app.post('/reset-all', (req, res) => {
    wss.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ reset: true }));
      }
    });
    console.log('🌀 Reset command sent to all clients.');
    res.send('Reset command sent.');
  });
};
