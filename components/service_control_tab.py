from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QProgressBar, QSpinBox, QComboBox,
                           QRadioButton, QButtonGroup, QTabWidget, QMessageBox,
                           QTableWidget, QTableWidgetItem, QHeaderView, QDialog, 
                           QTextBrowser, QScrollArea, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot, QSize, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QBrush, QPen
import os
import json
import time  # Add this import for time.sleep()
from datetime import datetime
from pathlib import Path
import re

from .service_manager import ServiceManager
from .timeline_widget import TimelineWidget, StatusIndicator

class ServiceControlTab(QWidget):
    """Tab for controlling and monitoring the background service"""
    
    def __init__(self):
        super().__init__()
        self.service_manager = ServiceManager()
        self.log_entries = []
        self.initUI()
        
        # Connect signals
        self.service_manager.service_status_changed.connect(self.on_service_status_changed)
        self.service_manager.detection_results_updated.connect(self.on_detection_results_updated)
    
    def initUI(self):
        # Use a modern, clean layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for responsive design
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create content widget for scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(30, 30, 30, 30)
        scroll_layout.setSpacing(25)

        # Add notification banner
        self.notification_banner = QFrame()
        self.notification_banner.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        notification_layout = QHBoxLayout(self.notification_banner)
        
        self.notification_icon = QLabel("ℹ️")
        self.notification_icon.setFont(QFont('Segoe UI', 14))
        notification_layout.addWidget(self.notification_icon)
        
        self.notification_text = QLabel("Background service is not running")
        self.notification_text.setFont(QFont('Helvetica', 12))
        self.notification_text.setStyleSheet("color: #1565C0;")
        notification_layout.addWidget(self.notification_text)
        
        # Add close button for notification
        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                color: #333333;
            }
        """)
        close_btn.clicked.connect(lambda: self.notification_banner.hide())
        notification_layout.addWidget(close_btn)
        
        # Hide notification initially
        self.notification_banner.hide()
        
        scroll_layout.addWidget(self.notification_banner)

        # Header with status indicator
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #1976D2;
                border-radius: 15px;
                padding: 0px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(25, 20, 25, 20)
        
        # Left side - title and description
        title_section = QVBoxLayout()
        
        title_label = QLabel("Background Service Dashboard")
        title_label.setFont(QFont('Helvetica', 22, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_section.addWidget(title_label)
        
        description = QLabel("Monitor and control the ransomware detection service")
        description.setFont(QFont('Helvetica', 12))
        description.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        title_section.addWidget(description)
        
        header_layout.addLayout(title_section, stretch=7)
        
        # Right side - status indicator
        status_section = QVBoxLayout()
        status_section.setContentsMargins(0, 0, 0, 0)
        
        self.status_container = QFrame()
        self.status_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 8px;
            }
        """)
        self.status_container.setMinimumWidth(150)
        self.status_container.setMaximumHeight(100)
        
        status_con_layout = QVBoxLayout(self.status_container)
        status_con_layout.setContentsMargins(10, 10, 10, 10)
        status_con_layout.setSpacing(5)
        
        status_title = QLabel("SERVICE STATUS")
        status_title.setFont(QFont('Helvetica', 10, QFont.Bold))
        status_title.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        status_title.setAlignment(Qt.AlignCenter)
        status_con_layout.addWidget(status_title)
        
        self.status_indicator = StatusIndicator()
        status_con_layout.addWidget(self.status_indicator, alignment=Qt.AlignCenter)
        
        self.status_text = QLabel("Checking...")
        self.status_text.setFont(QFont('Helvetica', 12, QFont.Bold))
        self.status_text.setStyleSheet("color: white;")
        self.status_text.setAlignment(Qt.AlignCenter)
        status_con_layout.addWidget(self.status_text)
        
        status_section.addWidget(self.status_container, alignment=Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addLayout(status_section, stretch=3)
        
        scroll_layout.addWidget(header)

        # Control panel
        control_card = QFrame()
        control_card.setObjectName("controlCard")
        control_card.setStyleSheet("""
            QFrame#controlCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(20, 20, 20, 20)
        
        # Control panel title
        title = QLabel("Service Control Panel")
        title.setFont(QFont('Helvetica', 16, QFont.Bold))
        title.setStyleSheet("color: #333333;")
        control_layout.addWidget(title)
        
        # Button grid layout
        button_grid = QHBoxLayout()
        button_grid.setContentsMargins(0, 10, 0, 10)
        button_grid.setSpacing(15)
        
        # Service control buttons
        self.install_btn = self.create_control_button("Install Service", "#2196F3", "#1976D2", self.install_service)
        self.start_btn = self.create_control_button("Start Service", "#4CAF50", "#388E3C", self.start_service)
        self.stop_btn = self.create_control_button("Stop Service", "#F44336", "#D32F2F", self.stop_service)
        self.uninstall_btn = self.create_control_button("Uninstall Service", "#FF9800", "#F57C00", self.uninstall_service)
        
        # Add buttons to grid
        button_grid.addWidget(self.install_btn)
        button_grid.addWidget(self.start_btn)
        button_grid.addWidget(self.stop_btn)
        button_grid.addWidget(self.uninstall_btn)
        
        control_layout.addLayout(button_grid)
        
        # Add action buttons in second row
        action_grid = QHBoxLayout()
        action_grid.setContentsMargins(0, 5, 0, 5)
        action_grid.setSpacing(15)
        
        # Refresh status button
        refresh_btn = self.create_action_button("Refresh Status", "#673AB7", "#5E35B1", self.refresh_status)
        action_grid.addWidget(refresh_btn)
        
        # Force scan button
        scan_btn = self.create_action_button("Force Immediate Scan", "#009688", "#00796B", self.force_scan)
        action_grid.addWidget(scan_btn)
        
        control_layout.addLayout(action_grid)
        
        scroll_layout.addWidget(control_card)

        # Timeline visualization
        timeline_card = QFrame()
        timeline_card.setObjectName("timelineCard")
        timeline_card.setStyleSheet("""
            QFrame#timelineCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        timeline_layout = QVBoxLayout(timeline_card)
        timeline_layout.setContentsMargins(20, 20, 20, 20)
        
        # Timeline section title
        timeline_title = QLabel("Service Activity Timeline")
        timeline_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        timeline_title.setStyleSheet("color: #333333;")
        timeline_layout.addWidget(timeline_title)
        
        # Timeline visualization widget
        self.timeline_widget = TimelineWidget()
        self.timeline_widget.setMinimumHeight(150)
        timeline_layout.addWidget(self.timeline_widget)
        
        # Status summary
        self.status_summary = QLabel("Waiting for service data...")
        self.status_summary.setFont(QFont('Helvetica', 12))
        self.status_summary.setStyleSheet("color: #666666;")
        self.status_summary.setAlignment(Qt.AlignCenter)
        self.status_summary.setWordWrap(True)
        timeline_layout.addWidget(self.status_summary)
        
        # Results table with improved styling
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Time", "Severity", "Suspicious", "Total"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setMinimumHeight(200)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 6px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        timeline_layout.addWidget(self.results_table)
        
        scroll_layout.addWidget(timeline_card)

        # Log section
        logs_card = QFrame()
        logs_card.setObjectName("logsCard")
        logs_card.setStyleSheet("""
            QFrame#logsCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        logs_layout = QVBoxLayout(logs_card)
        logs_layout.setContentsMargins(20, 20, 20, 20)
        
        # Logs section header
        logs_header = QHBoxLayout()
        
        logs_title = QLabel("Service Logs")
        logs_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        logs_title.setStyleSheet("color: #333333;")
        logs_header.addWidget(logs_title)
        
        # View logs button
        view_logs_btn = QPushButton("View Full Logs")
        view_logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        view_logs_btn.clicked.connect(self.show_logs)
        logs_header.addWidget(view_logs_btn, alignment=Qt.AlignRight)
        
        logs_layout.addLayout(logs_header)
        
        # Log display
        self.log_browser = QTextBrowser()
        self.log_browser.setFont(QFont('Consolas', 10))
        self.log_browser.setMaximumHeight(200)
        self.log_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: #f8f9fa;
                padding: 10px;
            }
        """)
        logs_layout.addWidget(self.log_browser)
        
        scroll_layout.addWidget(logs_card)

        # Settings card
        settings_card = QFrame()
        settings_card.setObjectName("settingsCard")
        settings_card.setStyleSheet("""
            QFrame#settingsCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        
        # Settings title
        settings_title = QLabel("Service Settings")
        settings_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        settings_title.setStyleSheet("color: #333333;")
        settings_layout.addWidget(settings_title)
        
        # Settings form
        settings_form = QFrame()
        settings_form.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 15px;")
        form_layout = QVBoxLayout(settings_form)
        
        # Scan interval
        interval_layout = QHBoxLayout()
        
        interval_label = QLabel("Scan Interval:")
        interval_label.setFont(QFont('Helvetica', 12))
        interval_layout.addWidget(interval_label)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(30)
        self.interval_spin.setFont(QFont('Helvetica', 12))
        self.interval_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
                min-width: 80px;
            }
        """)
        interval_layout.addWidget(self.interval_spin)
        
        self.interval_units = QComboBox()
        self.interval_units.addItems(["Minutes", "Hours"])
        self.interval_units.setCurrentIndex(0)
        self.interval_units.setFont(QFont('Helvetica', 12))
        self.interval_units.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
                min-width: 100px;
            }
        """)
        interval_layout.addWidget(self.interval_units)
        interval_layout.addStretch()
        
        form_layout.addLayout(interval_layout)
        
        # Detection level
        level_layout = QHBoxLayout()
        
        level_label = QLabel("Detection Level:")
        level_label.setFont(QFont('Helvetica', 12))
        level_layout.addWidget(level_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Low", "Medium", "High"])
        self.level_combo.setCurrentIndex(1)
        self.level_combo.setFont(QFont('Helvetica', 12))
        self.level_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
                min-width: 150px;
            }
        """)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        
        form_layout.addLayout(level_layout)
        
        # Apply button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        apply_btn.clicked.connect(self.apply_settings)
        form_layout.addWidget(apply_btn, alignment=Qt.AlignRight)
        
        settings_layout.addWidget(settings_form)
        
        scroll_layout.addWidget(settings_card)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Start monitoring log file
        self.start_log_monitoring()
        
        # Update UI state based on current service status
        QTimer.singleShot(500, self.update_ui_state)

    def create_control_button(self, text, bg_color, hover_color, callback):
        """Helper to create styled control buttons"""
        btn = QPushButton(text)
        btn.setMinimumHeight(45)
        btn.setFont(QFont('Helvetica', 12, QFont.Bold))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #BDBDBD;
                color: #EEEEEE;
            }}
        """)
        btn.clicked.connect(callback)
        return btn
        
    def create_action_button(self, text, bg_color, hover_color, callback):
        """Helper to create styled action buttons"""
        btn = QPushButton(text)
        btn.setMinimumHeight(40)
        btn.setFont(QFont('Helvetica', 12))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 8px;
                padding: 8px 15px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        btn.clicked.connect(callback)
        return btn
        
    def update_ui_state(self):
        """Update UI based on service state"""
        installed = self.service_manager.is_service_installed()
        self.install_btn.setEnabled(not installed)
        self.uninstall_btn.setEnabled(installed)
        
        # Refresh service status
        self.service_manager.check_service_status()
        self.service_manager.check_detection_results()

    def start_log_monitoring(self):
        """Start monitoring log file for real-time updates"""
        self.log_timer = QTimer()
        self.log_timer.setInterval(5000)  # Check every 5 seconds
        self.log_timer.timeout.connect(self.update_logs)
        self.log_timer.start()
    
    def update_logs(self):
        """Update log display with latest entries"""
        try:
            log_path = Path("C:/ProgramData/RansomwareDetection/logs/detection_service.log")
            if log_path.exists():
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    # Get last 10 lines
                    last_lines = lines[-10:]
                
                # Format and display logs
                formatted_logs = ""
                for line in last_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse log timestamp
                    try:
                        timestamp, rest = line.split(" - ", 1)
                        
                        # Check log level to add color
                        if "ERROR" in rest:
                            line = f'<span style="color:red">{timestamp}</span> - {rest}'
                        elif "WARNING" in rest:
                            line = f'<span style="color:orange">{timestamp}</span> - {rest}'
                        elif "INFO" in rest:
                            line = f'<span style="color:blue">{timestamp}</span> - {rest}'
                        else:
                            line = f'<span style="color:#666">{timestamp}</span> - {rest}'
                    except:
                        # Just use the line as is
                        pass
                    
                    formatted_logs += f"{line}<br>"
                
                self.log_browser.setHtml(formatted_logs)
                
                # Extract service events for timeline
                service_events = self.parse_log_for_events(lines)
                if service_events:
                    self.timeline_widget.set_events(service_events)
                    
                    # Update status summary with latest event information
                    if service_events:
                        latest_event = service_events[-1]
                        event_type = latest_event.get('type')
                        time_str = latest_event['time'].strftime("%Y-%m-%d %H:%M:%S")
                        
                        if event_type == "start":
                            self.status_summary.setText(f"Service started at {time_str}")
                        elif event_type == "stop":
                            self.status_summary.setText(f"Service stopped at {time_str}")
                        elif event_type == "scan":
                            self.status_summary.setText(f"Scan started at {time_str}")
                        elif event_type == "scan_complete":
                            self.status_summary.setText(f"Last scan completed at {time_str}")
        except Exception as e:
            print(f"Error updating logs: {e}")
    
    def parse_log_for_events(self, log_lines):
        """Parse log file for significant events to display on timeline"""
        events = []
        
        for line in log_lines:
            try:
                # Extract timestamp
                timestamp_str = re.search(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                if not timestamp_str:
                    continue
                
                timestamp_str = timestamp_str.group(0)
                
                # Convert to datetime
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                
                # Determine event type
                event_type = None
                if "Service starting" in line:
                    event_type = "start"
                elif "Service stopped" in line:
                    event_type = "stop"
                elif "Starting scan" in line:
                    event_type = "scan"
                elif "Scan complete" in line:
                    event_type = "scan_complete"
                
                if event_type:
                    events.append({
                        'time': timestamp,
                        'type': event_type,
                        'description': line.split(" - ")[-1].strip()
                    })
            except Exception as e:
                print(f"Error parsing log line: {e}")
        
        return events
        
    def refresh_status(self):
        """Refresh service status immediately"""
        self.service_manager.check_service_status()
        self.update_ui_state()
        self.show_acknowledgment("Status refreshed", "info")

    def show_logs(self):
        """Show service logs in a dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Service Logs")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        log_browser = QTextBrowser()
        log_browser.setFont(QFont('Consolas', 10))
        
        try:
            log_path = Path("C:/ProgramData/RansomwareDetection/logs/detection_service.log")
            if log_path.exists():
                with open(log_path, 'r') as f:
                    log_browser.setText(f.read())
            else:
                log_browser.setText("No logs found")
        except Exception as e:
            log_browser.setText(f"Error reading logs: {e}")
        
        layout.addWidget(log_browser)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        dialog.exec_()

    def show_acknowledgment(self, message, level="success"):
        """Show acknowledgment with animation"""
        colors = {
            "success": ("#4CAF50", "#E8F5E9"),
            "info": ("#2196F3", "#E3F2FD"),
            "warning": ("#FF9800", "#FFF3E0"),
            "error": ("#F44336", "#FFEBEE")
        }
        fg_color, bg_color = colors.get(level, colors["info"])
        
        self.notification_banner.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        self.notification_text.setStyleSheet(f"color: {fg_color};")
        self.notification_text.setText(message)
        self.notification_banner.show()
        
        # Auto-hide after 5 seconds
        QTimer.singleShot(5000, self.notification_banner.hide)
    
    def install_service(self):
        """Install the Windows service"""
        # Check admin rights first
        if not self.service_manager.is_admin():
            self.show_admin_instructions()
            return
        
        # Continue with normal installation logic if we have admin rights
        reply = QMessageBox.question(
            self, 
            "Install Service",
            "This will install the background detection service.\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.install_btn.setEnabled(False)
            self.install_btn.setText("Installing...")
            self.show_acknowledgment("Installing service, please wait...", "info")
            
            success, message = self.service_manager.install_service()
            
            if success:
                self.show_acknowledgment(f"Success: {message}", "success")
                self.update_ui_state()
                
                # Show a help dialog if first-time installation
                QMessageBox.information(
                    self,
                    "Installation Complete",
                    "The background service has been successfully installed.\n\n"
                    "If you experience any issues with starting the service, please check:\n"
                    "1. You are running as administrator\n"
                    "2. Windows service manager is functioning properly\n"
                    "3. Logs at C:/ProgramData/RansomwareDetection/logs\n\n"
                    "You can now start the service using the 'Start Service' button."
                )
            else:
                # Show extended error dialog with possible troubleshooting steps
                error_dialog = QDialog(self)
                error_dialog.setWindowTitle("Service Installation Failed")
                error_dialog.setMinimumSize(600, 400)
                
                layout = QVBoxLayout(error_dialog)
                
                # Error details
                error_label = QLabel("Service installation failed")
                error_label.setStyleSheet("font-weight: bold; color: #F44336; font-size: 16px;")
                layout.addWidget(error_label)
                
                error_details = QTextBrowser()
                error_details.setPlainText(message)
                layout.addWidget(error_details)
                
                # Troubleshooting section
                troubleshoot_label = QLabel("Troubleshooting Steps:")
                troubleshoot_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                layout.addWidget(troubleshoot_label)
                
                troubleshoot_list = QTextBrowser()
                troubleshoot_list.setHtml(
                    "<ol>"
                    "<li>Make sure you're running the application as Administrator</li>"
                    "<li>Verify PyWin32 is installed: <code>pip install pywin32</code></li>"
                    "<li>Try running: <code>python -m win32com.client.makepy winmgmt</code></li>"
                    "<li>Check Windows Event Viewer for system errors</li>"
                    "<li>Check logs at: <code>C:/ProgramData/RansomwareDetection/logs</code></li>"
                    "<li>Restart your computer and try again</li>"
                    "</ol>"
                )
                layout.addWidget(troubleshoot_list)
                
                # Close button
                close_btn = QPushButton("Close")
                close_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        border-radius: 5px;
                        padding: 8px 15px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #1976D2;
                    }
                """)
                close_btn.clicked.connect(error_dialog.close)
                layout.addWidget(close_btn, alignment=Qt.AlignRight)
                
                error_dialog.exec_()
                
            self.install_btn.setText("Install Service")
            self.install_btn.setEnabled(True)
            
    def show_admin_instructions(self):
        """Show instructions for running as administrator"""
        admin_dialog = QDialog(self)
        admin_dialog.setWindowTitle("Administrator Privileges Required")
        admin_dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(admin_dialog)
        
        # Title
        title = QLabel("Administrator Privileges Required")
        title.setFont(QFont('Helvetica', 16, QFont.Bold))
        title.setStyleSheet("color: #F44336;")
        layout.addWidget(title)
        
        # Info text
        info = QTextBrowser()
        info.setHtml("""
            <p>This operation requires administrator privileges to manage Windows services.</p>
            <h3>How to run this application as administrator:</h3>
            
            <h4>Method 1: Using the included launcher</h4>
            <ol>
                <li>Close this application</li>
                <li>Navigate to the application folder</li>
                <li>Find the file <b>run_as_admin.py</b></li>
                <li>Right-click on it and select <b>"Run as administrator"</b></li>
                <li>Accept the User Account Control (UAC) prompt</li>
            </ol>
            
            <h4>Method 2: For the main executable</h4>
            <ol>
                <li>Close this application</li>
                <li>Find the application shortcut or executable file</li>
                <li>Right-click on it and select <b>"Run as administrator"</b></li>
                <li>Accept the User Account Control (UAC) prompt</li>
            </ol>
            
            <h4>Method 3: For Python script</h4>
            <ol>
                <li>Open Command Prompt as administrator
                    <ul>
                        <li>Press Windows key</li>
                        <li>Type "cmd"</li>
                        <li>Right-click on "Command Prompt"</li>
                        <li>Select "Run as administrator"</li>
                    </ul>
                </li>
                <li>Navigate to application folder</li>
                <li>Run: <code>python main.py</code></li>
            </ol>
        """)
        layout.addWidget(info)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(admin_dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        admin_dialog.exec_()

    def uninstall_service(self):
        """Uninstall the Windows service"""
        reply = QMessageBox.question(
            self, 
            "Uninstall Service",
            "This will remove the background detection service.\nDo you want to continue?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.uninstall_btn.setEnabled(False)
            self.uninstall_btn.setText("Uninstalling...")
            
            success, message = self.service_manager.uninstall_service()
            
            if success:
                self.show_acknowledgment(f"Success: {message}", "success")
                self.update_ui_state()
            else:
                QMessageBox.critical(self, "Error", message)
                
            self.uninstall_btn.setText("Uninstall Service")
            self.uninstall_btn.setEnabled(True)
            
    def start_service(self):
        """Start the Windows service"""
        self.start_btn.setEnabled(False)
        self.start_btn.setText("Starting...")
        
        success, message = self.service_manager.start_service()
        
        if success:
            self.show_acknowledgment(f"Success: {message}", "success")
        else:
            # Show troubleshooting dialog for service start failures
            if "failed to start" in message.lower() or "time" in message.lower():
                self.show_service_troubleshooting_dialog(message)
            else:
                QMessageBox.critical(self, "Error", message)
            
        self.start_btn.setText("Start Service")
        self.start_btn.setEnabled(True)

    def show_service_troubleshooting_dialog(self, error_message):
        """Show a helpful troubleshooting dialog for service start issues"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Service Start Issue")
        dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Error title
        title = QLabel("Service Failed to Start")
        title.setFont(QFont('Helvetica', 16, QFont.Bold))
        title.setStyleSheet("color: #F44336;")
        layout.addWidget(title)
        
        # Error message
        message = QLabel(error_message)
        message.setWordWrap(True)
        message.setStyleSheet("background-color: #FFEBEE; padding: 10px; border-radius: 5px;")
        layout.addWidget(message)
        
        # Troubleshooting steps
        troubleshooting = QTextBrowser()
        troubleshooting.setHtml("""
            <h3>Troubleshooting Steps:</h3>
            
            <p><b>1. Check Service Dependencies</b></p>
            <ul>
                <li>Ensure PyWin32 is properly installed in your environment:
                <br><code>pip install pywin32==303</code> (use a specific version)</li>
                <li>Run the PyWin32 post-install script:
                <br><code>python -m win32com.client.makepy winmgmt</code></li>
            </ul>
            
            <p><b>2. Verify Logs</b></p>
            <ul>
                <li>Check logs at: <code>C:/ProgramData/RansomwareDetection/logs/</code></li>
                <li>Look for specific error messages in <code>detection_service.log</code> and <code>service_installation.log</code></li>
                <li>Check Windows Event Viewer for system errors</li>
            </ul>
            
            <p><b>3. Permissions Issues</b></p>
            <ul>
                <li>Confirm you're running as administrator</li>
                <li>Check that your account has the "Log on as a service" right</li>
                <li>Verify that your Python installation path doesn't contain spaces or special characters</li>
            </ul>
            
            <p><b>4. Try Manual Restart</b></p>
            <ul>
                <li>Try uninstalling the service and reinstalling it</li>
                <li>Restart your computer and try again</li>
            </ul>
        """)
        layout.addWidget(troubleshooting)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # View logs button
        logs_btn = QPushButton("View Service Logs")
        logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        logs_btn.clicked.connect(self.show_logs)
        button_layout.addWidget(logs_btn)
        
        # Try reinstall button
        reinstall_btn = QPushButton("Reinstall Service")
        reinstall_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        reinstall_btn.clicked.connect(self.reinstall_service)
        button_layout.addWidget(reinstall_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def reinstall_service(self):
        """Reinstall the service to fix potential issues"""
        # First try to uninstall
        self.service_manager.stop_service()
        time.sleep(2)  # Brief pause
        self.service_manager.uninstall_service()
        time.sleep(2)  # Brief pause
        
        # Then reinstall
        success, message = self.service_manager.install_service()
        if success:
            self.show_acknowledgment(f"Service reinstalled: {message}", "success")
        else:
            QMessageBox.critical(self, "Error", f"Failed to reinstall service: {message}")

    def stop_service(self):
        """Stop the Windows service"""
        self.stop_btn.setEnabled(False)
        self.stop_btn.setText("Stopping...")
        
        success, message = self.service_manager.stop_service()
        
        if success:
            self.show_acknowledgment(f"Success: {message}", "success")
        else:
            QMessageBox.critical(self, "Error", message)
            
        self.stop_btn.setText("Stop Service")
        self.stop_btn.setEnabled(True)
        
    def apply_settings(self):
        """Apply settings to the service"""
        # Get interval in seconds based on selected unit (minutes or hours)
        interval_value = self.interval_spin.value()
        if self.interval_units.currentText() == "Hours":
            interval_seconds = interval_value * 3600
        else:
            interval_seconds = interval_value * 60
            
        # Get detection level
        detection_level = self.level_combo.currentText().lower()
        
        # Create settings object
        settings = {
            "scan_interval": interval_seconds,
            "detection_level": detection_level
        }
        
        # Send settings to service
        success = self.service_manager.update_settings(settings)
        
        if success:
            self.show_acknowledgment("Settings applied successfully", "success")
        else:
            self.show_acknowledgment("Settings saved but could not be applied to running service", "warning")
            
    def force_scan(self):
        """Force an immediate scan"""
        success = self.service_manager.trigger_scan()
        
        if success:
            self.show_acknowledgment("Scan initiated. Results will appear shortly.", "info")
        else:
            self.show_acknowledgment("Could not communicate with service. Is it running?", "error")

    @pyqtSlot(str, dict)
    def on_service_status_changed(self, status, details):
        """Update UI based on service status changes with acknowledgments"""
        timestamp = details.get("timestamp", "")
        
        if status == "running":
            self.status_indicator.set_status("running")
            self.status_text.setText("Running")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")
            
            # Update button states
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
        elif status == "stopped":
            self.status_indicator.set_status("stopped")
            self.status_text.setText("Stopped")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")
            
            # Update button states
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
        elif status == "scanning":
            self.status_indicator.set_status("scanning")
            self.status_text.setText("Scanning")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")
            
        elif status == "scan_complete":
            self.status_indicator.set_status("running")
            self.status_text.setText("Running")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")
            
        elif status == "initialized":
            self.status_indicator.set_status("stopped")
            self.status_text.setText("Ready")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")
            
            # Update button states
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            
        elif status == "stopping":
            self.status_indicator.set_status("stopped")
            self.status_text.setText("Stopping...")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")
            
        else:  # unknown or error
            self.status_indicator.set_status("unknown")
            self.status_text.setText("Unknown")
            self.status_text.setStyleSheet("color: white; font-weight: bold;")

    @pyqtSlot(dict)
    def on_detection_results_updated(self, results):
        """Update UI based on detection results updates"""
        # Update results table
        self.results_table.setRowCount(0)
        
        # Add overall results
        if "last_scan" in results:
            last_scan = results["last_scan"]
            
            # Check if results contain actual results
            if "results" in results and "_system_indicators" in results["results"]:
                system_indicators = results["results"]["_system_indicators"]
                suspicious_count = sum(1 for k, v in results["results"].items() 
                                    if k != "_system_indicators" and v.get("is_suspicious", False))
                total_count = len(results["results"]) - 1  # Subtract system indicators
                
                severity = self.calculate_severity(suspicious_count, total_count)
                
                # Add to table
                self.add_result_row(last_scan, severity, suspicious_count, total_count)
                
        # Add history entries if available
        if "history" in results:
            for entry in results["history"]:
                if "timestamp" in entry and "summary" in entry:
                    timestamp = entry["timestamp"]
                    severity = entry["summary"].get("severity", "Unknown")
                    suspicious = entry["summary"].get("suspicious_count", 0)
                    total = entry["summary"].get("total_count", 0)
                    
                    self.add_result_row(timestamp, severity, suspicious, total)
                    
    def add_result_row(self, timestamp, severity, suspicious, total):
        """Add a row to the results table"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Add items
        self.results_table.setItem(row, 0, QTableWidgetItem(timestamp))
        
        # Severity with color coding
        severity_item = QTableWidgetItem(severity)
        if severity == "Severe":
            severity_item.setForeground(QColor("#F44336"))
        elif severity == "Mild":
            severity_item.setForeground(QColor("#FF9800"))
        elif severity == "Low":
            severity_item.setForeground(QColor("#FFEB3B"))
        else:
            severity_item.setForeground(QColor("#4CAF50"))
        
        self.results_table.setItem(row, 1, severity_item)
        self.results_table.setItem(row, 2, QTableWidgetItem(str(suspicious)))
        self.results_table.setItem(row, 3, QTableWidgetItem(str(total)))
        
    def calculate_severity(self, suspicious, total):
        """Calculate severity level based on suspicious count"""
        if suspicious >= 5:
            return "Severe"
        elif suspicious >= 2:
            return "Mild" 
        elif suspicious >= 1:
            return "Low"
        else:
            return "Normal"
