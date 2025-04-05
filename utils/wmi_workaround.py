"""
WMI Workaround Module for Ransomware Detection

This module provides alternatives to directly using PyWin32's WMI functionality,
which often encounters issues with the 'winmgmt' typelib registration.
"""
import os
import sys
import subprocess
import platform
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'wmi_helper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WMIWorkaround")

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

def check_wmi_module():
    """Check if the WMI module is available and install it if needed"""
    try:
        import wmi
        logger.info("WMI module is already installed")
        return True
    except ImportError:
        logger.warning("WMI module not found, attempting to install it")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "wmi"])
            logger.info("WMI module installed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to install WMI module: {e}")
            return False

def get_system_info_wmi():
    """Get system information using the WMI module instead of PyWin32"""
    try:
        import wmi
        c = wmi.WMI()
        
        # Get OS information
        os_info = c.Win32_OperatingSystem()[0]
        
        # Get processor information
        cpu_info = c.Win32_Processor()[0]
        
        # Get memory information
        mem_info = c.Win32_ComputerSystem()[0]
        
        # Format the information
        system_info = {
            "os_name": os_info.Caption,
            "os_version": f"{os_info.Version} Build {os_info.BuildNumber}",
            "os_arch": os_info.OSArchitecture,
            "computer_name": os_info.CSName,
            "last_boot": os_info.LastBootUpTime,
            "cpu_name": cpu_info.Name,
            "cpu_cores": cpu_info.NumberOfCores,
            "cpu_threads": cpu_info.NumberOfLogicalProcessors,
            "total_memory_gb": round(int(mem_info.TotalPhysicalMemory) / (1024**3), 2)
        }
        
        logger.info("Successfully retrieved system information using WMI module")
        return system_info
    except Exception as e:
        logger.error(f"Error getting system info via WMI: {e}")
        logger.error(traceback.format_exc())
        return None

def get_running_processes_wmi():
    """Get list of running processes using WMI module"""
    try:
        import wmi
        c = wmi.WMI()
        processes = []
        
        for process in c.Win32_Process():
            try:
                processes.append({
                    "pid": process.ProcessId,
                    "name": process.Name,
                    "path": process.ExecutablePath or "",
                    "command_line": process.CommandLine or "",
                    "creation_time": process.CreationDate if hasattr(process, 'CreationDate') else "",
                    "memory_usage_kb": process.WorkingSetSize // 1024 if hasattr(process, 'WorkingSetSize') else 0
                })
            except Exception as inner_e:
                logger.warning(f"Error processing process {process.Name}: {inner_e}")
        
        logger.info(f"Successfully retrieved {len(processes)} running processes")
        return processes
    except Exception as e:
        logger.error(f"Error getting running processes via WMI: {e}")
        logger.error(traceback.format_exc())
        return None

def get_services_wmi():
    """Get list of Windows services using WMI module"""
    try:
        import wmi
        c = wmi.WMI()
        services = []
        
        for service in c.Win32_Service():
            services.append({
                "name": service.Name,
                "display_name": service.DisplayName,
                "status": service.State,
                "start_mode": service.StartMode,
                "path": service.PathName or ""
            })
        
        logger.info(f"Successfully retrieved {len(services)} Windows services")
        return services
    except Exception as e:
        logger.error(f"Error getting services via WMI: {e}")
        logger.error(traceback.format_exc())
        return None

def monitor_process_creation(callback=None, duration=60):
    """Monitor process creation for a specified duration (in seconds)"""
    try:
        import wmi
        import time
        
        c = wmi.WMI()
        process_watcher = c.Win32_Process.watch_for("creation")
        
        logger.info(f"Monitoring process creation for {duration} seconds...")
        end_time = time.time() + duration
        
        while time.time() < end_time:
            try:
                new_process = process_watcher(timeout_ms=1000)  # 1 second timeout
                if new_process:
                    process_info = {
                        "event": "process_created",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "pid": new_process.ProcessId,
                        "name": new_process.Name,
                        "path": new_process.ExecutablePath or "",
                        "command_line": new_process.CommandLine or ""
                    }
                    
                    logger.info(f"New process detected: {new_process.Name} (PID: {new_process.ProcessId})")
                    
                    # Call the callback function if provided
                    if callback and callable(callback):
                        callback(process_info)
            except Exception as inner_e:
                # Timeout or other error, continue monitoring
                pass
        
        logger.info("Process monitoring completed")
        return True
    except Exception as e:
        logger.error(f"Error monitoring processes via WMI: {e}")
        logger.error(traceback.format_exc())
        return False

def monitor_file_changes(path, callback=None, duration=60):
    """
    Monitor file changes in a specified directory using PowerShell instead of WMI
    This is a workaround since WMI file monitoring is difficult without proper typelib registration
    """
    try:
        # Create a PowerShell script that monitors file system changes
        ps_script = f"""
$folder = "{path}"
$filter = "*.*"  # Monitor all files
$fsw = New-Object System.IO.FileSystemWatcher $folder, $filter
$fsw.IncludeSubdirectories = $true
$fsw.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::DirectoryName

# Define events
$onChanged = Register-ObjectEvent $fsw "Changed" -Action {{
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "CHANGE,$timestamp,$name,$changeType"
}}

$onCreated = Register-ObjectEvent $fsw "Created" -Action {{
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "CREATE,$timestamp,$name,$changeType"
}}

$onDeleted = Register-ObjectEvent $fsw "Deleted" -Action {{
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "DELETE,$timestamp,$name,$changeType"
}}

$onRenamed = Register-ObjectEvent $fsw "Renamed" -Action {{
    $name = $Event.SourceEventArgs.Name
    $oldName = $Event.SourceEventArgs.OldName
    $changeType = $Event.SourceEventArgs.ChangeType
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "RENAME,$timestamp,$name,$oldName,$changeType"
}}

# Start monitoring
$fsw.EnableRaisingEvents = $true
Write-Host "START,File monitoring started,{path}"

# Run for the specified duration
Start-Sleep -Seconds {duration}

# Clean up
Unregister-Event -SourceIdentifier $onChanged.Name
Unregister-Event -SourceIdentifier $onCreated.Name
Unregister-Event -SourceIdentifier $onDeleted.Name
Unregister-Event -SourceIdentifier $onRenamed.Name
$fsw.EnableRaisingEvents = $false
$fsw.Dispose()
Write-Host "STOP,File monitoring stopped,{path}"
"""
        
        # Save the script to a temporary file
        temp_script = os.path.join(os.environ.get('TEMP', ''), 'file_monitor.ps1')
        with open(temp_script, 'w') as f:
            f.write(ps_script)
        
        logger.info(f"Monitoring file changes in '{path}' for {duration} seconds...")
        
        # Run the PowerShell script
        process = subprocess.Popen(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-File', temp_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Process the output
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line.startswith(("CHANGE", "CREATE", "DELETE", "RENAME")):
                    parts = line.split(",")
                    event_type = parts[0]
                    timestamp = parts[1]
                    file_name = parts[2]
                    
                    logger.info(f"File event: {event_type} - {file_name}")
                    
                    # Build event info
                    event_info = {
                        "event": event_type.lower(),
                        "timestamp": timestamp,
                        "file": file_name,
                        "path": os.path.join(path, file_name)
                    }
                    
                    # Add old name for rename events
                    if event_type == "RENAME" and len(parts) >= 4:
                        event_info["old_name"] = parts[3]
                    
                    # Call the callback function if provided
                    if callback and callable(callback):
                        callback(event_info)
        
        # Clean up
        try:
            os.remove(temp_script)
        except:
            pass
        
        logger.info("File monitoring completed")
        return True
    except Exception as e:
        logger.error(f"Error monitoring files: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("WMI Workaround Utility")
    print("======================")
    
    # Check for the WMI module
    print("\nChecking for WMI module...")
    if check_wmi_module():
        print("WMI module is available.")
    else:
        print("WMI module could not be installed. Some functionality may be limited.")
    
    print("\nGetting system information...")
    sys_info = get_system_info_wmi()
    if sys_info:
        print(f"OS: {sys_info['os_name']} {sys_info['os_version']} ({sys_info['os_arch']})")
        print(f"CPU: {sys_info['cpu_name']} ({sys_info['cpu_cores']} cores, {sys_info['cpu_threads']} threads)")
        print(f"Memory: {sys_info['total_memory_gb']} GB")
    
    # Example of using process monitoring
    print("\nWould you like to monitor processes for 10 seconds? (y/n)")
    choice = input().lower()
    if choice == 'y':
        def process_callback(info):
            print(f"New process: {info['name']} (PID: {info['pid']}) - Command: {info['command_line']}")
        
        print("Monitoring process creation for 10 seconds...")
        monitor_process_creation(process_callback, 10)
    
    print("\nWMI workaround utility completed.")
