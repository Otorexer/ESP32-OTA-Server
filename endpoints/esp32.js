const path = require('path');
const fs = require('fs');

module.exports = function setupEsp32Endpoints(app) {
  const publicDir = path.join(__dirname, '..', 'public');
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
    console.log('✅ "public" folder created automatically.');
  } else {
    console.log('📂 "public" folder already exists.');
  }
  app.get('/esp32/files', (req, res) => {
    fs.readdir(publicDir, (err, files) => {
      if (err) return res.status(500).json({ error: 'Cannot read directory.' });
      res.json(files);
    });
  });
  app.get('/esp32/:filename', (req, res) => {
    const filename = req.params.filename;
    const filePath = path.join(publicDir, filename);
    if (filename.includes('/') || filename.includes('\\')) {
      return res.status(400).send('Invalid filename.');
    }
    fs.access(filePath, fs.constants.R_OK, (err) => {
      if (err) return res.status(404).send('File not found.');
      res.sendFile(filePath);
    });
  });
};
