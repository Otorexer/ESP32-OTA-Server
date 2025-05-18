const express = require('express');
const path = require('path');
const fs = require('fs');

module.exports = function setupFrontend(app, frontendPath) {
  if (!fs.existsSync(frontendPath)) {
    fs.mkdirSync(frontendPath, { recursive: true });
    console.log('✅ "frontend" folder created automatically.');
  } else {
    console.log('📂 "frontend" folder already exists.');
  }

  app.use(express.static(frontendPath));

  app.get('/', (req, res) => {
    res.sendFile(path.join(frontendPath, 'index.html'));
  });
};
