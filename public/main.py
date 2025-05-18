import uasyncio as asyncio
import machine
import neopixel
import ujson
from ws import AsyncWebsocketClient
import urequests as requests

# ====== Configuration ======
WS_URL = "ws://192.168.137.1:3000/"  # WebSocket server URL
PING_URL = "http://192.168.137.1:3000/ping"  # HTTP health check endpoint

PIN_INTERNAL = 48          # GPIO pin for the internal NeoPixel
NUM_INTERNAL = 1           # Only one internal NeoPixel
PIN_STRIP = 18             # GPIO pin for the 1x8 NeoPixel strip
NUM_STRIP = 8              # Number of LEDs on the strip

# ====== Hardware Setup ======
np_internal = neopixel.NeoPixel(machine.Pin(PIN_INTERNAL), NUM_INTERNAL)
np_strip = neopixel.NeoPixel(machine.Pin(PIN_STRIP), NUM_STRIP)

# ====== LED Control ======
def set_color(color_val, intensity_val=None):
    # Accept only format like "255,0,0"
    if isinstance(color_val, str) and ',' in color_val:
        try:
            rgb = tuple(int(x) for x in color_val.split(','))
            if len(rgb) == 3:
                # Apply intensity if given
                if intensity_val is not None:
                    percent = max(0, min(int(intensity_val), 100))
                    rgb_adj = tuple(int(x * percent / 100) for x in rgb)
                else:
                    rgb_adj = rgb
                # Update both NeoPixels at the same time
                np_internal[0] = rgb_adj
                for i in range(NUM_STRIP):
                    np_strip[i] = rgb_adj
                np_internal.write()
                np_strip.write()
                print(f"[LED] Updated to: {rgb_adj} (intensity {intensity_val})")
                return
        except Exception as e:
            print("[LED] Error decoding RGB:", e)
    print("[LED] Invalid color format (expected 'R,G,B'):", color_val)

# ====== Ping Server Health Task ======
async def ping_server_forever():
    fail_count = 0
    while True:
        try:
            resp = requests.get(PING_URL)
            data = resp.text
            resp.close()
            if data.strip() == "pong":
                print("[PING] pong received.")
                fail_count = 0
            else:
                print("[PING] Bad response:", data)
                fail_count += 1
        except Exception as e:
            print("[PING] Ping failed:", e)
            fail_count += 1
        if fail_count >= 3:
            print("[PING] Failed 3 times. Rebooting...")
            await asyncio.sleep(1)
            machine.reset()
        await asyncio.sleep(1)

# ====== WebSocket Logic ======
async def ws_client_forever():
    while True:
        try:
            ws = AsyncWebsocketClient()
            await ws.handshake(WS_URL)
            print("[WS] Connected to server")
            while True:
                msg = await ws.recv()
                if not msg:
                    print("[WS] Disconnected, closing socket...")
                    await ws.close()
                    break
                try:
                    data = ujson.loads(msg)
                    if 'color' in data:
                        intensity = data.get('intensity')
                        set_color(data['color'], intensity)
                    if 'effect' in data and data['effect'] == 'rainbow':
                        print("[WS] Rainbow effect triggered.")
                        await color_rainbow_effect(duration=8)
                    if 'reset' in data and data['reset']:
                        print("[WS] Reset requested, restarting...")
                        machine.reset()
                except Exception as e:
                    print("Error processing message:", e)
        except Exception as e:
            print("[WS] Connection or communication error:", e)
        print("[WS] Retrying connection in 3 seconds...")
        await asyncio.sleep(3)

# ====== Main Entrypoint ======
def main():
    loop = asyncio.get_event_loop()
    loop.create_task(ws_client_forever())
    loop.create_task(ping_server_forever())
    loop.run_forever()

if __name__ == '__main__':
    main()
