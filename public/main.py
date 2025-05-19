import uasyncio as asyncio
import machine
import ujson
from ws import AsyncWebsocketClient
import urequests as requests

WS_URL = "ws://192.168.137.1:3000/"
PING_URL = "http://192.168.137.1:3000/ping"

def log(tag, msg):
    print(f"{tag}:{msg}")

async def ping_server_forever():
    fail_count = 0
    while True:
        try:
            resp = requests.get(PING_URL)
            data = resp.text
            resp.close()
            if data.strip() == "pong":
                log("PING", "OK")
                fail_count = 0
            else:
                log("PING", f"BadResp:{data}")
                fail_count += 1
        except Exception as e:
            log("PING", f"Error:{e}")
            fail_count += 1
        if fail_count >= 3:
            log("PING", "3 fail, rebooting")
            await asyncio.sleep(1)
            machine.reset()
        await asyncio.sleep(1)

async def ws_client_forever():
    while True:
        try:
            ws = AsyncWebsocketClient()
            await ws.handshake(WS_URL)
            log("WS", "Connected")
            while True:
                msg = await ws.recv()
                if not msg:
                    log("WS", "Disconnected, closing")
                    await ws.close()
                    break
                try:
                    data = ujson.loads(msg)
                    if 'reset' in data and data['reset']:
                        log("WS", "Reset cmd, rebooting")
                        machine.reset()
                    # Place for more commands
                except Exception as e:
                    log("WS", f"Parse error:{e}")
        except Exception as e:
            log("WS", f"Conn/comm error:{e}")
        log("WS", "Retry in 3s")
        await asyncio.sleep(3)

def main():
    loop = asyncio.get_event_loop()
    loop.create_task(ws_client_forever())
    loop.create_task(ping_server_forever())
    loop.run_forever()

if __name__ == '__main__':
    main()
