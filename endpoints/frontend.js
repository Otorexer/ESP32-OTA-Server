// endpoints/frontend.js

const express = require('express');
const path = require('path');
const fs = require('fs');

module.exports = function setupFrontend(app, frontendPath) {
  // Ensure frontend folder exists
  if (!fs.existsSync(frontendPath)) {
    fs.mkdirSync(frontendPath, { recursive: true });
    console.log('✅ "frontend" folder created automatically.');
  } else {
    console.log('📂 "frontend" folder already exists.');
  }

  // Serve static frontend files
  app.use(express.static(frontendPath));

  // Serve index.html at root
  app.get('/', (req, res) => {
    res.sendFile(path.join(frontendPath, 'index.html'));
  });
};
