import os
import sys
import time
import logging
import json
import hashlib
import threading
import glob
from pathlib import Path
import psutil
import re
import ctypes
import subprocess
from datetime import datetime

# Import our WMI workaround functions
from utils.wmi_workaround import get_system_info_wmi, monitor_process_creation, monitor_file_changes

class LightweightDetector:
    """Core library for ransomware detection with lightweight scanning capabilities"""
    
    def __init__(self, incremental=False, detection_level="medium"):
        self.logger = logging.getLogger('LightweightDetector')
        self.incremental = incremental
        self.detection_level = detection_level
        self.last_scan_data = {}
        self.known_signatures = self._load_signatures()
        self.critical_dirs = self._get_critical_directories()
        self.monitored_extensions = [
            '.docx', '.xlsx', '.pptx', '.pdf', '.zip', '.jpg', '.png',
            '.txt', '.csv', '.db', '.sql', '.mp3', '.mp4', '.avi'
        ]
        self.suspicious_extensions = [
            '.locked', '.encrypted', '.crypto', '.crypt', '.crypted',
            '.crypz', '.encrypt', '.enc', '.ezz', '.exx', '.wncry',
            '.locky', '.kraken', '.cerber', '.zzz'
        ]
        
        # Cache for file hashes to reduce disk I/O
        self.file_hash_cache = {}
        
        # Thread lock for synchronization
        self.lock = threading.RLock()
        
        # Get CPU cores for parallel processing
        self.cpu_count = max(1, psutil.cpu_count(logical=False) - 1)
        if self.cpu_count <= 0:
            self.cpu_count = 1
        
        # Initialize system info from WMI workaround
        self.system_info = get_system_info_wmi()
        if self.system_info:
            self.logger.info(f"System info obtained successfully: {self.system_info['os_name']} on {self.system_info['computer_name']}")
        else:
            self.logger.warning("Could not obtain system information via WMI")
            
        # Flag to control monitoring threads
        self.monitoring_active = False
        self.process_monitor_thread = None
        self.file_monitor_threads = {}
        
    def _load_signatures(self):
        """Load known ransomware signatures"""
        try:
            # Try multiple paths to find the signatures file
            possible_paths = [
                Path(__file__).parent / "data" / "ransomware_signatures.json",
                Path("core/data/ransomware_signatures.json"),
                Path("d:/Movies/Sanika/Ransomware Cuckoo-MTD_New/Ransomware Cuckoo-MTD_New/core/data/ransomware_signatures.json")
            ]
            
            for sig_file in possible_paths:
                if sig_file.exists():
                    with open(sig_file, 'r') as f:
                        return json.load(f)
                        
            # If we get here, create a default signatures file
            default_path = Path(__file__).parent / "data"
            default_path.mkdir(parents=True, exist_ok=True)
            default_sig_file = default_path / "ransomware_signatures.json"
            
            # Basic signatures
            signatures = {
                "e6f9fbac26eca66f0dbf23d5b762dc1d": "WannaCry",
                "5ff465afaabcbf0150d1a3ab2c2e74f0": "Petya"
            }
            
            with open(default_sig_file, 'w') as f:
                json.dump(signatures, f)
                
            return signatures
        except Exception as e:
            self.logger.error(f"Error loading signatures: {e}")
            return {}
            
    def _get_critical_directories(self):
        """Get list of critical directories to monitor"""
        dirs = []
        
        # Add user directories
        try:
            for user_dir in Path("C:/Users").glob("*"):
                if user_dir.is_dir() and not user_dir.name.endswith('$'):
                    dirs.append(str(user_dir / "Documents"))
                    dirs.append(str(user_dir / "Desktop"))
                    dirs.append(str(user_dir / "Downloads"))
                    dirs.append(str(user_dir / "Pictures"))
        except Exception as e:
            self.logger.error(f"Error getting user directories: {e}")
            
        # Add common system directories
        dirs.extend([
            "C:/ProgramData",
            "C:/Windows/Temp"
        ])
        
        # Filter to only existing directories
        return [d for d in dirs if os.path.exists(d)]
    
    def set_detection_level(self, level):
        """Change detection sensitivity level"""
        valid_levels = ["low", "medium", "high"]
        if level.lower() in valid_levels:
            self.detection_level = level.lower()
            return True
        return False
        
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash of a file with caching"""
        try:
            # Check if hash is in cache
            file_stats = os.stat(file_path)
            cache_key = f"{file_path}:{file_stats.st_mtime}:{file_stats.st_size}"
            
            with self.lock:
                if cache_key in self.file_hash_cache:
                    return self.file_hash_cache[cache_key]
            
            # Calculate hash if not cached
            md5_hash = hashlib.md5()
            
            with open(file_path, "rb") as f:
                # Read the file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    
            hash_result = md5_hash.hexdigest()
            
            # Update cache
            with self.lock:
                self.file_hash_cache[cache_key] = hash_result
                
            return hash_result
        except Exception as e:
            self.logger.debug(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def scan_file(self, file_path):
        """Scan a single file for suspicious attributes"""
        try:
            result = {
                "is_suspicious": False,
                "reasons": [],
                "last_checked": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Skip if file doesn't exist or isn't accessible
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                return None
                
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Check for suspicious extensions
            if file_ext in self.suspicious_extensions:
                result["is_suspicious"] = True
                result["reasons"].append(f"Suspicious extension: {file_ext}")
            
            # Skip further processing if not a monitored extension and not already suspicious
            if file_ext not in self.monitored_extensions and not result["is_suspicious"]:
                return None
                
            # Check file size - ransomware often produces files of similar sizes
            try:
                file_size = os.path.getsize(file_path)
                if 1024 <= file_size <= 4096:  # Small encrypted files often in this range
                    result["reasons"].append("Suspicious file size")
                    if self.detection_level != "low":  # Medium and high sensitivity
                        result["is_suspicious"] = True
            except:
                pass
                
            # For high detection level, calculate and check file hash
            if self.detection_level == "high":
                file_hash = self.calculate_file_hash(file_path)
                if file_hash and file_hash in self.known_signatures:
                    result["is_suspicious"] = True
                    result["reasons"].append(f"Matched known signature: {self.known_signatures[file_hash]}")
                
            # If file was modified in last 5 minutes, flag for monitoring
            try:
                mod_time = os.path.getmtime(file_path)
                if time.time() - mod_time < 300:  # 5 minutes
                    result["recently_modified"] = True
            except:
                pass
                
            return result
        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")
            return None
            
    def _scan_directory(self, directory, results):
        """Scan a single directory and its files"""
        try:
            if not os.path.exists(directory):
                return
                
            # Get all files in directory and immediate subdirectories
            file_paths = []
            for root, _, files in os.walk(directory, topdown=True):
                if os.path.abspath(root) != os.path.abspath(directory):
                    if len(root.split(os.sep)) - len(directory.split(os.sep)) > 2:
                        # Limit depth to reduce load
                        continue
                for file in files:
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)
                    
                    # Limit number of files to scan per directory
                    if len(file_paths) > 100 and self.detection_level != "high":
                        break
            
            # Process each file
            for file_path in file_paths:
                if self.incremental:
                    # Skip files that haven't changed since last scan
                    try:
                        last_mod_time = os.path.getmtime(file_path)
                        if file_path in self.last_scan_data and \
                           "last_modified" in self.last_scan_data[file_path] and \
                           self.last_scan_data[file_path]["last_modified"] >= last_mod_time:
                            # File hasn't changed, use cached result
                            results[file_path] = self.last_scan_data[file_path]["result"]
                            continue
                    except:
                        pass
                
                # Scan file
                file_result = self.scan_file(file_path)
                if file_result:
                    with self.lock:
                        results[file_path] = file_result
                        # Store last modified time for incremental scanning
                        if self.incremental:
                            if file_path not in self.last_scan_data:
                                self.last_scan_data[file_path] = {}
                            self.last_scan_data[file_path]["last_modified"] = os.path.getmtime(file_path)
                            self.last_scan_data[file_path]["result"] = file_result
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
            
    def check_system_indicators(self):
        """Check system-wide indicators of ransomware activity"""
        indicators = {
            "is_suspicious": False,
            "reasons": []
        }
        
        # Check for high CPU usage by suspicious processes
        try:
            suspicious_processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent']):
                # Skip system processes
                if proc.info['name'].lower() in ['system', 'registry', 'svchost.exe', 'services.exe']:
                    continue
                    
                # Flag high CPU usage
                if proc.info['cpu_percent'] > 70:
                    suspicious_processes.append(proc.info['name'])
            
            if suspicious_processes:
                indicators["reasons"].append(f"High CPU usage: {', '.join(suspicious_processes)}")
                if len(suspicious_processes) > 2:
                    indicators["is_suspicious"] = True
        except Exception as e:
            self.logger.error(f"Error checking processes: {e}")
            
        # Check for multiple file operations in short time (Windows only)
        try:
            # This would require a more sophisticated monitoring system
            # Here we're just checking if file activity seems high based on process open handles
            file_activity_count = 0
            
            for proc in psutil.process_iter(['name', 'open_files']):
                try:
                    if proc.info['open_files'] and len(proc.info['open_files']) > 10:
                        file_activity_count += 1
                except:
                    pass
                    
            if file_activity_count > 3:
                indicators["reasons"].append("High file I/O activity detected")
                indicators["is_suspicious"] = True
        except Exception as e:
            self.logger.debug(f"Error checking file activity: {e}")
        
        return indicators
        
    def run_scan(self, force_full_scan=False):
        """Run a complete scan including file and system checks"""
        start_time = time.time()
        self.logger.info(f"Starting {'full' if force_full_scan else 'incremental'} scan")
        
        # Reset incremental scanning if forced
        if force_full_scan and self.incremental:
            self.last_scan_data = {}
        
        # Create shared results dictionary
        scan_results = {}
        
        # Check system-wide indicators
        system_check = self.check_system_indicators()
        scan_results["_system_indicators"] = system_check
        
        # Scan directories in parallel
        threads = []
        for directory in self.critical_dirs:
            thread = threading.Thread(
                target=self._scan_directory,
                args=(directory, scan_results)
            )
            thread.start()
            threads.append(thread)
            
            # Limit concurrent threads to avoid overloading
            if len(threads) >= self.cpu_count:
                threads[0].join()
                threads.pop(0)
        
        # Wait for remaining threads
        for thread in threads:
            thread.join()
            
        # Log scan statistics
        scan_duration = time.time() - start_time
        suspicious_count = sum(1 for result in scan_results.values() if result.get("is_suspicious", False))
        self.logger.info(f"Scan complete in {scan_duration:.2f}s - {len(scan_results)} items checked, {suspicious_count} suspicious")
        
        return scan_results
        
    def start_monitoring(self):
        """Start background monitoring of processes and files"""
        if self.monitoring_active:
            return False
            
        self.monitoring_active = True
        self.logger.info("Starting background monitoring")
        
        # Start process monitoring in a separate thread
        self.process_monitor_thread = threading.Thread(
            target=self._process_monitor_loop,
            daemon=True
        )
        self.process_monitor_thread.start()
        
        # Start file monitoring for critical directories
        for directory in self.critical_dirs:
            if os.path.exists(directory):
                thread = threading.Thread(
                    target=self._file_monitor_loop,
                    args=(directory,),
                    daemon=True
                )
                thread.start()
                self.file_monitor_threads[directory] = thread
                
        return True
        
    def stop_monitoring(self):
        """Stop all monitoring activities"""
        self.monitoring_active = False
        self.logger.info("Stopping background monitoring")
        
        # Wait for threads to finish
        if self.process_monitor_thread and self.process_monitor_thread.is_alive():
            self.process_monitor_thread.join(timeout=2)
        
        for directory, thread in self.file_monitor_threads.items():
            if thread and thread.is_alive():
                thread.join(timeout=2)
                
        self.file_monitor_threads = {}
        
    def _process_monitor_loop(self):
        """Background loop for process monitoring"""
        while self.monitoring_active:
            try:
                monitor_process_creation(self._on_new_process_detected, duration=60)
                # Short sleep before next monitoring cycle
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in process monitoring: {e}")
                time.sleep(5)  # Longer sleep on error
                
    def _on_new_process_detected(self, process_info):
        """Handler for new process detection"""
        # Filter interesting processes
        suspicious = False
        reasons = []
        
        # Check for suspicious process names
        suspicious_names = ["encrypt", "ransom", "crypt", "locker", "wncry"]
        name = process_info.get("name", "").lower()
        
        for sus_name in suspicious_names:
            if sus_name in name:
                suspicious = True
                reasons.append(f"Suspicious process name: {name}")
                break
                
        # Check for suspicious command line arguments
        cmd_line = process_info.get("command_line", "").lower()
        if any(item in cmd_line for item in ["/encrypt", "-encrypt", "encrypt", "ransom"]):
            suspicious = True
            reasons.append(f"Suspicious command line: {cmd_line}")
            
        # Log findings
        if suspicious:
            self.logger.warning(f"Suspicious process detected: {process_info['name']} (PID: {process_info['pid']})")
            for reason in reasons:
                self.logger.warning(f"  Reason: {reason}")
                
            # In a real system, you might want to take some protective action here
            # Such as:
            # 1. Alerting the user
            # 2. Temporarily suspending the process
            # 3. Adding to quarantine list
                
        else:
            self.logger.debug(f"Normal process detected: {process_info['name']} (PID: {process_info['pid']})")
            
    def _file_monitor_loop(self, directory):
        """Background loop for file monitoring in a specific directory"""
        while self.monitoring_active:
            try:
                monitor_file_changes(directory, self._on_file_changed, duration=120)
                # Short sleep before next monitoring cycle
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error monitoring files in {directory}: {e}")
                time.sleep(5)  # Longer sleep on error
                
    def _on_file_changed(self, file_event):
        """Handler for file change detection"""
        # Check if this is a suspicious change
        event_type = file_event.get("event", "").lower()
        file_path = file_event.get("path", "")
        file_name = file_event.get("file", "")
        
        if not file_path or not os.path.exists(file_path):
            return
            
        # Most important to check for file extension changes and new suspicious extensions
        _, ext = os.path.splitext(file_name)
        
        if ext.lower() in self.suspicious_extensions:
            self.logger.warning(f"Suspicious file detected: {file_path} - Event: {event_type}")
            
            # Check if this is a legitimate file that was just changed
            orig_name = file_event.get("old_name", "")
            if orig_name and event_type == "rename":
                self.logger.warning(f"Possible encryption of file: {orig_name} → {file_name}")
                
            # In a real system, you would take protective actions here
            # Such as:
            # 1. Backup the original file if available
            # 2. Alert the user
            # 3. Add to quarantine list
        
        # Also check for rapid creation of many files (potentially mass encryption)
        # This would require keeping state across calls, which this stub doesn't implement
