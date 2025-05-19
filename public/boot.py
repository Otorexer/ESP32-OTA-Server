import network
import time
import machine
import sys
import urequests as requests
import os
import gc
import ujson

def load_wifi_networks():
    try:
        with open("wifi.json") as f:
            data = ujson.load(f)
        return data.get("networks", [])
    except Exception as e:
        print("BOOT:WiFi.json load error:", e)
        return []

WIFI_NETWORKS = load_wifi_networks()
SERVER_URLS = [
    'http://192.168.137.1:3000/esp32',
    'http://192.168.137.1:3000',
]
MAX_RETRIES = 10
PERSISTENT_FILES = {'boot.py', 'boot_new.py', 'wifi.json'}

def log(tag, msg):
    print(f"{tag}:{msg}")

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        log('WIFI', 'Already connected')
        return wlan.ifconfig()
    try:
        scan_list = wlan.scan()
        found_ssids = set(x[0].decode() if isinstance(x[0], bytes) else x[0] for x in scan_list)
        log('WIFI', f"Found: {','.join(found_ssids)}")
    except Exception as e:
        log('WIFI', f"Scan error:{e}")
        found_ssids = set()
    matched = [(ssid, pwd) for ssid, pwd in WIFI_NETWORKS if ssid in found_ssids]
    if not matched:
        log('WIFI', 'No known SSIDs found, rebooting...')
        time.sleep(2)
        machine.reset()
    for ssid, pwd in matched:
        log('WIFI', f"Connecting to {ssid}")
        wlan.connect(ssid, pwd)
        for attempt in range(1, MAX_RETRIES + 1):
            if wlan.isconnected():
                break
            log('WIFI', f"  Try {attempt}/{MAX_RETRIES}")
            time.sleep(1)
        if wlan.isconnected():
            log('WIFI', f'Connected: {ssid}')
            return wlan.ifconfig()
        else:
            log('WIFI', f'Failed: {ssid}')
    log('WIFI', 'No connection, rebooting...')
    time.sleep(2)
    machine.reset()

def clean_files():
    existing = os.listdir()
    log('FS', f"Files: {existing}")
    for f in existing:
        if f not in PERSISTENT_FILES:
            try:
                os.remove(f)
                log('FS', f"Deleted: {f}")
            except Exception as e:
                log('FS', f"Delete error: {f}:{e}")
    gc.collect()

def files_identical(f1, f2):
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
        log('FS', f"Compare fail: {e}")
        return False

def update_boot_script():
    if 'boot_new.py' not in os.listdir():
        return
    log('BOOT', 'boot_new.py found')
    if files_identical('boot.py', 'boot_new.py'):
        log('BOOT', 'boot_new.py identical, deleting')
        os.remove('boot_new.py')
    else:
        log('BOOT', 'boot.py differs, updating & reboot')
        os.remove('boot.py')
        os.rename('boot_new.py', 'boot.py')
        time.sleep(2)
        machine.reset()

def download_files():
    last_error = None
    for server in SERVER_URLS:
        try:
            log('DL', f"Requesting file list: {server}")
            resp = requests.get(f"{server}/files")
            file_list = resp.json()
            resp.close()
            if not file_list:
                log('DL', 'No files on server, rebooting')
                time.sleep(2)
                machine.reset()
            for name in file_list:
                log('DL', f"Downloading: {name}")
                resp2 = requests.get(f"{server}/{name}")
                data = resp2.content
                dest = 'boot_new.py' if name == 'boot.py' else name
                with open(dest, 'wb') as f:
                    f.write(data)
                resp2.close()
                log('DL', f"Saved: {dest} ({len(data)} bytes)")
            return
        except Exception as e:
            log('DL', f"Error: {e}")
            last_error = e
    log('DL', f"All servers failed, rebooting: {last_error}")
    time.sleep(2)
    machine.reset()

def main():
    try:
        try:
            import esp
            log('BOOT', f"Flash size: {esp.flash_size()}")
        except Exception as e:
            log('BOOT', f"Flash size err:{e}")
        try:
            uname = os.uname()
            log('BOOT', f"uname:{uname}")
        except Exception as e:
            log('BOOT', f"uname err:{e}")
        ip = connect_wifi()
        log('WIFI', f'IP: {ip}')
        clean_files()
        download_files()
        update_boot_script()
        log('BOOT', 'Startup OK')
    except Exception as e:
        log('ERR', f"Unexpected: {e}")
        time.sleep(2)
        machine.reset()

if __name__ == '__main__':
    main()
