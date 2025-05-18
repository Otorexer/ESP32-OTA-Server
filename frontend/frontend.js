const statusEl = document.getElementById('status');
const colorPicker = document.getElementById('colorPicker');
const intensitySlider = document.getElementById('intensitySlider');
const intensityValue = document.getElementById('intensityValue');

let socket;
let currentColor;
let currentIntensity;
let lastSentColor = '';
let lastSentIntensity = '';
let initialized = false;
let updating = false; // flag to prevent loops

function hexToRgb(hex) {
  const bigint = parseInt(hex.slice(1), 16);
  return [
    (bigint >> 16) & 255,
    (bigint >> 8) & 255,
    bigint & 255
  ].join(',');
}
function rgbToHex(rgb) {
  const parts = rgb.split(',').map(Number);
  return '#' + parts.map(x => x.toString(16).padStart(2, '0')).join('');
}
function connectWebSocket() {
  socket = new WebSocket(`ws://${location.host}`);
  initialized = false;
  socket.addEventListener('open', () => {
    statusEl.textContent = 'Connected to WebSocket';
    lastSentColor = '';
    lastSentIntensity = '';
  });
  socket.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.color && data.intensity) {
        updating = true; // don't emit update while UI is being updated
        const hex = rgbToHex(data.color);
        colorPicker.value = hex;
        intensitySlider.value = data.intensity;
        intensityValue.textContent = data.intensity;
        currentColor = colorPicker.value;
        currentIntensity = data.intensity;
        lastSentColor = currentColor;
        lastSentIntensity = currentIntensity;
        updating = false;
        if (!initialized) initialized = true;
      }
    } catch (err) {
      // ignore
    }
  });
  socket.addEventListener('close', () => {
    statusEl.textContent = 'Disconnected. Reconnecting...';
    setTimeout(connectWebSocket, 3000);
  });
  socket.addEventListener('error', (err) => {
    console.error('WebSocket error:', err);
  });
}
colorPicker.addEventListener('input', (e) => {
  currentColor = e.target.value;
});
intensitySlider.addEventListener('input', (e) => {
  currentIntensity = e.target.value;
  intensityValue.textContent = currentIntensity;
});

// Only send if values changed, not during remote update, and initialized
setInterval(() => {
  if (
    initialized &&
    !updating &&
    socket &&
    socket.readyState === WebSocket.OPEN &&
    (currentColor !== lastSentColor || currentIntensity !== lastSentIntensity)
  ) {
    const rgb = hexToRgb(currentColor);
    const message = JSON.stringify({ color: rgb, intensity: currentIntensity });
    socket.send(message);
    lastSentColor = currentColor;
    lastSentIntensity = currentIntensity;
  }
}, 30);

connectWebSocket();
