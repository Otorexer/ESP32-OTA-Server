# ESP32 WebSocket OTA Server and Client

A lightweight and efficient server-client framework designed to manage ESP32 devices through WebSockets and OTA (Over-the-Air) updates. It includes a Node.js server for managing commands, firmware updates, and ESP32 device interaction via WiFi, and MicroPython client scripts that run directly on ESP32 devices to execute received commands and update firmware automatically.

---

## 📌 Overview

This project is structured into two main components:

- **Node.js Server**:

  - Hosts files for OTA updates.
  - Provides WebSocket communication with connected ESP32 devices.
  - Sends commands for LED control (RGB colors, intensity) and device reset.

- **ESP32 Client (MicroPython)**:

  - Connects to WiFi and the Node.js WebSocket server.
  - Listens for commands to control onboard NeoPixel LED and device resets.
  - Handles automatic OTA firmware/script updates.

---

## 🚧 Project Structure

```
.
├── index.js             # Main Node.js WebSocket and HTTP server script
├── package.json         # Dependencies and npm scripts
└── public               # OTA firmware/scripts and ESP32 client-side scripts
    ├── boot.py          # OTA and WiFi connection management script for ESP32
    ├── main.py          # WebSocket communication and LED control for ESP32
    └── ws.py            # WebSocket client implementation for ESP32 (MicroPython)
```

---

## 🚀 Features

- **OTA updates**: Automatically distribute updates to connected ESP32 devices.
- **Real-time control**: Send RGB color commands and intensity to LEDs via WebSockets.
- **Device Management**: Issue commands to reset or manage ESP32 devices remotely.
- **Automatic reconnection**: ESP32 devices automatically reconnect to WiFi and WebSocket server if connection is lost.

---

## ⚙️ Installation

### Prerequisites

- [Node.js](https://nodejs.org/) (>= 16.x)
- ESP32 board(s) flashed with [MicroPython](https://micropython.org/download/esp32/)

### Server-side (Node.js):

Clone and set up the repository:

```bash
git clone https://github.com/yourusername/esp32-ws-ota-server.git
cd esp32-ws-ota-server
npm install
```

Start the server:

```bash
npm start
```

> Server runs by default on `http://localhost:3000`.

---

## ⚡ ESP32 Client Setup

### Initial MicroPython Setup

1. Flash the ESP32 device with the latest MicroPython firmware using [esptool](https://github.com/espressif/esptool).

2. Copy files from `public/` to your ESP32 device root using a MicroPython file manager such as [ampy](https://github.com/scientifichackers/ampy), [rshell](https://github.com/dhylands/rshell), or [Thonny IDE](https://thonny.org/).

```bash
# Example using ampy:
ampy -p /dev/ttyUSB0 put public/boot.py
ampy -p /dev/ttyUSB0 put public/main.py
ampy -p /dev/ttyUSB0 put public/ws.py
```

3. Edit the configuration parameters in `public/boot.py` and `public/main.py` if necessary (WiFi SSID/password, server URL/IP).

---

## 🔧 Usage

### Sending Commands from Server

You can control connected ESP32 devices via HTTP POST requests:

#### Set RGB Color with Intensity:

```bash
curl -X POST http://localhost:3000/led/255,0,0/50
```

> Sets LED color to red at 50% intensity.

#### Set RGB Color (default intensity 100%):

```bash
curl -X POST http://localhost:3000/led/0,255,0
```

> Sets LED color to green at full brightness.

#### Reset all connected ESP32 devices:

```bash
curl -X POST http://localhost:3000/reset-all
```

> Sends a reset command to all connected ESP32 devices.

---

## 📡 OTA Firmware Updates

- Place updated Python scripts or files in the `public` directory.
- ESP32 devices will automatically check and download updates upon boot and periodically as configured.

---

## 🛡️ Security Notice

- The current implementation does not include authentication or encryption for WebSocket or HTTP requests. It's recommended to deploy behind a firewall and only on a trusted network.

---

## 📖 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🤝 Contribution

Contributions are welcome! Feel free to open issues and submit pull requests.

---