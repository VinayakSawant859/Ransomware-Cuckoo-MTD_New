import win32api
import win32con
import logging

logging.basicConfig(filename='detection/registry_monitoring.log', level=logging.INFO)

def monitor_registry():
    key = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE, 'SOFTWARE', 0, win32con.KEY_READ)
    ransomware_detected = False
    try:
        info = win32api.RegQueryInfoKey(key)
        logging.info(f"Registry Info: {info}")
        if "ransomware" in str(info).lower():  # Example condition for detection
            ransomware_detected = True
    except Exception as e:
        logging.error(f"Error: {e}")
    return ransomware_detected

if __name__ == "__main__":
    result = monitor_registry()
    exit(0 if not result else 1)  # Exit 0 for no ransomware, 1 for ransomware detected
