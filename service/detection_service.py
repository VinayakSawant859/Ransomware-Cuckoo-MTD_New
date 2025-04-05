
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os
import time
import logging
import json
import traceback
from pathlib import Path

# Configure logging to a known location
log_dir = Path("C:/ProgramData/RansomwareDetection/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "service_installation.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RansomwareDetectionService")

# Log startup
logger.info("Service script loading")

class RansomwareDetectionService(win32serviceutil.ServiceFramework):
    _svc_name_ = "RansomwareDetectionService"
    _svc_display_name_ = "Ransomware Detection Background Service"
    _svc_description_ = "Background monitoring service for ransomware detection and prevention"
    
    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            self.running = False
            logger.info("Service initialized")
        except Exception as e:
            logger.error(f"Error in service initialization: {e}")
            logger.error(traceback.format_exc())
            raise
        
    def SvcStop(self):
        try:
            logger.info('Service stop requested')
            self.running = False
            win32event.SetEvent(self.stop_event)
            self.update_status("stopped")
        except Exception as e:
            logger.error(f"Error during stop: {e}")
            logger.error(traceback.format_exc())
        
    def SvcDoRun(self):
        try:
            logger.info('Service starting')
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.running = True
            self.update_status("running")
            self.main()
        except Exception as e:
            logger.error(f"Error during service run: {e}")
            logger.error(traceback.format_exc())
            self.update_status("error", {"error": str(e)})

    def update_status(self, status, details=None):
        try:
            status_file = Path("C:/ProgramData/RansomwareDetection/service_status.json")
            status_data = {
                "status": status,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "hostname": socket.gethostname()
            }
            if details:
                status_data["details"] = details
            with open(status_file, 'w') as f:
                json.dump(status_data, f)
            logger.info(f"Status updated to: {status}")
        except Exception as e:
            logger.error(f"Error updating status: {e}")
        
    def main(self):
        try:
            logger.info("Service main loop starting")
            self.update_status("running")
            
            while self.running:
                if win32event.WaitForSingleObject(self.stop_event, 5000) == win32event.WAIT_OBJECT_0:
                    break
                time.sleep(1)
                
            self.update_status("stopped")
            logger.info("Service main loop finished")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.error(traceback.format_exc())

if __name__ == '__main__':
    try:
        logger.info(f"Service script called with args: {sys.argv}")
        if len(sys.argv) == 1:
            logger.info("Starting service dispatcher")
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(RansomwareDetectionService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            logger.info(f"Handling command: {sys.argv[1]}")
            win32serviceutil.HandleCommandLine(RansomwareDetectionService)
    except Exception as e:
        logger.error(f"Top level exception: {e}")
        logger.error(traceback.format_exc())
        raise
