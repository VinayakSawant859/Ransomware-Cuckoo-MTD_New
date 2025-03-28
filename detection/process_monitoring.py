import psutil
import logging

logging.basicConfig(filename='detection/process_monitoring.log', level=logging.INFO)

def monitor_processes():
    ransomware_detected = False
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        logging.info(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, CPU Usage: {proc.info['cpu_percent']}%")
        if "ransomware" in proc.info['name'].lower():  # Example condition for detection
            ransomware_detected = True
    return ransomware_detected

if __name__ == "__main__":
    result = monitor_processes()
    exit(0 if not result else 1)  # Exit 0 for no ransomware, 1 for ransomware detected
