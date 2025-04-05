"""
Standalone Service Runner

This script provides a way to manage the Ransomware Detection Service
without requiring the main GUI application to be running.
It provides command-line control of service installation and operation.
"""
import os
import sys
import argparse
import traceback
import ctypes
import subprocess
import time
import logging
import json
from pathlib import Path

# Configure logging
log_dir = Path("C:/ProgramData/RansomwareDetection/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "standalone_service.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StandaloneService")

def is_admin():
    """Check if script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def get_service_script():
    """Get absolute path to the service script"""
    # First try to find the script in the expected location
    # Use absolute path to avoid any working directory issues
    current_dir = os.path.dirname(os.path.abspath(__file__))
    service_script = os.path.join(current_dir, "service", "detection_service.py")
    
    if os.path.exists(service_script):
        return os.path.abspath(service_script)
    
    # Try to find the script in any subdirectory
    for root, _, files in os.walk(current_dir):
        for file in files:
            if file == "detection_service.py":
                return os.path.abspath(os.path.join(root, file))
    
    # If not found, return the expected path anyway
    return os.path.abspath(service_script)

def run_python_command(args, timeout=30, check=True):
    """Run a Python command with the same interpreter as this script"""
    python_exe = sys.executable
    command = [python_exe] + args
    
    try:
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=check
        )
        logger.info(f"Command returned: {result.returncode}")
        if result.stdout.strip():
            logger.info(f"Command output: {result.stdout.strip()}")
        if result.stderr.strip():
            logger.warning(f"Command error: {result.stderr.strip()}")
        return result
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}: {e.stderr}")
        return e
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def ensure_pywin32_installed():
    """Make sure pywin32 is properly installed"""
    logger.info("Checking PyWin32 installation...")
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
        logger.info("PyWin32 modules found")
        return True
    except ImportError:
        logger.warning("PyWin32 not properly installed, attempting to fix...")
        try:
            # Try to install or repair pywin32
            run_python_command(["-m", "pip", "install", "--upgrade", "pywin32==302"])
            
            # Run the post-install script if it exists
            script_dir = os.path.dirname(sys.executable)
            postinstall_script = os.path.join(script_dir, "Scripts", "pywin32_postinstall.py")
            
            if os.path.exists(postinstall_script):
                run_python_command([postinstall_script, "-install"])
            
            # Test again
            import win32serviceutil
            import win32service
            logger.info("PyWin32 successfully installed/fixed")
            return True
        except Exception:
            logger.error("Failed to install/fix PyWin32. Run repair_pywin32.py first.")
            return False

def install_service():
    """Install the ransomware detection service"""
    logger.info("Installing service...")
    if not is_admin():
        logger.error("Administrator privileges required to install service")
        print("ERROR: Administrator privileges required to install service")
        print("Please run this script as Administrator")
        return False
    
    if not ensure_pywin32_installed():
        return False
    
    service_script = get_service_script()
    if not os.path.exists(service_script):
        logger.error(f"Service script not found: {service_script}")
        return False
    
    logger.info(f"Using service script: {service_script}")
    
    # Create the service environment file to help with path issues
    env_file = os.path.join(os.path.dirname(service_script), "service_env.json")
    env_data = {
        "PYTHONPATH": sys.path,
        "EXECUTABLE": sys.executable,
        "BASE_DIR": os.path.dirname(os.path.abspath(__file__))
    }
    
    try:
        with open(env_file, 'w') as f:
            json.dump(env_data, f, indent=2)
        logger.info(f"Created environment file: {env_file}")
    except Exception as e:
        logger.error(f"Failed to create environment file: {str(e)}")
    
    # Run the installation
    logger.info("Running service installation...")
    result = run_python_command([service_script, "install"])
    
    if result and result.returncode == 0:
        logger.info("Service installed successfully")
        print("Service installed successfully")
        return True
    else:
        logger.error("Failed to install service")
        print("ERROR: Failed to install service. Check the logs for details.")
        print(f"Log file: {log_file}")
        return False

def uninstall_service():
    """Uninstall the ransomware detection service"""
    logger.info("Uninstalling service...")
    if not is_admin():
        logger.error("Administrator privileges required to uninstall service")
        print("ERROR: Administrator privileges required to uninstall service")
        print("Please run this script as Administrator")
        return False
    
    service_script = get_service_script()
    if not os.path.exists(service_script):
        logger.error(f"Service script not found: {service_script}")
        return False
    
    # Stop the service first
    stop_service()
    
    # Run the uninstallation
    logger.info("Running service removal...")
    result = run_python_command([service_script, "remove"], check=False)
    
    if result and result.returncode == 0:
        logger.info("Service uninstalled successfully")
        print("Service uninstalled successfully")
        return True
    else:
        logger.error("Failed to uninstall service")
        print("ERROR: Failed to uninstall service. Check the logs for details.")
        print(f"Log file: {log_file}")
        return False

def start_service():
    """Start the ransomware detection service"""
    logger.info("Starting service...")
    
    # Check if service exists
    result = subprocess.run(
        ["sc", "query", "RansomwareDetectionService"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error("Service is not installed")
        print("ERROR: Service is not installed")
        return False
    
    # Use SC command directly for better reliability
    start_result = subprocess.run(
        ["sc", "start", "RansomwareDetectionService"],
        capture_output=True,
        text=True
    )
    
    if start_result.returncode == 0:
        logger.info("Service start command issued successfully")
        print("Service start command issued successfully")
        
        # Verify the service actually started
        time.sleep(2)  # Give it a moment to start
        status = get_service_status()
        if status == "RUNNING":
            logger.info("Service started successfully")
            print("Service is running")
            return True
        else:
            logger.error(f"Service failed to start. Status: {status}")
            print(f"ERROR: Service failed to start. Status: {status}")
            print("Try running the service in test mode to diagnose issues:")
            print(f"  {sys.executable} {get_service_script()} test")
            return False
    else:
        error = start_result.stderr.strip() or start_result.stdout.strip()
        logger.error(f"Failed to start service: {error}")
        print(f"ERROR: Failed to start service: {error}")
        return False

def stop_service():
    """Stop the ransomware detection service"""
    logger.info("Stopping service...")
    
    # Use SC command directly
    stop_result = subprocess.run(
        ["sc", "stop", "RansomwareDetectionService"],
        capture_output=True,
        text=True
    )
    
    if stop_result.returncode == 0:
        logger.info("Service stop command issued successfully")
        print("Service stop command issued successfully")
        
        # Verify the service actually stopped
        time.sleep(2)  # Give it a moment to stop
        status = get_service_status()
        if status != "RUNNING":
            logger.info("Service stopped successfully")
            print("Service is stopped")
            return True
        else:
            logger.error("Service is still running after stop command")
            print("ERROR: Service is still running after stop command")
            return False
    else:
        error = stop_result.stderr.strip() or stop_result.stdout.strip()
        logger.error(f"Failed to stop service: {error}")
        print(f"ERROR: Failed to stop service: {error}")
        return False

def get_service_status():
    """Get the current status of the service"""
    logger.info("Checking service status...")
    
    # Use SC command to query service status
    result = subprocess.run(
        ["sc", "query", "RansomwareDetectionService"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        output = result.stdout.strip()
        if "RUNNING" in output:
            return "RUNNING"
        elif "STOPPED" in output:
            return "STOPPED"
        elif "START_PENDING" in output:
            return "STARTING"
        elif "STOP_PENDING" in output:
            return "STOPPING"
        else:
            return "UNKNOWN"
    else:
        return "NOT_INSTALLED"

def test_service():
    """Run the service in test mode (foreground)"""
    logger.info("Running service in test mode...")
    
    service_script = get_service_script()
    if not os.path.exists(service_script):
        logger.error(f"Service script not found: {service_script}")
        return False
    
    print(f"Running service in test mode using: {service_script}")
    print("Press Ctrl+C to stop the test")
    
    # Run the service in test mode
    try:
        subprocess.run([sys.executable, service_script, "test"])
        return True
    except KeyboardInterrupt:
        print("\nTest mode stopped by user")
        return True
    except Exception as e:
        logger.error(f"Error running service test: {str(e)}")
        print(f"ERROR: Failed to run service test: {str(e)}")
        return False

def diagnose_service():
    """Run various diagnostics on the service"""
    logger.info("Running service diagnostics...")
    print("\n===== SERVICE DIAGNOSTICS =====")
    
    # Check Python environment
    print("\n1. Python Environment:")
    print(f"   Python: {sys.executable}")
    print(f"   Version: {sys.version}")
    
    # Check PyWin32
    print("\n2. PyWin32 Installation:")
    try:
        import win32serviceutil
        print("   PyWin32 is installed and importable")
    except ImportError:
        print("   ERROR: PyWin32 is not properly installed")
    
    # Check service script
    service_script = get_service_script()
    print("\n3. Service Script:")
    if os.path.exists(service_script):
        print(f"   Found at: {service_script}")
    else:
        print(f"   ERROR: Script not found: {service_script}")
    
    # Check service status
    print("\n4. Service Status:")
    status = get_service_status()
    print(f"   Current status: {status}")
    
    # Check service logs
    print("\n5. Service Logs:")
    service_log = log_dir / "detection_service.log"
    install_log = log_dir / "service_installation.log"
    
    if service_log.exists():
        print(f"   Service log found: {service_log}")
        # Show last 5 lines of log
        try:
            with open(service_log, 'r') as f:
                lines = f.readlines()
                print("\n   Last log entries:")
                for line in lines[-5:]:
                    print(f"   {line.strip()}")
        except Exception as e:
            print(f"   Error reading log: {str(e)}")
    else:
        print(f"   No service log found at {service_log}")
    
    if install_log.exists():
        print(f"\n   Installation log found: {install_log}")
    else:
        print(f"\n   No installation log found at {install_log}")
    
    print("\n===== END OF DIAGNOSTICS =====")

def main():
    """Main function to parse arguments and execute commands"""
    parser = argparse.ArgumentParser(
        description='Standalone Service Runner for Ransomware Detection',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('action', choices=['install', 'uninstall', 'start', 'stop', 'status', 'test', 'diagnose'],
                        help='''Action to perform:
install   - Install the service
uninstall - Remove the service
start     - Start the service
stop      - Stop the service
status    - Check service status
test      - Run service in test mode
diagnose  - Run diagnostics''')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute the requested action
    if args.action == 'install':
        if not is_admin():
            # Try to relaunch as admin
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                f'"{os.path.abspath(__file__)}" install', None, 1
            )
        else:
            install_service()
    elif args.action == 'uninstall':
        if not is_admin():
            # Try to relaunch as admin
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable,
                f'"{os.path.abspath(__file__)}" uninstall', None, 1
            )
        else:
            uninstall_service()
    elif args.action == 'start':
        start_service()
    elif args.action == 'stop':
        stop_service()
    elif args.action == 'status':
        status = get_service_status()
        print(f"Service status: {status}")
    elif args.action == 'test':
        test_service()
    elif args.action == 'diagnose':
        diagnose_service()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"ERROR: {str(e)}")
        print(f"Check log for details: {log_file}")
    
    # If running by double-clicking, keep console window open
    if len(sys.argv) <= 1:
        print("\nUsage: standalone_service.py [install|uninstall|start|stop|status|test|diagnose]")
        print("\nPress Enter to exit...")
        input()
