import psutil
import time
import logging

logging.basicConfig(filename='detection/behavioral_analysis.log', level=logging.INFO)

def monitor_processes():
    logging.info("Starting process monitoring...")
    ransomware_detected = False
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        logging.info(f"PID: {proc.info['pid']}, Name: {proc.info['name']}, Status: {proc.info['status']}")
        if "ransomware" in proc.info['name'].lower():  # Example condition for detection
            ransomware_detected = True
    return ransomware_detected

if __name__ == "__main__":
    result = monitor_processes()
    exit(0 if not result else 1)  # Exit 0 for no ransomware, 1 for ransomware detected