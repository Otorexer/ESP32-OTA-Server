// endpoints/control.js

module.exports = function setupControlEndpoints(app, wss) {
  // Reset all ESP32 clients
  app.post('/reset-all', (req, res) => {
    wss.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ reset: true }));
      }
    });
    console.log('🌀 Reset command sent to all clients.');
    res.send('Reset command sent.');
  });

  // Set color and intensity
  app.post('/led/:rgb/:intensity', (req, res) => {
    const rgb = req.params.rgb;
    const intensity = req.params.intensity;
    wss.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ color: rgb, intensity }));
      }
    });
    console.log(`🎨 Color sent: ${rgb} Intensity: ${intensity}`);
    res.send(`Color ${rgb} (intensity ${intensity}%) sent to all clients.`);
  });

  // Set color (default intensity 100)
  app.post('/led/:rgb', (req, res) => {
    const rgb = req.params.rgb;
    const intensity = '100';
    wss.clients.forEach(client => {
      if (client.readyState === 1) {
        client.send(JSON.stringify({ color: rgb, intensity }));
      }
    });
    console.log(`🎨 Color sent: ${rgb} Intensity: ${intensity}`);
    res.send(`Color ${rgb} (intensity ${intensity}%) sent to all clients.`);
  });
};
