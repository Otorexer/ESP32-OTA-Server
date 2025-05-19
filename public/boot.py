import network
import time
import machine
import sys
import urequests as requests
import os
import gc
import ujson

# ====== Configuration ======
def load_wifi_networks():
    try:
        with open("wifi.json") as f:
            data = ujson.load(f)
        return data.get("networks", [])
    except Exception as e:
        print("[BOOT] Error loading wifi.json:", e)
        return []

WIFI_NETWORKS = load_wifi_networks()

SERVER_URLS = [
    'http://192.168.137.1:3000/esp32',
    'http://192.168.137.1:3000',
]

MAX_RETRIES = 10
PERSISTENT_FILES = {'boot.py', 'boot_new.py', 'wifi.json'}

def log(msg: str) -> None:
    print(f"[BOOT] {msg}")

def list_files(title: str = "Current files") -> None:
    log(f"--- {title} ---")
    files = sorted(os.listdir())
    if not files:
        log("(empty)")
    else:
        for f in files:
            log(f)
    log("-------------------")

def connect_wifi() -> tuple:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        log('Already connected.')
        return wlan.ifconfig()
    try:
        scan_list = wlan.scan()
        found_ssids = set(x[0].decode() if isinstance(x[0], bytes) else x[0] for x in scan_list)
        log(f"Visible networks: {', '.join(found_ssids) or '(none)'}")
    except Exception as e:
        log(f"Scan failed: {e}")
        found_ssids = set()
    matched = [(ssid, pwd) for ssid, pwd in WIFI_NETWORKS if ssid in found_ssids]
    if not matched:
        log('No configured SSIDs found in scan. Rebooting immediately...')
        time.sleep(2)
        machine.reset()
    for ssid, pwd in matched:
        log(f"Trying SSID: {ssid}")
        wlan.connect(ssid, pwd)
        for attempt in range(1, MAX_RETRIES + 1):
            if wlan.isconnected():
                break
            log(f"  Connecting... attempt {attempt}/{MAX_RETRIES}")
            time.sleep(1)
        if wlan.isconnected():
            log(f'Connected to {ssid}')
            return wlan.ifconfig()
        else:
            log(f'Failed to connect to {ssid}')
    log('Could not connect to any found network. Restarting...')
    time.sleep(2)
    machine.reset()

def clean_files() -> None:
    list_files("Before cleaning")
    for f in os.listdir():
        if f not in PERSISTENT_FILES:
            try:
                os.remove(f)
                log(f"Deleted: {f}")
            except Exception as e:
                log(f"Error deleting {f}: {e}")
    gc.collect()
    list_files("After cleaning")

def files_identical(f1: str, f2: str) -> bool:
    try:
        with open(f1, 'rb') as a, open(f2, 'rb') as b:
            while True:
                ba = a.read(1024)
                bb = b.read(1024)
                if ba != bb:
                    return False
                if not ba:
                    return True
    except OSError as e:
        log(f"Comparison failed: {e}")
        return False

def update_boot_script() -> None:
    if 'boot_new.py' not in os.listdir():
        return
    log('boot_new.py found, comparing...')
    if files_identical('boot.py', 'boot_new.py'):
        log('Identical: removing boot_new.py')
        os.remove('boot_new.py')
    else:
        log('Differences found: updating boot.py')
        os.remove('boot.py')
        os.rename('boot_new.py', 'boot.py')
        log('boot.py updated, restarting...')
        time.sleep(2)
        machine.reset()

# ---- MODIFIED: download_files supports two servers ----
def download_files() -> None:
    # Try each server in order
    last_error = None
    for server in SERVER_URLS:
        try:
            log(f'Getting list of files from {server}...')
            response = requests.get(f"{server}/files")
            file_list = response.json()
            response.close()
            if not file_list:
                log('No files found on the server. Restarting...')
                time.sleep(2)
                machine.reset()
            total_bytes = 0
            for name in file_list:
                log(f'Downloading {name}...')
                resp = requests.get(f"{server}/{name}")
                data = resp.content
                size = len(data)
                total_bytes += size
                dest = 'boot_new.py' if name == 'boot.py' else name
                with open(dest, 'wb') as f:
                    f.write(data)
                resp.close()
                log(f'{dest} saved ({size} bytes)')
            log(f'Total downloaded: {total_bytes} bytes')
            list_files("After download")
            return  # SUCCESS, exit function!
        except Exception as e:
            log(f"Error downloading from {server}: {e}")
            last_error = e
            # Try next server
    # If both/all failed:
    log(f"All server(s) failed. Restarting...")
    time.sleep(2)
    machine.reset()
# ------------------------------------------------------

def main() -> None:
    try:
        # Print chip info at startup
        try:
            import esp
            flash_size = esp.flash_size()
            log(f'FLASH size: {flash_size // (1024*1024)} MB ({flash_size} bytes)')
        except Exception as e:
            log(f'FLASH size: Error {e}')
        try:
            uname = os.uname()
            log(f'ESP32 uname: {uname}')
        except Exception as e:
            log(f'ESP32 uname: Error {e}')
        ip = connect_wifi()
        log(f'Got IP: {ip}')
        clean_files()
        download_files()
        update_boot_script()
        log('Done. Continuing...')
    except Exception as e:
        log(f"Unexpected error: {e}")
        time.sleep(2)
        machine.reset()

if __name__ == '__main__':
    main()
