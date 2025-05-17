import uasyncio as asyncio
import machine
import neopixel
import ujson
from ws import AsyncWebsocketClient

# ====== Configuration ======
WS_URL = "ws://192.168.137.1:3000/"
PIN_INTERNAL = 48          # GPIO pin for the internal NeoPixel
NUM_INTERNAL = 1           # Only one internal NeoPixel

# ====== Hardware Setup ======
np_internal = neopixel.NeoPixel(machine.Pin(PIN_INTERNAL), NUM_INTERNAL)

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
                    rgb = tuple(int(x * percent / 100) for x in rgb)
                np_internal[0] = rgb
                np_internal.write()
                print(f"[LED] Updated to: {rgb} (intensity {intensity_val})")
                return
        except Exception as e:
            print("[LED] Error decoding RGB:", e)
    print("[LED] Invalid color format (expected 'R,G,B'):", color_val)

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
    loop.run_forever()

main()
