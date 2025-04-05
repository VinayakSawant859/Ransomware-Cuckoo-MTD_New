from PyQt5.QtCore import QObject, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QMessageBox, QDialog, QTextBrowser, 
                           QSpinBox, QComboBox)
import subprocess
import json
import time
import os
from pathlib import Path
import shutil
import sys

class ServiceManager(QObject):
    """Manages interactions with the background detection service"""
    
    # Define signals for UI updates
    service_status_changed = pyqtSignal(str, dict)
    detection_results_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        
        # Define file paths
        self.base_dir = Path("C:/ProgramData/RansomwareDetection")
        self.status_file = self.base_dir / "service_status.json"
        self.command_file = self.base_dir / "service_command.json"
        self.results_file = self.base_dir / "detection_results.json"
        self.settings_file = self.base_dir / "service_settings.json"
        
        # Create directories if needed
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs").mkdir(exist_ok=True)
        
        # Create default settings if they don't exist
        if not self.settings_file.exists():
            default_settings = {
                "scan_interval": 1800,  # 30 minutes
                "detection_level": "medium"
            }
            with open(self.settings_file, 'w') as f:
                json.dump(default_settings, f)
        
        # Service monitoring timer
        self.status_check_timer = QTimer()
        self.status_check_timer.timeout.connect(self.check_service_status)
        self.status_check_timer.start(5000)  # Check every 5 seconds
        
        # Results monitoring timer
        self.results_check_timer = QTimer()
        self.results_check_timer.timeout.connect(self.check_detection_results)
        self.results_check_timer.start(10000)  # Check every 10 seconds
        
        # Initialize status
        self._last_status_check = 0
        self._last_results_check = 0
        self._last_status = {"status": "unknown"}
        self._last_results_timestamp = None
        
        # Do initial checks
        self.check_service_status()
        self.check_detection_results()
        
    def is_service_installed(self):
        """Check if the service is installed on the system"""
        try:
            # Run SC query to check if service exists
            result = subprocess.run(
                ["sc", "query", "RansomwareDetectionService"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error checking service installation: {e}")
            return False

    def is_admin(self):
        """Check if application is running as administrator"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def install_service(self):
        """Install the background service"""
        try:
            # First check if we have admin privileges
            if not self.is_admin():
                # Create a helper file with instructions
                help_file = self.base_dir / "admin_instructions.txt"
                with open(help_file, 'w') as f:
                    f.write("""
=== HOW TO RUN AS ADMINISTRATOR ===

Method 1: Using run_as_admin.py
1. Close this application
2. Navigate to the application folder
3. Right-click on "run_as_admin.py"
4. Select "Run as administrator"

Method 2: For the main application
1. Close this application
2. Find the application icon or file
3. Right-click on it and select "Run as administrator"
4. Accept the User Account Control (UAC) prompt

Method 3: For Python script
1. Open Command Prompt as administrator
   - Press Windows key
   - Type "cmd"
   - Right-click on "Command Prompt"
   - Select "Run as administrator"
2. Navigate to application folder
3. Run: python main.py
                    """)
                
                return False, f"Administrator privileges required. Please see instructions at: {help_file}"
            
            # First check if PyWin32 is installed correctly
            try:
                import win32serviceutil
                import win32service
                import win32event
                import servicemanager
            except ImportError:
                return False, "PyWin32 is not installed or not configured properly. Please run 'pip install pywin32' and then run 'python -m win32com.client.makepy winmgmt'"
            
            # Create a simplified, more reliable service script
            service_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "service"))
            os.makedirs(service_dir, exist_ok=True)
            
            service_script = os.path.join(service_dir, "detection_service.py")
            
            # Write a more robust service script that logs errors and uses absolute paths
            with open(service_script, 'w') as f:
                f.write("""
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
""")
            
            # Log the path for debugging
            log_dir = Path("C:/ProgramData/RansomwareDetection/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "service_install_debug.log", "w") as f:
                f.write(f"Service script path: {service_script}\n")
                f.write(f"Current working directory: {os.getcwd()}\n")
                f.write(f"Python executable: {sys.executable}\n")
                
            # Run post-install script for PyWin32 if needed
            try:
                # Run the post-install script for PyWin32 to ensure it's properly set up
                pywin32_path = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pywin32_postinstall.py')
                if os.path.exists(pywin32_path):
                    subprocess.run([sys.executable, pywin32_path, "-install"], capture_output=True)
            except Exception as e:
                pass  # Ignore errors here, not critical
                
            # Install the service with more robust error handling and explicit admin check
            try:
                # Check for admin privileges
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    return False, "Administrator privileges required. Please run as administrator."
                
                # Try installing the service
                with open(log_dir / "service_install_debug.log", "a") as f:
                    f.write(f"Attempting to install service...\n")
                
                # Install the service with specific error handling
                install_cmd = [
                    sys.executable, 
                    service_script,
                    "install"
                ]
                
                try:
                    # Use subprocess.check_output for better error output
                    install_output = subprocess.check_output(
                        install_cmd, 
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                    with open(log_dir / "service_install_debug.log", "a") as f:
                        f.write(f"Install command output: {install_output}\n")
                
                except subprocess.CalledProcessError as e:
                    with open(log_dir / "service_install_debug.log", "a") as f:
                        f.write(f"Install command failed with code {e.returncode}: {e.output}\n")
                    return False, f"Service installation failed: {e.output}"
                    
                # Attempt to start the service to verify installation
                time.sleep(2)  # Give Windows time to register the service
                start_cmd = ["sc", "start", "RansomwareDetectionService"]
                start_result = subprocess.run(start_cmd, capture_output=True, text=True)
                
                # Set initial service status regardless of start result
                with open(self.status_file, 'w') as f:
                    json.dump({
                        "status": "installed",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }, f)
                
                # If start failed, note it but still return success for installation
                if start_result.returncode != 0:
                    with open(log_dir / "service_install_debug.log", "a") as f:
                        f.write(f"Service installed but failed to start: {start_result.stderr}\n")
                    return True, "Service installed successfully but couldn't be started automatically. Try starting it manually."
                
                return True, "Service installed and started successfully"
                
            except Exception as e:
                with open(log_dir / "service_install_debug.log", "a") as f:
                    f.write(f"Exception during installation: {str(e)}\n")
                import traceback
                with open(log_dir / "service_install_debug.log", "a") as f:
                    f.write(traceback.format_exc())
                return False, f"Error during service installation: {str(e)}"
                
        except Exception as e:
            return False, f"Error preparing service installation: {str(e)}"
            
    def uninstall_service(self):
        """Uninstall the background service"""
        try:
            # Path to service script
            service_script = os.path.abspath(
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                            "service", "detection_service.py")
            )
            # Call the service script with install command
            result = subprocess.run(
                [sys.executable, service_script, "remove"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, f"Service removal failed: {result.stderr}"
                
            return True, "Service uninstalled successfully"
        except Exception as e:
            return False, f"Error uninstalling service: {e}"

    def start_service(self):
        """Start the background service with improved robustness"""
        try:
            # First verify if service exists
            check_result = subprocess.run(
                ["sc", "query", "RansomwareDetectionService"],
                capture_output=True,
                text=True
            )
            
            if check_result.returncode != 0:
                # Service doesn't exist, try to install it first
                success, message = self.install_service()
                if not success:
                    return False, f"Service not installed and automatic installation failed: {message}"
            
            # Wait for any pending service operations to complete
            time.sleep(1)
            
            # Log attempt to start service
            log_dir = Path("C:/ProgramData/RansomwareDetection/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "service_start_debug.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Attempting to start service\n")
            
            # First check if the service is already running
            status_check = subprocess.run(
                ["sc", "query", "RansomwareDetectionService"],
                capture_output=True,
                text=True
            )
            
            if "RUNNING" in status_check.stdout:
                # Service is already running
                with open(log_dir / "service_start_debug.log", "a") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Service already running\n")
                return True, "Service is already running"
            
            # Try to start the service with a longer timeout
            result = subprocess.run(
                ["sc", "start", "RansomwareDetectionService"],
                capture_output=True,
                text=True
            )
            
            # Log start attempt results
            with open(log_dir / "service_start_debug.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - SC start result: {result.returncode}\n")
                if result.stdout:
                    f.write(f"STDOUT: {result.stdout}\n")
                if result.stderr:
                    f.write(f"STDERR: {result.stderr}\n")
            
            # Handle specific error codes
            if result.returncode != 0:
                error_text = result.stderr if result.stderr else result.stdout
                
                # Check for specific error codes for better messages
                if "1053" in error_text:
                    # Try alternative method via powershell
                    try:
                        with open(log_dir / "service_start_debug.log", "a") as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Trying PowerShell method\n")
                        
                        ps_cmd = "Start-Service -Name RansomwareDetectionService"
                        ps_result = subprocess.run(
                            ["powershell", "-Command", ps_cmd],
                            capture_output=True,
                            text=True
                        )
                        
                        if ps_result.returncode == 0:
                            # Wait for service to start
                            time.sleep(3)
                            return True, "Service started using PowerShell"
                    except Exception as e:
                        with open(log_dir / "service_start_debug.log", "a") as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - PowerShell error: {str(e)}\n")
                    
                    return False, "Service failed to start: The service did not respond to the start request in a timely fashion. Check logs at C:/ProgramData/RansomwareDetection/logs"
                elif "5" in error_text:
                    return False, "Access denied. Please run as administrator."
                else:
                    return False, f"Service start failed: {error_text}"
            
            # Success case - wait for service to fully initialize
            # Give more time for service to stabilize
            time.sleep(3)
            
            # Check if service is actually running
            verify_result = subprocess.run(
                ["sc", "query", "RansomwareDetectionService"],
                capture_output=True,
                text=True
            )
            
            if "RUNNING" in verify_result.stdout:
                return True, "Service started successfully"
            else:
                return False, "Service was started but is not currently running. Check service logs for errors."
            
        except Exception as e:
            return False, f"Error starting service: {str(e)}"

    def stop_service(self):
        """Stop the background service"""
        try:
            result = subprocess.run(
                ["sc", "stop", "RansomwareDetectionService"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, f"Service stop failed: {result.stderr}"
            return True, "Service stopped successfully"
        except Exception as e:
            return False, f"Error stopping service: {e}"

    def check_service_status(self):
        """Check the current status of the service"""
        current_time = time.time()
        
        # Limit status checks to avoid excessive file I/O
        if current_time - self._last_status_check < 3:  # At most every 3 seconds
            return
        
        self._last_status_check = current_time
        
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                    
                # Only emit signal if status has changed
                if status_data != self._last_status:
                    self._last_status = status_data
                    self.service_status_changed.emit(
                        status_data.get("status", "unknown"), 
                        status_data
                    )
            else:
                # If status file doesn't exist, check if service is running via SC
                result = subprocess.run(
                    ["sc", "query", "RansomwareDetectionService"], 
                    capture_output=True,
                    text=True
                )
                
                if "RUNNING" in result.stdout:
                    self.service_status_changed.emit("running", {"status": "running"})
                    self._last_status = {"status": "running"}
                elif "STOPPED" in result.stdout:
                    self.service_status_changed.emit("stopped", {"status": "stopped"})
                    self._last_status = {"status": "stopped"}
                else:
                    self.service_status_changed.emit("unknown", {"status": "unknown"})
                    self._last_status = {"status": "unknown"}
        except Exception as e:
            print(f"Error checking service status: {e}")

    def check_detection_results(self):
        """Check for updated detection results"""
        current_time = time.time()
        
        # Limit checks to avoid excessive file I/O
        if current_time - self._last_results_check < 5:  # At most every 5 seconds
            return
        
        self._last_results_check = current_time
        
        try:
            if self.results_file.exists():
                # Check file modification time
                mod_time = os.path.getmtime(self.results_file)
                
                # Only read if file has been updated since last check
                if self._last_results_timestamp is None or mod_time > self._last_results_timestamp:
                    self._last_results_timestamp = mod_time
                    with open(self.results_file, 'r') as f:
                        results = json.load(f)
                    self.detection_results_updated.emit(results)
        except Exception as e:
            print(f"Error checking detection results: {e}")

    def send_command(self, action, **kwargs):
        """Send a command to the background service"""
        command_data = {
            "action": action,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            **kwargs
        }
        try:
            with open(self.command_file, 'w') as f:
                json.dump(command_data, f)
            return True
        except Exception as e:
            print(f"Error sending command: {e}")
            return False

    def trigger_scan(self):
        """Trigger an immediate scan"""
        return self.send_command("scan_now")

    def update_settings(self, settings):
        """Update service settings"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
                
            return self.send_command("update_settings")
        except Exception as e:
            print(f"Error updating settings: {e}")
            return False
