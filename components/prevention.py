from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                           QMessageBox, QProgressBar, QTabWidget, QFileDialog, QDialog, QPlainTextEdit,
                           QSplitter, QCheckBox, QSpinBox, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor
import os
import sys
import time
import shutil

# Use system path to import utils module
sys.path.append("D:/Movies/Sanika/Ransomware Cuckoo-MTD_New/Ransomware Cuckoo-MTD_New")
from utils.file_operations import rotate_file_paths, scan_directory
from utils.file_hopper import get_file_hopper

class PreventionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize file hopper
        self.file_hopper = get_file_hopper()
        self.file_hopper.hop_interval = 60  # Set default hop interval to 60 seconds
        self.initUI()
        
    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        
        # Header with title and description
        header = QFrame()
        header.setStyleSheet("background-color: #f8f9fa; border-radius: 10px;")
        header_layout = QVBoxLayout(header)
        
        # Title
        title = QLabel("Ransomware Prevention & File Security")
        title.setFont(QFont("Helvetica", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        # Description
        description = QLabel("Monitor and secure files using Moving Target Defense to prevent ransomware attacks")
        description.setFont(QFont("Helvetica", 11))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #555555;")
        header_layout.addWidget(description)
        
        main_layout.addWidget(header)
        
        # Statistics bar
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        
        # Create stat panels
        self.monitored_files = self.create_stat_panel("Monitored Files", "0")
        self.suspicious_files = self.create_stat_panel("Suspicious Files", "0")
        self.quarantined_files = self.create_stat_panel("Quarantined Files", "0")
        
        stats_layout.addWidget(self.monitored_files)
        stats_layout.addWidget(self.suspicious_files)
        stats_layout.addWidget(self.quarantined_files)
        
        main_layout.addWidget(stats_frame)
        
        # Create tab widget for different prevention functions
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #333333;
                padding: 15px 35px;  /* Increased padding */
                margin: 1px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 16px;  /* Increased font size */
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #64B5F6;
                color: white;
            }
        """)

        # Create and add tabs
        monitor_tab = self.create_monitor_tab()
        mtd_tab = self.create_mtd_tab()
        quarantine_tab = self.create_quarantine_tab()

        tabs.addTab(monitor_tab, "File Monitor")
        tabs.addTab(mtd_tab, "Moving Target Defense")
        tabs.addTab(quarantine_tab, "Quarantine Management")
        
        main_layout.addWidget(tabs)

        # Refresh statistics on start
        self.refresh_statistics()

    def create_stat_panel(self, title, value):
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        layout = QVBoxLayout(panel)
        title_label = QLabel(title)
        title_label.setFont(QFont("Helvetica", 10))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #777777;")
        layout.addWidget(title_label)
        value_label = QLabel(value)
        value_label.setFont(QFont("Helvetica", 16, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName(f"{title.lower().replace(' ', '_')}_value")
        layout.addWidget(value_label)
        return panel
        
    def create_monitor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Controls area
        controls = QFrame()
        controls_layout = QHBoxLayout(controls)
        
        # Scan button
        scan_btn = QPushButton("Scan Directories")
        scan_btn.setIcon(QIcon("drawable/scan_icon.png"))
        scan_btn.setIconSize(QSize(16, 16))
        scan_btn.setMinimumHeight(40)
        scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        scan_btn.clicked.connect(self.scan_directories)
        controls_layout.addWidget(scan_btn)
        
        # Select directory button
        select_dir_btn = QPushButton("Select Directory")
        select_dir_btn.setIcon(QIcon("drawable/folder_icon.png"))
        select_dir_btn.setIconSize(QSize(16, 16))
        select_dir_btn.setMinimumHeight(40)
        select_dir_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        select_dir_btn.clicked.connect(self.select_directory)
        controls_layout.addWidget(select_dir_btn)
        layout.addWidget(controls)
        
        # Status bar
        self.status_bar = QLabel("Ready to scan")
        self.status_bar.setFont(QFont("Helvetica", 10))
        self.status_bar.setStyleSheet("color: #777777; padding: 5px; background-color: #f5f5f5; border-radius: 5px;")
        layout.addWidget(self.status_bar)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f5f5f5;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Files table
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(["Filename", "Path", "Status", "Action"])
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.files_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.files_table.setAlternatingRowColors(True)
        self.files_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.files_table)
        
        return tab
        
    def create_mtd_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # MTD Controls
        controls = QFrame()
        controls_layout = QHBoxLayout(controls)
        
        # Start MTD button with larger text
        self.mtd_start_btn = QPushButton("Start Moving Target Defense")
        self.mtd_start_btn.setIcon(QIcon("drawable/shield_icon.png"))
        self.mtd_start_btn.setIconSize(QSize(24, 24))  # Increased icon size
        self.mtd_start_btn.setMinimumHeight(60)  # Increased height
        self.mtd_start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                border-radius: 5px;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 16px;  /* Increased font size */
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        self.mtd_start_btn.clicked.connect(self.start_mtd)
        controls_layout.addWidget(self.mtd_start_btn)
        layout.addWidget(controls)
        
        # MTD Status
        self.mtd_status = QLabel("Moving Target Defense is ready")
        self.mtd_status.setFont(QFont("Helvetica", 12, QFont.Bold))
        self.mtd_status.setAlignment(Qt.AlignCenter)
        self.mtd_status.setStyleSheet("color: #555555; padding: 15px;")
        layout.addWidget(self.mtd_status)
        
        # MTD History table
        self.mtd_table = QTableWidget()
        self.mtd_table.setColumnCount(3)
        self.mtd_table.setHorizontalHeaderLabels(["Source", "Destination", "Timestamp"])
        self.mtd_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mtd_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mtd_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.mtd_table.setAlternatingRowColors(True)
        self.mtd_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.mtd_table)
        
        # Load MTD history if available
        self.load_mtd_history()
        
        return tab
        
    def create_quarantine_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Quarantine info
        info = QLabel("Safely view and manage quarantined files")
        info.setFont(QFont("Helvetica", 11))
        info.setStyleSheet("color: #555555;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        # Create tabs for different quarantine views
        quarantine_tabs = QTabWidget()
        quarantine_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #f0f0f0;
                color: #333333;
                padding: 8px 20px;
                margin: 1px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #64B5F6;
                color: white;
            }
        """)
        
        # Create main quarantine tab
        quarantine_files_tab = QWidget()
        quarantine_files_layout = QVBoxLayout(quarantine_files_tab)
        
        # Quarantine table
        self.quarantine_table = QTableWidget()
        self.quarantine_table.setColumnCount(4)
        self.quarantine_table.setHorizontalHeaderLabels(["Filename", "Original Path", "Quarantined On", "Actions"])
        self.quarantine_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.quarantine_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.quarantine_table.setAlternatingRowColors(True)
        self.quarantine_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        quarantine_files_layout.addWidget(self.quarantine_table)
        
        # Create hopping logs tab
        hopping_logs_tab = QWidget()
        hopping_logs_layout = QVBoxLayout(hopping_logs_tab)
        
        # Hopping control frame
        hopping_control_frame = QFrame()
        hopping_control_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 10px;")
        hopping_control_layout = QHBoxLayout(hopping_control_frame)
        
        # Add hopping controls
        hop_interval_label = QLabel("Hop Interval (seconds):")
        hop_interval_label.setFont(QFont("Helvetica", 10))
        hopping_control_layout.addWidget(hop_interval_label)
        
        self.hop_interval_spinner = QSpinBox()
        self.hop_interval_spinner.setRange(10, 3600)
        self.hop_interval_spinner.setValue(self.file_hopper.hop_interval)
        self.hop_interval_spinner.setFixedWidth(100)
        self.hop_interval_spinner.valueChanged.connect(self.update_hop_interval)
        hopping_control_layout.addWidget(self.hop_interval_spinner)
        
        # Add toggle button
        self.hopping_toggle_btn = QPushButton("Start File Hopping")
        self.hopping_toggle_btn.setCheckable(True)
        self.hopping_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:checked {
                background-color: #F44336;
            }
            QPushButton:checked:hover {
                background-color: #D32F2F;
            }
        """)
        self.hopping_toggle_btn.clicked.connect(self.toggle_file_hopping)
        hopping_control_layout.addWidget(self.hopping_toggle_btn)
        
        # Add spacer
        hopping_control_layout.addStretch()
        
        # Add refresh button
        refresh_logs_btn = QPushButton("Refresh Logs")
        refresh_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        refresh_logs_btn.clicked.connect(self.refresh_hopping_logs)
        hopping_control_layout.addWidget(refresh_logs_btn)
        
        hopping_logs_layout.addWidget(hopping_control_frame)
        
        # Hopping status label
        self.hopping_status = QLabel("File hopping is inactive")
        self.hopping_status.setFont(QFont("Helvetica", 11))
        self.hopping_status.setStyleSheet("color: #555555; padding: 10px;")
        self.hopping_status.setAlignment(Qt.AlignCenter)
        hopping_logs_layout.addWidget(self.hopping_status)
        
        # Hopping logs table
        self.hopping_logs_table = QTableWidget()
        self.hopping_logs_table.setColumnCount(4)
        self.hopping_logs_table.setHorizontalHeaderLabels(["Timestamp", "Filename", "Source", "Destination"])
        self.hopping_logs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.hopping_logs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.hopping_logs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.hopping_logs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.hopping_logs_table.setAlternatingRowColors(True)
        self.hopping_logs_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        hopping_logs_layout.addWidget(self.hopping_logs_table)
        
        # Add tabs to quarantine tabs
        quarantine_tabs.addTab(quarantine_files_tab, "Quarantined Files")
        quarantine_tabs.addTab(hopping_logs_tab, "File Hopping Logs")
        
        layout.addWidget(quarantine_tabs)
        
        # Load quarantine data
        self.load_quarantine_data()
        
        # Load hopping logs
        self.load_hopping_logs()
        
        return tab
    
    def update_hop_interval(self, value):
        """Update the hop interval for the file hopper"""
        self.file_hopper.hop_interval = value
        if self.file_hopper.running:
            # Show a message that the new interval will be applied on next hop
            status_msg = f"Hop interval updated to {value} seconds (applied on next hop)"
            self.hopping_status.setText(status_msg)
    
    def toggle_file_hopping(self, checked):
        """Toggle file hopping on/off"""
        if checked:
            # Start file hopping
            if self.file_hopper.start():
                self.hopping_toggle_btn.setText("Stop File Hopping")
                self.hopping_status.setText(f"File hopping is active (every {self.file_hopper.hop_interval} seconds)")
                self.hopping_status.setStyleSheet("color: #4CAF50; padding: 10px; font-weight: bold;")
            else:
                self.hopping_toggle_btn.setChecked(False)
                QMessageBox.warning(self, "Warning", "Could not start file hopping. See logs for details.")
        else:
            # Stop file hopping
            if self.file_hopper.stop():
                self.hopping_toggle_btn.setText("Start File Hopping")
                self.hopping_status.setText("File hopping is inactive")
                self.hopping_status.setStyleSheet("color: #555555; padding: 10px;")
            else:
                QMessageBox.warning(self, "Warning", "Could not stop file hopping. See logs for details.")
    
    def load_hopping_logs(self):
        """Load file hopping logs into the table"""
        self.hopping_logs_table.setRowCount(0)
        
        # Load from hop history
        hop_history = self.file_hopper.get_hop_history()
        
        # Also load from file if available
        if os.path.exists('prevention/file_hops.txt'):
            try:
                with open('prevention/file_hops.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if '->' in line and '@' in line:
                            file_path_part, timestamp_part = line.strip().split('@')
                            source, dest = file_path_part.strip().split('->')
                            hop_history.append({
                                'timestamp': timestamp_part.strip(),
                                'file': os.path.basename(dest.strip()),
                                'source': source.strip(),
                                'destination': dest.strip()
                            })
            except Exception as e:
                print(f"Error loading hop logs from file: {str(e)}")
        
        # Sort by timestamp (newest first)
        hop_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Add to table
        row = 0
        for hop in hop_history:
            self.hopping_logs_table.insertRow(row)
            
            # Add data
            self.hopping_logs_table.setItem(row, 0, QTableWidgetItem(hop.get('timestamp', '')))
            self.hopping_logs_table.setItem(row, 1, QTableWidgetItem(hop.get('file', '')))
            self.hopping_logs_table.setItem(row, 2, QTableWidgetItem(hop.get('source', '')))
            self.hopping_logs_table.setItem(row, 3, QTableWidgetItem(hop.get('destination', '')))
            
            row += 1
    
    def refresh_hopping_logs(self):
        """Refresh the hopping logs table"""
        self.load_hopping_logs()
        self.hopping_status.setText(
            f"File hopping is {'active' if self.file_hopper.running else 'inactive'}" + 
            (f" (every {self.file_hopper.hop_interval} seconds)" if self.file_hopper.running else "")
        )
        self.hopping_status.setStyleSheet(
            f"color: {'#4CAF50' if self.file_hopper.running else '#555555'}; padding: 10px;" + 
            (f"font-weight: bold;" if self.file_hopper.running else "")
        )
    
    def scan_directories(self):
        self.status_bar.setText("Scanning directory: test_data/")  # Added directory path
        self.progress_bar.setValue(10)
        
        # Simulate scanning progress
        QTimer.singleShot(500, lambda: self.progress_bar.setValue(30))
        QTimer.singleShot(1000, lambda: self.progress_bar.setValue(50))
        QTimer.singleShot(1500, lambda: self.progress_bar.setValue(70))
        QTimer.singleShot(2000, lambda: self.progress_bar.setValue(100))
        
        try:
            # Clear previous table data
            self.files_table.setRowCount(0)
            
            # Scan default directories
            dirs_to_scan = ["test_data"]
            self.scanned_files = []
            
            for directory in dirs_to_scan:
                if os.path.exists(directory):
                    self.status_bar.setText(f"Scanning directory: {os.path.abspath(directory)}")
                    results = scan_directory(directory)
                    self.scanned_files.extend(results)
            
            self.update_files_table(self.scanned_files)
            self.status_bar.setText(f"Scan complete. Found {len(self.scanned_files)} files.")
            self.progress_bar.setValue(100)
            self.refresh_statistics()
            
        except Exception as e:
            self.status_bar.setText(f"Error scanning: {str(e)}")
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Error", f"An error occurred while scanning: {str(e)}")

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory to Scan")
        if directory:
            self.status_bar.setText(f"Scanning directory: {directory}")
            self.progress_bar.setValue(10)
            
            try:
                # Clear previous table data
                self.files_table.setRowCount(0)
                
                results = scan_directory(directory)
                self.update_files_table(results)
                self.status_bar.setText(f"Scan complete. Found {len(results)} files in {directory}")
                self.progress_bar.setValue(100)
                self.refresh_statistics()
            except Exception as e:
                self.status_bar.setText(f"Error scanning: {str(e)}")
                self.progress_bar.setValue(0)
                QMessageBox.critical(self, "Error", f"An error occurred while scanning: {str(e)}")

    def start_mtd(self):
        self.mtd_start_btn.setEnabled(False)
        self.mtd_start_btn.setText("Processing...")
        self.mtd_status.setText("Running Moving Target Defense...")
        self.mtd_status.setStyleSheet("color: #2196F3; padding: 15px;")
        
        try:
            result, moved_files = rotate_file_paths()
            if result:
                # Group files by their movement stage
                detected_files = []
                secured_files = []
                
                for source, destination in moved_files:
                    if "suspicious_mtd" in destination:
                        detected_files.append(os.path.basename(source))
                    elif "safe_mtd" in destination:
                        secured_files.append(os.path.basename(source))
                
                # Get unique file count
                unique_files = len(set(detected_files + secured_files))
                
                self.mtd_status.setText(f"Prevention successful: {unique_files} {'file' if unique_files == 1 else 'files'} secured!")
                self.mtd_status.setStyleSheet("color: #4CAF50; padding: 15px;")
                
                # Update transfer text
                transfer_text = ""
                for file in detected_files:
                    transfer_text += f"🔍 Detected: {file}\n"
                for file in secured_files:
                    transfer_text += f"🛡️ Secured: {file}\n"
                
                if transfer_text:
                    QMessageBox.information(self, "File Transfers", 
                                          f"Moving Target Defense Results:\n\n{transfer_text}")
                
                # Ask user if they want to enable file hopping for secured files
                if secured_files and not self.file_hopper.running:
                    reply = QMessageBox.question(
                        self, 
                        "Enable File Hopping",
                        f"Do you want to enable automatic file hopping for the {len(secured_files)} secured files?\n\n"
                        "This will periodically move files between different locations to prevent attackers from targeting them.",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.file_hopper.start()
                        self.hopping_toggle_btn.setChecked(True)
                        self.hopping_toggle_btn.setText("Stop File Hopping")
                        self.hopping_status.setText(f"File hopping is active (every {self.file_hopper.hop_interval} seconds)")
                        self.hopping_status.setStyleSheet("color: #4CAF50; padding: 10px; font-weight: bold;")
                
                # Update tables and refresh data
                self.load_mtd_history()
                self.load_quarantine_data()
                self.load_hopping_logs()
                if hasattr(self, 'scanned_files'):
                    self.scan_directories()
                self.refresh_statistics()
                
            else:
                self.mtd_status.setText("No suspicious files found to secure.")
                self.mtd_status.setStyleSheet("color: #FF9800; padding: 15px;")
                
        except Exception as e:
            self.mtd_status.setText(f"Error: {str(e)}")
            self.mtd_status.setStyleSheet("color: #F44336; padding: 15px;")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        
        self.mtd_start_btn.setEnabled(True)
        self.mtd_start_btn.setText("Start Moving Target Defense")
    
    def update_files_table(self, files):
        self.files_table.setRowCount(0)  # Clear table
        row = 0
        for file_info in files:
            self.files_table.insertRow(row)
            filename = os.path.basename(file_info['path'])
            path = file_info['path']
            status = file_info['status']
            
            # Filename item
            self.files_table.setItem(row, 0, QTableWidgetItem(filename))
            
            # Path item
            self.files_table.setItem(row, 1, QTableWidgetItem(path))
            
            # Status item with color coding
            status_item = QTableWidgetItem(status)
            if status == "Suspicious":
                status_item.setForeground(QColor('#F44336'))  # Red for suspicious
                status_item.setFont(QFont("Helvetica", 9, QFont.Bold))
            elif status == "Quarantined":
                status_item.setForeground(QColor('#FF9800'))  # Orange for quarantined
            else:
                status_item.setForeground(QColor('#4CAF50'))  # Green for safe
            self.files_table.setItem(row, 2, status_item)
            
            # Add action button if file is suspicious
            if status == "Suspicious":
                action_btn = QPushButton("Quarantine")
                action_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 3px 8px;
                    }
                    QPushButton:hover {
                        background-color: #F57C00;
                    }
                """)
                action_btn.clicked.connect(lambda checked, p=path: self.quarantine_file(p))
                self.files_table.setCellWidget(row, 3, action_btn)
            
            row += 1
    
    def quarantine_file(self, path):
        try:
            # Show confirmation dialog
            filename = os.path.basename(path)
            reply = QMessageBox.question(self, 'Confirm Quarantine',
                                       f"Are you sure you want to quarantine file:\n{filename}?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                quarantine_dir = "safe_mtd"
                os.makedirs(quarantine_dir, exist_ok=True)
                
                quarantine_path = os.path.join(quarantine_dir, f"quarantined_{int(time.time())}_{filename}")
                shutil.move(path, quarantine_path)
                
                os.makedirs('prevention', exist_ok=True)
                with open('prevention/quarantine_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{path} -> {quarantine_path} @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                QMessageBox.information(self, "Success", 
                                      f"File has been quarantined successfully!\n\nSource: {path}\nDestination: {quarantine_path}")
                
                # Refresh the file table and other UI elements
                if hasattr(self, 'scanned_files'):
                    self.scan_directories()
                self.load_quarantine_data()
                self.refresh_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not quarantine file: {str(e)}")
    
    def load_mtd_history(self):
        self.mtd_table.setRowCount(0)
        
        try:
            # Helper function to check file existence and validity
            def file_exists(path):
                return os.path.exists(path) and os.path.getsize(path) > 0
            
            row = 0
            # First load transfers from suspicious_mtd log if it exists and has content
            if file_exists('prevention/suspicious_transfers.txt'):
                with open('prevention/suspicious_transfers.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        if '->' in line:
                            source, dest = line.strip().split('->')
                            # Verify source and destination still exist
                            if os.path.exists(source.strip()) or os.path.exists(dest.strip()):
                                self.mtd_table.insertRow(row)
                                self.mtd_table.setItem(row, 0, QTableWidgetItem(source.strip()))
                                self.mtd_table.setItem(row, 1, QTableWidgetItem(dest.strip()))
                                self.mtd_table.setItem(row, 2, QTableWidgetItem(time.strftime('%Y-%m-%d %H:%M')))
                                row += 1

            # Then load MTD routes
            if file_exists('prevention/mtd_routes.txt'):
                with open('prevention/mtd_routes.txt', 'r', encoding='utf-8') as f:
                    for line in reversed(f.readlines()):  # Show newest first
                        if '->' in line:
                            source, dest = line.strip().split('->')
                            # Verify source or destination still exists
                            if os.path.exists(source.strip()) or os.path.exists(dest.strip()):
                                self.mtd_table.insertRow(row)
                                self.mtd_table.setItem(row, 0, QTableWidgetItem(source.strip()))
                                self.mtd_table.setItem(row, 1, QTableWidgetItem(dest.strip()))
                                self.mtd_table.setItem(row, 2, QTableWidgetItem(time.strftime('%Y-%m-%d %H:%M')))
                                row += 1
                            
        except Exception as e:
            print(f"Error loading MTD history: {str(e)}")
    
    def load_quarantine_data(self):
        self.quarantine_table.setRowCount(0)
        
        try:
            quarantine_dir = "safe_mtd"
            if os.path.exists(quarantine_dir):
                # Get quarantine log data
                quarantine_data = {}
                if os.path.exists('prevention/quarantine_log.txt'):
                    with open('prevention/quarantine_log.txt', 'r', encoding='utf-8') as f:
                        for line in f:
                            if '->' in line and '@' in line:
                                path_part, time_part = line.strip().split('@')
                                source, dest = path_part.split('->')
                                quarantine_data[os.path.basename(dest.strip())] = {
                                    'original_path': source.strip(),
                                    'timestamp': time_part.strip()
                                }
                
                # Process files
                files = os.listdir(quarantine_dir)
                row = 0
                for file in files:
                    file_path = os.path.join(quarantine_dir, file)
                    if os.path.isfile(file_path):
                        self.quarantine_table.insertRow(row)
                        
                        # Get file info from quarantine data if available
                        if file in quarantine_data:
                            original_path = quarantine_data[file]['original_path']
                            quarantine_time = quarantine_data[file]['timestamp']
                        else:
                            # Extract info from filename for legacy files
                            parts = file.split("_")
                            if len(parts) > 2 and parts[0] == "quarantined":
                                original_path = "Unknown (Pre-existing)"
                                try:
                                    timestamp = int(parts[1])
                                    quarantine_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(timestamp))
                                except:
                                    quarantine_time = "Unknown"
                            else:
                                original_path = "Unknown"
                                quarantine_time = "Unknown"
                        
                        self.quarantine_table.setItem(row, 0, QTableWidgetItem(file))
                        self.quarantine_table.setItem(row, 1, QTableWidgetItem(original_path))
                        self.quarantine_table.setItem(row, 2, QTableWidgetItem(quarantine_time))
                        
                        # Add action buttons in a container
                        actions_widget = QWidget()
                        actions_layout = QHBoxLayout(actions_widget)
                        actions_layout.setContentsMargins(2, 2, 2, 2)
                        actions_layout.setSpacing(5)  # Add space between buttons
                        
                        # View button
                        view_btn = QPushButton("View")
                        view_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #2196F3;
                                color: white;
                                border: none;
                                border-radius: 3px;
                                padding: 3px 8px;
                            }
                            QPushButton:hover {
                                background-color: #1976D2;
                            }
                        """)
                        view_btn.clicked.connect(lambda checked, f=file_path: self.view_quarantined_file(f))
                        actions_layout.addWidget(view_btn)
                        
                        # Delete button
                        delete_btn = QPushButton("Delete")
                        delete_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #F44336;
                                color: white;
                                border: none;
                                border-radius: 3px;
                                padding: 3px 8px;
                            }
                            QPushButton:hover {
                                background-color: #D32F2F;
                            }
                        """)
                        delete_btn.clicked.connect(lambda checked, f=file: self.delete_quarantined(f))
                        actions_layout.addWidget(delete_btn)
                        
                        self.quarantine_table.setCellWidget(row, 3, actions_widget)
                        row += 1
                        
        except Exception as e:
            print(f"Error loading quarantine data: {str(e)}")

    def view_quarantined_file(self, file_path):
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create view dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("View Quarantined File")
            dialog.setMinimumSize(600, 400)
            
            # Create layout
            layout = QVBoxLayout(dialog)
            
            # File info
            info_frame = QFrame()
            info_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
            info_layout = QVBoxLayout(info_frame)
            
            # Add file information
            filename_label = QLabel(f"File: {os.path.basename(file_path)}")
            filename_label.setFont(QFont('Helvetica', 12, QFont.Bold))
            info_layout.addWidget(filename_label)
            
            path_label = QLabel(f"Path: {file_path}")
            path_label.setFont(QFont('Helvetica', 10))
            info_layout.addWidget(path_label)
            
            layout.addWidget(info_frame)
            
            # Text area for content
            text_area = QPlainTextEdit()
            text_area.setPlainText(content)
            text_area.setReadOnly(True)
            text_area.setFont(QFont('Courier New', 10))
            text_area.setStyleSheet("""
                QPlainTextEdit {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            layout.addWidget(text_area)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn, alignment=Qt.AlignRight)
            
            # Show dialog
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
    
    def delete_quarantined(self, filename):
        try:
            file_path = os.path.join("safe_mtd", filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                QMessageBox.information(self, "Success", f"File {filename} has been deleted from quarantine")
                self.load_quarantine_data()
                self.refresh_statistics()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not delete file: {str(e)}")
    
    def refresh_statistics(self):
        # Count files in directories
        monitored_count = 0
        if os.path.exists("test_data"):
            for root, _, files in os.walk("test_data"):
                monitored_count += len(files)
        
        suspicious_count = 0
        if os.path.exists("suspicious_mtd"):
            suspicious_count = len(os.listdir("suspicious_mtd"))
        
        quarantine_count = 0
        if os.path.exists("safe_mtd"):
            quarantine_count = len(os.listdir("safe_mtd"))
        
        # Update UI
        self.monitored_files.findChild(QLabel, "monitored_files_value").setText(str(monitored_count))
        self.suspicious_files.findChild(QLabel, "suspicious_files_value").setText(str(suspicious_count))
        self.quarantined_files.findChild(QLabel, "quarantined_files_value").setText(str(quarantine_count))
