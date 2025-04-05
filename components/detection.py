from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QMessageBox, QDialog, QTextBrowser, 
                           QSpinBox, QComboBox, QCalendarWidget, QTimeEdit, QCheckBox, QGroupBox, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QEasingCurve, QTimer, QTime, QDateTime
from PyQt5.QtGui import QFont, QMovie
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import subprocess
import json
import os
from utils.wmi_workaround import get_system_info_wmi, monitor_process_creation, monitor_file_changes
import threading
import time
from datetime import datetime

class DetectionWorker(QThread):
    finished = pyqtSignal(dict, tuple)
    error = pyqtSignal(str)

    def run(self):
        try:
            results = {}
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
                        ["python", f"detection/{script}"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    _, stderr = process.communicate(timeout=10)
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

class DetectionTab(QWidget):
    def __init__(self, screen):
        super().__init__()
        self.screen = screen
        self.isAnimated = False
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 20, 40, 20)
        
        # Create a container for initial centered content
        self.initial_container = QFrame()
        self.initial_container.setObjectName("initialContainer")
        self.initial_container.setStyleSheet("""
            QFrame#initialContainer {
                background-color: rgba(248, 249, 250, 0.7);
                border-radius: 15px;
                padding: 30px;
            }
        """)
        
        # Vertical layout with centered items
        initial_layout = QVBoxLayout(self.initial_container)
        initial_layout.setContentsMargins(40, 60, 40, 60)
        initial_layout.setSpacing(30)
        
        # Info Label centered with enhanced text
        self.info_label = QLabel("Monitor Ransomware Activities")
        subtitle = QLabel("Detect and analyze potential threats in real-time")
        
        self.info_label.setFont(QFont('Helvetica', 20, QFont.Bold))
        self.info_label.setStyleSheet("""
            QLabel {
                color: #333333;
                padding: 5px;
                background: transparent;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        initial_layout.addWidget(self.info_label)
        
        # Add subtitle
        subtitle.setFont(QFont('Helvetica', 13))
        subtitle.setStyleSheet("color: #666666;")
        subtitle.setAlignment(Qt.AlignCenter)
        initial_layout.addWidget(subtitle)
        
        # Start Detection Button centered
        self.start_detection_btn = QPushButton("Start Detection")
        self.start_detection_btn.setFixedSize(
            int(self.screen.width() * 0.2),  # Increased width
            int(self.screen.height() * 0.06)  # Increased height
        )
        self.start_detection_btn.setFont(QFont('Helvetica', 14, QFont.Bold))  # Larger font
        self.start_detection_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.start_detection_btn.clicked.connect(self.start_detection)
        initial_layout.addWidget(self.start_detection_btn, alignment=Qt.AlignCenter)
        
        # Add the initial container to main layout
        self.main_layout.addWidget(self.initial_container, alignment=Qt.AlignCenter)

        # Create content that will be visible after animation
        self.content_container = QFrame()
        self.content_container.hide()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setContentsMargins(20, 10, 20, 10)
        
        # Create header that will contain moved title and button in same row
        self.header_container = QFrame()
        header_layout = QHBoxLayout(self.header_container)
        header_layout.setContentsMargins(10, 5, 10, 15)  # Add bottom margin
        header_layout.setSpacing(20)  # Add spacing between elements
        
        # Header container for title and subtitle
        header_text_container = QFrame()
        header_text_layout = QVBoxLayout(header_text_container)
        header_text_layout.setContentsMargins(0, 0, 0, 0)
        header_text_layout.setSpacing(5)
        
        # These labels will be populated later during animation
        self.header_label = QLabel()
        self.header_label.setFont(QFont('Helvetica', 14, QFont.Bold))
        self.header_label.setStyleSheet("color: #333333;")
        self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_text_layout.addWidget(self.header_label)
        
        # Subtitle in header
        self.header_subtitle = QLabel("Detect and analyze potential threats")
        self.header_subtitle.setFont(QFont('Helvetica', 10))
        self.header_subtitle.setStyleSheet("color: #666666;")
        header_text_layout.addWidget(self.header_subtitle)
        
        header_layout.addWidget(header_text_container, 7)  # Give more space to text
        
        # Button in header with appropriate size
        self.header_button = QPushButton()
        header_layout.addWidget(self.header_button, 3)  # Less space for button
        
        content_layout.addWidget(self.header_container)
        
        # Threat level container
        threat_container = QFrame()
        threat_layout = QVBoxLayout(threat_container)
        
        # Severity and detection labels
        self.severity_label = QLabel()
        self.severity_label.setFont(QFont('Helvetica', 14, QFont.Bold))
        self.severity_label.setAlignment(Qt.AlignCenter)
        threat_layout.addWidget(self.severity_label)
        
        self.recently_detected_label = QLabel()
        self.recently_detected_label.setFont(QFont('Helvetica', 11))
        self.recently_detected_label.setAlignment(Qt.AlignCenter)
        threat_layout.addWidget(self.recently_detected_label)
        
        content_layout.addWidget(threat_container)
        
        # Loading indicator
        self.loading_widget = QLabel()
        self.loading_movie = QMovie("drawable/loading.gif")
        self.loading_widget.setMovie(self.loading_movie)
        self.loading_widget.setAlignment(Qt.AlignCenter)
        self.loading_widget.setMaximumHeight(30)
        self.loading_widget.hide()
        content_layout.addWidget(self.loading_widget)
        
        # Plot container
        plot_container = QFrame()
        plot_container.setMinimumHeight(int(self.screen.height() * 0.35))
        plot_container.setMaximumHeight(int(self.screen.height() * 0.4))
        plot_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(15, 15, 15, 15)
        
        self.figure = Figure(figsize=(
            int(self.screen.width() * 0.008),
            int(self.screen.height() * 0.005)
        ), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        plot_layout.addWidget(self.canvas)
        
        content_layout.addWidget(plot_container)
        
        # Suspicious files section
        self.suspicious_files_label = QLabel()
        self.suspicious_files_label.setFont(QFont('Helvetica', 10))
        self.suspicious_files_label.setStyleSheet("color: #666666;")
        self.suspicious_files_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.suspicious_files_label)

        self.main_layout.addWidget(self.content_container)

    def start_detection(self):
        if not self.isAnimated:
            # First click - perform animation and show content
            self.animate_transition()
        else:
            # Subsequent clicks - normal detection process
            self.start_actual_detection()

    def animate_transition(self):
        # Get current geometry
        initial_rect = self.initial_container.geometry()
        self.isAnimated = True
        
        # Create a copy of the button and label for header
        btn_text = self.start_detection_btn.text()
        btn_style = self.start_detection_btn.styleSheet()
        self.header_button.setText(btn_text)
        self.header_button.setFixedSize(
            int(self.screen.width() * 0.14),  # Wider button
            int(self.screen.height() * 0.045)  # Slightly taller button
        )
        self.header_button.setFont(QFont('Helvetica', 12, QFont.Bold))  # Increased font size
        self.header_button.setStyleSheet(btn_style)
        self.header_button.clicked.connect(self.start_actual_detection)
        
        # Set the main title in header
        self.header_label.setText("Monitor Ransomware Activities")
        
        # Hide initial container and show content
        self.initial_container.hide()
        self.content_container.show()
        
        # Start actual detection
        self.start_actual_detection()

    def start_actual_detection(self):
        self.header_button.setEnabled(False)
        self.header_button.setText("Detection in Progress...")
        self.loading_widget.show()
        self.loading_movie.start()
        
        self.detection_worker = DetectionWorker()
        self.detection_worker.finished.connect(lambda results, severity: 
                                              self.on_detection_complete(results, severity))
        self.detection_worker.error.connect(self.on_detection_error)
        self.detection_worker.start()

    def on_detection_complete(self, results, severity):
        # Update UI with results
        severity_text, severity_color = severity
        self.severity_label.setText(f"THREAT LEVEL: {severity_text.upper()}")
        self.severity_label.setStyleSheet(f"""
            color: {severity_color};
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 5px 15px;
        """)
        
        # Update detection details
        detected_count = sum(results.values())
        self.recently_detected_label.setText(f"Detected Issues: {detected_count}")
        
        # List suspicious modules
        suspicious = [name for name, is_suspicious in results.items() if is_suspicious]
        if suspicious:
            self.suspicious_files_label.setText("Suspicious activities found in:\n" + "\n".join(suspicious))
        else:
            self.suspicious_files_label.setText("No suspicious activities detected")
        
        # Clean up
        self.loading_widget.hide()
        self.loading_movie.stop()
        self.header_button.setEnabled(True)
        self.header_button.setText("Start Detection")
        
        # Update plot
        self.update_detection_plot(results)

    def on_detection_error(self, error_msg):
        QMessageBox.critical(self, "Error", f"Detection failed: {error_msg}")
        self.loading_widget.hide()
        self.loading_movie.stop()
        self.header_button.setEnabled(True)
        self.header_button.setText("Start Detection")

    def update_detection_plot(self, results):
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Prepare data
            modules = list(results.keys())
            values = [1 if v else 0 for v in results.values()]
            colors = ['#F44336' if v else '#4CAF50' for v in results.values()]
            
            # Create bar plot with improved styling
            bars = ax.bar(modules, values, color=colors)
            plot_font_size = int(self.screen.height() * 0.006)  # Reduced from 0.008
            ax.set_ylabel('Status (0: Safe, 1: Suspicious)', fontsize=plot_font_size)
            ax.set_title('Detection Results by Module', fontsize=plot_font_size * 1.2, pad=20)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45, ha='right', fontsize=plot_font_size)
            plt.yticks(fontsize=plot_font_size)
            
            # Add value labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       'Suspicious' if height > 0 else 'Safe',
                       ha='center', va='bottom', fontsize=plot_font_size * 0.7)  # Reduced from 0.8
            
            # Adjust layout to prevent label cutoff
            plt.subplots_adjust(bottom=0.2)
            self.figure.tight_layout()
            self.canvas.draw()
            
            # Remove any previous Analysis Info buttons 
            for i in range(self.main_layout.count()):
                item = self.main_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, QPushButton) and "Analysis Info" in widget.text():
                        widget.deleteLater()
            
            # Add info button - no need to check for tab identity anymore
            info_btn = QPushButton("ℹ️ Analysis Info")
            info_btn.setFont(QFont('Helvetica', 11))
            info_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 15px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            info_btn.clicked.connect(lambda: self.show_analysis_info(results))
            
            # Add to layout
            existing_buttons = [i for i in range(self.main_layout.count()) 
                              if isinstance(self.main_layout.itemAt(i).widget(), QPushButton) 
                              and "Analysis Info" in self.main_layout.itemAt(i).widget().text()]
            
            if not existing_buttons:
                self.main_layout.addWidget(info_btn, alignment=Qt.AlignRight)
            
        except Exception as e:
            print(f"Error updating plot: {str(e)}")

    def show_analysis_info(self, results):
        dialog = QDialog(self)
        dialog.setWindowTitle("Detection Analysis Information")
        dialog.setMinimumSize(800, 800)  # Increased dialog size
        
        layout = QVBoxLayout(dialog)
        
        # Create text browser for rich text display
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 20px;
                font-size: 18px;  /* Increased from 12px */
            }
        """)
        
        # Generate analysis text with larger sizes
        analysis_text = """
            <h2 style='font-size: 28px; margin-bottom: 20px;'>
                Detection Analysis Details
            </h2>
        """
        
        for module, is_suspicious in results.items():
            analysis_text += f"""
                <h3 style='font-size: 22px; margin-top: 20px;'>
                    {module} Analysis:
                </h3>
            """
            if is_suspicious:
                analysis_text += f"""
                    <p style='color: #F44336; font-size: 20px;'>
                        <b>⚠️ Suspicious Activity Detected</b>
                    </p>
                    <div style='font-size: 18px;'>
                        {self.get_module_explanation(module)}
                    </div>
                """
            else:
                analysis_text += f"""
                    <p style='color: #4CAF50; font-size: 20px;'>
                        ✓ No suspicious activity detected
                    </p>
                """
            analysis_text += "<br>"
        
        text_browser.setHtml(analysis_text)
        layout.addWidget(text_browser)
        
        # Close button with increased size
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(120, 40)  # Increased button size
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: px;  /* Increased font size */
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        dialog.exec_()

    def get_module_explanation(self, module):
        explanations = {
            "Behavioral": """
                <ul style='font-size: 14px; line-height: 1.6;'>
                    <li>Suspicious file system operations detected</li>
                    <li>Unusual process behavior identified</li>
                    <li>Potential file encryption activities observed</li>
                </ul>
            """,
            "File System": """
                <ul>
                    <li>Multiple file modifications in short time</li>
                    <li>Suspicious file extension changes detected</li>
                    <li>Unusual file access patterns identified</li>
                </ul>
            """,
            "Net Traffic": """
                <ul>
                    <li>Communication with known malicious IPs detected</li>
                    <li>Suspicious data transfer patterns observed</li>
                    <li>Potential command & control traffic identified</li>
                </ul>
            """,
            "Registry": """
                <ul>
                    <li>Suspicious registry key modifications detected</li>
                    <li>Attempt to modify system settings identified</li>
                    <li>Persistence mechanism creation detected</li>
                </ul>
            """,
            "Process": """
                <ul>
                    <li>Suspicious process creation patterns detected</li>
                    <li>Unusual process injection attempts observed</li>
                    <li>Potential process hollowing identified</li>
                </ul>
            """,
            "API": """
                <ul>
                    <li>Suspicious API call sequences detected</li>
                    <li>Known malicious API usage patterns identified</li>
                    <li>Potential encryption API abuse observed</li>
                </ul>
            """,
            "Static": """
                <ul>
                    <li>Suspicious file signatures detected</li>
                    <li>Known malicious code patterns identified</li>
                    <li>Potential packing/obfuscation detected</li>
                </ul>
            """
        }
        return explanations.get(module, "<p style='font-size: 14px;'>No detailed information available for this module.</p>")

    def start_periodic_detection(self):
        """
        Modified version of start_actual_detection that returns detection results
        for use with periodic scanning.
        """
        # Create a dictionary to store detection results
        detection_results = {}
        
        # Create and start the worker
        detection_worker = DetectionWorker()
        
        # Create a local event loop to make this function synchronous
        from PyQt5.QtCore import QEventLoop
        loop = QEventLoop()
        
        # Connect signals
        detection_worker.finished.connect(lambda results, severity: 
                                        self._handle_periodic_detection_results(results, severity, detection_results, loop))
        detection_worker.error.connect(lambda err: self._handle_periodic_detection_error(err, loop))
        
        # Start the worker
        detection_worker.start()
        
        # Wait for detection to complete
        loop.exec_()
        
        # Return the detection results
        return detection_results

    def _handle_periodic_detection_results(self, results, severity, detection_results, loop):
        """Helper method to process detection results for periodic scanning"""
        severity_text, severity_color = severity
        
        # Store detection information
        detection_results['results'] = results
        detection_results['threat_level'] = severity_text
        detection_results['severity_color'] = severity_color
        
        # Get list of suspicious modules/files
        detected_files = []
        for name, is_suspicious in results.items():
            if is_suspicious:
                detected_files.append(f"{name} module")
        
        # Check for any suspicious files in test_data directory
        try:
            import os
            suspicious_extensions = ['.locked', '.encrypted', '.crypto', '.crypt', '.crypted']
            for root, _, files in os.walk('test_data'):
                for file in files:
                    if any(file.endswith(ext) for ext in suspicious_extensions):
                        detected_files.append(os.path.join(root, file))
        except:
            pass
        
        # Add detected files to results
        detection_results['detected_files'] = detected_files
        
        # Update internal state if needed
        # ...
        
        # Exit the loop to continue execution
        loop.quit()

    def _handle_periodic_detection_error(self, error_msg, loop):
        """Helper method to handle detection errors for periodic scanning"""
        print(f"Periodic detection error: {error_msg}")
        # Exit the loop to continue execution
        loop.quit()

    def display_system_info(self):
        """Display system information obtained from WMI"""
        try:
            system_info = get_system_info_wmi()
            if not system_info:
                self.show_status_message("Could not retrieve system information", "error")
                return
                
            # Create a formatted display of system information
            info_text = f"""
<h3>System Information</h3>
<p><b>OS:</b> {system_info['os_name']} {system_info['os_version']} ({system_info['os_arch']})</p>
<p><b>Computer Name:</b> {system_info['computer_name']}</p>
<p><b>CPU:</b> {system_info['cpu_name']}</p>
<p><b>CPU Cores:</b> {system_info['cpu_cores']} (Logical: {system_info['cpu_threads']})</p>
<p><b>Memory:</b> {system_info['total_memory_gb']} GB</p>
<p><b>Last Boot Time:</b> {system_info['last_boot']}</p>
"""
            
            # Display in your UI (you'll need to adapt this to your actual UI components)
            # For example, if you have a QTextBrowser named system_info_display:
            if hasattr(self, 'system_info_display'):
                self.system_info_display.setHtml(info_text)
            else:
                self.show_status_message("System information retrieved successfully", "success")
                
        except Exception as e:
            self.show_status_message(f"Error retrieving system information: {str(e)}", "error")

    def start_real_time_monitoring(self):
        """Start real-time monitoring of processes and files"""
        try:
            # Start monitoring in separate threads
            self.monitoring_active = True
            
            # Start process monitoring
            self.process_monitor_thread = threading.Thread(
                target=self._process_monitoring_thread,
                daemon=True
            )
            self.process_monitor_thread.start()
            
            # Start file monitoring for selected directories
            self.monitored_directories = ["test_data"]  # Add more as needed
            self.file_monitor_threads = {}
            
            for directory in self.monitored_directories:
                if os.path.exists(directory):
                    thread = threading.Thread(
                        target=self._file_monitoring_thread,
                        args=(directory,),
                        daemon=True
                    )
                    thread.start()
                    self.file_monitor_threads[directory] = thread
                    
            self.show_status_message("Real-time monitoring started", "success")
            return True
            
        except Exception as e:
            self.show_status_message(f"Error starting monitoring: {str(e)}", "error")
            return False

    def _process_monitoring_thread(self):
        """Background thread for process monitoring"""
        while getattr(self, "monitoring_active", False):
            try:
                # Monitor for 60 seconds, then restart
                monitor_process_creation(self._on_process_detected, duration=60)
            except Exception as e:
                print(f"Process monitoring error: {e}")
            time.sleep(1)  # Short pause between monitoring cycles

    def _file_monitoring_thread(self, directory):
        """Background thread for file monitoring"""
        while getattr(self, "monitoring_active", False):
            try:
                # Monitor for 120 seconds, then restart
                monitor_file_changes(directory, self._on_file_changed, duration=120)
            except Exception as e:
                print(f"File monitoring error for {directory}: {e}")
            time.sleep(1)  # Short pause between monitoring cycles

    def _on_process_detected(self, process_info):
        """Handler for new process detection"""
        process_name = process_info.get("name", "Unknown")
        process_id = process_info.get("pid", 0)
        
        # Log the new process
        self.log_activity(f"New process: {process_name} (PID: {process_id})")
        
        # Check for suspicious processes
        suspicious_keywords = ["ransomware", "encrypt", "crypt", "locker"]
        if any(keyword in process_name.lower() for keyword in suspicious_keywords):
            self.log_activity(f"SUSPICIOUS PROCESS DETECTED: {process_name}", level="warning")
            # Add to suspicious processes list in UI
            self.add_suspicious_process(process_info)
            
    def _on_file_changed(self, file_event):
        """Handler for file change events"""
        event_type = file_event.get("event", "").lower()
        file_path = file_event.get("path", "")
        file_name = file_event.get("file", "")
        
        # Log the file event
        self.log_activity(f"File {event_type}: {file_path}")
        
        # Check for suspicious extensions
        _, ext = os.path.splitext(file_name)
        suspicious_extensions = ['.locked', '.encrypted', '.crypt', '.crypto']
        
        if ext.lower() in suspicious_extensions:
            self.log_activity(f"SUSPICIOUS FILE DETECTED: {file_path} ({ext})", level="warning")
            # Add to suspicious files list in UI
            self.add_suspicious_file({
                "path": file_path,
                "name": file_name,
                "event": event_type,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
