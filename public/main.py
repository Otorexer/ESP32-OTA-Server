import uasyncio as asyncio
import machine
import ujson
from ws import AsyncWebsocketClient
import urequests as requests

# ====== Configuration ======
WS_URL = "ws://192.168.137.1:3000/"  # WebSocket server URL
PING_URL = "http://192.168.137.1:3000/ping"  # HTTP health check endpoint

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
