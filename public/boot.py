# public/boot.py
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

SERVER_URL = 'http://192.168.137.1:3000'
MAX_RETRIES = 10
PERSISTENT_FILES = {'boot.py', 'main.py', 'wifi.json'}  # add wifi.json so it isn't deleted

# ====== Logging ======
def log(msg: str) -> None:
    print(f"[BOOT] {msg}")

# ====== Utility Functions ======
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
    """Connect to WiFi network. Returns IP info or resets if unable to connect."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        log('Already connected.')
        return wlan.ifconfig()
    for ssid, pwd in WIFI_NETWORKS:
        log(f'Trying SSID: {ssid}')
        wlan.connect(ssid, pwd)
        for attempt in range(1, MAX_RETRIES + 1):
            if wlan.isconnected():
                break
            log(f'  Connecting... attempt {attempt}/{MAX_RETRIES}')
            time.sleep(1)
        if wlan.isconnected():
            log(f'Connected to {ssid}')
            return wlan.ifconfig()
    log('Could not connect to any network. Restarting...')
    time.sleep(2)
    machine.reset()

def clean_files() -> None:
    """Delete all files except those in PERSISTENT_FILES."""
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
    """Compare contents of two files in 1KB blocks."""
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
    """Replace boot.py if boot_new.py differs."""
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

def download_files() -> None:
    """Download all files listed on the remote server."""
    try:
        log('Getting list of files...')
        response = requests.get(f"{SERVER_URL}/files")
        file_list = response.json()
        response.close()
        if not file_list:
            log('No files found on the server. Restarting...')
            time.sleep(2)
            machine.reset()
        total_bytes = 0
        for name in file_list:
            log(f'Downloading {name}...')
            resp = requests.get(f"{SERVER_URL}/{name}")
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
    except Exception as e:
        log(f"Error downloading files: {e}. Restarting...")
        time.sleep(2)
        machine.reset()

# ====== Main Entrypoint ======
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
