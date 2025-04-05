from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QFrame, QComboBox, QDateEdit, QTimeEdit,
                           QCheckBox, QFileDialog, QScrollArea, QGroupBox,
                           QFormLayout, QSpinBox, QTabWidget, QProgressBar,
                           QGraphicsDropShadowEffect, QTableWidget, QHeaderView,
                           QApplication, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt, QDate, QTime, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
import os
import json
from datetime import datetime, timedelta
import time

class ReportTab(QWidget):
    """Tab for generating and viewing comprehensive reports"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create preview_area first so it exists before we try to access it
        self.preview_area = QTableWidget()
        self.preview_area.setColumnCount(4)
        self.preview_area.setHorizontalHeaderLabels([
            "Time", "Type", "Details", "Status"
        ])
        self.preview_area.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.preview_area.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        self.preview_area.setMinimumHeight(200)
        
        # Now initialize the UI
        self.initUI()
        
    def initUI(self):
        # Main layout with scroll area for better responsiveness
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(20)

        # Add this to force minimum width
        scroll_content.setMinimumWidth(800)
        
        # After adding all widgets to scroll_layout, add this:
        scroll_layout.addStretch()  # Add this line to push content to top
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Make sure the preview area has a minimum height
        self.preview_area.setMinimumHeight(200)  # Add this line where preview_area is created
        
        # Make sure content is visible initially
        QTimer.singleShot(100, self.preview_area.resizeRowsToContents)

        # Header with Title and Description
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(10)
        
        title = QLabel("Report Generation")
        title.setFont(QFont('Helvetica', 22, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        
        scroll_layout.addWidget(header)
        
        # ===== REPORT OPTIONS SECTION =====
        options_section = QFrame()
        options_section.setObjectName("optionsCard")
        options_section.setStyleSheet("""
            QFrame#optionsCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        options_section.setGraphicsEffect(shadow)
        
        options_layout = QVBoxLayout(options_section)
        options_layout.setContentsMargins(20, 20, 20, 20)
        
        # Section Title
        options_title = QLabel("Report Options")
        options_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        options_title.setStyleSheet("color: #333333; margin-bottom: 10px;")
        options_layout.addWidget(options_title)
        
        # Form Content
        form_content = QFrame()
        form_content.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        form_layout = QFormLayout(form_content)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(15)
        
        # Report Type
        form_layout.addRow(QLabel("<b>Report Type:</b>"))
        
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Comprehensive System Report",
            "Threat Detection Summary",
            "MTD Activity Report",
            "System Performance Analysis"
        ])
        self.report_type.setMinimumHeight(40)
        self.report_type.setFont(QFont('Helvetica', 12))
        self.report_type.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #e0e0e0;
            }
        """)
        form_layout.addRow(self.report_type)
        
        # Time Range Group
        time_range_group = QGroupBox("Time Range")
        time_range_group.setFont(QFont('Helvetica', 12))
        time_range_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
                margin-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: #1976D2;
            }
        """)
        
        time_layout = QVBoxLayout(time_range_group)
        
        # Time range presets
        presets_layout = QHBoxLayout()
        
        self.preset_day = QPushButton("Last 24 Hours")
        self.preset_week = QPushButton("Last Week")
        self.preset_month = QPushButton("Last Month")
        self.preset_custom = QPushButton("Custom Range")
        
        for btn in [self.preset_day, self.preset_week, self.preset_month, self.preset_custom]:
            btn.setCheckable(True)
            btn.setMinimumHeight(35)
            btn.setFont(QFont('Helvetica', 11))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:checked {
                    background-color: #2196F3;
                    color: white;
                    border: 1px solid #1976D2;
                }
                QPushButton:hover:!checked {
                    background-color: #e0e0e0;
                }
            """)
            presets_layout.addWidget(btn)
        
        self.preset_day.setChecked(True)
        time_layout.addLayout(presets_layout)
        
        # Custom date/time range
        custom_range = QFrame()
        custom_range_layout = QHBoxLayout(custom_range)
        
        # Start date/time
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start Date:"))
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-1))
        self.start_date.setMinimumHeight(35)
        self.start_date.setStyleSheet("""
            QDateEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                padding: 5px;
            }
        """)
        start_layout.addWidget(self.start_date)
        
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime.currentTime())
        self.start_time.setMinimumHeight(35)
        self.start_time.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                padding: 5px;
            }
        """)
        start_layout.addWidget(self.start_time)
        
        custom_range_layout.addLayout(start_layout)
        
        # End date/time
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End Date:"))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setMinimumHeight(35)
        self.end_date.setStyleSheet("""
            QDateEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                padding: 5px;
            }
        """)
        end_layout.addWidget(self.end_date)
        
        end_layout.addWidget(QLabel("End Time:"))
        
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime.currentTime())
        self.end_time.setMinimumHeight(35)
        self.end_time.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                background-color: white;
                padding: 5px;
            }
        """)
        end_layout.addWidget(self.end_time)
        
        custom_range_layout.addLayout(end_layout)
        
        custom_range.setVisible(False)
        self.preset_custom.clicked.connect(lambda: custom_range.setVisible(True))
        for btn in [self.preset_day, self.preset_week, self.preset_month]:
            btn.clicked.connect(lambda: custom_range.setVisible(False))
        
        time_layout.addWidget(custom_range)
        form_layout.addRow(time_range_group)
        
        # Report Content Options
        content_group = QGroupBox("Content Options")
        content_group.setFont(QFont('Helvetica', 12))
        content_group.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
                margin-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: #1976D2;
            }
        """)
        
        content_layout = QVBoxLayout(content_group)
        
        self.include_threats = QCheckBox("Include Threat Detections")
        self.include_charts = QCheckBox("Include Visual Charts")
        self.include_mtd = QCheckBox("Include MTD Activities")
        self.include_sys_info = QCheckBox("Include System Information")
        
        # Set defaults
        self.include_threats.setChecked(True)
        self.include_charts.setChecked(True)
        self.include_mtd.setChecked(True)
        self.include_sys_info.setChecked(True)
        
        # Style checkboxes
        for cb in [self.include_threats, self.include_charts, self.include_mtd, self.include_sys_info]:
            cb.setFont(QFont('Helvetica', 11))
            cb.setStyleSheet("""
                QCheckBox {
                    spacing: 10px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    border: 1px solid #e0e0e0;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    border: 1px solid #2196F3;
                    background-color: #2196F3;
                }
            """)
            content_layout.addWidget(cb)
        
        form_layout.addRow(content_group)
        
        # Report Format
        form_layout.addRow(QLabel("<b>Report Format:</b>"))
        
        self.report_format = QComboBox()
        self.report_format.addItems(["PDF", "HTML", "Text"])
        self.report_format.setMinimumHeight(40)
        self.report_format.setFont(QFont('Helvetica', 12))
        self.report_format.setStyleSheet("""
            QComboBox {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px 15px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #e0e0e0;
            }
        """)
        form_layout.addRow(self.report_format)
        
        options_layout.addWidget(form_content)
        
        # Generate Report Button
        generate_btn = QPushButton("Generate Report")
        generate_btn.setMinimumHeight(85)  # Increased from 50 to 80
        generate_btn.setFont(QFont('Helvetica', 14, QFont.Bold))  # Increased font size from 14 to 16
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 25px;  /* Increased padding */
                margin-top: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        generate_btn.clicked.connect(self.generate_report)
        options_layout.addWidget(generate_btn)
        
        scroll_layout.addWidget(options_section)
        
        # ===== REPORT PREVIEW SECTION =====
        preview_section = QFrame()
        preview_section.setObjectName("previewCard")
        preview_section.setStyleSheet("""
            QFrame#previewCard {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Add drop shadow
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(15)
        shadow2.setColor(QColor(0, 0, 0, 30))
        shadow2.setOffset(0, 2)
        preview_section.setGraphicsEffect(shadow2)
        
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setContentsMargins(20, 20, 20, 20)
        
        # Preview header
        preview_header = QHBoxLayout()
        
        preview_title = QLabel("Report Preview")
        preview_title.setFont(QFont('Helvetica', 16, QFont.Bold))
        preview_title.setStyleSheet("color: #333333;")
        preview_header.addWidget(preview_title)
        
        # Export & Print buttons
        btn_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export Report")
        export_btn.setFont(QFont('Helvetica', 11))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        export_btn.clicked.connect(self.export_report)
        btn_layout.addWidget(export_btn)
        
        preview_header.addLayout(btn_layout)
        preview_layout.addLayout(preview_header)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                text-align: center;
                background-color: #f5f5f5;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 5px;
            }
        """)
        self.progress_bar.hide()
        preview_layout.addWidget(self.progress_bar)
        
        # Preview content area
        preview_layout.addWidget(self.preview_area)
        
        scroll_layout.addWidget(preview_section)
        
        main_layout.addWidget(scroll_area)
        scroll_area.setWidget(scroll_content)
        
    def generate_report(self):
        """Generate the report based on selected options"""
        # Show progress bar
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Clear existing data
        self.preview_area.setRowCount(0)
        
        # Get selected options
        report_type = self.report_type.currentText()
        
        # Get time range
        if self.preset_custom.isChecked():
            start_date = self.start_date.date().toString("yyyy-MM-dd")
            start_time = self.start_time.time().toString("hh:mm:ss")
            end_date = self.end_date.date().toString("yyyy-MM-dd")
            end_time = self.end_time.time().toString("hh:mm:ss")
            time_range = f"{start_date} {start_time} to {end_date} {end_time}"
        else:
            if self.preset_day.isChecked():
                time_range = "Last 24 Hours"
            elif self.preset_week.isChecked():
                time_range = "Last Week"
            else:
                time_range = "Last Month"

        # Simulate data generation with progress updates
        total_steps = 100
        current_step = 0
        
        # Sample data - in a real app, this would come from your detection system
        sample_data = [
            {"time": "2023-12-20 10:30:00", "type": "File Scan", "details": "Scanned system files", "status": "Complete"},
            {"time": "2023-12-20 10:35:00", "type": "Threat Detection", "details": "Suspicious file found", "status": "Warning"},
            {"time": "2023-12-20 10:40:00", "type": "MTD Action", "details": "File paths rotated", "status": "Success"},
            {"time": "2023-12-20 10:45:00", "type": "System Check", "details": "Memory analysis", "status": "Normal"},
            {"time": "2023-12-20 10:50:00", "type": "Network Scan", "details": "Port scanning complete", "status": "Complete"}
        ]
        
        # Update progress as we add rows
        for row, data in enumerate(sample_data):
            # Add row to table
            self.preview_area.insertRow(row)
            
            # Add items with appropriate styling
            time_item = QTableWidgetItem(data["time"])
            type_item = QTableWidgetItem(data["type"])
            details_item = QTableWidgetItem(data["details"])
            status_item = QTableWidgetItem(data["status"])
            
            # Color code status
            if data["status"] == "Warning":
                status_item.setForeground(QColor("#FFA000"))  # Orange for warning
            elif data["status"] == "Success":
                status_item.setForeground(QColor("#4CAF50"))  # Green for success
            elif data["status"] == "Complete":
                status_item.setForeground(QColor("#2196F3"))  # Blue for complete
                
            # Set items
            self.preview_area.setItem(row, 0, time_item)
            self.preview_area.setItem(row, 1, type_item)
            self.preview_area.setItem(row, 2, details_item)
            self.preview_area.setItem(row, 3, status_item)
            
            # Update progress
            current_step += (100 // len(sample_data))
            self.progress_bar.setValue(min(current_step, 100))
            QApplication.processEvents()
            
        # Finish progress
        self.progress_bar.setValue(100)
        QTimer.singleShot(500, lambda: self.progress_bar.hide())
        
        # Auto-size rows for better readability
        self.preview_area.resizeRowsToContents()
        
    def export_report(self):
        """Export the generated report"""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            os.path.join(os.path.expanduser("~"), "Documents", f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "PDF Files (*.pdf);;HTML Files (*.html);;Text Files (*.txt)"
        )
        
        if not file_path:
            return  # User cancelled the dialog
            
        # Add file extension if missing
        if "PDF" in selected_filter and not file_path.lower().endswith('.pdf'):
            file_path += '.pdf'
        elif "HTML" in selected_filter and not file_path.lower().endswith('.html'):
            file_path += '.html'
        elif "Text" in selected_filter and not file_path.lower().endswith('.txt'):
            file_path += '.txt'
        
        # Show progress bar
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        try:
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            
            # Get report data
            report_type = self.report_type.currentText()
            
            # Get time range info
            if self.preset_custom.isChecked():
                time_range = f"{self.start_date.date().toString('yyyy-MM-dd')} to {self.end_date.date().toString('yyyy-MM-dd')}"
            else:
                if self.preset_day.isChecked():
                    time_range = "Last 24 Hours"
                elif self.preset_week.isChecked():
                    time_range = "Last Week"
                else:
                    time_range = "Last Month"
            
            # Create different report formats based on selection
            if file_path.lower().endswith('.pdf'):
                self.create_pdf_report(file_path, report_type, time_range)
            elif file_path.lower().endswith('.html'):
                self.create_html_report(file_path, report_type, time_range)
            else:
                self.create_text_report(file_path, report_type, time_range)
                
            # Show success message
            QMessageBox.information(self, "Export Successful", f"Report saved successfully to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while saving the report:\n{str(e)}")
        finally:
            # Hide progress bar when done
            self.progress_bar.setValue(100)
            QTimer.singleShot(500, lambda: self.progress_bar.hide())
    
    def create_pdf_report(self, file_path, report_type, time_range):
        """Create a PDF report using ReportLab"""
        try:
            # First, let's make sure we have reportlab installed
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            except ImportError:
                # If reportlab is not installed, show a message and save as text instead
                QMessageBox.warning(
                    self, 
                    "PDF Generation",
                    "ReportLab library not found. Installing required dependencies...\n\n"
                    "Please wait while we install the necessary packages."
                )
                
                # Attempt to install reportlab
                import subprocess
                import sys
                
                # Show installation progress
                for i in range(0, 50):
                    self.progress_bar.setValue(i)
                    QApplication.processEvents()
                    time.sleep(0.02)
                    
                subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
                
                # Now try importing again
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                
                # Update progress after installation
                self.progress_bar.setValue(60)
                QApplication.processEvents()
            
            # Use reportlab to create a PDF file
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []
            
            # Set up styles
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            title_style.alignment = 1  # Center alignment
            
            subtitle_style = styles['Heading2']
            
            # Add title
            elements.append(Paragraph(report_type, title_style))
            elements.append(Spacer(1, 12))
            
            # Add time range
            elements.append(Paragraph(f"Time Range: {time_range}", styles['Normal']))
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 24))
            
            # Create table data
            table_data = []
            
            # Add headers
            headers = []
            for col in range(self.preview_area.columnCount()):
                headers.append(self.preview_area.horizontalHeaderItem(col).text())
            table_data.append(headers)
            
            # Add rows
            for row in range(self.preview_area.rowCount()):
                row_data = []
                for col in range(self.preview_area.columnCount()):
                    item = self.preview_area.item(row, col)
                    row_data.append(item.text() if item else "")
                table_data.append(row_data)
            
            # Create table
            table = Table(table_data, repeatRows=1)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            
            # Show progress as we build the PDF
            self.progress_bar.setValue(75)
            QApplication.processEvents()
            
            # Build the PDF file
            doc.build(elements)
            
            # Finish progress
            self.progress_bar.setValue(100)
            QApplication.processEvents()
            
        except Exception as e:
            raise Exception(f"PDF creation failed: {str(e)}")
    
    def create_html_report(self, file_path, report_type, time_range):
        """Create an HTML report"""
        try:
            # Simulate HTML creation with progress updates
            for i in range(101):
                self.progress_bar.setValue(i)
                QApplication.processEvents()
                time.sleep(0.01)
                
            # Create simple HTML report
            with open(file_path, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{report_type}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #1976D2; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ text-align: left; padding: 12px; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>{report_type}</h1>
    <p><b>Time Range:</b> {time_range}</p>
    <p><b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Report Data</h2>
    <table border="1">
        <tr>
            <th>Time</th>
            <th>Type</th>
            <th>Details</th>
            <th>Status</th>
        </tr>
""")
                
                # Add table data
                for row in range(self.preview_area.rowCount()):
                    f.write("<tr>")
                    for col in range(self.preview_area.columnCount()):
                        item = self.preview_area.item(row, col)
                        text = item.text() if item else ""
                        f.write(f"<td>{text}</td>")
                    f.write("</tr>\n")
                
                f.write("""
    </table>
</body>
</html>
""")
        except Exception as e:
            raise Exception(f"HTML creation failed: {str(e)}")
    
    def create_text_report(self, file_path, report_type, time_range):
        """Create a plain text report"""
        try:
            # Simulate text file creation with progress updates
            for i in range(101):
                self.progress_bar.setValue(i)
                QApplication.processEvents()
                time.sleep(0.01)
                
            # Write simple text report
            with open(file_path, 'w') as f:
                f.write(f"REPORT: {report_type}\n")
                f.write(f"Time Range: {time_range}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n" + "="*50 + "\n\n")
                
                # Add headers
                headers = []
                for col in range(self.preview_area.columnCount()):
                    headers.append(self.preview_area.horizontalHeaderItem(col).text())
                f.write(" | ".join(headers) + "\n")
                f.write("-" * 60 + "\n")
                
                # Add table data
                for row in range(self.preview_area.rowCount()):
                    row_data = []
                    for col in range(self.preview_area.columnCount()):
                        item = self.preview_area.item(row, col)
                        row_data.append(item.text() if item else "")
                    f.write(" | ".join(row_data) + "\n")
        except Exception as e:
            raise Exception(f"Text file creation failed: {str(e)}")