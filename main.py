import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QTabWidget, QFrame, QApplication,
                           QMessageBox, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QEventLoop
from PyQt5.QtGui import QFont, QPixmap, QColor, QMovie, QIcon
import subprocess
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import threading
import time

# Set matplotlib backend
import matplotlib
matplotlib.use('Qt5Agg')

from components.detection import DetectionTab
from components.prevention import PreventionTab
from components.periodic_scan import PeriodicScanTab
from components.service_control_tab import ServiceControlTab  # Add this import
from components.report_tab import ReportTab  # Add this import
from components.exit_tab import ExitTab  # Add import for ExitTab

class DetectionWorker(QThread):
    finished = pyqtSignal(dict, tuple)
    error = pyqtSignal(str)

    def run(self):
        try:
            results = {}
            # Run detection processes with error handling
            detection_modules = [
                ("Behavioral", "behavioral_analysis.py"),
                ("File System", "file_system_monitoring.py"),
                ("Net Traffic", "network_traffic_analysis.py"),
                ("Registry", "registry_monitoring.py"),
                ("Process", "process_monitoring.py"),
                ("API", "api_calls_analysis.py"),
                ("Static", "static_analysis.py")
            ]

            for module_name, script in detection_modules:
                try:
                    process = subprocess.Popen(
                        [sys.executable, f"detection/{script}"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    _, stderr = process.communicate(timeout=10)  # 10 second timeout
                    results[module_name] = process.returncode == 1
                    
                    if stderr and not stderr.decode().startswith("WARNING"):
                        print(f"Error in {module_name}: {stderr.decode()}")
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    results[module_name] = False
                except Exception as e:
                    print(f"Error running {module_name}: {str(e)}")
                    results[module_name] = False

            # Calculate severity
            detections = sum(results.values())
            if detections >= 5:
                severity = ("Severe", "#F44336")
            elif 2 <= detections <= 4:
                severity = ("Mild", "#FF9800")
            else:
                severity = ("Normal", "#4CAF50")
            
            self.finished.emit(results, severity)
            
        except Exception as e:
            self.error.emit(str(e))

class RansomwareApp(QMainWindow):
    def __init__(self, parent=None, user_email=None, user_role=None):
        super().__init__(parent)
        self.user_email = user_email
        self.user_role = user_role
        self.screen = QApplication.primaryScreen().geometry()
        self.initUI()
        self.showMaximized()

    def center_window(self):
        # Center window on screen
        frame = self.frameGeometry()
        center = QApplication.primaryScreen().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def initUI(self):
        self.setWindowTitle("Ransomware Detection and Prevention")

        # Define colors (matching original theme)
        self.bg_color = '#FFFFFF'
        self.frame_bg_color = '#F5F5F5'
        self.button_color = '#2196F3'
        self.button_hover_color = '#1976D2'
        self.label_fg_color = '#333333'
        self.status_fg_color = '#4CAF50'
        self.error_fg_color = '#F44336'

        # Create directory structure for service and data
        os.makedirs("C:/ProgramData/RansomwareDetection", exist_ok=True)
        os.makedirs("C:/ProgramData/RansomwareDetection/logs", exist_ok=True)
        
        # Ensure core data directory exists
        core_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "data")
        os.makedirs(core_data_dir, exist_ok=True)

        # Create and setup central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(
            int(self.screen.width() * 0.05),   # left
            int(self.screen.height() * 0.03),  # top
            int(self.screen.width() * 0.05),   # right
            int(self.screen.height() * 0.03)   # bottom
        )

        # Header with logo layout (similar to role_page)
        logo_frame = QFrame()
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setSpacing(40)
        logo_layout.setContentsMargins(0, 0, 0, 30)
        
        # Load and add logos - updated sizes to match role_page
        logo_files = ["pillai_flower.png", "pillai_name.png", "pillai_naac.png"]
        logo_sizes = [
            (int(self.screen.width() * 0.08), int(self.screen.height() * 0.1)),  # flower
            (int(self.screen.width() * 0.3), int(self.screen.height() * 0.1)),   # name
            (int(self.screen.width() * 0.08), int(self.screen.height() * 0.1))   # naac
        ]
        
        try:
            for logo_file, (width, height) in zip(logo_files, logo_sizes):
                logo_label = QLabel()
                pixmap = QPixmap(f"drawable/{logo_file}")
                scaled_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                logo_layout.addWidget(logo_label)
        except Exception as e:
            print(f"Could not load logos: {e}")
        
        main_layout.addWidget(logo_frame)

        # User info section with enhanced styling
        if self.user_email and self.user_role:
            user_frame = QFrame()
            user_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
            user_layout = QHBoxLayout(user_frame)
            
            role_icon = "👤" if self.user_role == 'student' else "👨‍🏫" if self.user_role == 'faculty' else "⚙️"
            user_info = QLabel(f"{role_icon} {self.user_role.title()}: {self.user_email}")
            user_info.setFont(QFont('Helvetica', 14))
            user_info.setStyleSheet("color: #333333;")
            user_layout.addWidget(user_info)
            
            main_layout.addWidget(user_frame)

        # Title with gradient background - reduced size and padding
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 15px;
                padding: 10px;
                margin-bottom: 15px;
            }
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)  # Reduced padding
        
        title = QLabel("Ransomware Detection and Prevention")
        title.setFont(QFont('Helvetica', 18, QFont.Bold))  # Reduced from 22/24
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        title_layout.addWidget(title)
        
        main_layout.addWidget(title_frame)

        # Tab widget with modern styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabBar::tab {
                padding: 12px 25px;
                background: #E0E0E0;
                color: #333333;
                font: bold 16px 'Helvetica';
                margin-right: 4px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2196F3, stop:1 #1976D2);
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #64B5F6;
                color: white;
            }
        """)

        # Create tabs
        self.detection_tab = QWidget()
        self.prevention_tab = QWidget()
        self.periodic_scan_tab = QWidget()
        self.service_tab = QWidget()  # Add new tab
        self.report_tab = QWidget()
        self.exit_tab = QWidget()

        # Add tabs - new order with service tab
        self.tab_widget.addTab(self.detection_tab, "Detection")
        self.tab_widget.addTab(self.prevention_tab, "Prevention")
        self.tab_widget.addTab(self.periodic_scan_tab, "Periodic Scanning")
        self.tab_widget.addTab(self.service_tab, "Background Service")  # Add the new tab
        self.tab_widget.addTab(self.report_tab, "Generate Report")
        
        # Use a flag to track whether we've already added the Exit tab
        self.exit_tab_added = False
        
        # Only add the Exit tab if it hasn't been added yet
        if not self.exit_tab_added:
            email = getattr(self, 'user_email', 'user@example.com')
            role = getattr(self, 'user_role', 'admin')
            
            self.exit_tab = ExitTab(user_info={"email": email, "role": role})
            self.exit_tab.logout_requested.connect(self.handle_logout)
            self.tab_widget.addTab(self.exit_tab, QIcon("drawable/exit_icon.png"), "Exit")
            self.exit_tab_added = True

        main_layout.addWidget(self.tab_widget)

        # Setup individual tabs
        self.setup_detection_tab()
        self.setup_prevention_tab()
        self.setup_periodic_scan_tab()
        self.setup_service_tab()  # Add this method call
        self.setup_report_tab()
        self.setup_exit_tab()

    def setup_detection_tab(self):
        detection_tab = DetectionTab(self.screen)
        layout = QVBoxLayout(self.detection_tab)
        layout.addWidget(detection_tab)

    def setup_prevention_tab(self):
        prevention_tab = PreventionTab()
        layout = QVBoxLayout(self.prevention_tab)
        layout.addWidget(prevention_tab)

    def setup_periodic_scan_tab(self):  # Add this new method
        periodic_scan_tab = PeriodicScanTab(detection_callback=self.run_detection)
        layout = QVBoxLayout(self.periodic_scan_tab)
        layout.addWidget(periodic_scan_tab)
        self.periodic_scan = periodic_scan_tab  # Save reference

    def setup_service_tab(self):
        """Setup service control tab"""
        service_tab = ServiceControlTab()
        layout = QVBoxLayout(self.service_tab)
        layout.addWidget(service_tab)

    def setup_report_tab(self):
        report_tab = ReportTab()  # Create ReportTab instance
        layout = QVBoxLayout(self.report_tab)
        layout.addWidget(report_tab)

    def setup_exit_tab(self):
        # Exit tab implementation
        layout = QVBoxLayout(self.exit_tab)
        
        warning_label = QLabel("Are you sure you want to exit?")
        warning_label.setFont(QFont('Helvetica', 18, QFont.Bold))
        warning_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(warning_label)

        exit_btn = QPushButton("Exit Application")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333;
                color: white;
                border: none;
                padding: 15px 30px;
                font: bold 16px 'Helvetica';
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn, alignment=Qt.AlignCenter)

    # Add a method to run detection from periodic scan
    def run_detection(self):
        # Don't switch tab - just run detection in background
        
        # Run detection and collect results
        detection_tab = self.detection_tab.findChild(DetectionTab)
        results = {}
        severity = ("Normal", "#4CAF50")  # Default values
        detected_files = []
        
        if detection_tab:
            # Just run the detection
            detection_tab.start_actual_detection()
            
        # Return results for periodic scanning
        return {
            'threat_level': severity[0] if isinstance(severity, tuple) else "Normal",
            'severity_color': severity[1] if isinstance(severity, tuple) else "#4CAF50",
            'detected_files': detected_files
        }

    def _handle_detection_results(self, detection_results, severity, results_dict, loop):
        # Store results
        results_dict['results'] = detection_results
        results_dict['severity'] = severity
        
        # Exit loop
        loop.quit()
        
    def _handle_detection_error(self, error, loop):
        print(f"Detection error: {error}")
        loop.quit()

    # Add a method to handle logout
    def handle_logout(self):
        """Handle logout request from exit tab"""
        # Clear any stored credentials
        try:
            auth_file = os.path.join(os.path.expanduser("~"), ".ransomware_app", "auth_token.json")
            if os.path.exists(auth_file):
                os.remove(auth_file)
        except:
            pass
        
        # Show login window again
        from components.login import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()
        
        # Close main window
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RansomwareApp()
    window.show()
    sys.exit(app.exec_())