module.exports = function setupPingEndpoint(app) {
  app.get('/ping', (req, res) => {
    res.send('pong');
  });
};
