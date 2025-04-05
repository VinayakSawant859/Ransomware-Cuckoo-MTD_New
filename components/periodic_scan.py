from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QGroupBox, QCheckBox, QComboBox, QSpinBox,
                           QTextBrowser, QFrame, QScrollArea, QFileDialog, QListWidget)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon
import json
import os
import time
import logging
import hashlib
import glob
import shutil
from datetime import datetime
from pathlib import Path
import traceback
import sys
from prevention.moving_target_defense import rotate_file_paths

class PeriodicScanWorker(QThread):
    """Worker thread for performing periodic scans of the system"""
    
    # Signals
    scan_started = pyqtSignal()
    scan_progress = pyqtSignal(int, str)  # progress percentage, message
    scan_completed = pyqtSignal(dict)  # scan results
    suspicious_files_found = pyqtSignal(list)  # signal for suspicious files
    
    def __init__(self, config_file="config/schedule_config.json"):
        super().__init__()
        self.running = True
        self.config_file = config_file
        self.last_scan_time = 0
        self.suspicious_extensions = [
            '.locked', '.encrypted', '.crypto', '.crypt', '.crypted', 
            '.crypz', '.encrypt', '.enc', '.ezz', '.exx', '.wncry', 
            '.locky', '.kraken', '.cerber', '.zzz'
        ]
        self.custom_scan_directories = ["test_data"]  # Default directory
        
        # Default to disabled
        self.enabled = False
        
        # Setup logging
        self.logger = self.setup_logging()
        self.load_config()
        
    def setup_logging(self):
        """Set up logging configuration"""
        logger = logging.getLogger('PeriodicScan')
        logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create handler if not already created
        if not logger.handlers:
            handler = logging.FileHandler('logs/periodic_scan.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            # Also add console handler for debugging
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.addHandler(console)
        
        return logger
        
    def load_config(self):
        """Load scan configuration from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.enabled = config.get('enabled', False)
                self.frequency = config.get('frequency', 'Hourly')
                self.hours = config.get('hours', 1)
                self.minutes = config.get('minutes', 0)
                self.seconds = config.get('seconds', 0)
                
                # Load custom directories if available
                if 'scan_directories' in config:
                    self.custom_scan_directories = config.get('scan_directories', ["test_data"])
                
                # Calculate interval in seconds
                if self.frequency == 'Custom':
                    self.interval = (self.hours * 3600) + (self.minutes * 60) + self.seconds
                elif self.frequency == 'Daily':
                    self.interval = 86400  # 24 hours
                elif self.frequency == 'Hourly':
                    self.interval = 3600  # 1 hour
                else:  # Default to 30 minutes
                    self.interval = 1800
                
                # Get last scan time if available
                if 'last_scan' in config:
                    try:
                        last_scan_str = config.get('last_scan')
                        last_scan_dt = datetime.strptime(last_scan_str, '%Y-%m-%d %H:%M:%S')
                        self.last_scan_time = last_scan_dt.timestamp()
                    except Exception as e:
                        self.logger.error(f"Error parsing last scan time: {e}")
                        self.last_scan_time = 0
            else:
                # Default settings
                self.enabled = False
                self.frequency = 'Hourly'
                self.interval = 3600
                self.hours = 1
                self.minutes = 0
                self.seconds = 0
                
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.logger.error(traceback.format_exc())
            # Default settings
            self.enabled = False
            self.frequency = 'Hourly'
            self.interval = 3600
            self.hours = 1
            self.minutes = 0
            self.seconds = 0
    
    def update_config(self, enabled=None, frequency=None, hours=None, minutes=None, seconds=None, scan_directories=None):
        """Update scan configuration"""
        try:
            if enabled is not None:
                self.enabled = enabled
            if frequency is not None:
                self.frequency = frequency
            if hours is not None:
                self.hours = hours
            if minutes is not None:
                self.minutes = minutes
            if seconds is not None:
                self.seconds = seconds
            if scan_directories is not None:
                self.custom_scan_directories = scan_directories
                
            # Calculate new interval
            if self.frequency == 'Custom':
                self.interval = (self.hours * 3600) + (self.minutes * 60) + self.seconds
            elif self.frequency == 'Daily':
                self.interval = 86400  # 24 hours
            elif self.frequency == 'Hourly':
                self.interval = 3600  # 1 hour
            else:  # Default to 30 minutes
                self.interval = 1800
                
            # Save to config file
            config = {
                'enabled': self.enabled,
                'frequency': self.frequency,
                'hours': self.hours,
                'minutes': self.minutes,
                'seconds': self.seconds,
                'scan_directories': self.custom_scan_directories
            }
            
            # Preserve last scan and history
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f:
                        old_config = json.load(f)
                    if 'last_scan' in old_config:
                        config['last_scan'] = old_config['last_scan']
                    if 'history' in old_config:
                        config['history'] = old_config['history']
                except Exception as e:
                    self.logger.error(f"Error reading old config: {e}")
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
                
            return True
        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    def run(self):
        """Run periodic scanning in a background thread"""
        self.logger.info("Periodic scan thread started")
        
        while self.running:
            try:
                # Check if scanning is enabled
                if self.enabled:
                    current_time = time.time()
                    time_since_last_scan = current_time - self.last_scan_time
                    
                    # Check if it's time for a scan
                    if time_since_last_scan >= self.interval:
                        # Update last scan time
                        self.last_scan_time = current_time
                        last_scan_str = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Update config with last scan time
                        try:
                            if os.path.exists(self.config_file):
                                with open(self.config_file, 'r') as f:
                                    config = json.load(f)
                            else:
                                config = {
                                    'enabled': self.enabled,
                                    'frequency': self.frequency,
                                    'hours': self.hours,
                                    'minutes': self.minutes,
                                    'seconds': self.seconds,
                                    'scan_directories': self.custom_scan_directories,
                                    'history': []
                                }
                                
                            config['last_scan'] = last_scan_str
                            
                            with open(self.config_file, 'w') as f:
                                json.dump(config, f)
                        except Exception as e:
                            self.logger.error(f"Error updating last scan time: {e}")
                            self.logger.error(traceback.format_exc())
                        
                        # Perform the scan
                        self.logger.info(f"Starting scheduled scan at {last_scan_str}")
                        self.scan_started.emit()
                        
                        # Perform the scan
                        scan_results = self.perform_scan()
                        
                        # Update scan history
                        self.update_scan_history(scan_results)
                        
                        # Emit completion signal
                        self.scan_completed.emit(scan_results)
                        
                        # Check for suspicious files and emit signal if found
                        if scan_results["suspicious_files"]:
                            self.suspicious_files_found.emit(scan_results["suspicious_files"])
                        
                # Short sleep to keep CPU usage low
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error in periodic scan thread: {e}")
                self.logger.error(traceback.format_exc())
                time.sleep(5)  # Longer sleep on error
    
    def perform_scan(self):
        """Perform a comprehensive system scan"""
        self.logger.info("Performing periodic scan")
        scan_results = {
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "suspicious_files": [],
            "total_files_scanned": 0,
            "threat_level": "Normal"
        }
        
        # Initialize directories to scan
        dirs_to_scan = self.custom_scan_directories
        
        # Log the directories being scanned
        self.logger.info(f"Scanning directories: {dirs_to_scan}")
        
        # Ensure suspicious_mtd directory exists
        os.makedirs("suspicious_mtd", exist_ok=True)
        
        # Track scan progress
        total_files = 0
        scanned_files = 0
        
        # First, count total files for progress tracking
        for scan_dir in dirs_to_scan:
            if os.path.exists(scan_dir):
                for root, _, files in os.walk(scan_dir):
                    total_files += len(files)
                    self.logger.debug(f"Found {len(files)} files in {root}")
            else:
                self.logger.warning(f"Directory {scan_dir} does not exist")
        
        self.logger.info(f"Found total of {total_files} files to scan")
        
        # Scan each directory
        for scan_dir in dirs_to_scan:
            if not os.path.exists(scan_dir):
                self.logger.warning(f"Directory {scan_dir} does not exist, skipping")
                continue
                
            self.scan_progress.emit(10, f"Scanning directory: {scan_dir}")
            self.logger.info(f"Scanning directory: {scan_dir}")
            
            # Look specifically for suspicious extensions - Enhanced to properly detect .locked files
            for ext in self.suspicious_extensions:
                pattern = os.path.join(scan_dir, f"**/*{ext}")
                self.logger.debug(f"Searching for pattern: {pattern}")
                
                # Use glob to find all matching files recursively
                for filepath in glob.glob(pattern, recursive=True):
                    self.logger.info(f"Found suspicious file with pattern {pattern}: {filepath}")
                    
                    try:
                        if os.path.isfile(filepath):
                            # Get file info
                            filename = os.path.basename(filepath)
                            file_size = os.path.getsize(filepath)
                            mod_time = os.path.getmtime(filepath)
                            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                            file_hash = self.calculate_file_hash(filepath)
                            
                            self.logger.info(f"Processing suspicious file: {filepath} with extension {ext}")
                            
                            # Add to suspicious files
                            scan_results["suspicious_files"].append({
                                "path": filepath,
                                "name": filename,
                                "size": file_size,
                                "modified": mod_time_str,
                                "hash": file_hash,
                                "reason": f"Suspicious extension: {ext}"
                            })
                            
                            # Move to suspicious_mtd directory
                            dest_path = os.path.join("suspicious_mtd", filename)
                            try:
                                shutil.copy2(filepath, dest_path)
                                self.logger.info(f"Copied suspicious file to {dest_path}")
                            except Exception as e:
                                self.logger.error(f"Error copying suspicious file: {e}")
                                self.logger.error(traceback.format_exc())
                    except Exception as e:
                        self.logger.error(f"Error processing suspicious file {filepath}: {e}")
                        self.logger.error(traceback.format_exc())
            
            # Standard file scan for other suspicious behaviors
            for root, _, files in os.walk(scan_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    
                    # Update progress
                    scanned_files += 1
                    progress = min(10 + int(80 * scanned_files / max(1, total_files)), 90)
                    self.scan_progress.emit(progress, f"Scanning: {file}")
                    
                    # Skip already identified suspicious files
                    if any(info["path"] == filepath for info in scan_results["suspicious_files"]):
                        continue
                    
                    # Check for suspicious content or behavior
                    try:
                        is_suspicious, reason = self.check_file_suspicious(filepath)
                        
                        if is_suspicious:
                            # Get file info
                            filename = os.path.basename(filepath)
                            file_size = os.path.getsize(filepath)
                            mod_time = os.path.getmtime(filepath)
                            mod_time_str = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                            file_hash = self.calculate_file_hash(filepath)
                            
                            self.logger.info(f"Found suspicious file: {filepath}, reason: {reason}")
                            
                            # Add to suspicious files
                            scan_results["suspicious_files"].append({
                                "path": filepath,
                                "name": filename,
                                "size": file_size,
                                "modified": mod_time_str,
                                "hash": file_hash,
                                "reason": reason
                            })
                            
                            # Move to suspicious_mtd directory
                            dest_path = os.path.join("suspicious_mtd", filename)
                            try:
                                shutil.copy2(filepath, dest_path)
                                self.logger.info(f"Copied suspicious file to {dest_path}")
                            except Exception as e:
                                self.logger.error(f"Error copying suspicious file: {e}")
                                self.logger.error(traceback.format_exc())
                    except Exception as e:
                        self.logger.error(f"Error scanning file {filepath}: {e}")
                        self.logger.error(traceback.format_exc())
        
        # Update scan statistics
        scan_results["total_files_scanned"] = scanned_files
        
        # Determine threat level
        suspicious_count = len(scan_results["suspicious_files"])
        self.logger.info(f"Scan completed. Found {suspicious_count} suspicious files out of {scanned_files} total files")
        
        if suspicious_count > 10:
            scan_results["threat_level"] = "Severe"
        elif suspicious_count > 5:
            scan_results["threat_level"] = "High"
        elif suspicious_count > 0:
            scan_results["threat_level"] = "Moderate"
        else:
            scan_results["threat_level"] = "Normal"
            
        self.logger.info(f"Threat level determined to be: {scan_results['threat_level']}")
        self.scan_progress.emit(100, "Scan completed")
        
        return scan_results
    
    def quarantine_suspicious_files(self, suspicious_files):
        """
        Move suspicious files to quarantine using Moving Target Defense
        Returns tuple of (success, list of moved files)
        """
        self.logger.info(f"Quarantining {len(suspicious_files)} suspicious files")
        try:
            # Call the MTD function to move files
            success, moved_files = rotate_file_paths()
            self.logger.info(f"MTD quarantine result: success={success}, moved_files={len(moved_files)}")
            return success, moved_files
        except Exception as e:
            self.logger.error(f"Error quarantining files: {e}")
            self.logger.error(traceback.format_exc())
            return False, []
    
    def check_file_suspicious(self, filepath):
        """Check if a file is suspicious based on content and attributes"""
        try:
            filename = os.path.basename(filepath)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Check for suspicious extensions - primary check
            if file_ext in self.suspicious_extensions:
                self.logger.info(f"File has suspicious extension: {filepath} - {file_ext}")
                return True, f"Suspicious extension: {file_ext}"
            
            # Check file content for known signatures
            try:
                with open(filepath, 'rb') as f:
                    header = f.read(256)  # Read first 256 bytes
                    
                    # Check for encrypted file headers or ransomware markers
                    if b'ENCRYPTED' in header or b'LOCKED' in header:
                        self.logger.info(f"File contains encryption markers: {filepath}")
                        return True, "Contains encryption markers"
                    
                    # Check for suspicious executables
                    if file_ext == '.exe' and b'This program cannot be run' in header:
                        self.logger.info(f"Suspicious executable found: {filepath}")
                        return True, "Suspicious executable"
            except Exception as e:
                self.logger.error(f"Error reading file content: {filepath} - {e}")
            
            # Check for recently modified files with suspicious names
            try:
                mod_time = os.path.getmtime(filepath)
                if time.time() - mod_time < 3600:  # Modified in the last hour
                    lower_filename = filename.lower()
                    if 'ransom' in lower_filename or 'crypt' in lower_filename or 'locked' in lower_filename:
                        self.logger.info(f"Recently modified suspicious filename: {filepath}")
                        return True, "Recently modified suspicious filename"
            except Exception as e:
                self.logger.error(f"Error checking modification time: {filepath} - {e}")
                
            return False, ""
            
        except Exception as e:
            self.logger.error(f"Error checking if file is suspicious {filepath}: {e}")
            self.logger.error(traceback.format_exc())
            return False, ""
    
    def calculate_file_hash(self, filepath):
        """Calculate MD5 hash of a file"""
        try:
            md5_hash = hashlib.md5()
            with open(filepath, "rb") as f:
                # Read the file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {e}")
            self.logger.error(traceback.format_exc())
            return "error-calculating-hash"
    
    def update_scan_history(self, scan_results):
        """Update scan history in the config file"""
        try:
            # Load existing config
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {
                    'enabled': self.enabled,
                    'frequency': self.frequency,
                    'hours': self.hours,
                    'minutes': self.minutes,
                    'seconds': self.seconds,
                    'scan_directories': self.custom_scan_directories,
                    'history': []
                }
            
            # Format scan results for history
            interval_text = ''
            if self.frequency == 'Custom':
                interval_text = f"{self.hours}h {self.minutes}m {self.seconds}s"
            else:
                interval_text = self.frequency.lower()
            
            # Determine threat level color based on result
            threat_level = scan_results["threat_level"]
            threat_color = "#4caf50"  # Default green for Normal
            
            if threat_level == "Severe":
                threat_color = "#f44336"  # Red for Severe
            elif threat_level == "High":
                threat_color = "#ff5722"  # Deep Orange for High
            elif threat_level == "Moderate":
                threat_color = "#ff9800"  # Orange for Moderate
                
            # Create HTML summary with proper threat level color
            html_summary = f"""<html><body><p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600; color:#1976d2;">⏱️ PERIODIC SCAN</span> completed at {scan_results["scan_time"]}<br /><span style=" font-size:small; color:#666666;">→ Configured with {self.frequency.lower()} ({self.hours}h {self.minutes}m {self.seconds}s) interval</span><br /><span style=" font-size:small; color:{threat_color};">→ Threat level: </span><span style=" font-size:small; font-weight:600; color:{threat_color};">{threat_level}</span></p></body></html>"""
            
            # Add suspicious file count if any were found
            suspicious_count = len(scan_results["suspicious_files"])
            if suspicious_count > 0:
                self.logger.info(f"Adding {suspicious_count} suspicious files to scan history")
                html_summary = html_summary.replace("</p></body></html>", f"<br /><span style=\" font-size:small; color:#666666;\">→ Found {suspicious_count} suspicious files</span></p></body></html>")
            
            # Update history
            if 'history' not in config:
                config['history'] = []
                
            # Add to history (limit to 50 entries)
            config['history'].append(html_summary)
            if len(config['history']) > 50:
                config['history'] = config['history'][-50:]
                
            # Save updated config
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
                
        except Exception as e:
            self.logger.error(f"Error updating scan history: {e}")
            self.logger.error(traceback.format_exc())
    
    def stop(self):
        """Stop the background thread"""
        self.running = False
        self.wait()

class PeriodicScanTab(QWidget):
    # Add new signal for navigation to Prevention tab
    navigate_to_prevention = pyqtSignal()
    
    def __init__(self, parent=None, detection_callback=None):
        super().__init__(parent)
        self.detection_callback = detection_callback
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.run_scheduled_scan)
        
        # Create the worker thread
        self.worker = PeriodicScanWorker()
        self.worker.scan_completed.connect(self.on_scan_completed)
        self.worker.suspicious_files_found.connect(self.on_suspicious_files_found)
        self.worker.start()
        
        self.initUI()
        self.load_schedule_config()

    def initUI(self):
        # Main layout with scroll area for better responsiveness
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        scroll_layout.setSpacing(25)
        
        # Header with title and description
        header = QFrame()
        header.setStyleSheet("background-color: #1976D2; border-radius: 10px;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 25, 20, 25)
        
        title = QLabel("Automated Scan Scheduler")
        title.setFont(QFont('Helvetica', 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        desc = QLabel("Configure periodic scans to continuously monitor your system for ransomware threats")
        desc.setFont(QFont('Helvetica', 12))
        desc.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        desc.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(desc)
        
        scroll_layout.addWidget(header)
        
        # Directory selection section
        dir_card = QFrame()
        dir_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        dir_layout = QVBoxLayout(dir_card)
        
        # Card title
        dir_title = QLabel("Scan Directories")
        dir_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        dir_title.setStyleSheet("color: #333; margin-bottom: 5px;")
        dir_layout.addWidget(dir_title)
        
        # Card subtitle
        dir_subtitle = QLabel("Select which directories to monitor for suspicious files")
        dir_subtitle.setFont(QFont('Helvetica', 11))
        dir_subtitle.setStyleSheet("color: #666;")
        dir_layout.addWidget(dir_subtitle)
        
        dir_layout.addSpacing(10)
        
        # Directory list
        self.dir_list = QListWidget()
        self.dir_list.setMinimumHeight(100)
        self.dir_list.setMaximumHeight(150)
        self.dir_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 5px;
            }
        """)
        dir_layout.addWidget(self.dir_list)
        
        # Directory buttons
        dir_buttons = QHBoxLayout()
        
        add_dir_btn = QPushButton("Add Directory")
        add_dir_btn.setIcon(QIcon("drawable/add_icon.png"))
        add_dir_btn.setFont(QFont('Helvetica', 12))
        add_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        add_dir_btn.clicked.connect(self.add_directory)
        dir_buttons.addWidget(add_dir_btn)
        
        remove_dir_btn = QPushButton("Remove")
        remove_dir_btn.setIcon(QIcon("drawable/remove_icon.png"))
        remove_dir_btn.setFont(QFont('Helvetica', 12))
        remove_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        remove_dir_btn.clicked.connect(self.remove_directory)
        dir_buttons.addWidget(remove_dir_btn)
        
        dir_layout.addLayout(dir_buttons)
        
        # Apply directory settings button
        apply_dir_btn = QPushButton("Apply Directory Settings")
        apply_dir_btn.setFont(QFont('Helvetica', 12, QFont.Bold))
        apply_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        apply_dir_btn.clicked.connect(self.save_directory_settings)
        dir_layout.addWidget(apply_dir_btn, alignment=Qt.AlignRight)
        
        scroll_layout.addWidget(dir_card)
        
        # Schedule settings card
        settings_card = QFrame()
        settings_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        settings_layout = QVBoxLayout(settings_card)
        
        # Card title
        card_title = QLabel("Scan Schedule")
        card_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        card_title.setStyleSheet("color: #333; margin-bottom: 5px;")
        settings_layout.addWidget(card_title)
        
        # Card subtitle
        card_subtitle = QLabel("Set up when automatic scans should run")
        card_subtitle.setFont(QFont('Helvetica', 11))
        card_subtitle.setStyleSheet("color: #666;")
        settings_layout.addWidget(card_subtitle)
        
        settings_layout.addSpacing(10)
        
        # Enable switch with improved styling
        enable_container = QFrame()
        enable_layout = QHBoxLayout(enable_container)
        enable_layout.setContentsMargins(0, 0, 0, 0)
        
        self.enable_schedule = QCheckBox("Enable Automatic Scanning")
        self.enable_schedule.setFont(QFont('Helvetica', 14))
        self.enable_schedule.setStyleSheet("""
            QCheckBox {
                color: #1976D2;
            }
            QCheckBox::indicator {
                width: 24px;
                height: 24px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #E0E0E0;
                background-color: white;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #1976D2;
                border: 2px solid #1976D2;
                border-radius: 4px;
            }
        """)
        self.enable_schedule.toggled.connect(self.toggle_scheduling)
        enable_layout.addWidget(self.enable_schedule)
        
        # Status indicator
        self.status_indicator = QLabel("Inactive")
        self.status_indicator.setFont(QFont('Helvetica', 12))
        self.status_indicator.setStyleSheet("color: #F44336;")
        self.status_indicator.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        enable_layout.addWidget(self.status_indicator)
        
        settings_layout.addWidget(enable_container)
        
        # Frequency selector
        freq_container = QFrame()
        freq_container.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        freq_layout = QVBoxLayout(freq_container)
        
        freq_title = QLabel("Scan Frequency")
        freq_title.setFont(QFont('Helvetica', 12, QFont.Bold))
        freq_layout.addWidget(freq_title)
        
        freq_options = QHBoxLayout()
        
        # Option buttons instead of combobox
        self.hourly_btn = QPushButton("Hourly")
        self.daily_btn = QPushButton("Daily")
        self.custom_btn = QPushButton("Custom")
        
        for btn, option in [(self.hourly_btn, "Hourly"), 
                           (self.daily_btn, "Daily"),
                           (self.custom_btn, "Custom")]:
            btn.setCheckable(True)
            btn.setAutoExclusive(True)  # Make buttons act like radio buttons
            btn.setFont(QFont('Helvetica', 12))
            btn.clicked.connect(lambda checked, opt=option: self.set_frequency(opt))
            freq_options.addWidget(btn)
        
        freq_layout.addLayout(freq_options)
        
        # Custom time settings
        self.custom_frame = QFrame()
        custom_layout = QHBoxLayout(self.custom_frame)
        custom_layout.setContentsMargins(0, 15, 0, 5)
        
        # Time inputs
        time_inputs = QHBoxLayout()
        time_inputs.setSpacing(15)
        
        for unit, range_val in [("Hours", (0, 23)), ("Minutes", (0, 59)), ("Seconds", (10, 59))]:
            group = QFrame()
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            
            spin = QSpinBox()
            spin.setRange(*range_val)
            spin.setFont(QFont('Helvetica', 16))
            spin.setStyleSheet("""
                QSpinBox {
                    border: 2px solid #E0E0E0;
                    border-radius: 5px;
                    padding: 5px;
                    min-height: 40px;
                    min-width: 80px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    width: 20px;
                    border-radius: 3px;
                }
            """)
            
            if unit == "Hours": self.hours_spin = spin
            elif unit == "Minutes": self.minutes_spin = spin
            else: self.seconds_spin = spin
            
            label = QLabel(unit)
            label.setFont(QFont('Helvetica', 12))
            label.setAlignment(Qt.AlignCenter)
            
            group_layout.addWidget(spin)
            group_layout.addWidget(label)
            time_inputs.addWidget(group)
        
        custom_layout.addLayout(time_inputs)
        
        # Apply button
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setFont(QFont('Helvetica', 12, QFont.Bold))
        self.apply_btn.setFixedWidth(120)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.apply_btn.clicked.connect(self.on_custom_time_changed)
        custom_layout.addWidget(self.apply_btn, alignment=Qt.AlignBottom)
        
        self.custom_frame.setVisible(False)
        freq_layout.addWidget(self.custom_frame)
        
        settings_layout.addWidget(freq_container)
        
        # Next scan display
        next_scan_container = QFrame()
        next_scan_container.setStyleSheet("""
            QFrame {
                background: linear-gradient(135deg, #E3F2FD, #BBDEFB);
                border-radius: 8px;
                padding: 5px;
                margin-top: 10px;
            }
        """)
        next_scan_layout = QVBoxLayout(next_scan_container)
        
        next_scan_title = QLabel("⏱️ NEXT SCHEDULED SCAN")
        next_scan_title.setFont(QFont('Helvetica', 12, QFont.Bold))
        next_scan_title.setStyleSheet("color: #0D47A1;")
        next_scan_title.setAlignment(Qt.AlignCenter)
        next_scan_layout.addWidget(next_scan_title)
        
        self.next_scan_label = QLabel("Not Scheduled")
        self.next_scan_label.setFont(QFont('Helvetica', 14))
        self.next_scan_label.setStyleSheet("color: #1565C0;")
        self.next_scan_label.setAlignment(Qt.AlignCenter)
        next_scan_layout.addWidget(self.next_scan_label)
        
        settings_layout.addWidget(next_scan_container)
        
        # Manual scan button
        manual_scan_btn = QPushButton("Run Manual Scan Now")
        manual_scan_btn.setFont(QFont('Helvetica', 14, QFont.Bold))
        manual_scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
                padding: 12px;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        manual_scan_btn.clicked.connect(self.run_manual_scan)
        settings_layout.addWidget(manual_scan_btn)
        
        scroll_layout.addWidget(settings_card)
        
        # History card
        history_card = QFrame()
        history_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        history_layout = QVBoxLayout(history_card)
        
        history_title = QLabel("Scan History")
        history_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        history_title.setStyleSheet("color: #333;")
        history_layout.addWidget(history_title)
        
        self.history_browser = QTextBrowser()
        self.history_browser.setFont(QFont('Helvetica', 12))
        self.history_browser.setMinimumHeight(200)
        self.history_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 10px;
            }
        """)
        history_layout.addWidget(self.history_browser)
        
        # Clear history button
        clear_btn = QPushButton("Clear History")
        clear_btn.setFont(QFont('Helvetica', 12))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #666;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        history_layout.addWidget(clear_btn, alignment=Qt.AlignRight)
        
        scroll_layout.addWidget(history_card)
        
        # Alert container for suspicious files (initially hidden)
        self.alert_container = QFrame()
        self.alert_container.setStyleSheet("""
            QFrame {
                background-color: #FFF3E0;
                border: 2px solid #FF9800;
                border-radius: 10px;
                padding: 10px;
                margin-top: 15px;
            }
        """)
        self.alert_container.setVisible(False)
        alert_layout = QVBoxLayout(self.alert_container)
        
        alert_title = QLabel("⚠️ SUSPICIOUS FILES DETECTED")
        alert_title.setFont(QFont('Helvetica', 14, QFont.Bold))
        alert_title.setStyleSheet("color: #E65100;")
        alert_title.setAlignment(Qt.AlignCenter)
        alert_layout.addWidget(alert_title)
        
        self.alert_details = QLabel()
        self.alert_details.setFont(QFont('Helvetica', 12))
        self.alert_details.setStyleSheet("color: #333;")
        self.alert_details.setWordWrap(True)
        alert_layout.addWidget(self.alert_details)
        
        # Go to prevention button
        go_to_prevention_btn = QPushButton("Go to Prevention Tab to Protect Files")
        go_to_prevention_btn.setFont(QFont('Helvetica', 12, QFont.Bold))
        go_to_prevention_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border-radius: 5px;
                padding: 10px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        go_to_prevention_btn.clicked.connect(self.go_to_prevention)
        alert_layout.addWidget(go_to_prevention_btn)
        
        scroll_layout.addWidget(self.alert_container)
        
        # Add stretch to push content to top
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def add_directory(self):
        """Add a directory to scan list"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if dir_path:
            # Check if already in list
            if self.dir_list.findItems(dir_path, Qt.MatchExactly):
                return
            
            self.dir_list.addItem(dir_path)

    def remove_directory(self):
        """Remove selected directory from scan list"""
        selected_items = self.dir_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.dir_list.takeItem(self.dir_list.row(item))

    def save_directory_settings(self):
        """Save directory settings to config"""
        directories = []
        for i in range(self.dir_list.count()):
            directories.append(self.dir_list.item(i).text())
        
        # Always ensure test_data is included for compatibility
        if "test_data" not in directories:
            directories.append("test_data")
            self.dir_list.addItem("test_data")
        
        # Update worker configuration
        self.worker.update_config(scan_directories=directories)
        
        # Show acknowledgment
        self.show_acknowledgment(f"Scan directories updated: {len(directories)} directories configured")

    def set_frequency(self, frequency):
        # Update custom frame visibility
        self.custom_frame.setVisible(frequency == "Custom")
        
        # Set button states
        self.hourly_btn.setChecked(frequency == "Hourly")
        self.daily_btn.setChecked(frequency == "Daily")
        self.custom_btn.setChecked(frequency == "Custom")
        
        # Update scheduling if enabled
        if self.enable_schedule.isChecked():
            self.start_scheduling(frequency)

    def toggle_scheduling(self, enabled):
        if enabled:
            # Get selected frequency
            if self.hourly_btn.isChecked():
                frequency = "Hourly"
            elif self.daily_btn.isChecked():
                frequency = "Daily"
            else:
                frequency = "Custom"
            
            # Update worker configuration
            self.worker.update_config(
                enabled=True,
                frequency=frequency,
                hours=self.hours_spin.value(),
                minutes=self.minutes_spin.value(),
                seconds=self.seconds_spin.value()
            )
            
            self.start_scheduling(frequency)
            self.status_indicator.setText("Active")
            self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.schedule_timer.stop()
            self.next_scan_label.setText("Not Scheduled")
            self.status_indicator.setText("Inactive")
            self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
            
            # Update worker configuration
            self.worker.update_config(enabled=False)
            
        self.save_schedule_config()

    def start_scheduling(self, frequency=None):
        if not frequency:
            if self.hourly_btn.isChecked():
                frequency = "Hourly"
            elif self.daily_btn.isChecked():
                frequency = "Daily"
            else:
                frequency = "Custom"
        
        if frequency == "Hourly":
            interval = 3600000  # 1 hour in ms
        elif frequency == "Daily":
            interval = 86400000  # 24 hours in ms
        else:  # Custom
            # Calculate milliseconds from hours, minutes and seconds
            hours = self.hours_spin.value()
            minutes = self.minutes_spin.value()
            seconds = self.seconds_spin.value()
            
            # Ensure we have at least some minimum time (10 seconds)
            if hours == 0 and minutes == 0 and seconds < 10:
                seconds = 10
                self.seconds_spin.setValue(10)
                
            total_seconds = hours * 3600 + minutes * 60 + seconds
            interval = total_seconds * 1000  # Convert to milliseconds
        
        # Start the timer
        self.schedule_timer.start(interval)
        
        # Update display
        next_scan = QDateTime.currentDateTime().addMSecs(interval)
        self.next_scan_label.setText(next_scan.toString('yyyy-MM-dd hh:mm:ss'))
        
        # Show active status
        self.status_indicator.setText("Active")
        self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def on_custom_time_changed(self):
        if self.enable_schedule.isChecked() and self.custom_btn.isChecked():
            hours = self.hours_spin.value()
            minutes = self.minutes_spin.value()
            seconds = self.seconds_spin.value()
            
            # Format a time string for display
            time_str = ""
            if hours > 0:
                time_str += f"{hours} hour{'s' if hours > 1 else ''} "
            if minutes > 0:
                time_str += f"{minutes} minute{'s' if minutes > 1 else ''} "
            if seconds > 0:
                time_str += f"{seconds} second{'s' if seconds > 1 else ''}"
            
            # Start scheduling with new time
            self.start_scheduling("Custom")
            self.save_schedule_config()
            
            # Show acknowledgment message
            self.show_acknowledgment(f"Custom schedule set: {time_str}")

    def show_acknowledgment(self, message):
        # Create temporary acknowledgment label with animation effect
        ack_label = QLabel(message)
        ack_label.setFont(QFont('Helvetica', 12))
        ack_label.setAlignment(Qt.AlignCenter)
        ack_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #4CAF50;
                border-radius: 5px;
                padding: 10px 15px;
            }
        """)
        
        # Add to layout temporarily below the next scan display
        parent_layout = self.next_scan_label.parent().layout()
        parent_layout.addWidget(ack_label)
        
        # Hide after 3 seconds
        QTimer.singleShot(3000, lambda: self.remove_acknowledgment(ack_label, parent_layout))

    def remove_acknowledgment(self, label, parent_layout):
        # Remove and delete the temporary acknowledgment label
        if label:
            parent_layout.removeWidget(label)
            label.deleteLater()

    def run_scheduled_scan(self):
        """Run a scheduled scan by triggering the worker thread"""
        # Only trigger scan if enabled
        if self.enable_schedule.isChecked():
            # Simulate triggering a scan in the worker thread
            self.worker.last_scan_time = 0  # Force an immediate scan
            
            # Show acknowledgment
            self.show_acknowledgment("Scheduled scan started")

    def run_manual_scan(self):
        """Manually trigger a scan"""
        # Force an immediate scan
        self.worker.last_scan_time = 0  
        
        # Show acknowledgment
        self.show_acknowledgment("Manual scan started")

    def on_scan_completed(self, results):
        """Handle scan results from worker thread"""
        # Update history with the scan results
        timestamp = QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        threat_level = results.get("threat_level", "Normal")
        suspicious_count = len(results.get("suspicious_files", []))
        
        # Determine color based on threat level
        if threat_level == "Severe":
            severity_color = "#f44336"  # Red
        elif threat_level == "High":
            severity_color = "#ff5722"  # Deep Orange
        elif threat_level == "Moderate":
            severity_color = "#ff9800"  # Orange
        else:
            severity_color = "#4CAF50"  # Green
        
        # Get frequency text
        if self.hourly_btn.isChecked():
            freq = "hourly"
        elif self.daily_btn.isChecked():
            freq = "daily"
        else:
            hours = self.hours_spin.value()
            minutes = self.minutes_spin.value()
            seconds = self.seconds_spin.value()
            freq = f"custom ({hours}h {minutes}m {seconds}s)"
        
        # Format the entry for the history browser
        history_entry = f"<p style='margin: 5px 0;'><b style='color: #1976D2;'>⏱️ PERIODIC SCAN</b> completed at {timestamp}<br/>"
        history_entry += f"<small style='color: #666; margin-left: 20px;'>→ Configured with {freq} interval</small>"
        history_entry += f"<br/><small style='color: {severity_color}; margin-left: 20px;'>→ Threat level: <b>{threat_level}</b></small>"
        
        # Add detected files if any
        if suspicious_count > 0:
            history_entry += f"<br/><small style='color: #666; margin-left: 20px;'>→ Found {suspicious_count} suspicious files</small>"
            
            # Add file details for the first few files
            max_files_to_show = min(suspicious_count, 3)
            history_entry += "<br/><small style='color: #666; margin-left: 30px;'>Files: "
            file_names = [results["suspicious_files"][i]["name"] for i in range(max_files_to_show)]
            history_entry += ", ".join(file_names)
            if suspicious_count > max_files_to_show:
                history_entry += f", and {suspicious_count - max_files_to_show} more"
            history_entry += "</small>"
        
        history_entry += "</p>"
        
        # Add to history browser
        self.history_browser.append(history_entry)
        
        # Update next scan time if enabled
        if self.enable_schedule.isChecked():
            # Calculate next scan time
            interval_ms = self.schedule_timer.interval()
            next_scan = QDateTime.currentDateTime().addMSecs(interval_ms)
            self.next_scan_label.setText(next_scan.toString('yyyy-MM-dd hh:mm:ss'))
        
        # Save updated history
        self.save_schedule_config()

    def on_suspicious_files_found(self, suspicious_files):
        """Handle suspicious files detected during scan"""
        if not suspicious_files:
            self.alert_container.setVisible(False)
            return
        
        # Show alert container
        self.alert_container.setVisible(True)
        
        # Format alert message
        file_count = len(suspicious_files)
        file_names = [f['name'] for f in suspicious_files[:3]]
        
        alert_text = f"Found {file_count} suspicious file"
        alert_text += "s" if file_count > 1 else ""
        alert_text += f": {', '.join(file_names)}"
        
        if file_count > 3:
            alert_text += f", and {file_count - 3} more"
        
        alert_text += "\n\nThese files may be ransomware-related and should be quarantined for safety."
        self.alert_details.setText(alert_text)
        
        # Offer quarantine functionality - automatically quarantine files
        success, moved_files = self.worker.quarantine_suspicious_files(suspicious_files)
        
        if success and moved_files:
            additional_text = f"\n\n✓ {len(moved_files)} file(s) automatically moved to secure quarantine."
            current_text = self.alert_details.text()
            self.alert_details.setText(current_text + additional_text)

    def go_to_prevention(self):
        """Navigate to Prevention tab"""
        # Emit signal to navigate to prevention tab
        self.navigate_to_prevention.emit()
        
        # Hide alert after navigation
        QTimer.singleShot(500, lambda: self.alert_container.setVisible(False))

    def clear_history(self):
        self.history_browser.clear()
        self.save_schedule_config()

    def load_schedule_config(self):
        try:
            with open('config/schedule_config.json', 'r') as f:
                config = json.load(f)
                
                # Set enable state
                self.enable_schedule.setChecked(config.get('enabled', False))
                
                # Set frequency
                frequency = config.get('frequency', 'Hourly')
                self.set_frequency(frequency)
                
                # Set time values
                self.hours_spin.setValue(config.get('hours', 0))
                self.minutes_spin.setValue(config.get('minutes', 30))
                self.seconds_spin.setValue(config.get('seconds', 0))
                
                # Load scan directories
                if 'scan_directories' in config:
                    directories = config.get('scan_directories', ["test_data"])
                    self.dir_list.clear()
                    for directory in directories:
                        self.dir_list.addItem(directory)
                else:
                    # Just add test_data as default
                    self.dir_list.clear()
                    self.dir_list.addItem("test_data")
                
                # Load history
                if 'history' in config and config['history']:
                    for entry in config['history']:
                        if entry:  # Only add non-empty entries
                            self.history_browser.append(entry)
                            
                # Update status indicator
                if self.enable_schedule.isChecked():
                    self.status_indicator.setText("Active")
                    self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
                else:
                    self.status_indicator.setText("Inactive")
                    self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
                    
        except FileNotFoundError:
            # Set defaults
            self.set_frequency("Hourly")
            self.hours_spin.setValue(0)
            self.minutes_spin.setValue(30)
            self.seconds_spin.setValue(0)
            # Add default directory
            self.dir_list.clear()
            self.dir_list.addItem("test_data")

    def save_schedule_config(self):
        # Get current frequency
        if self.hourly_btn.isChecked():
            frequency = "Hourly"
        elif self.daily_btn.isChecked():
            frequency = "Daily"
        else:
            frequency = "Custom"
            
        # Get scan directories
        directories = []
        for i in range(self.dir_list.count()):
            directories.append(self.dir_list.item(i).text())
            
        # Get history
        history = []
        html = self.history_browser.toHtml()
        for line in html.split('<p style='):
            if '⏱️ PERIODIC SCAN' in line:
                entry = line.strip()
                if entry:
                    history.append(entry)
        
        config = {
            'enabled': self.enable_schedule.isChecked(),
            'frequency': frequency,
            'hours': self.hours_spin.value(),
            'minutes': self.minutes_spin.value(),
            'seconds': self.seconds_spin.value(),
            'scan_directories': directories,
            'last_scan': QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss'),
            'history': history
        }
        
        os.makedirs('config', exist_ok=True)
        with open('config/schedule_config.json', 'w') as f:
            json.dump(config, f)
